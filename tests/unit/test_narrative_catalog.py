from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
from pathlib import Path

import pytest

from adapters.narrative_catalog import compile_catalog, decode_catalog, load_catalog
from app.engine_project import build_sample, generate_wire
from contracts.narratives import Narrative
from domain.canonical import canonical_json, seal


def sample() -> Narrative:
    return Narrative(
        "narrative:settlement-0000000000000001", "settlement", "안개 포구", "절벽 아래 포구."
    )


def test_catalog_is_deterministic_frozen_and_contains_no_mechanics(tmp_path: Path) -> None:
    one = sample()
    two = Narrative("narrative:quest-0000000000000002", "quest", "밤꽃", "밤꽃을 찾는 의뢰.")
    body = compile_catalog((one, two))
    assert body == compile_catalog((two, one))
    digest = hashlib.sha256(body).hexdigest()
    target = tmp_path / "catalog.json"
    target.write_bytes(body)
    decoded = load_catalog(target, digest)
    assert decoded == (two, one)
    with pytest.raises(FrozenInstanceError):
        setattr(decoded[0], "name_ko", "changed")
    with pytest.raises(ValueError, match="^NARRATIVE_CATALOG_HASH$"):
        decode_catalog(body + b" ", digest)
    with pytest.raises(ValueError, match="^NARRATIVE_DUPLICATE_ID$"):
        compile_catalog((one, one))


@pytest.mark.parametrize("name", ["", " ", "a" * 257, "bad\nname"])
def test_name_bounds_reject_empty_oversize_control(name: str) -> None:
    with pytest.raises(ValueError, match="^NARRATIVE_TEXT$"):
        Narrative("narrative:quest-0000000000000001", "quest", name, "premise")


def test_mechanical_field_rejected_even_with_valid_outer_hash() -> None:
    entry = {
        "entry_id": "narrative:quest-0000000000000001",
        "category": "quest",
        "name_ko": "quest",
        "description_ko": "premise",
        "damage": "10",
    }
    entries = seal((entry,))
    body = canonical_json(
        {
            "format": "reverie-narratives/v1",
            "entries": entries,
            "entries_sha256": hashlib.sha256(canonical_json(entries)).hexdigest(),
        }
    )
    with pytest.raises(ValueError, match="missing or unknown fields"):
        decode_catalog(body, hashlib.sha256(body).hexdigest())


def test_actual_sample_and_generated_unity_binding_match_source_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    body, manifest = build_sample(root)
    entries = decode_catalog(body, hashlib.sha256(body).hexdigest())
    assert len(entries) == 6
    assert {e.category for e in entries} == {"settlement", "creature", "facility", "quest"}
    assert "동판 비늘의 벼락 메기" in {e.name_ko for e in entries}
    assert (root / "content/narratives.json").read_bytes() == body
    assert (root / "content/narratives.manifest.json").read_bytes() == manifest
    assert (root / "clients/unity/Assets/Reverie/Scripts/Wire.Generated.cs").read_text(
        encoding="utf-8"
    ) == generate_wire()


def test_unqualified_dossier_edits_cannot_be_published(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    dossier = Path("docs/reference/QUILLTALE_CONTENT_CANDIDATES.json")
    evidence = Path("docs/reviews/QT-F04_GENERATION_EVIDENCE_2026-10-12.json")
    for path in (dossier, evidence):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / path).read_bytes())
    with (tmp_path / dossier).open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match="^NARRATIVE_DOSSIER_UNQUALIFIED$"):
        build_sample(tmp_path)
    assert not (tmp_path / "content").exists()
