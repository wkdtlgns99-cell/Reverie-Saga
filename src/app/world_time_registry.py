"""Compose world clock support while preserving the original foot-only bundle."""

from dataclasses import replace

from app.world_registry import world_bundle
from contracts.messages import EventPolicy
from contracts.skeleton import FeatureBundle, PresenterBinding
from contracts.turn import EngineBinding, NodeActivation, NodeKey
from contracts.world_time import TIME_PAYLOADS, TimePassed, WorldWait
from domain.canonical import array_value, object_value, seal
from domain.primitives import Phase
from domain.world import WorldCatalog
from engines.world_time import WorldTime
from orchestration.world_time import TimeCodec, TimePresenter, WorldWaitAdmission


def timed_world_bundle(world: WorldCatalog) -> FeatureBundle:
    base = world_bundle(world)
    engine = WorldTime()
    schema = dict(base.schema_document)
    schema["payloads"] = (
        *array_value(schema["payloads"]),
        {"schema": {"kind": "world.wait", "version": 1}, "fields": ("seconds",)},
        {"schema": {"kind": "world.time-passed", "version": 1}, "fields": ("start", "end")},
        {"schema": {"kind": "world.time-cue", "version": 1}, "fields": ("start", "end")},
    )
    schema["system"] = {
        "clock_owner": "system.clock",
        "queue_owner": "system.events",
        "pending_format": "queued-event/v1",
    }
    rules = dict(base.rules_document)
    policies = (
        *base.events,
        EventPolicy(
            TimePassed.SCHEMA, "record_only", Phase.PRESENT, 0, "reject", ("world.time",), (), ()
        ),
    )
    rules["event_policies"] = tuple(
        {
            "schema": {"kind": policy.schema.kind, "version": policy.schema.version},
            "mode": policy.mode,
            "delivery_phase": policy.delivery_phase.name,
            "priority": policy.priority,
            "late_route": policy.late_route,
            "producers": tuple(sorted(policy.producers)),
            "subscribers": tuple(sorted(policy.subscribers)),
            "cancellers": (),
        }
        for policy in sorted(policies, key=lambda p: (p.schema.kind, p.schema.version))
    )
    rules["execution"] = {
        "enable_simulation": True,
        "max_duration_seconds": 16,
        "cascade_waves": 1,
        "max_events_per_tick": 16,
        "max_pending": 1,
    }
    rules["clock"] = {
        "real_ns_per_idle_second": 10_000_000_000,
        "resolution_seconds": 1,
        "maximum_wait_seconds": 16,
        "fractional_idle_carry": "derived-session-only",
        "pause_and_provider_wait": "exclude",
    }
    return replace(
        base,
        feature_id="world-time-v1",
        bindings=(
            *base.bindings,
            EngineBinding(
                engine,
                "engines.world_time",
                (
                    NodeActivation(
                        NodeKey(Phase.RESOLVE, "world.time"), (WorldWait.SCHEMA,), False, False, "A"
                    ),
                ),
            ),
        ),
        events=policies,
        command_routes=(*base.command_routes, WorldWaitAdmission()),
        presenters=(
            *base.presenters,
            PresenterBinding("world.time-presenter", (TimePassed.SCHEMA,), TimePresenter()),
        ),
        codecs=(*base.codecs, *(TimeCodec(kind.SCHEMA) for kind in TIME_PAYLOADS)),
        schema_document=object_value(seal(schema)),
        rules_document=object_value(seal(rules)),
    )
