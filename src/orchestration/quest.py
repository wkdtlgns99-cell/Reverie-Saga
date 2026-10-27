"""Quest registered boundaries:observed reads,strict codecs,staging and presentation."""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
from typing import cast

from domain.npc_patrol import patrol_cells

from contracts.dialogue import INTENTS, QuestBound, QuestContent
from contracts.encounter import HIT_POINTS
from contracts.errors import CandidateError, ReadOnlyViolation, SchemaError
from contracts.messages import EventHeader, PresentationEvent, StateDelta, WorldEvent
from contracts.quest import (
    QUEST,
    QUEST_PAYLOADS,
    STAGE_FAMILY,
    GoalMet,
    QuestAccepted,
    QuestCompleted,
    QuestCue,
    QuestRead,
    QuestSpoken,
    QuestStageDelta,
    QuestStagePatch,
    QuestTalkCommand,
)
from contracts.read_views import ComponentKey, ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.trial import CELL_POSITION
from contracts.turn import (
    AdmittedAction,
    AdmittedCommand,
    AdmissionOutcome,
    CommitReceipt,
    GameCommand,
    ProtocolSnapshot,
    TurnPlan,
    TurnRejected,
    failure,
)
from contracts.watch import WATCH_NPC
from domain.canonical import (
    JsonObject,
    exact_fields,
    hash_document,
    int_value,
    object_value,
    pack,
    seal,
    text_value,
)
from domain.encounter import HitPointsRecord
from domain.primitives import (
    ComponentAddress,
    EntityId,
    EventId,
    FieldAddress,
    FieldFamily,
    FrozenPayload,
    MAX_INT,
    Phase,
    Tick,
    TypeKey,
    require_integer,
    require_namespace,
)
from domain.quest import NET_STEPS, SINGLE_STEPS, QuestRecord
from domain.state_types import ComponentRecord, CoreSnapshot
from orchestration.watch import WatchCheckpointPolicy


class _QuestView:
    __slots__ = ("_record", "_access")
    _record: QuestRecord
    _access: ViewAccess

    def __init__(self, record: QuestRecord, access: ViewAccess) -> None:
        object.__setattr__(self, "_record", record)
        object.__setattr__(self, "_access", access)

    def __setattr__(self, name: str, value: object) -> None:
        self._access.observe(FieldAddress(STAGE_FAMILY, self._record.entity_id), (), "write")
        raise ReadOnlyViolation(name)

    def __delattr__(self, name: str) -> None:
        self.__setattr__(name, None)

    @property
    def stage(self) -> int:
        self._access.observe(FieldAddress(STAGE_FAMILY, self._record.entity_id), (), "read")
        return self._record.stage


class QuestAdapter(QuestBound):
    @property
    def key(self) -> ComponentKey[QuestRead]:
        return QUEST

    def validate(self, record: ComponentRecord) -> None:
        if (
            type(record) is not QuestRecord
            or record.entity_id != self.quest_content.definition.quest_id
        ):
            raise ValueError("QUEST_RECORD")
        require_integer(record.stage, 0, 3)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> QuestRead:
        self.validate(record)
        return _QuestView(cast(QuestRecord, record), access)


