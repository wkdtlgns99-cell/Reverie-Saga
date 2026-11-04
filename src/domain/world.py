"""Seeded geography and local definitions;no provider or mutable simulation state."""

from dataclasses import asdict, dataclass
import hashlib
import re

from domain.canonical import (
    JsonObject,
    array_value,
    exact_fields,
    int_value,
    object_value,
    seal,
    text_value,
)
from domain.primitives import require_integer, require_namespace

WORLD_FORMAT = "reverie-world/v1"


def _text(value: str) -> None:
    if type(value) is not str or not value.strip() or len(value) > 256:
        raise ValueError("WORLD_TEXT")


@dataclass(frozen=True, slots=True)
class Continent:
    id: str
    name: str
    environment: str


@dataclass(frozen=True, slots=True)
class Country:
    id: str
    continent_id: str
    name: str
    livelihood: str
    export: str
    need: str


@dataclass(frozen=True, slots=True)
class Place:
    id: str
    country_id: str
    name: str
    role: str


@dataclass(frozen=True, slots=True)
class Route:
    origin: str
    destination: str
    distance_km: int
    kind: str


@dataclass(frozen=True, slots=True)
class WorldCatalog:
    seed_hex: str
    continents: tuple[Continent, ...]
    countries: tuple[Country, ...]
    places: tuple[Place, ...]
    routes: tuple[Route, ...]

    def __post_init__(self) -> None:
        if type(self.seed_hex) is not str or re.fullmatch("[0-9a-f]{64}", self.seed_hex) is None:
            raise ValueError("WORLD_SEED")
        for rows, cls, limit in (
            (self.continents, Continent, 8),
            (self.countries, Country, 64),
            (self.places, Place, 256),
            (self.routes, Route, 1024),
        ):
            if type(rows) is not tuple or not 1 <= len(rows) <= limit:
                raise ValueError("WORLD_COLLECTION")
            if any(type(row) is not cls for row in rows):
                raise ValueError("WORLD_ROW_TYPE")
        continents = self._ids(self.continents)
        countries = self._ids(self.countries)
        places = self._ids(self.places)
        for continent in self.continents:
            _text(continent.name)
            _text(continent.environment)
        for country in self.countries:
            for value in (country.name, country.livelihood, country.export, country.need):
                _text(value)
        for place in self.places:
            _text(place.name)
            _text(place.role)
        for country in self.countries:
            if type(country.continent_id) is not str or country.continent_id not in continents:
                raise ValueError("WORLD_CONTINENT_REFERENCE")
        for place in self.places:
            if type(place.country_id) is not str or place.country_id not in countries:
                raise ValueError("WORLD_COUNTRY_REFERENCE")
        if countries != {place.country_id for place in self.places}:
            raise ValueError("WORLD_EMPTY_COUNTRY")
        if continents != {country.continent_id for country in self.countries}:
            raise ValueError("WORLD_EMPTY_CONTINENT")
        pairs = []
        for route in self.routes:
            if (
                type(route.origin) is not str
                or type(route.destination) is not str
                or route.origin not in places
                or route.destination not in places
                or route.origin >= route.destination
            ):
                raise ValueError("WORLD_ROUTE_ENDPOINT")
            require_integer(route.distance_km, 1, 100_000)
            if type(route.kind) is not str or route.kind not in ("road", "sea"):
                raise ValueError("WORLD_ROUTE_KIND")
            origin_country = next(
                c for c in self.countries if c.id == self.place(route.origin).country_id
            )
            destination_country = next(
                c for c in self.countries if c.id == self.place(route.destination).country_id
            )
            same_continent = origin_country.continent_id == destination_country.continent_id
            if (route.kind == "road") != same_continent:
                raise ValueError("WORLD_ROUTE_GEOGRAPHY")
            pairs.append((route.origin, route.destination))
        if pairs != sorted(set(pairs)):
            raise ValueError("WORLD_ROUTE_ORDER")
        reached = {self.places[0].id}
        while True:
            previous = len(reached)
            for route in self.routes:
                if route.origin in reached or route.destination in reached:
                    reached.update((route.origin, route.destination))
            if len(reached) == previous:
                break
        if reached != places:
            raise ValueError("WORLD_DISCONNECTED")

    @staticmethod
    def _ids(rows: tuple[Continent, ...] | tuple[Country, ...] | tuple[Place, ...]) -> set[str]:
        ids = tuple(row.id for row in rows)
        for value in ids:
            if type(value) is not str:
                raise ValueError("WORLD_ID")
            require_namespace(value)
        if ids != tuple(sorted(set(ids))):
            raise ValueError("WORLD_ID_ORDER")
        return set(ids)

    def place(self, place_id: str) -> Place:
        if type(place_id) is not str:
            raise ValueError("WORLD_UNKNOWN_PLACE")
        for place in self.places:
            if place.id == place_id:
                return place
        raise ValueError("WORLD_UNKNOWN_PLACE")

    def neighbors(self, place_id: str) -> tuple[tuple[Place, Route], ...]:
        self.place(place_id)
        return tuple(
            (self.place(r.destination if r.origin == place_id else r.origin), r)
            for r in self.routes
            if place_id in (r.origin, r.destination)
        )

    def document(self) -> JsonObject:
        return object_value(seal({"format": WORLD_FORMAT, **asdict(self)}))


