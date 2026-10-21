"""Retrieve self-activity through verified, isolated replay of retained save events."""

from dataclasses import dataclass
from typing import Literal

from app.headless import HeadlessSession, restore_checkpoint, state_io
from app.npc_memory import memory_bundle
from app.npc_memory_query import player_memory_recollection
from app.npc_work import stock_text, work_bundle
from contracts.npc_work import ProvisionPrepared
from contracts.messages import WorldEvent
from contracts.quest import QuestSpoken
from contracts.errors import ReplayFormatError
from contracts.dialogue import QuestContent
from contracts.persistence import DurableCheckpoint, SaveError, SaveSegment
from contracts.replay import ReplaySession
from contracts.turn import ProtocolSnapshot, TurnDriver, TurnPublication
from contracts.watch import NpcActed, WatchEcho, WatchReplied, WatchRequested
from domain.state_types import CoreSnapshot
from domain.npc_work import STOCK_CAP, ProvisionsRecord
from domain.npc_memory import NpcQuestMemoryRecord
from domain.watch import ECHO_DEPTH
from orchestration.replay import Runner

_CALL_LIMIT = 3


@dataclass(frozen=True, slots=True)
class NpcActivity:
    kind: Literal["bell", "reply", "provision"]
    tick: int
    event_id: str
    count: int

    def text(self) -> str:
        if self.kind == "provision":
            return f"NPC 활동 기록 · {self.tick}초: 공동 비축 물자 1개를 준비했습니다. (재고 {self.count}/{STOCK_CAP}개)"
        action = "종을 울렸습니다" if self.kind == "bell" else "호출에 응답했습니다"
        return f"NPC 활동 기록 · {self.tick}초: {action}. (누적 {self.count}회)"


@dataclass(frozen=True, slots=True)
class _AnsweredCall:
    request: WorldEvent
    reply: WorldEvent


def _answered_call(
    reply: WorldEvent, facts: tuple[WorldEvent, ...], actor_id: str
) -> _AnsweredCall:
    """Follow causal identities;simultaneous events alone never establish a caller."""
    events = {event.header.event_id: event for event in facts}
    current = reply
    for _ in range(ECHO_DEPTH + 2):
        causes = current.header.caused_by
        parent = events.get(causes[0]) if len(causes) == 1 else None
        if parent is None or parent.due_tick != reply.due_tick:
            break
        payload = parent.payload
        if isinstance(payload, WatchRequested):
            if (
                isinstance(reply.payload, WatchReplied)
                and payload.npc_id == reply.payload.npc_id
                and payload.actor_id == actor_id
            ):
                return _AnsweredCall(parent, reply)
            break
        if not (
            isinstance(payload, WatchEcho)
            and isinstance(reply.payload, WatchReplied)
            and payload.npc_id == reply.payload.npc_id
        ):
            break
        current = parent
    raise SaveError("NPC_RECOLLECTION_SOURCE", "response lacks a retained player call chain")


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
        if self._factory.collect_calls:
            for event in publication.facts:
                if (
                    isinstance(event.payload, WatchReplied)
                    and event.payload.npc_id == self._factory.npc_id
                ):
                    call = _answered_call(event, publication.facts, self._factory.actor_id)
                    self._factory.calls.append(call)
                    self._factory.call_count += 1
            self._factory.calls.sort(
                key=lambda call: (call.reply.due_tick, call.reply.header.event_id)
            )
            del self._factory.calls[:-_CALL_LIMIT]
        for event in publication.facts:
            payload = event.payload
            if isinstance(payload, QuestSpoken) and payload.npc_id == self._factory.npc_id:
                self._factory.conversations.append((event.due_tick, event.header.event_id))
                del self._factory.conversations[:-2]
                self._factory.conversation_counts.append(self._factory.call_count)
                del self._factory.conversation_counts[:-2]
            if (
                isinstance(payload, (NpcActed, WatchReplied, ProvisionPrepared))
                and payload.npc_id == self._factory.npc_id
            ):
                entry = NpcActivity(
                    "bell"
                    if isinstance(payload, NpcActed)
                    else "reply"
                    if isinstance(payload, WatchReplied)
                    else "provision",
                    event.due_tick,
                    event.header.event_id,
                    payload.after_bells
                    if isinstance(payload, NpcActed)
                    else payload.after_count
                    if isinstance(payload, WatchReplied)
                    else payload.after,
                )
                entries.append(entry)
                if isinstance(payload, ProvisionPrepared):
                    self._factory.work_entries.append(entry)
                    self._factory.work_entries.sort(key=lambda value: (value.tick, value.event_id))
                    del self._factory.work_entries[:-STOCK_CAP]
        entries.sort(key=lambda entry: (-entry.tick, entry.event_id))
        del entries[8:]
        return publication