class QuestCodec(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return QUEST.schema

    def encode(self, record: ComponentRecord) -> JsonObject:
        QuestAdapter(self.quest_content).validate(record)
        return {"stage": cast(QuestRecord, record).stage}

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        data = exact_fields(fields, ("stage",))
        record = QuestRecord(entity_id, int_value(data["stage"]))
        QuestAdapter(self.quest_content).validate(record)
        return record


class QuestPayloadCodec(QuestBound):
    def __init__(self, schema: TypeKey, content: QuestContent) -> None:
        super().__init__(content)
        if schema not in tuple(kind.SCHEMA for kind in QUEST_PAYLOADS):
            raise SchemaError("UNSUPPORTED_SCHEMA", "quest codec")
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if type(payload) not in QUEST_PAYLOADS or payload.schema != self.schema:
            raise ValueError("QUEST_PAYLOAD_TYPE")
        typed = cast(
            QuestTalkCommand
            | QuestStageDelta
            | QuestStagePatch
            | QuestAccepted
            | GoalMet
            | QuestCompleted
            | QuestSpoken
            | QuestCue,
            payload,
        )
        document = object_value(seal(asdict(typed)))
        self.decode(document)
        return document

    def decode(self, data: JsonObject) -> FrozenPayload:
        definition = self.quest_content.definition
        layout = definition.layout
        result: FrozenPayload
        if self.schema == QuestTalkCommand.SCHEMA:
            row = exact_fields(data, ("npc_id",))
            npc = text_value(row["npc_id"])
            require_namespace(npc)
            if not npc.startswith("actor:"):
                raise ValueError("QUEST_PAYLOAD_ID")
            result = QuestTalkCommand(EntityId(npc))
        elif self.schema == QuestStageDelta.SCHEMA:
            row = exact_fields(data, ("entity_id", "before_stage", "after_stage"))
            before, after = int_value(row["before_stage"]), int_value(row["after_stage"])
            require_integer(before, 0, 3)
            require_integer(after, 0, 3)
            if row["entity_id"] != definition.quest_id or before >= after:
                raise ValueError("QUEST_DELTA")
            result = QuestStageDelta(EntityId(definition.quest_id), before, after)
        elif self.schema == QuestStagePatch.SCHEMA:
            row = exact_fields(data, ("stage",))
            stage = int_value(row["stage"])
            require_integer(stage, 0, 3)
            result = QuestStagePatch(stage)
        elif self.schema == GoalMet.SCHEMA:
            row = exact_fields(data, ("quest_id", "target_id"))
            if row["quest_id"] != definition.quest_id or row["target_id"] != layout.enemy_id:
                raise ValueError("QUEST_FACT_BINDING")
            result = GoalMet(definition.quest_id, layout.enemy_id)
        elif self.schema in (QuestAccepted.SCHEMA, QuestCompleted.SCHEMA):
            fields: tuple[str, ...] = ("quest_id", "actor_id", "npc_id")
            if self.schema == QuestCompleted.SCHEMA:
                fields += ("reward_id", "amount")
            row = exact_fields(data, fields)
            if (
                row["quest_id"] != definition.quest_id
                or row["actor_id"] != layout.actor_id
                or row["npc_id"] != layout.npc_id
            ):
                raise ValueError("QUEST_FACT_BINDING")
            if self.schema == QuestAccepted.SCHEMA:
                result = QuestAccepted(definition.quest_id, layout.actor_id, layout.npc_id)
            else:
                amount = int_value(row["amount"])
                if row["reward_id"] != definition.reward_id or amount != 1:
                    raise ValueError("QUEST_FACT_REWARD")
                result = QuestCompleted(
                    definition.quest_id,
                    layout.actor_id,
                    layout.npc_id,
                    definition.reward_id,
                    amount,
                )
        else:
            row = exact_fields(data, ("quest_id", "npc_id", "intent"))
            intent = text_value(row["intent"])
            if (
                row["quest_id"] != definition.quest_id
                or row["npc_id"] != layout.npc_id
                or intent not in INTENTS
            ):
                raise ValueError("QUEST_FACT_BINDING")
            cls = QuestSpoken if self.schema == QuestSpoken.SCHEMA else QuestCue
            result = cls(definition.quest_id, layout.npc_id, intent)
        return result


class QuestReducer(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return QuestStageDelta.SCHEMA

    @property
    def owner_id(self) -> str:
        return "quest.rules"

    def _value(self, delta: StateDelta) -> QuestStageDelta:
        if type(delta) is not QuestStageDelta:
            raise CandidateError("INVALID_DELTA", "quest delta type")
        try:
            QuestPayloadCodec(self.schema, self.quest_content).encode(delta)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", "quest delta bounds") from error
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._value(delta)
        if (value.before_stage, value.after_stage) not in SINGLE_STEPS or before.component(
            QUEST, value.entity_id
        ).stage != value.before_stage:
            raise CandidateError("INVALID_DELTA", "quest single step/endpoint")
        editor.apply_patch(
            ComponentAddress(QUEST.schema, value.entity_id), QuestStagePatch(value.after_stage)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if not changes:
            raise CandidateError("INVALID_DELTA", "empty quest composition")
        values = tuple(self._value(value) for value in changes)
        if any((v.before_stage, v.after_stage) not in SINGLE_STEPS for v in values):
            raise CandidateError("INVALID_DELTA", "quest composition step")
        if any(a.after_stage != b.before_stage for a, b in zip(values, values[1:])):
            raise CandidateError("INVALID_DELTA", "quest composition continuity")
        result = QuestStageDelta(
            values[0].entity_id, values[0].before_stage, values[-1].after_stage
        )
        if (result.before_stage, result.after_stage) not in NET_STEPS:
            raise CandidateError("INVALID_DELTA", "quest net transition")
        return result

    def is_identity(self, delta: StateDelta) -> bool:
        self._value(delta)
        return False

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._value(delta)
        if (value.before_stage, value.after_stage) not in NET_STEPS or after.component(
            QUEST, value.entity_id
        ).stage != value.after_stage:
            raise CandidateError("INVALID_DELTA", "quest net endpoint/transition")


class QuestPatchRoute(QuestBound):
    @property
    def schema(self) -> TypeKey:
        return QuestStagePatch.SCHEMA

    @property
    def component_schema(self) -> TypeKey:
        return QUEST.schema

    @property
    def family(self) -> FieldFamily:
        return STAGE_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        QuestAdapter(self.quest_content).validate(before)
        QuestPayloadCodec(self.schema, self.quest_content).encode(patch)
        return replace(cast(QuestRecord, before), stage=cast(QuestStagePatch, patch).stage)


class QuestAdmission(QuestBound):
    def __init__(self, content: QuestContent, *, npc_patrol: bool = False) -> None:
        super().__init__(content)
        self._npc_cells = patrol_cells(content.definition.layout, npc_patrol)
        self._npc_patrol = npc_patrol

    @property
    def schema(self) -> TypeKey:
        return QuestTalkCommand.SCHEMA

    @property
    def reads(self) -> tuple[FieldFamily, ...]:
        return tuple(
            FieldFamily(k, f)
            for k, f in (
                ("encounter.hp", "hp"),
                ("trial.position", "cell"),
                ("trial.position", "space_id"),
                ("watch.npc", "cell"),
                ("watch.npc", "space_id"),
            )
        )

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        layout = self.quest_content.definition.layout
        if command.actor_id != layout.actor_id:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        body = QuestPayloadCodec(self.schema, self.quest_content).encode(command.payload)
        if state.component(HIT_POINTS, layout.actor_id).hp == 0:
            return TurnRejected(failure("ACTOR_DEFEATED"), command.expected_revision)
        payload = cast(QuestTalkCommand, command.payload)
        if payload.npc_id != layout.npc_id:
            return TurnRejected(failure("INVALID_TARGET"), command.expected_revision)
        actor, npc = (
            state.component(CELL_POSITION, layout.actor_id),
            state.component(WATCH_NPC, layout.npc_id),
        )
        if npc.space_id != layout.space_id or npc.cell not in self._npc_cells:
            raise CandidateError("INVALID_ACTION", "quest giver reference")
        cell = actor.cell
        if (
            actor.space_id != npc.space_id
            or abs(cell % 3 - npc.cell % 3) + abs(cell // 3 - npc.cell // 3) > 1
        ):
            return TurnRejected(failure("OUT_OF_RANGE"), command.expected_revision)
        if start_tick >= MAX_INT:
            raise CandidateError("INTEGER_OVERFLOW", "quest duration")
        target = Tick(start_tick + 1)
        payload_hash = hash_document(
            "payload/v1", {"schema": {"kind": self.schema.kind, "version": 1}, "payload": body}
        )
        key = (
            "a1-"
            + hashlib.sha256(
                pack(("action-key/v1", world_id, str(target), command.actor_id, payload_hash))
            ).hexdigest()
        )
        return AdmittedCommand(
            TurnPlan(command, start_tick, target), AdmittedAction(command.actor_id, payload, key)
        )


class QuestCheckpointPolicy(QuestBound):
    def __init__(self, content: QuestContent, *, npc_patrol: bool = False) -> None:
        super().__init__(content)
        self._npc_cells = patrol_cells(content.definition.layout, npc_patrol)
        self._npc_patrol = npc_patrol

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        content = self.quest_content
        matches = tuple(r for r in core.components if r.schema == QUEST.schema)
        if len(matches) != 1:
            raise ValueError("QUEST_CHECKPOINT_RECORDS")
        record = matches[0]
        QuestAdapter(content).validate(record)
        if core.components != tuple(
            sorted(core.components, key=lambda r: (r.schema.kind, r.schema.version, r.entity_id))
        ):
            raise ValueError("QUEST_CHECKPOINT_ORDER")
        remaining = tuple(r for r in core.components if r is not record)
        WatchCheckpointPolicy(content.definition.layout, npc_patrol=self._npc_patrol).validate(
            replace(core, components=remaining), protocol
        )
        targets = tuple(
            r
            for r in remaining
            if type(r) is HitPointsRecord and r.entity_id == content.definition.layout.enemy_id
        )
        if len(targets) != 1:
            raise ValueError("QUEST_CHECKPOINT_TARGET")
        hp = targets[0].hp
        stage = cast(QuestRecord, record).stage
        if stage == 1 and hp == 0 or stage >= 2 and hp > 0:
            raise ValueError("QUEST_CHECKPOINT_PROGRESS")


class QuestPresenter(QuestBound):
    def map(
        self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort
    ) -> tuple[PresentationEvent, ...]:
        definition = self.quest_content.definition
        stage = committed.component(QUEST, EntityId(definition.quest_id)).stage
        cues: list[PresentationEvent] = []
        for event in facts:
            payload = event.payload
            QuestPayloadCodec(payload.schema, self.quest_content).encode(payload)
            if isinstance(payload, QuestCompleted) and stage != 3:
                raise ValueError("QUEST_PRESENTATION_ENDPOINT")
            if isinstance(payload, GoalMet) and stage < 2:
                raise ValueError("QUEST_PRESENTATION_ENDPOINT")
            if isinstance(payload, QuestAccepted) and stage < 1:
                raise ValueError("QUEST_PRESENTATION_ENDPOINT")
            if isinstance(payload, QuestSpoken):
                required = {
                    "offer": (1, 2),
                    "reminder": (1,),
                    "completion": (3,),
                    "gratitude": (3,),
                }
                if stage not in required[payload.intent]:
                    raise ValueError("QUEST_PRESENTATION_ENDPOINT")
                cue = QuestCue(definition.quest_id, payload.npc_id, payload.intent)
                identifier = EventId(
                    "p1-"
                    + hashlib.sha256(
                        pack(
                            ("cue-id/v1", event.header.event_id, "quest.presenter", str(len(cues)))
                        )
                    ).hexdigest()
                )
                cues.append(
                    PresentationEvent(
                        EventHeader(
                            identifier,
                            cue.schema,
                            "quest.presenter",
                            receipt.tick,
                            Phase.PRESENT,
                            0,
                            0,
                            len(cues),
                            (event.header.event_id,),
                            (),
                        ),
                        cue,
                        "important",
                        "keep_all",
                        "",
                    )
                )
        return tuple(cues)
