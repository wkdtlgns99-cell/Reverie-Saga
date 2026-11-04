"""Accepted speech commands,own-memory changes and live generation input/output."""

from dataclasses import asdict, dataclass
import hashlib
from typing import Protocol

from contracts.messages import CommandPayload, FactPayload, PresentationPayload, StateDelta
from contracts.read_views import ComponentKey, ComponentPatch
from domain.canonical import JsonObject, canonical_json, object_value, seal
from domain.primitives import EntityId, FieldAddress, FieldFamily, TypeKey
from domain.world_conversation import CONVERSATION_SCHEMA, ConversationState, Exchange

CONVERSATION_OWNER = "world.conversation"
CONVERSATION_FAMILY = FieldFamily(CONVERSATION_SCHEMA.kind, "state")


class ConversationRead(Protocol):
    @property
    def state(self) -> ConversationState: ...


CONVERSATION = ComponentKey[ConversationRead](CONVERSATION_SCHEMA)


@dataclass(frozen=True, slots=True)
class PlayerSay(CommandPayload):
    npc_id: str
    text: str
    SCHEMA = TypeKey("world.player-say", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class ContinueSpeech(CommandPayload):
    speech_id: str
    SCHEMA = TypeKey("world.continue-speech", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class NpcReply(CommandPayload):
    speech_id: str
    text: str
    model: str
    context_sha256: str
    proposal: str
    SCHEMA = TypeKey("world.npc-reply", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class ConversationDelta(StateDelta):
    entity_id: EntityId
    before_count: int
    before_digest: str
    before_speaker: str
    before_remaining: int
    entry: Exchange
    speaker: str
    remaining: int
    append: bool
    SCHEMA = TypeKey("world.conversation-delta", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA

    @property
    def target(self) -> FieldAddress:
        return FieldAddress(CONVERSATION_FAMILY, self.entity_id)


@dataclass(frozen=True, slots=True)
class ConversationPatch(ComponentPatch):
    change: ConversationDelta
    SCHEMA = TypeKey("world.conversation-patch", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class SpeechAdvanced(FactPayload):
    actor_id: EntityId
    speech_id: str
    speaker: str
    start: int
    end: int
    SCHEMA = TypeKey("world.speech-advanced", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class SpeechCue(PresentationPayload):
    actor_id: EntityId
    speech_id: str
    speaker: str
    start: int
    end: int
    SCHEMA = TypeKey("world.speech-cue", 1)

    @property
    def schema(self) -> TypeKey:
        return self.SCHEMA


@dataclass(frozen=True, slots=True)
class ConversationContext:
    npc_id: str
    npc_name: str
    occupation: str
    disposition: str
    place_name: str
    country_name: str
    livelihood: str
    environment: str
    logical_tick: int
    activity: str
    site: str
    public_facts: tuple[tuple[str, str], ...]
    available_action: str
    current: Exchange
    memories: tuple[Exchange, ...]

    def document(self) -> JsonObject:
        return object_value(seal(asdict(self)))

    @property
    def sha256(self) -> str:
        return hashlib.sha256(canonical_json(self.document())).hexdigest()


@dataclass(frozen=True, slots=True)
class GeneratedReply:
    text: str
    proposal: str
    model: str
    context_sha256: str
    total_tokens: int | None = None


class ConversationGenerator(Protocol):
    def generate(self, context: ConversationContext) -> GeneratedReply: ...
    def cancel(self) -> None: ...


CONVERSATION_PAYLOADS = (
    PlayerSay,
    ContinueSpeech,
    NpcReply,
    ConversationDelta,
    ConversationPatch,
    SpeechAdvanced,
    SpeechCue,
)