class _ActivityFactory:
    def __init__(
        self, content: QuestContent, npc_id: str, *, npc_work: bool, collect_calls: bool = False
    ) -> None:
        self.bundles = (work_bundle(content) if npc_work else memory_bundle(content),)
        self.npc_id = npc_id
        self.actor_id = content.definition.layout.actor_id
        self.collect_calls = collect_calls
        self.calls: list[_AnsweredCall] = []
        self.call_count = 0
        self.conversation_counts: list[int] = []
        self.entries: list[NpcActivity] = []
        self.work_entries: list[NpcActivity] = []
        self.conversations: list[tuple[int, str]] = []
        self.session: HeadlessSession | None = None

    def restore(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> ReplaySession:
        self.session = restore_checkpoint(core, protocol, bundles=self.bundles)
        return _ActivitySession(self.session, self)


def recent_activity(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    npc_work: bool = False,
) -> tuple[NpcActivity, ...]:
    """Publish only after the canonical runner verifies every retained step.

    Saves retain compact hashes, not full event bodies. Replay uses a separate
    in-memory session with no durable port and never touches the live attachment.
    """
    factory = _verified_activity(
        segment,
        npc_id,
        content=content,
        current=current,
        npc_work=npc_work,
        error_code="NPC_ACTIVITY_SOURCE",
    )
    return tuple(factory.entries)


def activity_messages(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    npc_work: bool = False,
) -> tuple[str, ...]:
    """Keep retained work separate from frequent bells;never infer lost events."""
    if npc_id != content.definition.layout.npc_id:
        raise SaveError("NPC_ACTIVITY_SOURCE", "activity owner differs from selected NPC")
    try:
        factory = _verified_activity(
            segment,
            npc_id,
            content=content,
            current=current,
            npc_work=npc_work,
            error_code="NPC_ACTIVITY_SOURCE",
        )
    except ReplayFormatError as error:
        raise SaveError("NPC_ACTIVITY_SOURCE", "retained activity format mismatch") from error
    messages = tuple(entry.text() for entry in reversed(factory.entries)) or (
        "현재 저장 구간에 남은 NPC 자기 활동이 없습니다.",
    )
    if not npc_work:
        return messages
    stocks = tuple(
        record
        for record in current.core.components
        if isinstance(record, ProvisionsRecord) and record.entity_id == npc_id
    )
    if len(stocks) != 1:
        raise SaveError("NPC_ACTIVITY_SOURCE", "activity requires selected NPC provisions")
    return (
        *messages,
        f"NPC 비축 작업 · {segment.checkpoint.core.tick}초 이후 저장 기록에서 확인했습니다.",
        *(
            tuple(
                f"NPC 비축 작업 · {entry.tick}초: +1개 (당시 {entry.count}/{STOCK_CAP}개)"
                for entry in factory.work_entries
            )
            or (
                "현재 저장 구간에 남은 비축 작업 기록이 없습니다. "
                "재고로 과거 작업을 추정하지 않습니다.",
            )
        ),
        stock_text(stocks[0].stock),
    )


def _verified_activity(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    npc_work: bool,
    error_code: str,
    collect_calls: bool = False,
) -> _ActivityFactory:
    factory = _ActivityFactory(content, npc_id, npc_work=npc_work, collect_calls=collect_calls)
    runner = Runner(
        segment.checkpoint.core,
        segment.checkpoint.protocol,
        factory=factory,
        io=state_io(factory.bundles),
    )
    if runner.run(segment.trace):
        raise SaveError(error_code, "retained activity replay mismatch")
    session = factory.session
    if session is None or (
        session.snapshot() != current.core or session.protocol() != current.protocol
    ):
        raise SaveError(error_code, "activity source differs from live attachment")
    return factory


def work_recollection(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    conversation_id: str,
) -> tuple[str, ...]:
    """Derive only retained own work after the previous committed conversation.

    A retained checkpoint may already contain stock,with no surviving production
    facts. Neither stock nor periodic rules are evidence of those missing events.
    """
    factory = _conversation_activity(
        segment, npc_id, content=content, current=current, conversation_id=conversation_id
    )
    return _work_lines(factory, segment, current)


def return_recollection(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    conversation_id: str,
) -> tuple[str, ...]:
    """Recall own work and answered player calls through one verified source replay."""
    factory = _conversation_activity(
        segment,
        npc_id,
        content=content,
        current=current,
        conversation_id=conversation_id,
        collect_calls=True,
    )
    previous = factory.conversations[-2][0] if len(factory.conversations) > 1 else None
    lower_bound = segment.checkpoint.core.tick if previous is None else previous
    count = factory.call_count - (factory.conversation_counts[-2] if previous is not None else 0)
    calls = tuple(call for call in factory.calls if call.reply.due_tick > lower_bound)
    session = factory.session
    if session is None:
        raise RuntimeError("verified recollection requires a restored session")
    memories = tuple(
        record
        for record in session.snapshot().components
        if isinstance(record, NpcQuestMemoryRecord) and record.entity_id == npc_id
    )
    if len(memories) != 1:
        raise SaveError("NPC_RECOLLECTION_SOURCE", "recollection requires selected NPC memory")
    heading = (
        "NPC 호출 회상 · 현재 저장 구간에서 확인한 응답입니다."
        if previous is None
        else f"NPC 호출 회상 · 지난 대화({previous}초) 뒤에 끝낸 응답입니다."
    )
    return (
        *_work_lines(factory, segment, current),
        heading,
        *(
            (
                f"확인한 호출 응답 {count}건 중 최근 {len(calls)}건입니다.",
                *(
                    f"NPC 호출 회상 · {call.request.due_tick}초의 플레이어 호출에 "
                    f"{call.reply.due_tick}초에 응답했습니다."
                    for call in calls
                ),
            )
            if calls
            else ("현재 저장 구간에 새로 확인된 호출 응답이 없습니다.",)
        ),
        *player_memory_recollection(memories[0]),
    )


def _conversation_activity(
    segment: SaveSegment,
    npc_id: str,
    *,
    content: QuestContent,
    current: DurableCheckpoint,
    conversation_id: str,
    collect_calls: bool = False,
) -> _ActivityFactory:
    if npc_id != content.definition.layout.npc_id:
        raise SaveError("NPC_RECOLLECTION_SOURCE", "recollection owner differs from selected NPC")
    try:
        factory = _verified_activity(
            segment,
            npc_id,
            content=content,
            current=current,
            npc_work=True,
            error_code="NPC_RECOLLECTION_SOURCE",
            collect_calls=collect_calls,
        )
    except ReplayFormatError as error:
        raise SaveError(
            "NPC_RECOLLECTION_SOURCE", "retained recollection format mismatch"
        ) from error
    if not factory.conversations or factory.conversations[-1] != (
        current.core.tick,
        conversation_id,
    ):
        raise SaveError(
            "NPC_RECOLLECTION_SOURCE", "recollection requires the current committed talk"
        )
    return factory


def _work_lines(
    factory: _ActivityFactory, segment: SaveSegment, current: DurableCheckpoint
) -> tuple[str, ...]:
    previous = factory.conversations[-2][0] if len(factory.conversations) > 1 else None
    lower_bound = segment.checkpoint.core.tick if previous is None else previous
    entries = tuple(
        entry for entry in factory.work_entries if lower_bound < entry.tick <= current.core.tick
    )
    heading = (
        "NPC 작업 회상 · 현재 저장 구간에서 확인한 작업입니다."
        if previous is None
        else f"NPC 작업 회상 · 지난 대화({previous}초) 뒤에 끝낸 작업입니다."
    )
    return (
        heading,
        *(
            tuple(f"NPC 작업 회상 · {entry.tick}초: 물자 1개를 준비했습니다." for entry in entries)
            or ("현재 저장 구간에 새로 확인된 비축 작업이 없습니다.",)
        ),
    )
