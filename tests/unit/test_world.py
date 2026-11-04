"""Independent topology/content invariants for the reusable world package."""

from dataclasses import replace
import hashlib
from pathlib import Path

import pytest

from app.world_catalog import DEVELOPMENT_WORLD, load_world, main
from domain.canonical import canonical_json, object_value, seal
from domain.world import Route, decode_world, elaborate_place, generate_world


def test_development_catalog_is_reused_and_has_confirmed_scale() -> None:
    before = DEVELOPMENT_WORLD.read_bytes()
    world = load_world()
    assert (len(world.continents), len(world.countries), len(world.places)) == (6, 6, 12)
    assert len({c.environment for c in world.continents}) == 6
    assert len({c.livelihood for c in world.countries}) == 6
    assert all(sum(p.country_id == c.id for p in world.places) == 2 for c in world.countries)
    assert all(
        {p.role for p in world.places if p.country_id == c.id} == {"수도", "무역항"}
        for c in world.countries
    )
    assert load_world() == world
    assert DEVELOPMENT_WORLD.read_bytes() == before


def test_world_routes_reach_every_city_and_cross_every_continent() -> None:
    world = load_world()
    frontier = [world.places[0].id]
    seen = set(frontier)
    while frontier:
        current = frontier.pop()
        for place, route in world.neighbors(current):
            assert route.distance_km > 0
            if place.id not in seen:
                seen.add(place.id)
                frontier.append(place.id)
    assert seen == {p.id for p in world.places}
    assert len([r for r in world.routes if r.kind == "road"]) == 6
    assert len([r for r in world.routes if r.kind == "sea"]) == 6
    assert world.neighbors("place:p0-a")[0][0].id == "place:p0-b"


def test_seeded_world_roundtrip_and_generation_do_not_use_provider() -> None:
    a = generate_world("a" * 64)
    b = generate_world("b" * 64)
    assert a == generate_world("a" * 64)
    assert a.routes != b.routes
    assert a.places == b.places
    assert decode_world(a.document()) == a
    fixture = load_world()
    assert fixture == generate_world(fixture.seed_hex)
    assert canonical_json(fixture.document()) + b"\n" == DEVELOPMENT_WORLD.read_bytes()


def test_local_elaboration_is_stable_independent_of_visit_order() -> None:
    world = load_world()
    original = canonical_json(world.document())
    first = elaborate_place(world, "place:p0-a")
    for place in reversed(world.places):
        local = elaborate_place(world, place.id)
        assert len(local.residents) == 4
        assert len({r.id for r in local.residents}) == 4
        assert all(r.workplace in local.sites for r in local.residents)
        assert all(0 <= r.work_start_hour < r.work_end_hour < 24 for r in local.residents)
    assert elaborate_place(load_world(), "place:p0-a") == first
    assert canonical_json(world.document()) == original


@pytest.mark.parametrize("seed", ["", "A" * 64, "0" * 63, "x" * 64, True, 1])
def test_invalid_seed_rejected(seed: object) -> None:
    with pytest.raises(ValueError, match="WORLD_SEED"):
        generate_world(seed)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "change,code",
    [
        ("duplicate", "WORLD_ID_ORDER"),
        ("country", "WORLD_COUNTRY_REFERENCE"),
        ("route", "WORLD_ROUTE_ENDPOINT"),
        ("disconnected", "WORLD_DISCONNECTED"),
        ("bool", "integer outside declared range"),
        ("kind", "WORLD_ROUTE_KIND"),
    ],
)
def test_bad_world_definitions_reject_instead_of_repair(change: str, code: str) -> None:
    world = load_world()
    with pytest.raises(ValueError, match=code):
        if change == "duplicate":
            replace(world, places=(world.places[0], *world.places))
        elif change == "country":
            replace(
                world,
                places=(replace(world.places[0], country_id="country:missing"), *world.places[1:]),
            )
        elif change == "route":
            replace(world, routes=(Route("place:missing", "place:p0-a", 10, "road"),))
        elif change == "disconnected":
            replace(world, routes=tuple(r for r in world.routes if r.kind == "road"))
        elif change == "bool":
            replace(world, routes=(replace(world.routes[0], distance_km=True), *world.routes[1:]))
        else:
            replace(world, routes=(replace(world.routes[0], kind="teleport"), *world.routes[1:]))


def test_unknown_place_and_unknown_document_field_rejected() -> None:
    world = load_world()
    with pytest.raises(ValueError, match="WORLD_UNKNOWN_PLACE"):
        elaborate_place(world, "place:missing")
    with pytest.raises(ValueError, match="missing or unknown fields"):
        decode_world(object_value(seal({**world.document(), "extra": 1})))


def test_land_road_cannot_connect_separate_continents() -> None:
    world = load_world()
    index = next(i for i, route in enumerate(world.routes) if route.kind == "sea")
    routes = list(world.routes)
    routes[index] = replace(routes[index], kind="road")
    with pytest.raises(ValueError, match="WORLD_ROUTE_GEOGRAPHY"):
        replace(world, routes=tuple(routes))


def test_cli_loads_fixed_file_without_mutation(capsys: pytest.CaptureFixture[str]) -> None:
    before = hashlib.sha256(DEVELOPMENT_WORLD.read_bytes()).digest()
    assert main(["--place", "place:p0-a"]) == 0
    output = capsys.readouterr().out
    assert "대륙 6 / 국가 6 / 주요 도시 12" in output
    assert "물버들" in output and "여울항" in output
    assert hashlib.sha256(DEVELOPMENT_WORLD.read_bytes()).digest() == before


def test_invalid_catalog_file_has_no_silent_regeneration(tmp_path: Path) -> None:
    catalog = tmp_path / "world.json"
    catalog.write_bytes(b"{}")
    with pytest.raises(ValueError, match="missing or unknown fields"):
        load_world(catalog)
    assert catalog.read_bytes() == b"{}"
