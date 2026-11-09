"""Select the registered village profile and upgrade old progress without rewriting it."""

from dataclasses import replace
import hashlib
from pathlib import Path
import secrets

from adapters.save_slots import LegacySlotProfile, SqliteSlots, cleanup_owned_clone
from adapters.sqlite_store import SqliteCommitStore, validate_save
from adapters.world_attachment import current_world, remember_world
from app.durable import DurableSession
from app.world_combat_registry import combat_world_bundle
from app.headless import state_io
from app.world_session import world_checkpoint
from app.world_transport_registry import transport_world_bundle
from app.world_village_registry import village_world_bundle
from contracts.persistence import DurableCheckpoint, SaveError
from contracts.skeleton import FeatureBundle
from contracts.state_io import StateIO
from domain.canonical import pack
from domain.world import WorldCatalog
from domain.world_combat import CombatRecord, CombatState
from domain.world_social import SocialCatalog
from domain.world_supply import SupplyScenario
from domain.world_transport import TransportRules
from domain.world_travel import WORLD_ACTOR
from domain.world_village import ENTRANCE, VillageRecord


def _upgrade(
    previous: DurableCheckpoint, io: StateIO, *, combat: bool = False
) -> DurableCheckpoint:
    core, protocol = previous.core, previous.protocol
    pins = io.pins
    world_id = (
        "w1-"
        + hashlib.sha256(
            pack(
                (
                    "world-id/v1",
                    core.world_seed_hex,
                    pins.rules_fingerprint,
                    pins.gameplay_catalog_hash,
                )
            )
        ).hexdigest()
    )
    records = core.components
    if not any(isinstance(record, VillageRecord) for record in records):
        records = (*records, VillageRecord(WORLD_ACTOR, ENTRANCE))
    if combat:
        records = (*records, CombatRecord(WORLD_ACTOR, CombatState()))
    components = tuple(
        sorted(
            records,
            key=lambda item: (item.schema.kind, item.schema.version, item.entity_id),
        )
    )
    upgraded = DurableCheckpoint(
        replace(core, world_id=world_id, pins=pins, components=components),
        replace(protocol, branch_id=secrets.token_hex(16), receipts=()),
    )
    io.validate_checkpoint(upgraded.core, upgraded.protocol)
    return upgraded


def _owner(
    store: SqliteCommitStore,
    bundle: FeatureBundle,
    io: StateIO,
    legacy: LegacySlotProfile | None = None,
) -> DurableSession:
    try:
        return DurableSession(store, (bundle,), io, legacy=legacy)
    except (ValueError, TypeError, RuntimeError, OSError):
        store.close()
        raise


def _current_owner(
    base: Path,
    store: SqliteCommitStore,
    bundle: FeatureBundle,
    io: StateIO,
    legacy: LegacySlotProfile | None = None,
) -> DurableSession:
    try:
        if current_world(base) != store.path:
            raise SaveError("WORLD_VIEW_CHANGED", "working branch changed")
    except (ValueError, TypeError, RuntimeError, OSError):
        store.close()
        raise
    return _owner(store, bundle, io, legacy)


def _upgrade_working(
    base: Path, source: Path, bundle: FeatureBundle, io: StateIO, legacy: LegacySlotProfile
) -> DurableSession:
    try:
        former = SqliteCommitStore.open(source, io=legacy.io)
        selected = legacy
    except SaveError as error:
        if error.code != "UNSUPPORTED_RULESET" or legacy.older is None:
            raise
        selected = legacy.older
        former = SqliteCommitStore.open(source, io=selected.io)
    try:
        if current_world(base) != source:
            raise SaveError("WORLD_VIEW_CHANGED", "working branch changed")
        slots = SqliteSlots(former, source.parent / "slots", io=io)
        store = slots.stage_checkpoint(selected.upgrade(former.load()))
        try:
            session = _owner(store, bundle, io, legacy)
        except (ValueError, TypeError, RuntimeError, OSError):
            cleanup_owned_clone(store.path, source.parent)
            raise
        try:
            remember_world(base, store.path)
        except (ValueError, TypeError, RuntimeError, OSError):
            session.close()
            if current_world(base) == source:
                cleanup_owned_clone(store.path, source.parent)
            raise
        return session
    finally:
        former.close()


def open_knowledge_world(
    base: Path,
    world: WorldCatalog,
    scenario: SupplyScenario,
    social: SocialCatalog,
    transport: TransportRules,
    *,
    village: bool = False,
    require_existing: bool = False,
    combat: bool = False,
) -> DurableSession:
    source = current_world(base)
    old = transport_world_bundle(world, social, transport, scenario, knowledge=True)
    old_io = state_io((old,))
    exists = source.exists()
    if not village and not combat:
        if not exists and not require_existing:
            initial = world_checkpoint(
                world, supply=scenario, social=social, transport=transport, knowledge=True
            )
            return _current_owner(
                base, SqliteCommitStore.create(source, initial, io=old_io), old, old_io
            )
        try:
            return _current_owner(base, SqliteCommitStore.open(source, io=old_io), old, old_io)
        except SaveError as error:
            if error.code != "UNSUPPORTED_RULESET":
                raise
    village_bundle = village_world_bundle(old, scenario.place_id)
    village_io = state_io((village_bundle,))
    if not combat:
        new, io = village_bundle, village_io
        legacy = LegacySlotProfile(old_io, lambda previous: _upgrade(previous, io))
        if exists or require_existing:
            try:
                return _current_owner(base, SqliteCommitStore.open(source, io=io), new, io, legacy)
            except SaveError as error:
                if error.code != "UNSUPPORTED_RULESET":
                    raise
            combat_bundle = combat_world_bundle(village_bundle, scenario.place_id)
            combat_io = state_io((combat_bundle,))
            combat_legacy = _combat_legacy(old_io, village_io, combat_io)
            try:
                return _current_owner(
                    base,
                    SqliteCommitStore.open(source, io=combat_io),
                    combat_bundle,
                    combat_io,
                    combat_legacy,
                )
            except SaveError as error:
                if error.code != "UNSUPPORTED_RULESET" or not village:
                    raise
            return _upgrade_working(base, source, new, io, legacy)
    else:
        new = combat_world_bundle(village_bundle, scenario.place_id)
        io = state_io((new,))
        legacy = _combat_legacy(old_io, village_io, io)
    if not exists and not require_existing:
        initial = world_checkpoint(
            world, supply=scenario, social=social, transport=transport, knowledge=True
        )
        return _current_owner(
            base, SqliteCommitStore.create(source, legacy.upgrade(initial), io=io), new, io, legacy
        )
    try:
        return _current_owner(base, SqliteCommitStore.open(source, io=io), new, io, legacy)
    except SaveError as error:
        if error.code != "UNSUPPORTED_RULESET" or not (village or combat):
            raise
    return _upgrade_working(base, source, new, io, legacy)


def _combat_legacy(old: StateIO, village: StateIO, current: StateIO) -> LegacySlotProfile:
    def upgrade(previous: DurableCheckpoint) -> DurableCheckpoint:
        return _upgrade(previous, current, combat=True)

    return LegacySlotProfile(village, upgrade, LegacySlotProfile(old, upgrade))


def validate_knowledge_world(path: Path, old: FeatureBundle, place_id: str) -> DurableCheckpoint:
    return validate_save(
        path,
        io=state_io((old,)),
        fallbacks=(
            lambda: state_io((village_world_bundle(old, place_id),)),
            lambda: state_io((combat_world_bundle(village_world_bundle(old, place_id), place_id),)),
        ),
    )
