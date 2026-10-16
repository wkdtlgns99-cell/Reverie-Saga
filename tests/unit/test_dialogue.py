from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path

import pytest

from adapters.quest_dialogue import (
    compile_dialogue,
    decode_candidate,
    decode_catalog,
    publish_fresh,
)
from app.quest import harbor_definition
from contracts.dialogue import DialogueLine
from domain.canonical import array_value, canonical_json, decode_json, object_value
from tests.unit.quest_fixtures import candidate, catalog, receipt


@pytest.mark.parametrize("text", ("", " ", "\n", "가", "가" * 342))
def test_dialogue_text_rejects_invalid_and_nfd(text: str) -> None:
    with pytest.raises(ValueError, match="DIALOGUE_TEXT"):
        DialogueLine("offer", text)


def test_utf8_boundary_and_exact_intent() -> None:
    assert len(DialogueLine("offer", "가" * 341 + "a").text_ko.encode()) == 1024
    with pytest.raises(ValueError, match="DIALOGUE_INTENTS"):
        DialogueLine("Offer", "대사")


@pytest.mark.parametrize("extra", ("stage", "reward", "approval", "commands"))
def test_model_cannot_supply_authoritative_or_approval_fields(extra: str) -> None:
    document = dict(object_value(decode_json(candidate())))
    document[extra] = 3
    with pytest.raises(ValueError):
        decode_candidate(canonical_json(document))


@pytest.mark.parametrize("kind", ("missing", "duplicate", "reverse"))
def test_intent_set_and_canonical_order(kind: str) -> None:
    document = dict(object_value(decode_json(candidate())))
    lines = list(array_value(document["lines"]))
    document["lines"] = tuple(
        lines[:-1]
        if kind == "missing"
        else (*lines[:-1], lines[0])
        if kind == "duplicate"
        else lines[::-1]
    )
    with pytest.raises(ValueError, match="DIALOGUE_INTENTS"):
        decode_candidate(canonical_json(document))


@pytest.mark.parametrize(
    "field,value",
    (("decision", "NEEDS_REVIEW"), ("output_sha256", "0" * 64), ("brief_sha256", "invalid")),
)
def test_forged_or_changed_approval_rejected(field: str, value: str) -> None:
    body = candidate()
    approval = dict(object_value(decode_json(receipt(body))))
    approval[field] = value
    with pytest.raises(ValueError):
        compile_dialogue(body, canonical_json(approval))


def test_provenance_only_changes_do_not_change_behavioral_pin() -> None:
    body = candidate()
    approval = dict(object_value(decode_json(receipt(body))))
    original = compile_dialogue(body, canonical_json(approval))
    approval["approved_by"] = "another-test-reviewer"
    approval["approved_utc"] = "2026-10-13T03:00:00+00:00"
    assert compile_dialogue(body, canonical_json(approval)) == original
    content = decode_catalog(original, hashlib.sha256(original).hexdigest(), harbor_definition())
    changed = replace(
        content,
        dialogue=replace(
            content.dialogue,
            lines=(
                replace(content.dialogue.lines[0], text_ko="다른 승인 대사"),
                *content.dialogue.lines[1:],
            ),
        ),
    )
    assert changed.catalog_sha256 != content.catalog_sha256


def test_catalog_hash_and_immutable_publication(tmp_path: Path) -> None:
    body = catalog()
    with pytest.raises(ValueError, match="DIALOGUE_CATALOG_HASH"):
        decode_catalog(body, "0" * 64, harbor_definition())
    target = tmp_path / "approved.json"
    publish_fresh(target, body)
    with pytest.raises(FileExistsError):
        publish_fresh(target, b"other")
    assert target.read_bytes() == body
    assert not target.with_name(target.name + ".pending").exists()


def test_compilation_binds_raw_candidate_bytes_not_canonical_reencoding() -> None:
    import json

    # Whitespace is allowed in raw provider output. The approval records these exact bytes,
    # while the behavioral catalog canonicalizes the decoded text document.
    body = json.dumps(json.loads(candidate()), ensure_ascii=False, indent=1).encode()
    assert (
        hashlib.sha256(body).hexdigest()
        != hashlib.sha256(canonical_json(decode_json(body))).hexdigest()
    )
    compiled = compile_dialogue(body, receipt(body))
    selected = decode_catalog(compiled, hashlib.sha256(compiled).hexdigest(), harbor_definition())
    assert selected.output_sha256 == hashlib.sha256(body).hexdigest()


@pytest.mark.parametrize("field", ("output_sha256", "brief_sha256"))
def test_load_uses_trusted_full_catalog_pin_not_authenticated_provenance(field: str) -> None:
    original = catalog()
    trusted = hashlib.sha256(original).hexdigest()
    document = dict(object_value(decode_json(original)))
    approval = dict(object_value(document["approval"]))
    approval[field] = "1" * 64
    document["approval"] = approval
    changed = canonical_json(document)
    with pytest.raises(ValueError, match="DIALOGUE_CATALOG_HASH"):
        decode_catalog(changed, trusted, harbor_definition())
    # A caller choosing a new pin chooses a new trusted input. The loader has no original
    # raw provider bytes/brief or signing authority and cannot authenticate this label.
    selected = decode_catalog(changed, hashlib.sha256(changed).hexdigest(), harbor_definition())
    assert getattr(selected, field) == "1" * 64