def decode_world(document: JsonObject) -> WorldCatalog:
    row = exact_fields(
        document, ("format", "seed_hex", "continents", "countries", "places", "routes")
    )
    if row["format"] != WORLD_FORMAT:
        raise ValueError("WORLD_FORMAT")
    continents = []
    for raw in array_value(row["continents"]):
        r = exact_fields(raw, ("id", "name", "environment"))
        continents.append(Continent(*(text_value(r[k]) for k in ("id", "name", "environment"))))
    countries = []
    for raw in array_value(row["countries"]):
        keys = ("id", "continent_id", "name", "livelihood", "export", "need")
        r = exact_fields(raw, keys)
        countries.append(Country(*(text_value(r[k]) for k in keys)))
    places = []
    for raw in array_value(row["places"]):
        place_keys = ("id", "country_id", "name", "role")
        r = exact_fields(raw, place_keys)
        places.append(Place(*(text_value(r[k]) for k in place_keys)))
    routes = []
    for raw in array_value(row["routes"]):
        r = exact_fields(raw, ("origin", "destination", "distance_km", "kind"))
        routes.append(
            Route(
                text_value(r["origin"]),
                text_value(r["destination"]),
                int_value(r["distance_km"]),
                text_value(r["kind"]),
            )
        )
    return WorldCatalog(
        text_value(row["seed_hex"]),
        tuple(continents),
        tuple(countries),
        tuple(places),
        tuple(routes),
    )


@dataclass(frozen=True, slots=True)
class RegionalProfile:
    name: str
    environment: str
    country: str
    livelihood: str
    export: str
    need: str
    capital: str
    port: str


# Original prototype premises,not imported v1 lore. Mechanical effects are not implied.
PROFILES = (
    RegionalProfile(
        "새봄 대륙",
        "강과 비옥한 범람원",
        "여울 왕국",
        "수로 농업과 곡물 운송",
        "곡물",
        "철제 농기구",
        "물버들",
        "여울항",
    ),
    RegionalProfile(
        "적사 대륙",
        "건조한 사막과 오아시스",
        "모래샘 연맹",
        "우물 공동관리와 대상 교역",
        "소금",
        "목재",
        "샘고리",
        "붉은돛",
    ),
    RegionalProfile(
        "서리 대륙",
        "설산과 긴 겨울",
        "백로 공국",
        "광산 채굴과 겨울 비축",
        "철광석",
        "곡물",
        "흰벼랑",
        "해빙항",
    ),
    RegionalProfile(
        "청우 대륙",
        "몬순 숲과 큰 강",
        "비숲 연방",
        "산림 관리와 강 운송",
        "목재",
        "소금",
        "비나루",
        "푸른하구",
    ),
    RegionalProfile(
        "흑요 대륙",
        "화산섬과 지열 지대",
        "잿빛 자유국",
        "지열 가마와 금속 가공",
        "철제 농기구",
        "철광석",
        "불가마",
        "검은닻",
    ),
    RegionalProfile(
        "해풍 대륙",
        "군도와 계절풍 항로",
        "별돛 동맹",
        "조선업과 원양 운송",
        "선박",
        "목재",
        "별돛",
        "바람문",
    ),
)


def _number(seed: str, key: str, limit: int) -> int:
    return int.from_bytes(hashlib.sha256(f"world/v1:{seed}:{key}".encode()).digest()[:8]) % limit


def generate_world(seed_hex: str) -> WorldCatalog:
    if type(seed_hex) is not str or re.fullmatch("[0-9a-f]{64}", seed_hex) is None:
        raise ValueError("WORLD_SEED")
    continents: list[Continent] = []
    countries: list[Country] = []
    places: list[Place] = []
    routes: list[Route] = []
    for i, profile in enumerate(PROFILES):
        continent, country = f"continent:c{i}", f"country:k{i}"
        capital, port = f"place:p{i}-a", f"place:p{i}-b"
        continents.append(Continent(continent, profile.name, profile.environment))
        countries.append(
            Country(
                country,
                continent,
                profile.country,
                profile.livelihood,
                profile.export,
                profile.need,
            )
        )
        places.extend(
            (
                Place(capital, country, profile.capital, "수도"),
                Place(port, country, profile.port, "무역항"),
            )
        )
        routes.append(Route(capital, port, 10 + _number(seed_hex, capital, 91), "road"))
        other_port = f"place:p{(i + 1) % len(PROFILES)}-b"
        a, b = sorted((port, other_port))
        routes.append(Route(a, b, 100 + _number(seed_hex, a + b, 901), "sea"))
    return WorldCatalog(
        seed_hex,
        tuple(continents),
        tuple(countries),
        tuple(places),
        tuple(sorted(routes, key=lambda r: (r.origin, r.destination))),
    )


@dataclass(frozen=True, slots=True)
class Resident:
    id: str
    name: str
    occupation: str
    disposition: str
    workplace: str
    work_start_hour: int
    work_end_hour: int


@dataclass(frozen=True, slots=True)
class LocalDetail:
    place_id: str
    sites: tuple[str, ...]
    residents: tuple[Resident, ...]


def elaborate_place(world: WorldCatalog, place_id: str) -> LocalDetail:
    place = world.place(place_id)
    country = next(c for c in world.countries if c.id == place.country_id)
    sites = ("주거지", "시장", "행정청", "부두" if place.role == "무역항" else "작업장")
    residents = []
    occupations = ("운송인", "상인", "기록관", country.livelihood)
    dispositions = ("신중함", "사교적", "과묵함", "호기심 많음")
    for i, occupation in enumerate(occupations):
        identifier = "resident:" + place.id.split(":")[1] + f"-{i}"
        start = 6 + _number(world.seed_hex, identifier, 4)
        residents.append(
            Resident(
                identifier,
                f"{place.name} 주민 {i + 1}",
                occupation,
                dispositions[_number(world.seed_hex, identifier + ":trait", 4)],
                sites[i],
                start,
                start + 8,
            )
        )
    return LocalDetail(place.id, sites, tuple(residents))
