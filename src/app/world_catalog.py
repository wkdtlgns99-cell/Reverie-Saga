"""Read a pinned development world;generation is an explicit offline operation."""

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from domain.canonical import canonical_json, decode_json, object_value
from domain.world import WorldCatalog, decode_world, elaborate_place, generate_world
from domain.world_social import SocialCatalog, decode_social
from domain.world_transport import TransportRules, decode_transport

DEVELOPMENT_WORLD = Path(__file__).resolve().parents[2] / "content/worlds/development-world-v1.json"
DEVELOPMENT_SOCIAL = DEVELOPMENT_WORLD.with_name("development-social-v1.json")
DEVELOPMENT_TRANSPORT = DEVELOPMENT_WORLD.with_name("development-transport-v1.json")


def load_world(path: Path = DEVELOPMENT_WORLD) -> WorldCatalog:
    return decode_world(object_value(decode_json(path.read_bytes())))


def load_social(world: WorldCatalog, path: Path = DEVELOPMENT_SOCIAL) -> SocialCatalog:
    return decode_social(object_value(decode_json(path.read_bytes())), world)


def load_transport(world: WorldCatalog, path: Path = DEVELOPMENT_TRANSPORT) -> TransportRules:
    return decode_transport(object_value(decode_json(path.read_bytes())), world)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reverie Saga world catalog")
    parser.add_argument("--catalog", type=Path, default=DEVELOPMENT_WORLD)
    parser.add_argument("--generate-seed", help="Explicitly generate canonical JSON to stdout")
    parser.add_argument("--place", default="place:p0-a")
    args = parser.parse_args(argv)
    if args.generate_seed is not None:
        sys.stdout.buffer.write(
            canonical_json(generate_world(args.generate_seed).document()) + b"\n"
        )
        return 0
    world = load_world(args.catalog)
    detail = elaborate_place(world, args.place)
    print(
        f"대륙 {len(world.continents)} / 국가 {len(world.countries)} / "
        f"주요 도시 {len(world.places)}"
    )
    print(world.place(args.place).name)
    for resident in detail.residents:
        print(f"{resident.name}: {resident.occupation}, {resident.disposition}")
    for place, route in world.neighbors(args.place):
        print(f"→ {place.name}: {route.distance_km}km ({route.kind})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
