"""Registered speech admission,strict memory codecs and append/last-entry staging."""

from dataclasses import asdict, replace
import hashlib
import re

from contracts.errors import CandidateError, SchemaError
from contracts.messages import EventHeader, PresentationEvent, StateDelta, WorldEvent
from contracts.read_views import ComponentPatch, ReadPort, StagingEditor, ViewAccess
from contracts.skeleton import CommandRoute
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
from contracts.world_conversation import (
    CONVERSATION,
    CONVERSATION_FAMILY,
    CONVERSATION_OWNER,
    ConversationDelta,
    ConversationPatch,
    ConversationRead,
    ContinueSpeech,
    NpcReply,
    PlayerSay,
    SpeechAdvanced,
    SpeechCue,
)
from contracts.world_population import INVENTORY_FAMILY, SETTLEMENT, SETTLEMENT_FAMILY
from contracts.world_supply import SUPPLY_FAMILY
from contracts.world_travel import TRAVELER, TRAVEL_FAMILY
from domain.canonical import (
    JsonObject,
    array_value,
    exact_fields,
    int_value,
    object_value,
    pack,
    seal,
    text_value,
)
from domain.primitives import (
    ComponentAddress,
    EntityId,
    EventId,
    FrozenPayload,
    Phase,
    Tick,
    TypeKey,
    require_integer,
    require_namespace,
)
from domain.state_types import ComponentRecord, CoreSnapshot
from domain.world import Resident, WorldCatalog, elaborate_place
from domain.world_conversation import (
    CONVERSATION_SCHEMA,
    MAX_EXCHANGES,
    SPEECH_SEGMENT_SECONDS,
    ConversationRecord,
    ConversationState,
    Exchange,
    begin_reply,
    begin_speech,
    continue_speech,
    exchange_digest,
    npc_rate,
    speech_seconds,
)
from domain.world_population import resident_activity
from domain.world_supply import SupplyScenario
from domain.world_travel import WORLD_ACTOR, TravelerRecord
from orchestration.world_conversation_context import context_from_read
from domain.primitives import FieldFamily
from contracts.world_social import SOCIAL_FAMILY
from domain.world_social import SocialCatalog
from orchestration.world_population import _StateView
from orchestration.world_supply import SupplyCheckpointPolicy

EXCHANGE_FIELDS = tuple(Exchange.__dataclass_fields__)
DELTA_FIELDS = (
    "entity_id",
    "before_count",
    "before_digest",
    "before_speaker",
    "before_remaining",
    "entry",
    "speaker",
    "remaining",
    "append",
)
REJECTIONS = (
    "DIALOGUE_TEXT",
    "DIALOGUE_SPEAKING",
    "DIALOGUE_HISTORY_FULL",
    "DIALOGUE_STALE",
    "DIALOGUE_ALREADY_REPLIED",
    "DIALOGUE_WRONG_NPC",
    "DIALOGUE_NO_SPEECH",
    "DIALOGUE_NO_UTTERANCE",
    "DIALOGUE_OUT_OF_REACH",
    "DIALOGUE_NPC_UNAVAILABLE",
    "DIALOGUE_CONTEXT_STALE",
    "DIALOGUE_PROPOSAL",
    "DIALOGUE_REPLY_PROVENANCE",
)


def decode_exchange(data: JsonObject) -> Exchange:
    d = exact_fields(data, EXCHANGE_FIELDS)
    return Exchange(
        text_value(d["speech_id"]),
        text_value(d["npc_id"]),
        text_value(d["place_id"]),
        text_value(d["player_text"]),
        int_value(d["player_start"]),
        int_value(d["player_end"]),
        text_value(d["reply_text"]),
        int_value(d["reply_start"]),
        int_value(d["reply_end"]),
        text_value(d["model"]),
        text_value(d["context_sha256"]),
        text_value(d["proposal"]),
    )


def encode_exchange(entry: Exchange) -> JsonObject:
    Exchange(**asdict(entry))
    return object_value(seal(asdict(entry)))


def _local_npc(state: ReadPort, npc_id: str, tick: int) -> tuple[Resident, str]:
    travel = state.component(TRAVELER, WORLD_ACTOR).state
    if travel.destination_id:
        raise ValueError("DIALOGUE_OUT_OF_REACH")
    local = state.component(SETTLEMENT, EntityId(travel.place_id)).state
    resident = None if local is None else next((r for r in local.residents if r.id == npc_id), None)
    if resident is None:
        raise ValueError("DIALOGUE_WRONG_NPC")
    if resident_activity(resident, tick).activity == "잠자는 중":
        raise ValueError("DIALOGUE_NPC_UNAVAILABLE")
    return resident, travel.place_id


