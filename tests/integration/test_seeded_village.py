from pathlib import Path

from domain.canonical import array_value, canonical_json, int_value, object_value
from tests.integration.test_world_village import pipe, send


def test_new_worlds_with_equal_seeds_generate_the_same_village_and_dungeon(tmp_path: Path) -> None:
    first = tmp_path / "one.sqlite"
    seed = "1" * 64
    with pipe(first, seed=seed) as streams:
        start = send(streams, 1, "inspect")
        layout = object_value(start["layout"])
        assert layout["seed"] == seed
        assert layout["version"] == 1
        assert layout["terrain"] == "강과 비옥한 범람원"
        rows = array_value(start["rows"])
        village = tuple(map(object_value, array_value(layout["village"])))
        gate = next(item for item in village if item["kind"] == "gate")
        assert (gate["x"], gate["y"]) == (layout["gate_x"], layout["gate_y"])
        assert gate["x"] not in (1, 7, 9)
        assert any(item["kind"] == "house" for item in village)
        for item in village:
            if item["kind"] == "road":
                row = rows[int_value(item["y"])]
                assert isinstance(row, str) and row[int_value(item["x"])] == "."
        dungeon = tuple(map(object_value, array_value(layout["dungeon"])))
        orcs = tuple(item for item in dungeon if item["kind"] == "orc")
        assert len(orcs) == 1
        orc = orcs[0]
        assert any(
            (item["x"], item["y"], item["kind"]) == (orc["x"], orc["y"], "dungeon-floor")
            for item in dungeon
        )
        moved = send(streams, 2, "step", "right")
        assert moved["x"] == 2 and moved["tick"] == 1
        assert moved["layout"] == layout
    with pipe(first, seed=seed) as streams:
        resumed = send(streams, 1, "inspect")
        assert resumed["layout"] == layout and resumed["tick"] == 1
    with pipe(tmp_path / "two.sqlite", seed=seed) as streams:
        second = send(streams, 1, "inspect")
        assert second["tick"] == 0
        assert canonical_json(second["layout"]) == canonical_json(layout)
    with pipe(tmp_path / "three.sqlite", seed="2" * 64) as streams:
        different = object_value(send(streams, 1, "inspect")["layout"])
        assert different["village"] != layout["village"]
        assert different["dungeon"] != layout["dungeon"]
