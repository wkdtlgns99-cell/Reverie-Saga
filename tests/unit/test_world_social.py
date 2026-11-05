"""Independent social contract arithmetic and strict fixed-world data boundaries."""

from dataclasses import replace

import pytest

from app.world_catalog import load_social, load_world
from domain.canonical import JsonValue, array_value, object_value, seal
from orchestration.world_social import SocialStateCodec
from domain.world_social import (
    credit_delivery,
    decode_social,
    initial_social,
    reaction,
    social_action,
    validate_social,
)


def test_fixed_catalog_covers_world_and_mixed_residents() -> None:
    world = load_world()
    catalog = load_social(world)
    assert len(catalog.ancestries) == 6 and len(catalog.factions) == 18
    assert len(catalog.diplomacy) == 15 and len(catalog.residents) == 48
    assert {r.ancestry_id for r in catalog.residents} == {a.id for a in catalog.ancestries}
    for place in world.places:
        identities = tuple(r for r in catalog.residents if r.place_id == place.id)
        assert len(identities) == 4 and len({r.ancestry_id for r in identities}) == 4
        assert catalog.local(place.id).country_id == place.country_id
    assert catalog.diplomatic_score("country:k0", "country:k2") == 20
    assert catalog.diplomatic_score("country:k5", "country:k1") == -20
    assert catalog.diplomatic_score("country:k0", "country:k1") == 0
    assert decode_social(catalog.document(), world) == catalog


def test_protest_repair_delivery_and_familiarity_are_distinct() -> None:
    catalog = load_social(load_world())
    state = initial_social(catalog)
    place = "place:p0-a"
    for _ in range(2):
        state = social_action(state, catalog, place, "protest")
    scores = dict(state.reputation)
    assert scores["faction:city-p0-a"] == -30
    assert scores["faction:nation-k0"] == -10
    assert reaction(state, catalog, place) == -40
    assert reaction(state, catalog, "place:p0-b") == -10
    for expected in (-34, -28):
        state = social_action(state, catalog, place, "reconcile")
        assert reaction(state, catalog, place) == expected
    delivered = credit_delivery(state, catalog, place)
    assert dict(delivered.reputation)["faction:city-p0-a"] == 0
    assert dict(delivered.reputation)["faction:nation-k0"] == -3
    assert credit_delivery(delivered, catalog, place) == delivered
    person = next(r for r in catalog.residents if r.place_id == place)
    identified = social_action(
        delivered, catalog, place, "identify", person.ancestry_id, "country:k0"
    )
    assert reaction(identified, catalog, place) == 17
    assert reaction(identified, catalog, place, person.npc_id) == 19
    assert delivered.ancestry_id == "" and delivered.country_id == ""


def test_reconcile_preserves_positive_national_merit_and_cannot_farm_goodwill() -> None:
    catalog = load_social(load_world())
    state = credit_delivery(initial_social(catalog), catalog, "place:p0-b")
    state = replace(
        state,
        reputation=tuple(
            (key, -5 if key == "faction:city-p0-a" else score) for key, score in state.reputation
        ),
    )
    repaired = social_action(state, catalog, "place:p0-a", "reconcile")
    assert dict(repaired.reputation)["faction:city-p0-a"] == 0
    assert dict(repaired.reputation)["faction:nation-k0"] == 5
    with pytest.raises(ValueError, match="^SOCIAL_NOTHING_TO_REPAIR$"):
        social_action(repaired, catalog, "place:p0-a", "reconcile")


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("ancestry_id", True, "string required"),
        ("country_id", "country:k0", "SOCIAL_IDENTITY"),
        ("credited_places", ("place:missing",), "SOCIAL_CREDITED_PLACES"),
        ("credited_places", ("place:p0-a", "place:p0-a"), "SOCIAL_CREDITED_PLACES"),
        ("reputation", (), "SOCIAL_REPUTATION_COVERAGE"),
    ],
)
def test_state_rejects_malformed_or_incomplete_values(
    field: str, value: JsonValue, code: str
) -> None:
    catalog = load_social(load_world())
    with pytest.raises(ValueError, match="^" + code + "$"):
        data = dict(SocialStateCodec(catalog).encode(initial_social(catalog)))
        data[field] = value
        SocialStateCodec(catalog).decode(object_value(seal(data)))


def test_bounds_exact_int_and_identity_once() -> None:
    catalog = load_social(load_world())
    state = initial_social(catalog)
    for score in (True, -101, 101):
        with pytest.raises(ValueError, match="integer outside declared range"):
            validate_social(
                replace(state, reputation=tuple((key, score) for key, _ in state.reputation)),
                catalog,
            )
    for _ in range(30):
        state = social_action(state, catalog, "place:p0-a", "protest")
    assert reaction(state, catalog, "place:p0-a") == -100
    identified = social_action(state, catalog, "place:p0-a", "identify", "ancestry:human", "none")
    assert reaction(identified, catalog, "place:p0-a") == -100
    with pytest.raises(ValueError, match="^SOCIAL_IDENTITY_LOCKED$"):
        social_action(
            identified, catalog, "place:p0-a", "identify", "ancestry:sylvan", "country:k2"
        )
    for operation, ancestry, country, code in (
        ("unknown", "", "", "INVALID_COMMAND"),
        ("protest", "ancestry:human", "", "INVALID_COMMAND"),
        ("identify", "ancestry:missing", "none", "SOCIAL_IDENTITY"),
    ):
        with pytest.raises(ValueError, match="^" + code + "$"):
            social_action(
                initial_social(catalog), catalog, "place:p0-a", operation, ancestry, country
            )


@pytest.mark.parametrize(
    "part", ["extra", "missing", "duplicate", "world", "bool", "npc", "ancestry"]
)
def test_catalog_decoder_rejects_invalid_bindings(part: str) -> None:
    world = load_world()
    catalog = load_social(world)
    data = dict(catalog.document())
    if part == "extra":
        data["secret"] = "unvalidated"
    elif part == "missing":
        del data["ancestries"]
    elif part == "duplicate":
        rows = array_value(data["factions"])
        data["factions"] = (*rows, rows[0])
    elif part == "world":
        data["world_seed"] = "0" * 64
    elif part == "bool":
        first, *rest = catalog.diplomacy
        invalid = replace(catalog, diplomacy=(replace(first, score=True), *rest))
        data = dict(invalid.document())
    elif part == "npc":
        resident, *residents = catalog.residents
        data = dict(
            replace(
                catalog, residents=(replace(resident, faction_id="faction:city-p1-a"), *residents)
            ).document()
        )
    else:
        ancestry, *ancestries = catalog.ancestries
        data = dict(
            replace(catalog, ancestries=(replace(ancestry, name=""), *ancestries)).document()
        )
    codes = {
        "extra": "missing or unknown fields",
        "missing": "missing or unknown fields",
        "duplicate": "SOCIAL_COLLECTION",
        "world": "SOCIAL_WORLD_BINDING",
        "bool": "integer required",
        "npc": "SOCIAL_RESIDENT_BINDING",
        "ancestry": "SOCIAL_TEXT",
    }
    with pytest.raises(ValueError, match="^" + codes[part] + "$"):
        decode_social(object_value(seal(data)), world)