class ConversationAdmission:
    reads: tuple[FieldFamily, ...] = (
        CONVERSATION_FAMILY,
        TRAVEL_FAMILY,
        SETTLEMENT_FAMILY,
        SUPPLY_FAMILY,
        INVENTORY_FAMILY,
    )

    def __init__(
        self,
        world: WorldCatalog,
        scenario: SupplyScenario,
        schema: TypeKey,
        *,
        social: SocialCatalog | None = None,
    ) -> None:
        self.world, self.scenario, self.schema = world, scenario, schema
        self.social = social
        if social is not None:
            self.reads = (*self.reads, SOCIAL_FAMILY)

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        if command.actor_id != WORLD_ACTOR:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        payload = command.payload
        before = state.component(CONVERSATION, WORLD_ACTOR).state
        key = (
            "a1-"
            + hashlib.sha256(pack(("world-speech/v1", world_id, command.command_id))).hexdigest()
        )
        try:
            if type(payload) is PlayerSay and isinstance(payload, PlayerSay):
                if type(payload.npc_id) is not str:
                    raise ValueError("DIALOGUE_WRONG_NPC")
                resident, place = _local_npc(state, payload.npc_id, start_tick)
                _, duration = begin_speech(
                    before, resident, place, payload.text, "speech:s" + key[3:], start_tick
                )
            elif type(payload) is ContinueSpeech and isinstance(payload, ContinueSpeech):
                _, duration = continue_speech(before, payload.speech_id)
            elif type(payload) is NpcReply and isinstance(payload, NpcReply):
                if not before.exchanges:
                    raise ValueError("DIALOGUE_NO_UTTERANCE")
                resident, _ = _local_npc(state, before.exchanges[-1].npc_id, start_tick)
                context = context_from_read(
                    state, self.world, self.scenario, start_tick, social=self.social
                )
                if payload.context_sha256 != context.sha256:
                    raise ValueError("DIALOGUE_CONTEXT_STALE")
                if payload.proposal != "none" and payload.proposal != context.available_action:
                    raise ValueError("DIALOGUE_PROPOSAL")
                _, duration = begin_reply(
                    before,
                    resident,
                    payload.speech_id,
                    payload.text,
                    payload.model,
                    payload.context_sha256,
                    payload.proposal,
                    start_tick,
                )
            else:
                return TurnRejected(failure("INVALID_COMMAND"), command.expected_revision)
        except ValueError as error:
            if str(error) not in REJECTIONS:
                raise
            return TurnRejected(failure(str(error)), command.expected_revision)
        return AdmittedCommand(
            TurnPlan(command, start_tick, Tick(start_tick + duration)),
            AdmittedAction(command.actor_id, payload, key),
        )


class SpeechGate:
    def __init__(self, inner: CommandRoute) -> None:
        self.inner = inner
        self.schema = inner.schema
        self.reads = tuple(dict.fromkeys((*inner.reads, CONVERSATION_FAMILY)))

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        if state.component(CONVERSATION, WORLD_ACTOR).state.remaining:
            return TurnRejected(failure("DIALOGUE_SPEAKING"), command.expected_revision)
        return self.inner.admit(command, state, start_tick=start_tick, world_id=world_id)


class ConversationAdapter:
    key = CONVERSATION

    def validate(self, record: ComponentRecord) -> None:
        if (
            type(record) is not ConversationRecord
            or not isinstance(record, ConversationRecord)
            or record.entity_id != WORLD_ACTOR
            or type(record.entity_id) is not str
            or type(record.state) is not ConversationState
        ):
            raise ValueError("DIALOGUE_RECORD")
        ConversationState(record.state.exchanges, record.state.speaker, record.state.remaining)

    def wrap(self, record: ComponentRecord, access: ViewAccess) -> ConversationRead:
        self.validate(record)
        if not isinstance(record, ConversationRecord):
            raise ValueError("DIALOGUE_RECORD")
        return _StateView(record.state, CONVERSATION_FAMILY, record.entity_id, access)


