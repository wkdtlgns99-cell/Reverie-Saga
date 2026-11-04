"""COMMIT-owned speech and memory;no live provider,wall clock or economy authority."""

from contracts.errors import CandidateError
from contracts.messages import EmittedFact
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from contracts.world_conversation import (
    CONVERSATION,
    CONVERSATION_FAMILY,
    CONVERSATION_OWNER,
    ConversationDelta,
    ContinueSpeech,
    NpcReply,
    PlayerSay,
    SpeechAdvanced,
)
from contracts.world_population import SETTLEMENT, SETTLEMENT_FAMILY
from contracts.world_travel import TRAVELER, TRAVEL_FAMILY
from domain.primitives import EntityId, Phase
from domain.world_conversation import (
    PLAYER_CHARACTERS_PER_SECOND,
    SPEECH_SEGMENT_SECONDS,
    begin_reply,
    begin_speech,
    continue_speech,
    exchange_digest,
    npc_rate,
    speech_seconds,
)


class WorldConversation:
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            CONVERSATION_OWNER,
            (Phase.RESOLVE,),
            tuple(
                PhaseAccess(Phase.RESOLVE, f)
                for f in (CONVERSATION_FAMILY, SETTLEMENT_FAMILY, TRAVEL_FAMILY)
            ),
            (PhaseAccess(Phase.RESOLVE, CONVERSATION_FAMILY),),
            (),
            (SpeechAdvanced.SCHEMA,),
            (),
            "local",
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        action = invocation.action
        if action is None:
            raise CandidateError("INVALID_COMMAND", "conversation invocation")
        before = invocation.state.component(CONVERSATION, action.actor_id).state
        payload = action.payload
        if isinstance(payload, ContinueSpeech):
            after, duration = continue_speech(before, payload.speech_id)
            speaker = before.speaker
        else:
            traveler = invocation.state.component(TRAVELER, action.actor_id).state
            local = invocation.state.component(SETTLEMENT, EntityId(traveler.place_id)).state
            if local is None:
                raise CandidateError("INVALID_COMMAND", "missing saved local NPC")
            npc_id = (
                payload.npc_id
                if isinstance(payload, PlayerSay)
                else before.exchanges[-1].npc_id
                if isinstance(payload, NpcReply) and before.exchanges
                else ""
            )
            resident = next((r for r in local.residents if r.id == npc_id), None)
            if resident is None:
                raise CandidateError("INVALID_COMMAND", "missing saved NPC")
            if isinstance(payload, PlayerSay):
                duration = min(
                    SPEECH_SEGMENT_SECONDS,
                    speech_seconds(payload.text, PLAYER_CHARACTERS_PER_SECOND),
                )
                after, duration = begin_speech(
                    before,
                    resident,
                    traveler.place_id,
                    payload.text,
                    "speech:s" + action.semantic_key.removeprefix("a1-"),
                    invocation.logical_tick - duration,
                )
                speaker = "player"
            elif isinstance(payload, NpcReply):
                duration = min(
                    SPEECH_SEGMENT_SECONDS, speech_seconds(payload.text, npc_rate(resident))
                )
                after, duration = begin_reply(
                    before,
                    resident,
                    payload.speech_id,
                    payload.text,
                    payload.model,
                    payload.context_sha256,
                    payload.proposal,
                    invocation.logical_tick - duration,
                )
                speaker = "npc"
            else:
                raise CandidateError("INVALID_COMMAND", "conversation payload")
        entry = after.exchanges[-1]
        delta = ConversationDelta(
            action.actor_id,
            len(before.exchanges),
            exchange_digest(before.exchanges[-1] if before.exchanges else None),
            before.speaker,
            before.remaining,
            entry,
            after.speaker,
            after.remaining,
            len(after.exchanges) > len(before.exchanges),
        )
        fact = SpeechAdvanced(
            action.actor_id,
            entry.speech_id,
            speaker,
            invocation.logical_tick - duration,
            invocation.logical_tick,
        )
        return EngineResult((delta,), (EmittedFact(fact, invocation.logical_tick, ()),), ())
