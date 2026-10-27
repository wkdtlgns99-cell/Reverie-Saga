"""Strict registered serialization and presentation for NPC gate support."""

from contracts.dialogue import QuestBound, QuestContent
from contracts.npc_gate_aid import GateAidCue, GateAssisted
from domain.canonical import JsonObject, exact_fields, int_value, text_value
from domain.primitives import EntityId, FrozenPayload, TypeKey, require_integer
from domain.watch import WAKE_PERIOD


class GateAidPayloadCodec(QuestBound):
    def __init__(
        self, schema: TypeKey, content: QuestContent, *, npc_call_aid: bool = False
    ) -> None:
        super().__init__(content)
        if schema not in (GateAssisted.SCHEMA, GateAidCue.SCHEMA):
            raise ValueError("NPC_AID_PAYLOAD")
        if type(npc_call_aid) is not bool:
            raise ValueError("NPC_CALL_AID_CONTENT")
        self._npc_call_aid = npc_call_aid
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        expected = GateAssisted if self.schema == GateAssisted.SCHEMA else GateAidCue
        if type(payload) is not expected or not isinstance(payload, (GateAssisted, GateAidCue)):
            raise ValueError("NPC_AID_PAYLOAD")
        layout = self.scenario_layout
        if (
            type(payload.npc_id) is not str
            or payload.npc_id != layout.npc_id
            or type(payload.target_id) is not str
            or payload.target_id != layout.gate_id
        ):
            raise ValueError("NPC_AID_PAYLOAD")
        result: JsonObject = {"npc_id": payload.npc_id, "target_id": payload.target_id}
        if isinstance(payload, GateAidCue):
            try:
                require_integer(payload.logical_tick, 1)
            except ValueError as error:
                raise ValueError("NPC_AID_PAYLOAD") from error
            if not self._npc_call_aid and payload.logical_tick % WAKE_PERIOD:
                raise ValueError("NPC_AID_PAYLOAD")
            result = {**result, "logical_tick": payload.logical_tick}
        return result

    def decode(self, data: JsonObject) -> FrozenPayload:
        names = ("npc_id", "target_id")
        fields = exact_fields(
            data, (*names, "logical_tick") if self.schema == GateAidCue.SCHEMA else names
        )
        npc, target = (
            EntityId(text_value(fields["npc_id"])),
            EntityId(text_value(fields["target_id"])),
        )
        value = (
            GateAssisted(npc, target)
            if self.schema == GateAssisted.SCHEMA
            else GateAidCue(npc, target, int_value(fields["logical_tick"]))
        )
        self.encode(value)
        return value
