"""Compose live-conversation state with the unchanged supply/world infrastructure."""

from dataclasses import fields, replace

from app.world_supply_registry import supply_world_bundle
from contracts.messages import EventPolicy
from contracts.read_views import AdapterBinding
from contracts.skeleton import FeatureBundle, PresenterBinding
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from contracts.world_conversation import (
    CONVERSATION_FAMILY,
    CONVERSATION_OWNER,
    CONVERSATION_PAYLOADS,
    ContinueSpeech,
    NpcReply,
    PlayerSay,
    SpeechAdvanced,
)
from contracts.world_population import SETTLEMENT_FAMILY
from contracts.world_travel import TRAVEL_FAMILY
from domain.canonical import array_value, object_value, seal
from domain.primitives import FieldSpec, Phase
from domain.world import WorldCatalog
from domain.world_conversation import (
    MAX_EXCHANGES,
    MAX_SPEECH_CHARACTERS,
    NPC_RATES,
    PLAYER_CHARACTERS_PER_SECOND,
    SPEECH_SEGMENT_SECONDS,
)
from domain.world_supply import SupplyScenario
from engines.world_conversation import WorldConversation
from orchestration.world_conversation import (
    ConversationAdapter,
    ConversationAdmission,
    ConversationCheckpointPolicy,
    ConversationCodec,
    ConversationPatchRoute,
    ConversationPayloadCodec,
    ConversationReducer,
    SpeechGate,
    SpeechPresenter,
)


def conversation_world_bundle(
    world: WorldCatalog, scenario: SupplyScenario = SupplyScenario()
) -> FeatureBundle:
    base = supply_world_bundle(world, scenario)
    schema = dict(base.schema_document)
    schema["components"] = (
        *array_value(schema["components"]),
        {
            "schema": {"kind": "world.conversation", "version": 1},
            "fields": {
                "state": {
                    "owner": CONVERSATION_OWNER,
                    "storage": "CORE",
                    "tier": "A",
                    "unit": "conversation_history",
                    "scale": 1,
                }
            },
        },
    )
    schema["payloads"] = (
        *array_value(schema["payloads"]),
        *(
            {
                "schema": {"kind": cls.SCHEMA.kind, "version": cls.SCHEMA.version},
                "fields": tuple(f.name for f in fields(cls)),
            }
            for cls in CONVERSATION_PAYLOADS
        ),
    )
    policies = (
        *base.events,
        EventPolicy(
            SpeechAdvanced.SCHEMA,
            "record_only",
            Phase.PRESENT,
            0,
            "reject",
            (CONVERSATION_OWNER,),
            (),
            (),
        ),
    )
    rules = dict(base.rules_document)
    rules["conversation"] = {
        "text_limit_codepoints": MAX_SPEECH_CHARACTERS,
        "normalization": "strict-NFC",
        "player_codepoints_per_second": PLAYER_CHARACTERS_PER_SECOND,
        "npc_rates": NPC_RATES,
        "max_exchanges": MAX_EXCHANGES,
        "segment_seconds": SPEECH_SEGMENT_SECONDS,
        "memory": "all-accepted-exchanges-no-silent-retirement",
        "context": "own-recent-and-relevant-v1-4096bytes",
        "speech_is": "heard-content-not-objective-truth-or-formal-quest",
        "reach": "same-city-saved-awake-NPC",
        "provider_wait": "excluded",
        "failed_reply": "retain-player-speech-retry-or-continue",
    }
    rules["event_policies"] = tuple(
        {
            "schema": {"kind": p.schema.kind, "version": p.schema.version},
            "mode": p.mode,
            "delivery_phase": p.delivery_phase.name,
            "priority": p.priority,
            "late_route": p.late_route,
            "producers": tuple(sorted(p.producers)),
            "subscribers": tuple(sorted(p.subscribers)),
            "cancellers": (),
        }
        for p in sorted(policies, key=lambda p: (p.schema.kind, p.schema.version))
    )
    specs = tuple(
        replace(s, consumers=tuple(sorted(set((*s.consumers, CONVERSATION_OWNER)))))
        if s.family in (SETTLEMENT_FAMILY, TRAVEL_FAMILY)
        else s
        for s in base.field_specs
    )
    kinds = (PlayerSay, ContinueSpeech, NpcReply)
    return replace(
        base,
        feature_id="world-conversation-v1",
        bindings=(
            *base.bindings,
            EngineBinding(
                WorldConversation(),
                "engines.world_conversation",
                (
                    NodeActivation(
                        NodeKey(Phase.RESOLVE, CONVERSATION_OWNER),
                        tuple(cls.SCHEMA for cls in kinds),
                        False,
                        False,
                        "A",
                    ),
                ),
            ),
        ),
        read_adapters=(*base.read_adapters, AdapterBinding(ConversationAdapter())),
        field_specs=(
            *specs,
            FieldSpec(
                CONVERSATION_FAMILY,
                "CORE",
                "A",
                CONVERSATION_OWNER,
                ("system.admission", CONVERSATION_OWNER),
                "records",
                "conversation_history",
                1,
                None,
                None,
                MAX_EXCHANGES,
            ),
        ),
        events=policies,
        command_routes=(
            *(SpeechGate(r) for r in base.command_routes),
            *(ConversationAdmission(world, scenario, cls.SCHEMA) for cls in kinds),
        ),
        delta_routes=(*base.delta_routes, ConversationReducer()),
        presenters=(
            *base.presenters,
            PresenterBinding("world.speech-presenter", (SpeechAdvanced.SCHEMA,), SpeechPresenter()),
        ),
        codecs=(
            *base.codecs,
            *(ConversationPayloadCodec(cls.SCHEMA) for cls in CONVERSATION_PAYLOADS),
        ),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
        component_codecs=(*base.component_codecs, ConversationCodec()),
        patch_routes=(*base.patch_routes, ConversationPatchRoute()),
        checkpoint_policy=ConversationCheckpointPolicy(world, scenario),
    )