class ConversationCodec:
    schema = CONVERSATION_SCHEMA

    def encode(self, record: ComponentRecord) -> JsonObject:
        ConversationAdapter().validate(record)
        if not isinstance(record, ConversationRecord):
            raise ValueError("DIALOGUE_RECORD")
        return {
            "state": {
                "exchanges": tuple(encode_exchange(e) for e in record.state.exchanges),
                "speaker": record.state.speaker,
                "remaining": record.state.remaining,
            }
        }

    def decode(self, entity_id: EntityId, fields: JsonObject) -> ComponentRecord:
        row = exact_fields(fields, ("state",))
        d = exact_fields(row["state"], ("exchanges", "speaker", "remaining"))
        record = ConversationRecord(
            entity_id,
            ConversationState(
                tuple(decode_exchange(object_value(e)) for e in array_value(d["exchanges"])),
                text_value(d["speaker"]),
                int_value(d["remaining"]),
            ),
        )
        ConversationAdapter().validate(record)
        return record


def _validate_change(delta: ConversationDelta) -> None:
    if delta.entity_id != WORLD_ACTOR or type(delta.entity_id) is not str:
        raise ValueError("DIALOGUE_DELTA")
    require_integer(delta.before_count, 0, MAX_EXCHANGES)
    require_integer(delta.before_remaining)
    require_integer(delta.remaining)
    if (
        type(delta.before_digest) is not str
        or re.fullmatch("[0-9a-f]{64}", delta.before_digest) is None
        or type(delta.before_speaker) is not str
        or delta.before_speaker not in ("", "player", "npc")
        or type(delta.speaker) is not str
        or delta.speaker not in ("", "player", "npc")
        or type(delta.append) is not bool
        or type(delta.entry) is not Exchange
    ):
        raise ValueError("DIALOGUE_DELTA")
    encode_exchange(delta.entry)


def _encode_change(delta: ConversationDelta) -> JsonObject:
    _validate_change(delta)
    return object_value(seal(asdict(delta)))


def _decode_change(data: JsonObject) -> ConversationDelta:
    d = exact_fields(data, DELTA_FIELDS)
    append = d["append"]
    if type(append) is not bool:
        raise ValueError("DIALOGUE_DELTA")
    delta = ConversationDelta(
        EntityId(text_value(d["entity_id"])),
        int_value(d["before_count"]),
        text_value(d["before_digest"]),
        text_value(d["before_speaker"]),
        int_value(d["before_remaining"]),
        decode_exchange(object_value(d["entry"])),
        text_value(d["speaker"]),
        int_value(d["remaining"]),
        append,
    )
    _validate_change(delta)
    return delta


class ConversationPayloadCodec:
    def __init__(self, schema: TypeKey) -> None:
        self.schema = schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise SchemaError("UNSUPPORTED_SCHEMA", "conversation payload")
        if type(payload) is PlayerSay and isinstance(payload, PlayerSay):
            if type(payload.npc_id) is not str or type(payload.text) is not str:
                raise ValueError("DIALOGUE_TEXT")
            return {"npc_id": payload.npc_id, "text": payload.text}
        if type(payload) is ContinueSpeech and isinstance(payload, ContinueSpeech):
            if type(payload.speech_id) is not str:
                raise ValueError("DIALOGUE_NO_SPEECH")
            return {"speech_id": payload.speech_id}
        if type(payload) is NpcReply and isinstance(payload, NpcReply):
            if any(
                type(v) is not str
                for v in (
                    payload.speech_id,
                    payload.text,
                    payload.model,
                    payload.context_sha256,
                    payload.proposal,
                )
            ):
                raise ValueError("DIALOGUE_REPLY_PROVENANCE")
            return object_value(seal(asdict(payload)))
        if type(payload) is ConversationDelta and isinstance(payload, ConversationDelta):
            return _encode_change(payload)
        if type(payload) is ConversationPatch and isinstance(payload, ConversationPatch):
            return {"change": _encode_change(payload.change)}
        if type(payload) in (SpeechAdvanced, SpeechCue) and isinstance(
            payload, (SpeechAdvanced, SpeechCue)
        ):
            if payload.actor_id != WORLD_ACTOR or payload.speaker not in ("player", "npc"):
                raise ValueError("DIALOGUE_SPEECH_FACT")
            require_namespace(payload.speech_id)
            require_integer(payload.start)
            require_integer(payload.end, payload.start + 1, payload.start + SPEECH_SEGMENT_SECONDS)
            return object_value(seal(asdict(payload)))
        raise SchemaError("UNSUPPORTED_SCHEMA", "conversation class")

    def decode(self, data: JsonObject) -> FrozenPayload:
        result: FrozenPayload
        if self.schema == PlayerSay.SCHEMA:
            d = exact_fields(data, ("npc_id", "text"))
            result = PlayerSay(text_value(d["npc_id"]), text_value(d["text"]))
        elif self.schema == ContinueSpeech.SCHEMA:
            result = ContinueSpeech(text_value(exact_fields(data, ("speech_id",))["speech_id"]))
        elif self.schema == NpcReply.SCHEMA:
            d = exact_fields(data, ("speech_id", "text", "model", "context_sha256", "proposal"))
            result = NpcReply(
                text_value(d["speech_id"]),
                text_value(d["text"]),
                text_value(d["model"]),
                text_value(d["context_sha256"]),
                text_value(d["proposal"]),
            )
        elif self.schema == ConversationDelta.SCHEMA:
            result = _decode_change(data)
        elif self.schema == ConversationPatch.SCHEMA:
            result = ConversationPatch(
                _decode_change(object_value(exact_fields(data, ("change",))["change"]))
            )
        elif self.schema in (SpeechAdvanced.SCHEMA, SpeechCue.SCHEMA):
            d = exact_fields(data, ("actor_id", "speech_id", "speaker", "start", "end"))
            cls = SpeechAdvanced if self.schema == SpeechAdvanced.SCHEMA else SpeechCue
            result = cls(
                EntityId(text_value(d["actor_id"])),
                text_value(d["speech_id"]),
                text_value(d["speaker"]),
                int_value(d["start"]),
                int_value(d["end"]),
            )
        else:
            raise SchemaError("UNSUPPORTED_SCHEMA", "conversation schema")
        self.encode(result)
        return result


