"""Saved own conversation history and deterministic utterance durations."""

from dataclasses import asdict, dataclass, replace
import hashlib
import re
import unicodedata
from types import MappingProxyType

from domain.canonical import canonical_json, seal
from domain.primitives import EntityId, TypeKey, require_integer, require_namespace
from domain.state_types import ComponentRecord
from domain.world import Resident

CONVERSATION_SCHEMA = TypeKey("world.conversation", 1)
MAX_SPEECH_CHARACTERS = 512
MAX_EXCHANGES = 4096
SPEECH_SEGMENT_SECONDS = 16
PLAYER_CHARACTERS_PER_SECOND = 6
NPC_RATES = MappingProxyType({"신중함": 4, "사교적": 6, "과묵함": 5, "호기심 많음": 7})
PROPOSALS = ("none", "accept", "collect", "deliver")


def validate_speech(text: str) -> None:
    if (
        type(text) is not str
        or not 1 <= len(text) <= MAX_SPEECH_CHARACTERS
        or not text.strip()
        or unicodedata.normalize("NFC", text) != text
        or any(unicodedata.category(c) in ("Cc", "Cs") and c not in "\n\t" for c in text)
    ):
        raise ValueError("DIALOGUE_TEXT")
    text.encode("utf-8", errors="strict")


def speech_seconds(text: str, characters_per_second: int) -> int:
    validate_speech(text)
    require_integer(characters_per_second, 1, 20)
    return (len(text) + characters_per_second - 1) // characters_per_second


def npc_rate(resident: Resident) -> int:
    return NPC_RATES[resident.disposition]


@dataclass(frozen=True, slots=True)
class Exchange:
    speech_id: str
    npc_id: str
    place_id: str
    player_text: str
    player_start: int
    player_end: int
    reply_text: str = ""
    reply_start: int = 0
    reply_end: int = 0
    model: str = ""
    context_sha256: str = ""
    proposal: str = "none"

    def __post_init__(self) -> None:
        for value in (
            self.speech_id,
            self.npc_id,
            self.place_id,
            self.reply_text,
            self.model,
            self.context_sha256,
            self.proposal,
        ):
            if type(value) is not str:
                raise ValueError("DIALOGUE_EXCHANGE")
        require_namespace(self.speech_id)
        require_namespace(self.npc_id)
        require_namespace(self.place_id)
        validate_speech(self.player_text)
        require_integer(self.player_start)
        require_integer(self.player_end, self.player_start + 1)
        require_integer(self.reply_start)
        require_integer(self.reply_end)
        if self.player_end - self.player_start != speech_seconds(
            self.player_text, PLAYER_CHARACTERS_PER_SECOND
        ):
            raise ValueError("DIALOGUE_DURATION")
        if self.proposal not in PROPOSALS:
            raise ValueError("DIALOGUE_PROPOSAL")
        if self.reply_text:
            validate_speech(self.reply_text)
            if (
                self.reply_start < self.player_end
                or self.reply_end <= self.reply_start
                or re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", self.model) is None
                or re.fullmatch(r"[0-9a-f]{64}", self.context_sha256) is None
            ):
                raise ValueError("DIALOGUE_REPLY_PROVENANCE")
        elif (
            self.reply_start
            or self.reply_end
            or self.model
            or self.context_sha256
            or self.proposal != "none"
        ):
            raise ValueError("DIALOGUE_REPLY_PROVENANCE")


@dataclass(frozen=True, slots=True)
class ConversationState:
    exchanges: tuple[Exchange, ...] = ()
    speaker: str = ""
    remaining: int = 0

    def __post_init__(self) -> None:
        if type(self.exchanges) is not tuple or len(self.exchanges) > MAX_EXCHANGES:
            raise ValueError("DIALOGUE_HISTORY")
        ids = []
        previous_end = 0
        for exchange in self.exchanges:
            if type(exchange) is not Exchange:
                raise ValueError("DIALOGUE_HISTORY")
            Exchange(**asdict(exchange))
            if exchange.player_start < previous_end:
                raise ValueError("DIALOGUE_ORDER")
            previous_end = exchange.reply_end or exchange.player_end
            ids.append(exchange.speech_id)
        if len(set(ids)) != len(ids):
            raise ValueError("DIALOGUE_DUPLICATE")
        require_integer(self.remaining)
        if (
            type(self.speaker) is not str
            or self.speaker not in ("", "player", "npc")
            or bool(self.speaker) != bool(self.remaining)
            or (self.speaker and not self.exchanges)
        ):
            raise ValueError("DIALOGUE_PROGRESS")
        if self.exchanges and self.speaker:
            last = self.exchanges[-1]
            duration = (
                last.player_end - last.player_start
                if self.speaker == "player"
                else last.reply_end - last.reply_start
            )
            if (
                self.remaining >= duration
                or (self.speaker == "player" and last.reply_text)
                or duration <= 0
            ):
                raise ValueError("DIALOGUE_PROGRESS")


