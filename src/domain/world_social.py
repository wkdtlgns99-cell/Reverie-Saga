"""Separate ancestry,political membership and earned reputation from world truth."""

from dataclasses import asdict, dataclass, replace
from itertools import combinations
import unicodedata

from domain.canonical import (
    JsonObject,
    array_value,
    exact_fields,
    int_value,
    object_value,
    seal,
    text_value,
)
from domain.primitives import EntityId, TypeKey, require_integer, require_namespace
from domain.state_types import ComponentRecord
from domain.world import WorldCatalog, elaborate_place

SOCIAL_SCHEMA = TypeKey("world.social", 1)
HOSTILE_THRESHOLD = -30
SOCIAL_DURATIONS = {"identify": 1, "protest": 5, "reconcile": 10}
PROTEST_REPUTATION = (-15, -5)
RECONCILE_REPUTATION = (5, 1)
DELIVERY_REPUTATION = (20, 5)
SHARED_ANCESTRY_FAMILIARITY = 2


def _text(value: str) -> None:
    if (
        type(value) is not str
        or not value.strip()
        or len(value) > 256
        or unicodedata.normalize("NFC", value) != value
    ):
        raise ValueError("SOCIAL_TEXT")


def _rows(rows: tuple[object, ...], row_type: type[object], count: int) -> None:
    if type(rows) is not tuple or len(rows) != count or any(type(r) is not row_type for r in rows):
        raise ValueError("SOCIAL_COLLECTION")


@dataclass(frozen=True, slots=True)
class Ancestry:
    id: str
    name: str
    culture: str


@dataclass(frozen=True, slots=True)
class Faction:
    id: str
    name: str
    country_id: str
    place_id: str


@dataclass(frozen=True, slots=True)
class Diplomacy:
    first: str
    second: str
    score: int
    reason: str


@dataclass(frozen=True, slots=True)
class ResidentIdentity:
    npc_id: str
    place_id: str
    ancestry_id: str
    faction_id: str


@dataclass(frozen=True, slots=True)
class SocialCatalog:
    world_seed: str
    ancestries: tuple[Ancestry, ...]
    factions: tuple[Faction, ...]
    diplomacy: tuple[Diplomacy, ...]
    residents: tuple[ResidentIdentity, ...]

    def validate(self, world: WorldCatalog) -> None:
        if self.world_seed != world.seed_hex or type(self.world_seed) is not str:
            raise ValueError("SOCIAL_WORLD_BINDING")
        for rows, cls, count in (
            (self.ancestries, Ancestry, 6),
            (self.factions, Faction, 18),
            (self.residents, ResidentIdentity, 48),
        ):
            _rows(rows, cls, count)
        for identifiers in (
            tuple(a.id for a in self.ancestries),
            tuple(f.id for f in self.factions),
            tuple(r.npc_id for r in self.residents),
        ):
            for identifier in identifiers:
                if type(identifier) is not str:
                    raise ValueError("SOCIAL_ID")
                require_namespace(identifier)
            if identifiers != tuple(sorted(set(identifiers))):
                raise ValueError("SOCIAL_ORDER")
        for ancestry in self.ancestries:
            _text(ancestry.name)
            _text(ancestry.culture)
        countries = {c.id for c in world.countries}
        places = {p.id for p in world.places}
        for faction in self.factions:
            _text(faction.name)
            if type(faction.country_id) is not str or faction.country_id not in countries:
                raise ValueError("SOCIAL_COUNTRY")
            if type(faction.place_id) is not str or (
                faction.place_id and world.place(faction.place_id).country_id != faction.country_id
            ):
                raise ValueError("SOCIAL_PLACE")
        national = tuple(f.country_id for f in self.factions if not f.place_id)
        local = tuple(f.place_id for f in self.factions if f.place_id)
        if len(national) != len(countries) or set(national) != countries:
            raise ValueError("SOCIAL_COUNTRY_COVERAGE")
        if len(local) != len(places) or set(local) != places:
            raise ValueError("SOCIAL_PLACE_COVERAGE")
        if type(self.diplomacy) is not tuple or any(
            type(r) is not Diplomacy for r in self.diplomacy
        ):
            raise ValueError("SOCIAL_DIPLOMACY")
        if tuple((r.first, r.second) for r in self.diplomacy) != tuple(
            combinations(sorted(countries), 2)
        ):
            raise ValueError("SOCIAL_DIPLOMACY_COVERAGE")
        for relation in self.diplomacy:
            if type(relation.score) is not int or relation.score not in (-20, 0, 20):
                raise ValueError("SOCIAL_DIPLOMACY_SCORE")
            _text(relation.reason)
        expected = {
            r.id: p.id for p in world.places for r in elaborate_place(world, p.id).residents
        }
        if {r.npc_id for r in self.residents} != set(expected):
            raise ValueError("SOCIAL_RESIDENT_COVERAGE")
        ancestry_ids = {a.id for a in self.ancestries}
        for resident in self.residents:
            if (
                type(resident.place_id) is not str
                or resident.place_id != expected[resident.npc_id]
                or type(resident.ancestry_id) is not str
                or resident.ancestry_id not in ancestry_ids
                or type(resident.faction_id) is not str
                or resident.faction_id != self.local(resident.place_id).id
            ):
                raise ValueError("SOCIAL_RESIDENT_BINDING")

    def national(self, country_id: str) -> Faction:
        for faction in self.factions:
            if faction.country_id == country_id and not faction.place_id:
                return faction
        raise ValueError("SOCIAL_COUNTRY")

    def local(self, place_id: str) -> Faction:
        if type(place_id) is not str or not place_id:
            raise ValueError("SOCIAL_PLACE")
        for faction in self.factions:
            if faction.place_id == place_id:
                return faction
        raise ValueError("SOCIAL_PLACE")

    def diplomatic_score(self, first: str, second: str) -> int:
        self.national(first)
        self.national(second)
        if first == second:
            return 20
        pair = tuple(sorted((first, second)))
        return next(r.score for r in self.diplomacy if (r.first, r.second) == pair)

    def document(self) -> JsonObject:
        return object_value(seal({"format": "reverie-social/v1", **asdict(self)}))


