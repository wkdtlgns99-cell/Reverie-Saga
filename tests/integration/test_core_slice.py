from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from adapters.sqlite_store import validate_save
from app.durable import DurableSession, create_durable, resume_durable
from app.headless import _CheckpointFactory, state_io
from app.watch import WatchBootstrapSpec, bootstrap_watch
from app.watch_registry import watch_bundle
from contracts.encounter import AttackCommand, Defeated, EncounterMoveBlocked, InteractCommand, RestCommand
from contracts.messages import CommandPayload
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.turn import GameCommand, TurnCommitted, TurnRejected
from contracts.trial import MoveCommand
from contracts.watch import BellCommand, NpcActed
from domain.canonical import array_value, canonical_json, decode_json, hash_document, object_value
from domain.encounter import ATTACK_PROFILE_ID, ENEMY_ID, GATE_ID, GateRecord, HitPointsRecord, StaminaRecord
from domain.primitives import CommandId, WorldRevision
from domain.trial import ACTOR_ID, CellPositionRecord
from domain.watch import NPC_ID, LanternRecord, ReplyRecord, WatchNpcRecord
from orchestration.replay import Runner


# Independent settled rules: damage2/cost1/surviving counter1/rest1/pulse2/charge cap3.
# Cell, gate, actor HP, enemy HP, stamina, NPC bells, replies, charge.
STATES = (
    (0, 0, 3, 5, 2, 0, 0, 1), (3, 0, 3, 5, 2, 1, 0, 2),
    (3, 0, 3, 5, 2, 1, 0, 3), (3, 1, 3, 5, 2, 2, 0, 3),
    (4, 1, 3, 5, 2, 2, 0, 3), (7, 1, 3, 5, 2, 3, 0, 3),
    (7, 1, 2, 3, 1, 3, 0, 3), (7, 1, 2, 3, 1, 4, 1, 3),
    (7, 1, 1, 1, 0, 4, 1, 3), (7, 1, 1, 1, 1, 5, 1, 3),
    (7, 1, 1, 0, 0, 5, 1, 3), (8, 1, 1, 0, 0, 6, 1, 3),
)


def _commands() -> tuple[GameCommand, ...]:
    actions: tuple[CommandPayload, ...] = (
        MoveCommand(1, 0), MoveCommand(0, 1), MoveCommand(1, 0),
        InteractCommand(GATE_ID, "open"), MoveCommand(1, 0), MoveCommand(0, 1),
        AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID), BellCommand(NPC_ID),
        AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID), RestCommand(),
        AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID), MoveCommand(1, 0),
    )
    return tuple(GameCommand(CommandId("c1:" + "0" * 32 + ":" + "1" * 32 + ":" + str(i)),
                             ACTOR_ID, WorldRevision(i - 1), action)
                 for i, action in enumerate(actions, 1))


def _head(owner: DurableSession) -> DurableCheckpoint:
    return DurableCheckpoint(owner.snapshot(), owner.protocol())


