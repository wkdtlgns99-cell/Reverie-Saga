from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import cast
import shutil

import pytest

from app.client_session import ClientSession
from app.client_text import turn_messages
from app.headless import state_io
from app.scenarios import scenario_name
from app.scenarios import select_scenario
from app.watch import WatchBootstrapSpec, bootstrap_watch
from app.watch_registry import watch_bundle
from contracts.errors import BootstrapError
from contracts.encounter import InteractCommand
from contracts.messages import CommandPayload
from contracts.persistence import SaveError, WorldUnavailable
from contracts.turn import GameCommand, TurnAborted, TurnCommitted
from contracts.watch import BellCommand, WaitCommand
from domain.encounter import GATE_ID
from domain.primitives import CommandId, EntityId
from domain.scenario import Scenario
from domain.trial import ACTOR_ID
from domain.watch import NPC_ID
from engines.encounter import EncounterActions, EncounterMovement
from engines.watch import WatchRespond
from tests.integration.test_durable_turn import UncertainPort


class _SkippingRespond(WatchRespond):
    def __init__(self) -> None:
        self.extension_marker = "legacy-compatible"


@pytest.mark.parametrize("key", ("harbor", "grove"))
def test_nonlegacy_constructor_skipping_binding_rejected_at_boot(key: str) -> None:
    selected = watch_bundle(select_scenario(key).layout)
    replacement = _SkippingRespond()
    selected = replace(
        selected,
        bindings=tuple(
            replace(binding, engine=replacement)
            if binding.engine.manifest.engine_id == "watch.respond"
            else binding
            for binding in selected.bindings
        ),
    )
    with pytest.raises(BootstrapError) as caught:
        state_io((selected,))
    assert caught.value.code == "INVALID_SCENARIO_BINDING"


def test_legacy_constructor_skipping_extension_still_registered() -> None:
    selected = watch_bundle()
    replacement = _SkippingRespond()
    selected = replace(
        selected,
        bindings=tuple(
            replace(binding, engine=replacement)
            if binding.engine.manifest.engine_id == "watch.respond"
            else binding
            for binding in selected.bindings
        ),
    )
    assert state_io((selected,)).pins == state_io((watch_bundle(),)).pins


def test_nonlegacy_bootstrap_rejects_position_different_from_pin() -> None:
    layout = select_scenario("grove").layout
    with pytest.raises(BootstrapError) as caught:
        bootstrap_watch(WatchBootstrapSpec("0" * 64, "0" * 32, "1" * 32), layout=layout)
    assert caught.value.code == "INVALID_INITIAL_STATE"
    assert caught.value.detail == "SCENARIO_INITIAL_CELL"


@pytest.mark.parametrize("engine", (EncounterActions, EncounterMovement))
def test_encounter_engine_rejects_wrong_layout_type(
    engine: type[EncounterActions] | type[EncounterMovement],
) -> None:
    with pytest.raises(ValueError, match="^SCENARIO_TYPE$"):
        engine(cast(Scenario, None))


def test_wait_narration_uses_selected_actor_name(tmp_path: Path) -> None:
    layout = select_scenario("grove").layout
    session = ClientSession(tmp_path / "game.sqlite", layout)
    try:
        session.act("wait")
        names = {layout.actor_id: "여행자", layout.npc_id: "정찰자"}
        lines = turn_messages(
            session.owner.last_publication(), wait_seconds=1, names=names, actor_id=layout.actor_id
        )
        assert lines[0] == "여행자가 1초 동안 기다렸습니다."
        assert not any("플레이어" in line for line in lines)
    finally:
        session.close()