def decode_social(document: JsonObject, world: WorldCatalog) -> SocialCatalog:
    row = exact_fields(
        document, ("format", "world_seed", "ancestries", "factions", "diplomacy", "residents")
    )
    if row["format"] != "reverie-social/v1":
        raise ValueError("SOCIAL_FORMAT")
    ancestries = []
    for raw in array_value(row["ancestries"]):
        r = exact_fields(raw, ("id", "name", "culture"))
        ancestries.append(Ancestry(*(text_value(r[k]) for k in ("id", "name", "culture"))))
    factions = []
    for raw in array_value(row["factions"]):
        keys = ("id", "name", "country_id", "place_id")
        r = exact_fields(raw, keys)
        factions.append(Faction(*(text_value(r[k]) for k in keys)))
    diplomacy = []
    for raw in array_value(row["diplomacy"]):
        r = exact_fields(raw, ("first", "second", "score", "reason"))
        diplomacy.append(
            Diplomacy(
                text_value(r["first"]),
                text_value(r["second"]),
                int_value(r["score"]),
                text_value(r["reason"]),
            )
        )
    residents = []
    for raw in array_value(row["residents"]):
        keys = ("npc_id", "place_id", "ancestry_id", "faction_id")
        r = exact_fields(raw, keys)
        residents.append(ResidentIdentity(*(text_value(r[k]) for k in keys)))
    catalog = SocialCatalog(
        text_value(row["world_seed"]),
        tuple(ancestries),
        tuple(factions),
        tuple(diplomacy),
        tuple(residents),
    )
    catalog.validate(world)
    return catalog


@dataclass(frozen=True, slots=True)
class SocialState:
    ancestry_id: str
    country_id: str
    reputation: tuple[tuple[str, int], ...]
    credited_places: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SocialRecord(ComponentRecord):
    entity_id: EntityId
    state: SocialState

    @property
    def schema(self) -> TypeKey:
        return SOCIAL_SCHEMA


def initial_social(catalog: SocialCatalog) -> SocialState:
    return SocialState("", "", tuple((f.id, 0) for f in catalog.factions))