def apply_change(before: ConversationState, delta: ConversationDelta) -> ConversationState:
    _validate_change(delta)
    old = before.exchanges[-1] if before.exchanges else None
    if (
        len(before.exchanges) != delta.before_count
        or exchange_digest(old) != delta.before_digest
        or before.speaker != delta.before_speaker
        or before.remaining != delta.before_remaining
    ):
        raise ValueError("DIALOGUE_DELTA_BEFORE")
    if delta.append:
        if before.remaining or delta.entry.reply_text:
            raise ValueError("DIALOGUE_DELTA_TRANSITION")
        duration = delta.entry.player_end - delta.entry.player_start
        entries = (*before.exchanges, delta.entry)
        speaker = "player"
        remaining = max(0, duration - SPEECH_SEGMENT_SECONDS)
    elif old is None:
        raise ValueError("DIALOGUE_DELTA_TRANSITION")
    elif before.remaining:
        if delta.entry != old:
            raise ValueError("DIALOGUE_DELTA_TRANSITION")
        entries = before.exchanges
        speaker = before.speaker
        remaining = max(0, before.remaining - SPEECH_SEGMENT_SECONDS)
    else:
        if (
            old.reply_text
            or not delta.entry.reply_text
            or replace(
                delta.entry,
                reply_text="",
                reply_start=0,
                reply_end=0,
                model="",
                context_sha256="",
                proposal="none",
            )
            != old
        ):
            raise ValueError("DIALOGUE_DELTA_TRANSITION")
        entries = (*before.exchanges[:-1], delta.entry)
        speaker = "npc"
        duration = delta.entry.reply_end - delta.entry.reply_start
        remaining = max(0, duration - SPEECH_SEGMENT_SECONDS)
    if delta.remaining != remaining or delta.speaker != (speaker if remaining else ""):
        raise ValueError("DIALOGUE_DELTA_PROGRESS")
    return ConversationState(entries, delta.speaker, delta.remaining)


class ConversationReducer:
    schema = ConversationDelta.SCHEMA
    owner_id = CONVERSATION_OWNER

    def _delta(self, delta: StateDelta) -> ConversationDelta:
        if type(delta) is not ConversationDelta or not isinstance(delta, ConversationDelta):
            raise CandidateError("INVALID_DELTA", "conversation class")
        _validate_change(delta)
        return delta

    def stage(self, delta: StateDelta, before: ReadPort, editor: StagingEditor) -> None:
        value = self._delta(delta)
        try:
            apply_change(before.component(CONVERSATION, value.entity_id).state, value)
        except ValueError as error:
            raise CandidateError("INVALID_DELTA", str(error)) from error
        editor.apply_patch(
            ComponentAddress(CONVERSATION_SCHEMA, value.entity_id), ConversationPatch(value)
        )

    def compose(self, changes: tuple[StateDelta, ...]) -> StateDelta:
        if len(changes) != 1:
            raise CandidateError("INVALID_DELTA", "one conversation change per command")
        return self._delta(changes[0])

    def is_identity(self, delta: StateDelta) -> bool:
        self._delta(delta)
        return False

    def validate_net(self, delta: StateDelta, after: ReadPort) -> None:
        value = self._delta(delta)
        state = after.component(CONVERSATION, value.entity_id).state
        if (
            len(state.exchanges) != value.before_count + int(value.append)
            or not state.exchanges
            or state.exchanges[-1] != value.entry
            or state.speaker != value.speaker
            or state.remaining != value.remaining
        ):
            raise CandidateError("INVALID_DELTA", "conversation net mismatch")