@pytest.mark.parametrize(
    "kind",
    (
        "engine",
        "read",
        "command",
        "delta",
        "presenter",
        "payload",
        "component",
        "patch",
        "checkpoint",
    ),
)
def test_each_registered_consumer_checked_against_pinned_binding(kind: str) -> None:
    selected, old = watch_bundle(select_scenario("grove").layout), watch_bundle()
    match kind:
        case "engine":
            selected = replace(selected, bindings=(old.bindings[0], *selected.bindings[1:]))
        case "read":
            selected = replace(
                selected, read_adapters=(old.read_adapters[0], *selected.read_adapters[1:])
            )
        case "command":
            selected = replace(
                selected, command_routes=(old.command_routes[0], *selected.command_routes[1:])
            )
        case "delta":
            selected = replace(
                selected, delta_routes=(old.delta_routes[0], *selected.delta_routes[1:])
            )
        case "presenter":
            selected = replace(selected, presenters=(old.presenters[0], *selected.presenters[1:]))
        case "payload":
            selected = replace(selected, codecs=(old.codecs[0], *selected.codecs[1:]))
        case "component":
            selected = replace(
                selected, component_codecs=(old.component_codecs[0], *selected.component_codecs[1:])
            )
        case "patch":
            selected = replace(
                selected, patch_routes=(old.patch_routes[0], *selected.patch_routes[1:])
            )
        case "checkpoint":
            selected = replace(selected, checkpoint_policy=old.checkpoint_policy)
    with pytest.raises(BootstrapError) as caught:
        state_io((selected,))
    assert caught.value.code == "INVALID_SCENARIO_BINDING"


@pytest.mark.parametrize("key", ("harbor", "grove"))
@pytest.mark.parametrize(
    "kind,expected",
    (("gate", "INVALID_TARGET"), ("npc", "INVALID_TARGET"), ("actor", "UNAUTHORIZED_ACTOR")),
)
def test_legacy_gate_npc_actor_rejected_without_mutation(
    tmp_path: Path, key: str, kind: str, expected: str
) -> None:
    layout = select_scenario(key).layout
    session = ClientSession(tmp_path / "game.sqlite", layout)
    try:
        before, protocol = session.owner.snapshot(), session.owner.protocol()
        payload: CommandPayload = (
            InteractCommand(GATE_ID, "open")
            if kind == "gate"
            else (BellCommand(NPC_ID) if kind == "npc" else WaitCommand(1))
        )
        command = GameCommand(
            CommandId(f"c1:{protocol.branch_id}:{protocol.streams[0].stream_id}:1"),
            ACTOR_ID if kind == "actor" else layout.actor_id,
            protocol.revision,
            payload,
        )
        publication = session.owner.submit(command, attachment_id=session.owner.attachment_id)
        assert not isinstance(publication.outcome, TurnCommitted)
        assert publication.outcome.failure.code == expected
        assert (session.owner.snapshot(), session.owner.protocol()) == (before, protocol)
    finally:
        session.close()


@pytest.mark.parametrize(
    "source,target",
    (("legacy", "harbor"), ("harbor", "legacy"), ("legacy", "grove"), ("grove", "legacy")),
)
def test_legacy_scenario_pin_mismatch_both_directions(
    tmp_path: Path, source: str, target: str
) -> None:
    source_layout, target_layout = select_scenario(source).layout, select_scenario(target).layout
    path = tmp_path / "source" / "game.sqlite"
    session = ClientSession(path, source_layout)
    session.act("wait")
    session.save("slot01")
    session.close()
    before_bytes = path.read_bytes()
    with pytest.raises(SaveError) as caught:
        ClientSession(path, target_layout)
    assert caught.value.code == "UNSUPPORTED_RULESET"
    assert path.read_bytes() == before_bytes
    other = ClientSession(tmp_path / "target" / "game.sqlite", target_layout)
    try:
        current = other.update()
        slots = tmp_path / "target" / "slots"
        slots.mkdir(exist_ok=True)
        shutil.copyfile(tmp_path / "source" / "slots" / "slot01.sqlite", slots / "slot01.sqlite")
        with pytest.raises(SaveError) as caught:
            other.load("slot01")
        assert caught.value.code == "UNSUPPORTED_RULESET"
        assert other.update() == current
    finally:
        other.close()


