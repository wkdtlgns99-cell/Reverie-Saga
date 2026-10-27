"""Fixed component metadata stays shared while component state remains independent."""

from dataclasses import FrozenInstanceError

import pytest

from contracts.encounter import GATE, HIT_POINTS, STAMINA
from contracts.trial import CELL_POSITION, TRIAL_MAP
from contracts.watch import LANTERN, REPLY, WATCH_NPC
from domain.encounter import GateRecord, HitPointsRecord, StaminaRecord
from domain.primitives import EntityId, TypeKey
from domain.state_types import ComponentRecord
from domain.trial import CellPositionRecord, TrialMapRecord
from domain.watch import LanternRecord, ReplyRecord, WatchNpcRecord

ACTOR, GATE_ID, SPACE = EntityId("actor:trial"), EntityId("object:gate"), EntityId("space:trial")


@pytest.mark.parametrize(
    ("kind", "registered", "first", "second"),
    (
        (
            "encounter.gate",
            GATE.schema,
            GateRecord(GATE_ID, SPACE, 4, 0),
            GateRecord(GATE_ID, SPACE, 4, 1),
        ),
        ("encounter.hp", HIT_POINTS.schema, HitPointsRecord(ACTOR, 3), HitPointsRecord(ACTOR, 0)),
        ("encounter.stamina", STAMINA.schema, StaminaRecord(ACTOR, 2), StaminaRecord(ACTOR, 0)),
        (
            "trial.map",
            TRIAL_MAP.schema,
            TrialMapRecord(SPACE, 3, 3, 1000, (1,)),
            TrialMapRecord(SPACE, 3, 3, 1000, (2,)),
        ),
        (
            "trial.position",
            CELL_POSITION.schema,
            CellPositionRecord(ACTOR, SPACE, 0),
            CellPositionRecord(ACTOR, SPACE, 3),
        ),
        (
            "watch.npc",
            WATCH_NPC.schema,
            WatchNpcRecord(ACTOR, SPACE, 6, 0),
            WatchNpcRecord(ACTOR, SPACE, 6, 1),
        ),
        ("watch.lantern", LANTERN.schema, LanternRecord(GATE_ID, 0), LanternRecord(GATE_ID, 3)),
        ("watch.reply", REPLY.schema, ReplyRecord(ACTOR, 0), ReplyRecord(ACTOR, 1)),
    ),
)
def test_fixed_schema_is_shared_and_immutable_across_record_states(
    kind: str, registered: TypeKey, first: ComponentRecord, second: ComponentRecord
) -> None:
    expected = TypeKey(kind, 1)
    assert first != second
    assert first.schema == second.schema == registered == expected
    schema = first.schema
    assert schema is first.schema is second.schema is registered
    with pytest.raises(FrozenInstanceError):
        setattr(schema, "version", 2)
    assert first.schema == second.schema == registered == expected
