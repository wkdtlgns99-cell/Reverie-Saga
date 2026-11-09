"""Atomic current-world reference so a loaded private save survives application restart."""

import os
from pathlib import Path
import re
import tempfile

from adapters.sqlite_store import safe_path
from contracts.persistence import SaveError
from domain.canonical import canonical_json, decode_json, exact_fields, text_value

_REFERENCE_MAX_BYTES = 1024


def _reference(base: Path) -> Path:
    return safe_path(base.with_name(base.name + ".active.json"))


def _target(base: Path, name: str) -> Path:
    if name != base.name and re.fullmatch(r"\.loaded-[0-9a-f]{32}\.sqlite", name) is None:
        raise SaveError("WORLD_ATTACHMENT_INVALID", "unexpected working filename")
    target = safe_path(base.parent / name)
    if target.parent != safe_path(base).parent:
        raise SaveError("WORLD_ATTACHMENT_INVALID", "working path escaped root")
    return target


def _read_reference(reference: Path) -> bytes | None:
    try:
        with reference.open("rb") as stream:
            body = stream.read(_REFERENCE_MAX_BYTES + 1)
    except FileNotFoundError:
        return None
    if len(body) > _REFERENCE_MAX_BYTES:
        raise SaveError("WORLD_ATTACHMENT_INVALID", "reference too large")
    return body


def current_world(base: Path) -> Path:
    base = safe_path(base)
    reference = _reference(base)
    body = _read_reference(reference)
    if body is None:
        return base
    try:
        row = exact_fields(decode_json(body), ("format", "working_name"))
        if row["format"] != "reverie-world-attachment/v1":
            raise ValueError("reference format")
        target = _target(base, text_value(row["working_name"]))
    except ValueError as error:
        raise SaveError("WORLD_ATTACHMENT_INVALID", "invalid reference") from error
    if not target.is_file():
        # A slot load may have replaced the reference and retired this target.
        if _read_reference(reference) != body:
            raise SaveError("WORLD_VIEW_CHANGED", "active working branch changed")
        raise SaveError("WORLD_ATTACHMENT_MISSING", "referenced world is missing")
    return target


def remember_world(base: Path, active: Path) -> None:
    base, active = safe_path(base), safe_path(active)
    if _target(base, active.name) != active or not active.is_file():
        raise SaveError("WORLD_ATTACHMENT_INVALID", "unowned working location")
    reference = _reference(base)
    body = canonical_json({"format": "reverie-world-attachment/v1", "working_name": active.name})
    descriptor, name = tempfile.mkstemp(prefix=".world-reference-", dir=reference.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, reference)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