@dataclass(frozen=True, slots=True)
class ConversationRecord(ComponentRecord):
    entity_id: EntityId
    state: ConversationState

    @property
    def schema(self) -> TypeKey:
        return CONVERSATION_SCHEMA


def exchange_digest(exchange: Exchange | None) -> str:
    return hashlib.sha256(
        canonical_json(None if exchange is None else seal(asdict(exchange)))
    ).hexdigest()


def begin_speech(
    state: ConversationState,
    resident: Resident,
    place_id: str,
    text: str,
    speech_id: str,
    start_tick: int,
) -> tuple[ConversationState, int]:
    if state.remaining:
        raise ValueError("DIALOGUE_SPEAKING")
    if len(state.exchanges) >= MAX_EXCHANGES:
        raise ValueError("DIALOGUE_HISTORY_FULL")
    seconds = speech_seconds(text, PLAYER_CHARACTERS_PER_SECOND)
    entry = Exchange(speech_id, resident.id, place_id, text, start_tick, start_tick + seconds)
    elapsed = min(SPEECH_SEGMENT_SECONDS, seconds)
    remaining = seconds - elapsed
    return ConversationState(
        (*state.exchanges, entry), "player" if remaining else "", remaining
    ), elapsed


def begin_reply(
    state: ConversationState,
    resident: Resident,
    speech_id: str,
    text: str,
    model: str,
    context_sha256: str,
    proposal: str,
    start_tick: int,
) -> tuple[ConversationState, int]:
    if state.remaining:
        raise ValueError("DIALOGUE_SPEAKING")
    if not state.exchanges or state.exchanges[-1].speech_id != speech_id:
        raise ValueError("DIALOGUE_STALE")
    before = state.exchanges[-1]
    if before.reply_text:
        raise ValueError("DIALOGUE_ALREADY_REPLIED")
    if before.npc_id != resident.id:
        raise ValueError("DIALOGUE_WRONG_NPC")
    seconds = speech_seconds(text, npc_rate(resident))
    entry = replace(
        before,
        reply_text=text,
        reply_start=start_tick,
        reply_end=start_tick + seconds,
        model=model,
        context_sha256=context_sha256,
        proposal=proposal,
    )
    elapsed = min(SPEECH_SEGMENT_SECONDS, seconds)
    remaining = seconds - elapsed
    return ConversationState(
        (*state.exchanges[:-1], entry), "npc" if remaining else "", remaining
    ), elapsed


def continue_speech(state: ConversationState, speech_id: str) -> tuple[ConversationState, int]:
    if not state.remaining or not state.exchanges or state.exchanges[-1].speech_id != speech_id:
        raise ValueError("DIALOGUE_NO_SPEECH")
    elapsed = min(SPEECH_SEGMENT_SECONDS, state.remaining)
    remaining = state.remaining - elapsed
    return replace(state, speaker=state.speaker if remaining else "", remaining=remaining), elapsed


def _terms(text: str) -> frozenset[str]:
    words = re.findall(r"\w+", text.casefold())
    return frozenset((*words, *(word[i : i + 2] for word in words for i in range(len(word) - 1))))


def retrieve_memories(
    state: ConversationState, npc_id: str, query: str, *, byte_budget: int = 4096, limit: int = 6
) -> tuple[Exchange, ...]:
    require_integer(byte_budget)
    require_integer(limit, 0, 32)
    # The current player's pending utterance is supplied separately,never duplicated as history.
    own = tuple(e for e in state.exchanges[:-1] if e.npc_id == npc_id)
    terms = _terms(query)
    recent = list(range(max(0, len(own) - 2), len(own)))[::-1]
    relevant = sorted(
        (
            (len(terms & _terms(e.player_text + " " + e.reply_text)), i)
            for i, e in enumerate(own[: max(0, len(own) - 2)])
        ),
        reverse=True,
    )
    candidates = (*recent, *(i for score, i in relevant if score))
    selected: list[int] = []
    used = 0
    for index in candidates:
        size = len(canonical_json(seal(asdict(own[index]))))
        if len(selected) < limit and used + size <= byte_budget:
            selected.append(index)
            used += size
    return tuple(own[i] for i in sorted(selected))