@pytest.mark.parametrize("field", ("initial_cell", "gate_cell", "enemy_cell", "npc_cell"))
@pytest.mark.parametrize("bad", (True, 1.5, [1]))
def test_all_cell_exact_type_boundaries(field: str, bad: object) -> None:
    with pytest.raises(ValueError, match="^SCENARIO_CELL$"):
        layout, value = select_scenario("grove").layout, cast(int, bad)
        match field:
            case "initial_cell":
                replace(layout, initial_cell=value)
            case "gate_cell":
                replace(layout, gate_cell=value)
            case "enemy_cell":
                replace(layout, enemy_cell=value)
            case "npc_cell":
                replace(layout, npc_cell=value)


@pytest.mark.parametrize(
    "bad,code", (((True,), "SCENARIO_CELL"), ((1.5,), "SCENARIO_CELL"), ([7], "SCENARIO_WALLS"))
)
def test_wall_exact_type_boundaries(bad: object, code: str) -> None:
    with pytest.raises(ValueError, match=f"^{code}$"):
        replace(select_scenario("grove").layout, blocked_cells=cast(tuple[int, ...], bad))


@pytest.mark.parametrize(
    "field", ("scenario_id", "actor_id", "enemy_id", "npc_id", "space_id", "gate_id", "lantern_id")
)
def test_oversized_identity_rejected(field: str) -> None:
    layout = select_scenario("grove").layout
    prefix = getattr(layout, field).split(":")[0] + ":"
    with pytest.raises(ValueError, match="^SCENARIO_ID$"):
        replace(layout, **{field: prefix + "a" * 129})


@pytest.mark.parametrize("engine", (EncounterActions, EncounterMovement))
def test_scenario_subclass_rejected(
    engine: type[EncounterActions] | type[EncounterMovement],
) -> None:
    class Derived(Scenario):
        pass

    with pytest.raises(ValueError, match="^SCENARIO_TYPE$"):
        engine(Derived())


@pytest.mark.parametrize("key", ("harbor", "grove"))
@pytest.mark.parametrize("committed", (False, True))
def test_nonlegacy_uncertain_commit_recovery_no_second_execution(
    tmp_path: Path, key: str, committed: bool
) -> None:
    layout = select_scenario(key).layout
    session = ClientSession(tmp_path / "game.sqlite", layout)
    owner = session.owner
    port = UncertainPort(owner._attachment.store, commit=committed, unreadable=True)
    owner._attachment.owner._driver._commit_port = port
    try:
        with pytest.raises(WorldUnavailable, match="SAVE_UNCERTAIN"):
            session.act("bell")
        with pytest.raises(WorldUnavailable):
            session.retry()
        with pytest.raises(WorldUnavailable):
            session.recover()
        port.unreadable = False
        result = session.recover()
        view = result.view
        assert view is not None
        assert (view.tick, view.npc_replies) == ((1, 1) if committed else (0, 0))
        assert port.persist_calls == 1
        assert isinstance(
            owner.last_publication().outcome, TurnCommitted if committed else TurnAborted
        )
        if committed:
            assert session.retry().view == view
            assert port.persist_calls == 1
        else:
            owner._attachment.owner._driver._commit_port = owner._attachment.store
            next_action = session.act("bell")
            assert next_action.status == "COMMITTED" and next_action.view is not None
            assert (next_action.view.tick, next_action.view.npc_replies) == (1, 1)
            assert port.persist_calls == 1
    finally:
        session.close()


@pytest.mark.parametrize("key", ("harbor", "grove"))
def test_sqlite_lexical_roles_and_generic_label(tmp_path: Path, key: str) -> None:
    layout = replace(
        select_scenario(key).layout, actor_id=EntityId("actor:aaa"), enemy_id=EntityId("actor:zzz")
    )
    assert scenario_name(layout) == "연습 구간"
    path = tmp_path / "game.sqlite"
    session = ClientSession(path, layout)
    try:
        session.act("bell")
        saved = session.update().view
        session.save("slot01")
        session.act("wait", seconds=2)
        loaded = session.load("slot01")
        assert loaded.view == saved
        resumed = Path(loaded.working_path)
        session.close()
        session = ClientSession(resumed, layout)
        assert session.update().view == saved
        next_action = session.act("bell")
        assert next_action.status == "COMMITTED" and next_action.view is not None
        assert next_action.view.npc_replies == 2
    finally:
        session.close()