def _check_state(owner: DurableSession, tick: int) -> None:
    core = owner.snapshot()
    state = (
        next(c.cell for c in core.components if isinstance(c, CellPositionRecord) and c.entity_id == ACTOR_ID),
        next(c.is_open for c in core.components if isinstance(c, GateRecord)),
        next(c.hp for c in core.components if isinstance(c, HitPointsRecord) and c.entity_id == ACTOR_ID),
        next(c.hp for c in core.components if isinstance(c, HitPointsRecord) and c.entity_id == ENEMY_ID),
        next(c.value for c in core.components if isinstance(c, StaminaRecord)),
        next(c.bells for c in core.components if isinstance(c, WatchNpcRecord)),
        next(c.count for c in core.components if isinstance(c, ReplyRecord)),
        next(c.charge for c in core.components if isinstance(c, LanternRecord)),
    )
    assert state == STATES[tick - 1]
    assert core.tick == tick
    assert owner.protocol().revision == tick
    assert len(core.pending) == 1
    queued = state_io((watch_bundle(),)).decode_pending(core.pending[0])
    assert queued.event.due_tick == (tick // 2 + 1) * 2
    if tick >= 2:
        assert queued.event.header.caused_by


@pytest.mark.parametrize("reopen_before_load", [False, True])
def test_combined_gameplay_midcombat_save_load_replay(tmp_path: Path, reopen_before_load: bool) -> None:
    bundles = (watch_bundle(),)
    selected = state_io(bundles)
    initial = bootstrap_watch(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32))
    owner = create_durable(tmp_path / "combined.sqlite", DurableCheckpoint(initial.snapshot(), initial.protocol()), bundles=bundles)
    requests = _commands()
    publications: list[bytes] = []
    try:
        for tick, request in enumerate(requests, 1):
            publication = owner.submit(request, attachment_id=owner.attachment_id)
            assert isinstance(publication.outcome, TurnCommitted)
            assert not publication.diagnostics
            assert sum(isinstance(f.payload, NpcActed) for f in publication.facts) == (1 if tick % 2 == 0 else 0)
            assert sum(isinstance(f.payload, Defeated) for f in publication.facts) == (1 if tick == 11 else 0)
            if tick in (1, 3):
                blocked = next(f.payload for f in publication.facts if isinstance(f.payload, EncounterMoveBlocked))
                assert blocked.reason == ("wall" if tick == 1 else "door")
            publications.append(canonical_json(selected.encode_publication(publication)))
            _check_state(owner, tick)
            if tick == 7:
                saved = _head(owner)
                saved_body = canonical_json(selected.encode_core(saved.core))
                exported = owner.export("slot01")
                assert exported.core_hash == selected.hash_core(saved.core)
                assert exported.protocol_hash == hash_document("protocol/v1", selected.encode_protocol(saved.protocol))
                assert validate_save(tmp_path / "slots/slot01.sqlite", io=selected) == saved
            if tick == 9:
                before = _head(owner)
                rejected = owner.submit(GameCommand(requests[9].command_id, ACTOR_ID, WorldRevision(9),
                                                    AttackCommand(ENEMY_ID, ATTACK_PROFILE_ID)), attachment_id=owner.attachment_id)
                assert isinstance(rejected.outcome, TurnRejected)
                assert rejected.outcome.failure.code == "INSUFFICIENT_STAMINA"
                assert not rejected.facts and rejected.diff is None
                assert _head(owner) == before and len(owner.retained_segment().trace.steps) == 9
        finished = _head(owner)
        whole = owner.retained_segment()
        assert len(whole.trace.steps) == 12
        runner = Runner(whole.checkpoint.core, whole.checkpoint.protocol, factory=_CheckpointFactory(bundles), io=selected)
        assert runner.run(whole.trace) == ()
        assert runner.run(whole.trace) == ()
        facts = array_value(object_value(decode_json(publications[7]))["facts"])
        without_npc = tuple(f for f in facts if object_value(object_value(object_value(f)["header"])["type_key"])["kind"] != "watch.npc-acted")
        assert len(without_npc) == len(facts) - 1
        altered = replace(whole.trace.steps[7], expected_facts_hash=hash_document("turn-facts/v1", without_npc))
        bad_trace = replace(whole.trace, steps=(*whole.trace.steps[:7], altered, *whole.trace.steps[8:]))
        mismatches = runner.run(bad_trace)
        assert len(mismatches) == 1 and mismatches[0].step_index == 7 and mismatches[0].path == "$facts_hash"
        if reopen_before_load:
            path = owner.working_path
            owner.close()
            owner = resume_durable(path, bundles=bundles)
            assert _head(owner) == finished
        old_token = owner.attachment_id
        loaded = owner.load("slot01")
        assert loaded.revision == 7 and loaded.attachment_id != old_token
        assert _head(owner) == saved
        assert canonical_json(selected.encode_core(owner.snapshot())) == saved_body
        with pytest.raises(SaveError, match="STALE_ATTACHMENT"):
            owner.submit(requests[7], attachment_id=old_token)
        assert _head(owner) == saved
        duplicate = owner.submit(requests[6], attachment_id=owner.attachment_id)
        assert isinstance(duplicate.outcome, TurnCommitted)
        assert duplicate.outcome.receipt == saved.protocol.receipts[-1].receipt
        assert not duplicate.facts and duplicate.diff is None
        assert _head(owner) == saved and len(owner.retained_segment().trace.steps) == 7
        for tick, request in enumerate(requests[7:], 8):
            publication = owner.submit(request, attachment_id=owner.attachment_id)
            assert canonical_json(selected.encode_publication(publication)) == publications[tick - 1]
            _check_state(owner, tick)
        assert _head(owner) == finished
        segment = owner.retained_segment()
        assert len(segment.trace.steps) == 12
        assert Runner(segment.checkpoint.core, segment.checkpoint.protocol,
                      factory=_CheckpointFactory(bundles), io=selected).run(segment.trace) == ()
        active = owner.working_path
    finally:
        owner.close()
    with resume_durable(active, bundles=bundles) as restored:
        assert _head(restored) == finished