def validate_social(state: SocialState, catalog: SocialCatalog) -> None:
    if (
        type(state) is not SocialState
        or type(state.ancestry_id) is not str
        or type(state.country_id) is not str
    ):
        raise ValueError("SOCIAL_STATE")
    if bool(state.ancestry_id) != bool(state.country_id) or (
        state.ancestry_id
        and (
            state.ancestry_id not in {a.id for a in catalog.ancestries}
            or state.country_id not in {"none", *(f.country_id for f in catalog.factions)}
        )
    ):
        raise ValueError("SOCIAL_IDENTITY")
    if type(state.reputation) is not tuple:
        raise ValueError("SOCIAL_REPUTATION")
    for entry in state.reputation:
        if type(entry) is not tuple or len(entry) != 2 or type(entry[0]) is not str:
            raise ValueError("SOCIAL_REPUTATION")
        require_integer(entry[1], -100, 100)
    if tuple(e[0] for e in state.reputation) != tuple(f.id for f in catalog.factions):
        raise ValueError("SOCIAL_REPUTATION_COVERAGE")
    places = state.credited_places
    if (
        type(places) is not tuple
        or any(type(p) is not str for p in places)
        or places != tuple(sorted(set(places)))
        or not set(places) <= {f.place_id for f in catalog.factions if f.place_id}
    ):
        raise ValueError("SOCIAL_CREDITED_PLACES")


def _change(
    state: SocialState,
    catalog: SocialCatalog,
    place_id: str,
    local: int,
    national: int,
    *,
    repair: bool = False,
) -> SocialState:
    faction = catalog.local(place_id)
    deltas = {faction.id: local, catalog.national(faction.country_id).id: national}
    scores = tuple(
        (key, min(0 if repair else 100, max(-100, value + deltas.get(key, 0))))
        if key in deltas and not (repair and value >= 0)
        else (key, value)
        for key, value in state.reputation
    )
    return replace(state, reputation=scores)


def social_action(
    state: SocialState,
    catalog: SocialCatalog,
    place_id: str,
    operation: str,
    ancestry_id: str = "",
    country_id: str = "",
) -> SocialState:
    validate_social(state, catalog)
    if any(type(v) is not str for v in (operation, ancestry_id, country_id)):
        raise ValueError("INVALID_COMMAND")
    if operation == "identify":
        if state.ancestry_id:
            raise ValueError("SOCIAL_IDENTITY_LOCKED")
        after = replace(state, ancestry_id=ancestry_id, country_id=country_id)
        if not ancestry_id:
            raise ValueError("SOCIAL_IDENTITY")
        validate_social(after, catalog)
        return after
    if ancestry_id or country_id or operation not in ("protest", "reconcile"):
        raise ValueError("INVALID_COMMAND")
    local = catalog.local(place_id)
    scores = dict(state.reputation)
    if (
        operation == "reconcile"
        and scores[local.id] >= 0
        and scores[catalog.national(local.country_id).id] >= 0
    ):
        raise ValueError("SOCIAL_NOTHING_TO_REPAIR")
    local_change, national_change = (
        PROTEST_REPUTATION if operation == "protest" else RECONCILE_REPUTATION
    )
    return _change(
        state, catalog, place_id, local_change, national_change, repair=operation == "reconcile"
    )


def credit_delivery(state: SocialState, catalog: SocialCatalog, place_id: str) -> SocialState:
    if place_id in state.credited_places:
        return state
    after = _change(state, catalog, place_id, *DELIVERY_REPUTATION)
    return replace(after, credited_places=tuple(sorted((*state.credited_places, place_id))))


def reaction(state: SocialState, catalog: SocialCatalog, place_id: str, npc_id: str = "") -> int:
    local = catalog.local(place_id)
    scores = dict(state.reputation)
    diplomacy = (
        0
        if state.country_id in ("", "none")
        else catalog.diplomatic_score(local.country_id, state.country_id)
    )
    familiarity = 0
    if npc_id:
        identity = next(
            (r for r in catalog.residents if r.npc_id == npc_id and r.place_id == place_id), None
        )
        if identity is None:
            raise ValueError("SOCIAL_RESIDENT_BINDING")
        familiarity = (
            SHARED_ANCESTRY_FAMILIARITY if identity.ancestry_id == state.ancestry_id else 0
        )
    return max(
        -100,
        min(
            100,
            diplomacy
            + scores[catalog.national(local.country_id).id]
            + scores[local.id]
            + familiarity,
        ),
    )