class ConversationPatchRoute:
    schema = ConversationPatch.SCHEMA
    component_schema = CONVERSATION_SCHEMA
    family = CONVERSATION_FAMILY

    def apply(self, before: ComponentRecord, patch: ComponentPatch) -> ComponentRecord:
        if (
            type(before) is not ConversationRecord
            or not isinstance(before, ConversationRecord)
            or type(patch) is not ConversationPatch
            or not isinstance(patch, ConversationPatch)
        ):
            raise ValueError("DIALOGUE_PATCH")
        return replace(before, state=apply_change(before.state, patch.change))


class ConversationCheckpointPolicy:
    def __init__(self, world: WorldCatalog, scenario: SupplyScenario) -> None:
        self.world, self.scenario = world, scenario

    def validate(self, core: CoreSnapshot, protocol: ProtocolSnapshot) -> None:
        records = tuple(c for c in core.components if isinstance(c, ConversationRecord))
        if len(records) != 1:
            raise ValueError("DIALOGUE_CHECKPOINT")
        SupplyCheckpointPolicy(self.world, self.scenario).validate(
            replace(
                core,
                components=tuple(
                    c for c in core.components if not isinstance(c, ConversationRecord)
                ),
            ),
            protocol,
        )
        record = records[0]
        ConversationAdapter().validate(record)
        travel = next(c.state for c in core.components if isinstance(c, TravelerRecord))
        state = record.state
        for index, entry in enumerate(state.exchanges):
            if entry.place_id not in travel.visited:
                raise ValueError("DIALOGUE_VISIT_BINDING")
            local = elaborate_place(self.world, entry.place_id)
            npc_index = next(
                (i for i, r in enumerate(local.residents) if r.id == entry.npc_id), None
            )
            if npc_index is None:
                raise ValueError("DIALOGUE_NPC_BINDING")
            if entry.reply_text and entry.reply_end - entry.reply_start != speech_seconds(
                entry.reply_text, npc_rate(local.residents[npc_index])
            ):
                raise ValueError("DIALOGUE_DURATION")
            if entry.proposal != "none" and (
                (npc_index == 0 and entry.proposal != "collect")
                or (npc_index == 1 and entry.proposal not in ("accept", "deliver"))
                or npc_index > 1
            ):
                raise ValueError("DIALOGUE_PROPOSAL")
            end = entry.reply_end or entry.player_end
            if index == len(state.exchanges) - 1 and state.remaining:
                if (
                    end - core.tick != state.remaining
                    or travel.destination_id
                    or travel.place_id != entry.place_id
                ):
                    raise ValueError("DIALOGUE_TICK_BINDING")
            elif end > core.tick:
                raise ValueError("DIALOGUE_TICK_BINDING")


class SpeechPresenter:
    def map(
        self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort
    ) -> tuple[PresentationEvent, ...]:
        cues: list[PresentationEvent] = []
        for event in facts:
            p = event.payload
            if type(p) is not SpeechAdvanced or not isinstance(p, SpeechAdvanced):
                raise SchemaError("UNSUPPORTED_SCHEMA", "speech presenter")
            if (
                committed.component(CONVERSATION, p.actor_id).state.exchanges[-1].speech_id
                != p.speech_id
            ):
                raise ValueError("DIALOGUE_PRESENTATION_STATE")
            identifier = (
                "p1-"
                + hashlib.sha256(
                    pack(
                        (
                            "cue-id/v1",
                            event.header.event_id,
                            "world.speech-presenter",
                            str(len(cues)),
                        )
                    )
                ).hexdigest()
            )
            cue = SpeechCue(p.actor_id, p.speech_id, p.speaker, p.start, p.end)
            cues.append(
                PresentationEvent(
                    EventHeader(
                        EventId(identifier),
                        cue.schema,
                        "world.speech-presenter",
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
