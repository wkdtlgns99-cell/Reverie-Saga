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


def test_evidence_row_must_be_qualified_even_when_dossier_hash_matches(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    for name in (
        "docs/reference/QUILLTALE_CONTENT_CANDIDATES.json",
        "docs/reviews/QT-F04_GENERATION_EVIDENCE_2026-10-12.json",
    ):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = (root / name).read_bytes()
        if "EVIDENCE" in name:
            raw = raw.replace(b"QUALIFIED_FOR_FUTURE_NARRATIVE_ADAPTATION", b"NOT_QUALIFIED", 1)
        target.write_bytes(raw)
    with pytest.raises(ValueError, match="^NARRATIVE_QUALIFICATION$"):
        build_sample(tmp_path)


def test_near_cap_catalog_fits_real_bridge_response(tmp_path: Path) -> None:
    import io
    from app.engine_bridge import EngineBridge, MAX_FRAME, write_frame
    from adapters.narrative_catalog import MAX_CATALOG_BYTES

    entries = tuple(
        Narrative(f"narrative:quest-{i:016x}", "quest", "q", "x" * 4096) for i in range(15)
    )
    body = compile_catalog(entries)
    assert MAX_CATALOG_BYTES < MAX_FRAME // 2
    assert len(body) > MAX_CATALOG_BYTES * 95 // 100
    bridge = EngineBridge(tmp_path / "max.sqlite", entries)
    try:
        output = io.BytesIO()
        write_frame(output, bridge.response("0"))
        assert int.from_bytes(output.getvalue()[:4], "big") < MAX_FRAME
    finally:
        bridge.close()
    with pytest.raises(ValueError, match="^NARRATIVE_CAPACITY$"):
        compile_catalog(
            entries + (Narrative("narrative:quest-0000000000000010", "quest", "q", "x" * 4096),)
        )


def test_schema_hash_covers_update_and_response_fields() -> None:
    from dataclasses import dataclass, fields
    from contracts.client import ClientUpdate
    from app.engine_bridge import SCHEMA_HASH, RESPONSE_FIELDS, schema_fingerprint

    @dataclass(frozen=True, slots=True)
    class ExtendedUpdate(ClientUpdate):
        extra_diagnostic: str = ""

    extended = tuple((f.name, str(f.type)) for f in fields(ExtendedUpdate))
    assert schema_fingerprint(update_fields=extended) != SCHEMA_HASH
    assert schema_fingerprint(response_fields=RESPONSE_FIELDS + (("extra", "str"),)) != SCHEMA_HASH


def test_codegen_maps_by_declared_type_and_rejects_unknown_types() -> None:
    from app.engine_project import wire_csharp_type

    assert wire_csharp_type("tuple[int, ...]") == "string[]"
    assert wire_csharp_type("tuple[str, ...]") == "string[]"
    assert wire_csharp_type("bool") == "bool"
    with pytest.raises(ValueError, match="^WIRE_ANNOTATION:float$"):
        wire_csharp_type("float")


@pytest.mark.parametrize(
    "old,new",
    [
        (b'"candidate_id": "harbor_salt_mist"', b'"candidate_id": "unqualified_other"'),
        (b"six named existing selections only;", b"all corpus selections;"),
        ('"adapted_name": "소금눈물 포구"'.encode(), '"adapted_name": "미확인 포구"'.encode()),
    ],
)
def test_evidence_set_scope_and_adaptation_are_bound(
    tmp_path: Path, old: bytes, new: bytes
) -> None:
    root = Path(__file__).resolve().parents[2]
    for name in (
        "docs/reference/QUILLTALE_CONTENT_CANDIDATES.json",
        "docs/reviews/QT-F04_GENERATION_EVIDENCE_2026-10-12.json",
    ):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = (root / name).read_bytes()
        if "EVIDENCE" in name:
            assert old in raw
            raw = raw.replace(old, new, 1)
        target.write_bytes(raw)
    with pytest.raises(ValueError, match="^NARRATIVE_QUALIFICATION$"):
        build_sample(tmp_path)
    assert not (tmp_path / "content").exists()
