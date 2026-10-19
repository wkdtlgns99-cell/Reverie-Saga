"""Retrieve self-activity through verified, isolated replay of retained save events."""

from dataclasses import dataclass
from typing import Literal

from app.headless import HeadlessSession, restore_checkpoint, state_io
from app.npc_memory import memory_bundle
from contracts.dialogue import QuestContent
from contracts.persistence import DurableCheckpoint, SaveError, SaveSegment
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot, TurnDriver, TurnPublication
from contracts.watch import NpcActed, WatchReplied
from domain.state_types import CoreSnapshot
from orchestration.replay import Runner


@dataclass(frozen=True, slots=True)
class NpcActivity:
    kind: Literal["bell", "reply"]
    tick: int
    event_id: str
    count: int

    def text(self) -> str:
        action = "종을 울렸습니다" if self.kind == "bell" else "호출에 응답했습니다"
        return f"NPC 활동 기록 · {self.tick}초: {action}. (누적 {self.count}회)"


class _ActivitySession:
    def __init__(self, session: HeadlessSession, factory: "_ActivityFactory") -> None:
        self._session, self._factory = session, factory

    @property
    def driver(self) -> TurnDriver:
        return self._session.driver

    def snapshot(self) -> CoreSnapshot:
        return self._session.snapshot()

    def protocol(self) -> ProtocolSnapshot:
        return self._session.protocol()

    def last_publication(self) -> TurnPublication:
        publication = self._session.last_publication()
        entries = self._factory.entries
        for event in publication.facts:
            payload = event.payload
            if (
                isinstance(payload, (NpcActed, WatchReplied))
                and payload.npc_id == self._factory.npc_id
            ):
                entries.append(
                    NpcActivity(
                        "bell" if isinstance(payload, NpcActed) else "reply",
                        event.due_tick,
                        event.header.event_id,
                        payload.after_bells
                        if isinstance(payload, NpcActed)
                        else payload.after_count,
                    )
                )
        entries.sort(key=lambda entry: (-entry.tick, entry.event_id))
        del entries[8:]
        return publication


class _ActivityFactory:
    def __init__(self, content: QuestContent, npc_id: str) -> None:
        self.bundles = (memory_bundle(content),)
        self.npc_id = npc_id
        self.entries: list[NpcActivity] = []
        self.session: HeadlessSession | None = None

    def restore(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplaySession:
        self.session = restore_checkpoint(core, protocol, bundles=self.bundles)
        return _ActivitySession(self.session, self)


def recent_activity(
    segment: SaveSegment, npc_id: str, *, content: QuestContent, current: DurableCheckpoint
) -> tuple[NpcActivity, ...]:
    """Publish only after the canonical runner verifies every retained step.

    Saves retain compact hashes, not full event bodies. Replay uses a separate
    in-memory session with no durable port and never touches the live attachment.
    """
    factory = _ActivityFactory(content, npc_id)
    runner = Runner(
        segment.checkpoint.core,
        segment.checkpoint.protocol,
        factory=factory,
        io=state_io(factory.bundles),
    )
    if runner.run(segment.trace):
        raise SaveError("NPC_ACTIVITY_SOURCE", "retained activity replay mismatch")
    session = factory.session
    if session is None or (
        session.snapshot() != current.core or session.protocol() != current.protocol
    ):
        raise SaveError("NPC_ACTIVITY_SOURCE", "activity source differs from live attachment")
    return tuple(factory.entries)
