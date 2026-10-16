"""G07: source-bound native replay-body evidence, isolated from production."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import asdict, dataclass
import hashlib
import importlib.metadata
import inspect
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import textwrap
import tokenize
import tomllib
from types import CodeType, FunctionType
from typing import Literal, NoReturn, cast
import xml.etree.ElementTree as ET

import coverage
from coverage.exceptions import CoverageException
import pytest

_ARTIFACTS = (
    "coverage.toml",
    "collect.log",
    "golden.log",
    "golden.junit.xml",
    "golden.coverage",
    "golden.coverage.json",
    "json.log",
)
_DOCUMENT_INPUTS = (
    "docs/work_orders/PHASE0_REFERENCE_VECTORS.json",
    "docs/work_orders/RS-P1-CORE_02_REFERENCE_VECTORS.json",
    "docs/work_orders/RS-P1-CORE_03_REFERENCE_VECTORS.json",
    "docs/work_orders/RS-P1-CORE_04_REFERENCE_VECTORS.json",
    "docs/reviews/QT-F07_DIALOGUE_EXAMPLE.json",
)
_CONFIG_INPUTS = ("pyproject.toml", ".importlinter-runtime.toml", "requirements-dev.lock")
_SOURCES = ("src/engines", "src/domain", "src/contracts")
_PHASES = ("collect", "golden", "json")
_ENV_KEYS = (
    "PYTHONPATH",
    "PYTHONHASHSEED",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
    "PYTHONIOENCODING",
    "PYTHONUTF8",
    "TEMP",
    "TMP",
)
_MIB = 1024 * 1024
_INVENTORY = "tools/replay_body_inventory.json"
_NESTED_POLICY = "reviewed_generator_expression_within_enclosing_body"


@dataclass(frozen=True, slots=True)
class MethodHit:
    key: str
    path: str
    body_start: int
    body_end: int
    executable_lines: tuple[int, ...]
    hit_lines: tuple[int, ...]
    golden_contexts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReplayCoverageResult:
    status: Literal["PASS", "FAIL", "UNVERIFIED"]
    freshness: Literal["CURRENT", "STALE", "UNKNOWN"]
    code: str | None
    detail: str
    methods: tuple[MethodHit, ...]


@dataclass(frozen=True, slots=True)
class _Nested:
    name: str
    first_line: int
    qualname: str
    policy: str


@dataclass(frozen=True, slots=True)
class _Method:
    key: str
    implementation: str
    path: str
    definition_line: int
    body_start: int
    body_end: int
    registries: tuple[str, ...]
    engine_id: str
    nested_code: tuple[_Nested, ...]


@dataclass(frozen=True, slots=True)
class _Node:
    node_id: str
    context: str
    registry: str


@dataclass(frozen=True, slots=True)
class _Inventory:
    source_sha256: dict[str, str]
    golden_nodes: tuple[_Node, ...]
    methods: tuple[_Method, ...]


class _EvidenceError(Exception):
    def __init__(
        self,
        code: str,
        detail: str,
        freshness: Literal["STALE", "UNKNOWN"] = "UNKNOWN",
    ) -> None:
        self.code, self.detail, self.freshness = code, detail[:4096], freshness
        super().__init__(code + ": " + self.detail)


def _fail(code: str, detail: str) -> NoReturn:
    raise _EvidenceError(code, detail)


def _object(value: object, keys: Sequence[str] | None = None) -> dict[str, object]:
    if not isinstance(value, dict) or any(type(k) is not str for k in value):
        _fail("MALFORMED_EVIDENCE", "expected string-keyed object")
    result = cast(dict[str, object], value)
    if keys is not None and set(result) != set(keys):
        _fail("MALFORMED_EVIDENCE", "unexpected/missing fields: " + str(sorted(result)))
    return result


def _array(value: object, cap: int, *, nonempty: bool = True) -> list[object]:
    if not isinstance(value, list) or (nonempty and not value):
        _fail("MALFORMED_EVIDENCE", "expected nonempty array")
    if len(value) > cap:
        _fail("BOUNDS", "array limit " + str(cap))
    return cast(list[object], value)


def _text(value: object, cap: int = 4096) -> str:
    if type(value) is not str or not value or "\x00" in value:
        _fail("MALFORMED_EVIDENCE", "expected nonempty string")
    if len(value) > cap:
        _fail("BOUNDS", "string limit " + str(cap))
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise _EvidenceError("MALFORMED_EVIDENCE", "invalid Unicode") from error
    return value


def _integer(value: object, minimum: int = 0, maximum: int = 1_000_000) -> int:
    if type(value) is not int:
        _fail("MALFORMED_EVIDENCE", "expected exact integer")
    if not minimum <= value <= maximum:
        _fail("BOUNDS", "integer outside " + str((minimum, maximum)))
    return value


def _digest(value: object, length: int = 64) -> str:
    result = _text(value)
    if re.fullmatch("[0-9a-f]{" + str(length) + "}", result) is None:
        _fail("MALFORMED_EVIDENCE", "invalid hexadecimal digest")
    return result


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail("MALFORMED_EVIDENCE", "duplicate JSON key " + key)
        result[key] = value
    return result


def _nonfinite(value: str) -> NoReturn:
    _fail("MALFORMED_EVIDENCE", "nonfinite JSON " + value)


def _decode(body: bytes) -> dict[str, object]:
    try:
        value: object = json.loads(
            body.decode("utf-8", errors="strict"),
            object_pairs_hook=_pairs,
            parse_constant=_nonfinite,
        )
        return _object(value)
    except (UnicodeError, ValueError, RecursionError) as error:
        raise _EvidenceError("MALFORMED_EVIDENCE", "invalid UTF-8 JSON") from error


def _sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _reject_links(path: Path) -> None:
    for parent in (path, *path.parents):
        if parent.exists() or parent.is_symlink():
            if parent.is_symlink() or parent.is_junction():
                _fail("INVALID_PATH", "linked path " + str(parent))
            if getattr(parent.lstat(), "st_file_attributes", 0) & 0x400:
                _fail("INVALID_PATH", "reparse path " + str(parent))


def _relative(value: object) -> str:
    name = _text(value)
    path = PurePosixPath(name)
    if (
        "\\" in name
        or ":" in name
        or path.is_absolute()
        or any(part in ("", ".", "..") for part in name.split("/"))
        or path.as_posix() != name
    ):
        _fail("INVALID_PATH", name)
    return name


def _path(root: Path, name: str) -> Path:
    result = root / _relative(name)
    _reject_links(result)
    if not result.resolve().is_relative_to(root):
        _fail("INVALID_PATH", name)
    # On Windows resolve() preserves the actual spelling of existing components.
    if result.exists() and result.resolve().relative_to(root).as_posix() != name:
        _fail("INVALID_PATH", "noncanonical spelling " + name)
    return result


def _location(project_root: Path, run_dir: Path) -> tuple[Path, Path]:
    if not project_root.is_absolute() or not run_dir.is_absolute():
        _fail("INVALID_PATH", "absolute root/run required")
    if ".." in project_root.parts or ".." in run_dir.parts:
        _fail("INVALID_PATH", "traversal")
    _reject_links(project_root)
    _reject_links(run_dir)
    if not project_root.is_dir():
        _fail("INVALID_PATH", "missing project root " + str(project_root))
    root = project_root.resolve(strict=True)
    run = run_dir.resolve()
    if (
        not root.is_dir()
        or run.parent != root / ".pytest_cache"
        or re.fullmatch(r"gov03-[0-9a-f]{32}", run.name) is None
    ):
        _fail("INVALID_PATH", "expected direct .pytest_cache/gov03-32hex child")
    return root, run


def _read(path: Path, cap: int, *, missing: str = "ARTIFACT_MISSING") -> bytes:
    _reject_links(path)
    if not path.is_file():
        _fail(missing, str(path))
    if path.stat().st_size > cap:
        _fail("BOUNDS", str(path))
    body = path.read_bytes()
    if len(body) > cap:
        _fail("BOUNDS", str(path))
    return body


def _hash_map(value: object) -> dict[str, str]:
    raw = _object(value)
    if not raw:
        _fail("MALFORMED_EVIDENCE", "empty input/source hashes")
    if len(raw) > 1024:
        _fail("BOUNDS", "input paths")
    result = {_relative(k): _digest(v) for k, v in sorted(raw.items())}
    if len({k.casefold() for k in result}) != len(result):
        _fail("INVALID_PATH", "case collision")
    return result


def _snapshot(root: Path) -> dict[str, str]:
    paths: list[Path] = []
    for folder in ("src", "tests", "tools", "content"):
        base = _path(root, folder)
        if not base.is_dir():
            _fail("ARTIFACT_MISSING", folder)
        for path in sorted(base.rglob("*")):
            if "__pycache__" in path.parts or path.suffix in (".pyc", ".pyo"):
                continue
            _reject_links(path)
            if path.is_file():
                paths.append(path)
    paths.extend(_path(root, name) for name in (*_CONFIG_INPUTS, *_DOCUMENT_INPUTS))
    result = {p.relative_to(root).as_posix(): _sha(p.read_bytes()) for p in sorted(paths)}
    return _hash_map(result)


def _packages() -> dict[str, str]:
    result: dict[str, str] = {}
    for distribution in importlib.metadata.distributions():
        name = re.sub(r"[-_.]+", "-", distribution.metadata["Name"]).lower()
        if name in result:
            _fail("UNSUPPORTED_VERSION", "duplicate distribution " + name)
        result[name] = distribution.version
    if (
        sys.version.split()[0] != "3.13.12"
        or result.get("coverage") != "7.16.2"
        or result.get("pytest") != "9.1.1"
        or "pip" not in result
    ):
        _fail("UNSUPPORTED_VERSION", "requires Python3.13.12/coverage7.16.2/pytest9.1.1/pip")
    return dict(sorted(result.items()))


def _inventory(root: Path, *, verify_sources: bool = True) -> _Inventory:
    raw = _object(
        _decode(_read(_path(root, _INVENTORY), 4 * _MIB)),
        ("schema_version", "source_sha256", "golden_nodes", "methods"),
    )
    if _integer(raw["schema_version"]) != 2:
        _fail("UNSUPPORTED_VERSION", "inventory schema")
    sources = _hash_map(raw["source_sha256"])
    nodes: list[_Node] = []
    for value in _array(raw["golden_nodes"], 4096):
        node = _object(value, ("node_id", "context", "registry"))
        node_id, context, registry = (_text(node[k]) for k in ("node_id", "context", "registry"))
        parts = node_id.split("::")
        if len(parts) != 2 or not parts[0].endswith(".py"):
            _fail("MALFORMED_EVIDENCE", "node " + node_id)
        _relative(parts[0])
        if context != parts[0][:-3].replace("/", ".") + "." + parts[1]:
            _fail("MALFORMED_EVIDENCE", "context " + node_id)
        nodes.append(_Node(node_id, context, registry))
    methods: list[_Method] = []
    for value in _array(raw["methods"], 256):
        row = _object(
            value,
            (
                "key",
                "implementation",
                "path",
                "definition_line",
                "body_start",
                "body_end",
                "registries",
                "engine_id",
                "nested_code",
            ),
        )
        owners = tuple(_text(v) for v in _array(row["registries"], 6))
        if owners != tuple(sorted(set(owners))):
            _fail("MALFORMED_EVIDENCE", "duplicate/unsorted registry")
        nested: list[_Nested] = []
        for code in _array(row["nested_code"], 256, nonempty=False):
            n = _object(code, ("name", "first_line", "qualname", "policy"))
            nested.append(
                _Nested(
                    _text(n["name"]),
                    _integer(n["first_line"], 1),
                    _text(n["qualname"]),
                    _text(n["policy"]),
                )
            )
        if len(set(nested)) != len(nested):
            _fail("MALFORMED_EVIDENCE", "duplicate nested-code identity")
        method = _Method(
            _text(row["key"]),
            _text(row["implementation"]),
            _relative(row["path"]),
            _integer(row["definition_line"], 1),
            _integer(row["body_start"], 1),
            _integer(row["body_end"], 1),
            owners,
            _text(row["engine_id"]),
            tuple(nested),
        )
        if not method.definition_line < method.body_start <= method.body_end:
            _fail("INVALID_RANGE", method.key)
        methods.append(method)
    keys = [m.key for m in methods]
    if keys != sorted(set(keys)) or len({n.node_id for n in nodes}) != len(nodes):
        _fail("MALFORMED_EVIDENCE", "duplicate/unsorted method or node identity")
    if len({n.context for n in nodes}) != len(nodes):
        _fail("MALFORMED_EVIDENCE", "duplicate context")
    if len(methods) != 35 or len(sources) != 8 or len(nodes) != 8:
        _fail("INVENTORY_MISMATCH", "requires reviewed35methods/8sources/8nodes")
    if {m.path for m in methods} != set(sources):
        _fail("INVENTORY_MISMATCH", "resolved source set")
    for name, digest in sorted(sources.items()) if verify_sources else ():
        if _sha(_read(_path(root, name), 16 * _MIB)) != digest:
            raise _EvidenceError("STALE_INPUT", "reviewed source " + name, "STALE")
    return _Inventory(sources, tuple(nodes), tuple(methods))


def _nested(code: CodeType) -> tuple[_Nested, ...]:
    result: list[_Nested] = []
    for value in code.co_consts:
        if isinstance(value, CodeType):
            result.append(
                _Nested(value.co_name, value.co_firstlineno, value.co_qualname, _NESTED_POLICY)
            )
            result.extend(_nested(value))
    return tuple(result)


def _registry(root: Path, inventory: _Inventory) -> None:
    # Explicit production factories;never import test-only engines or derive bodies from hits.
    from adapters.quest_dialogue import load_dialogue
    from app.encounter_registry import encounter_bundle
    from app.feature_registry import skeleton_bundle
    from app.npc_memory import memory_bundle
    from app.quest_definition import harbor_definition
    from app.quest_registry import quest_bundle
    from app.trial_registry import trial_bundle
    from app.watch_registry import watch_bundle
    from domain.primitives import EntityId

    catalog = _path(root, "content/dialogue/harbor-memory-v1.json")
    try:
        content = load_dialogue(
            catalog, catalog.with_suffix(".sha256").read_text().strip(), harbor_definition()
        )
    except ValueError as error:
        raise _EvidenceError(
            "INVENTORY_MISMATCH", "invalid approved factory catalog/pin"
        ) from error
    bundles = {
        "skeleton_bundle": skeleton_bundle(EntityId("actor:toy")),
        "trial_bundle": trial_bundle(),
        "encounter_bundle": encounter_bundle(),
        "watch_bundle": watch_bundle(),
        "quest_bundle": quest_bundle(content),
        "memory_bundle": memory_bundle(content),
    }
    actual: dict[str, tuple[FunctionType, set[str], str]] = {}
    for owner, bundle in bundles.items():
        for binding in bundle.bindings:
            cls = type(binding.engine)
            for name, member in inspect.getmembers(cls):
                if name.startswith("_"):
                    continue
                function = member.fget if isinstance(member, property) else member
                if not isinstance(function, FunctionType):
                    if callable(member) or isinstance(member, property):
                        _fail("INVENTORY_MISMATCH", "unsupported " + name)
                    continue
                key = f"{cls.__module__}.{cls.__qualname__}.{name}"
                engine_id = binding.engine.manifest.engine_id
                if key in actual:
                    if actual[key][0] is not function or actual[key][2] != engine_id:
                        _fail("INVENTORY_MISMATCH", key)
                    actual[key][1].add(owner)
                else:
                    actual[key] = (function, {owner}, engine_id)
    if set(actual) != {m.key for m in inventory.methods}:
        _fail("INVENTORY_MISMATCH", "registered public method set")
    if {n.registry for n in inventory.golden_nodes} != set(bundles):
        _fail("INVENTORY_MISMATCH", "registry contexts")
    for method in inventory.methods:
        function, owners, engine_id = actual[method.key]
        filename = inspect.getsourcefile(function)
        expected = _path(root, method.path)
        if (
            filename is None
            or Path(filename).resolve() != expected
            or function.__module__ + "." + function.__qualname__ != method.implementation
            or tuple(sorted(owners)) != method.registries
            or engine_id != method.engine_id
        ):
            _fail("INVENTORY_MISMATCH", method.key)
        lines = expected.read_text(encoding="utf-8").splitlines()
        source_lines, first_line = inspect.getsourcelines(function)
        # Bind reviewed starts,including multiline headers with no bytecode line.
        # Only coverage.analysis2 supplies executable statements;no AST/reachability.
        tokens = tokenize.generate_tokens(
            io.StringIO(textwrap.dedent("".join(source_lines))).readline
        )
        body_line = next(
            (token.start[0] + first_line - 1 for token in tokens if token.type == tokenize.INDENT),
            0,
        )
        executable = {line for _, _, line in function.__code__.co_lines() if line is not None}
        if (
            method.body_end > len(lines)
            or not first_line <= method.definition_line < method.body_start
            or first_line + len(source_lines) - 1 != method.body_end
            or re.match(
                r"\s*def " + re.escape(function.__name__) + r"\(", lines[method.definition_line - 1]
            )
            is None
            or body_line != method.body_start
            or max(executable, default=0) > method.body_end
            or _nested(function.__code__) != method.nested_code
            or any(
                n.name != "<genexpr>"
                or n.policy != _NESTED_POLICY
                or not method.body_start <= n.first_line <= method.body_end
                for n in method.nested_code
            )
        ):
            _fail("INVALID_RANGE", method.key)


def _environment(root: Path, run: Path) -> dict[str, str]:
    return {
        "PYTHONPATH": os.pathsep.join((str(root / "src"), str(root))),
        "PYTHONHASHSEED": "0",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "TEMP": str(run / "temp"),
        "TMP": str(run / "temp"),
    }


def _commands(run: Path, inventory: _Inventory) -> tuple[list[str], ...]:
    nodes = [n.node_id for n in inventory.golden_nodes]
    config = str(run / "coverage.toml")
    cache = ["-o", "cache_dir=" + str(run / "pytest-cache")]
    return (
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *cache, *nodes],
        [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--rcfile",
            config,
            "-m",
            "pytest",
            "-q",
            "-s",
            *cache,
            "-p",
            "tools.replay_body_coverage",
            "--basetemp",
            str(run / "pytest-temp"),
            "--junitxml",
            str(run / "golden.junit.xml"),
            *nodes,
        ],
        [
            sys.executable,
            "-m",
            "coverage",
            "json",
            "--rcfile",
            config,
            "--show-contexts",
            "-o",
            str(run / "golden.coverage.json"),
        ],
    )


def _configuration(run: Path) -> dict[str, object]:
    return {
        "tool": {
            "coverage": {
                "run": {
                    "branch": True,
                    "core": "pytrace",
                    "source": list(_SOURCES),
                    "dynamic_context": "test_function",
                    "data_file": str(run / "golden.coverage"),
                },
                "report": {"ignore_errors": False},
            }
        }
    }


def _artifacts(run: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    total = 0
    for name in sorted(_ARTIFACTS):
        path = _path(run, name)
        if not path.exists():
            result[name] = None
            continue
        body = _read(path, 16 * _MIB)
        total += len(body)
        result[name] = {"sha256": _sha(body), "bytes": len(body)}
    if total > 64 * _MIB:
        _fail("BOUNDS", "total artifacts")
    return result


def _descriptor(run: Path) -> dict[str, object]:
    descriptor = _object(
        _decode(_read(run / "run.json", 4 * _MIB)),
        (
            "schema_version",
            "run_id",
            "project_root",
            "baseline_head",
            "python",
            "packages",
            "inputs_before",
            "inputs_after",
            "inventory_sha256",
            "config_sha256",
            "phases",
            "artifacts",
        ),
    )
    if _integer(descriptor["schema_version"]) != 1:
        _fail("UNSUPPORTED_VERSION", "run schema")
    _digest(descriptor["run_id"], 32)
    _text(descriptor["project_root"])
    _digest(descriptor["baseline_head"], 40)
    python = _object(descriptor["python"], ("executable", "version"))
    for value in python.values():
        _text(value)
    packages = _object(descriptor["packages"])
    if not packages or len(packages) > 1024:
        _fail("BOUNDS", "package set")
    for key, value in packages.items():
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key) is None:
            _fail("MALFORMED_EVIDENCE", "distribution " + key)
        _text(value)
    _hash_map(descriptor["inputs_before"])
    _hash_map(descriptor["inputs_after"])
    _digest(descriptor["inventory_sha256"])
    _digest(descriptor["config_sha256"])
    phases = _array(descriptor["phases"], 3)
    if len(phases) != 3:
        _fail("MALFORMED_EVIDENCE", "three phases required")
    for phase in phases:
        row = _object(phase, ("id", "argv", "cwd", "environment", "exit_code", "elapsed_seconds"))
        _text(row["id"])
        _text(row["cwd"])
        for value in _array(row["argv"], 128):
            _text(value)
        environment = _object(row["environment"], _ENV_KEYS)
        for value in environment.values():
            _text(value)
        if row["exit_code"] is not None:
            _integer(row["exit_code"], -(2**31), 2**32 - 1)
        elapsed = row["elapsed_seconds"]
        if type(elapsed) is not float or not math.isfinite(elapsed) or elapsed < 0:
            _fail("MALFORMED_EVIDENCE", "elapsed seconds")
    artifacts = _object(descriptor["artifacts"])
    for name in sorted(artifacts):
        _relative(name)
    _object(artifacts, _ARTIFACTS)
    total = 0
    for name, value in sorted(artifacts.items()):
        if value is None:
            continue
        row = _object(value, ("sha256", "bytes"))
        _digest(row["sha256"])
        total += _integer(row["bytes"], 0, 16 * _MIB)
    if total > 64 * _MIB:
        _fail("BOUNDS", "total artifacts")
    return descriptor


def _evidence(root: Path, run: Path, inventory: _Inventory) -> dict[str, object]:
    descriptor = _descriptor(run)
    if descriptor["project_root"] != str(root) or descriptor["run_id"] != run.name[6:]:
        _fail("INVALID_PATH", "run identity")
    if descriptor["python"] != {"executable": sys.executable, "version": sys.version.split()[0]}:
        _fail("UNSUPPORTED_VERSION", "interpreter provenance")
    if descriptor["packages"] != _packages():
        _fail("UNSUPPORTED_VERSION", "installed distribution set/version drift")
    actual = _artifacts(run)
    for name in sorted(_ARTIFACTS):
        if actual[name] is None or _object(descriptor["artifacts"])[name] is None:
            _fail("ARTIFACT_MISSING", name)
    for name in sorted(_ARTIFACTS):
        if actual[name] != _object(descriptor["artifacts"])[name]:
            _fail("ARTIFACT_HASH", name)
    if descriptor["config_sha256"] != _sha((run / "coverage.toml").read_bytes()):
        _fail("ARTIFACT_HASH", "coverage.toml")
    current = _snapshot(root)
    if (
        descriptor["inputs_before"] != descriptor["inputs_after"]
        or descriptor["inputs_before"] != current
        or descriptor["inventory_sha256"] != current[_INVENTORY]
    ):
        raise _EvidenceError("STALE_INPUT", "executed input set/bytes changed", "STALE")
    try:
        config: object = tomllib.loads((run / "coverage.toml").read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as error:
        raise _EvidenceError("MALFORMED_EVIDENCE", "coverage.toml") from error
    if json.dumps(config, sort_keys=True) != json.dumps(_configuration(run), sort_keys=True):
        _fail("MALFORMED_EVIDENCE", "coverage.toml effective configuration")
    phases = _array(descriptor["phases"], 3)
    for name, argv, value in zip(_PHASES, _commands(run, inventory), phases, strict=True):
        row = _object(value)
        if (row["id"], row["argv"], row["cwd"], row["environment"]) != (
            name,
            argv,
            str(root),
            _environment(root, run),
        ):
            _fail("MALFORMED_EVIDENCE", "producer command/environment " + name)
    return descriptor


def _selection(run: Path, inventory: _Inventory, descriptor: dict[str, object]) -> None:
    phases = tuple(_object(v) for v in _array(descriptor["phases"], 3))
    if phases[0]["exit_code"] != 0:
        _fail("REPLAY_FAILED", "collect exit")
    collected = (run / "collect.log").read_text(encoding="utf-8")
    if [line.strip() for line in collected.splitlines() if "::" in line] != [
        n.node_id for n in inventory.golden_nodes
    ]:
        _fail("SELECTION_MISMATCH", "collected node identities/order")
    body = (run / "golden.junit.xml").read_bytes()
    if re.search(rb"<!\s*(DOCTYPE|ENTITY)\b", body, re.IGNORECASE):
        _fail("MALFORMED_EVIDENCE", "DTD/entity forbidden")
    try:
        tree = ET.fromstring(body.decode("utf-8", errors="strict"))
    except (ET.ParseError, UnicodeError) as error:
        raise _EvidenceError("MALFORMED_EVIDENCE", "golden.junit.xml") from error
    cases = tree.findall(".//testcase")
    pairs = [(case.get("classname"), case.get("name")) for case in cases]
    expected = [tuple(n.context.rsplit(".", 1)) for n in inventory.golden_nodes]
    if sorted(pairs, key=str) != sorted(expected):
        _fail("SELECTION_MISMATCH", "JUnit identities/count")
    for suite in tree.iter("testsuite"):
        if (
            suite.get("tests"),
            suite.get("failures"),
            suite.get("errors"),
            suite.get("skipped"),
        ) != (
            str(len(expected)),
            "0",
            "0",
            "0",
        ):
            _fail("REPLAY_FAILED", "JUnit totals")
    if tree.tag != "testsuites" or len(tree.findall("testsuite")) != 1:
        _fail("MALFORMED_EVIDENCE", "JUnit structure")
    if any(list(tree.iter(tag)) for tag in ("failure", "error", "skipped")):
        _fail("REPLAY_FAILED", "JUnit unsuccessful outcome")
    if any(phase["exit_code"] != 0 for phase in phases):
        _fail("REPLAY_FAILED", "native phase exit")
    golden = (run / "golden.log").read_text(encoding="utf-8")
    if re.search(r"\b(?:XPASS|xpassed|xfailed|XFAIL)\b", golden):
        _fail("REPLAY_FAILED", "xfail/xpass diagnostics")
    markers = [
        line[len("RS_G07_TRACER ") :]
        for line in golden.splitlines()
        if line.startswith("RS_G07_TRACER ")
    ]
    expected_marker = {"module": "coverage.pytracer", "class": "PyTracer", "version": "7.16.2"}
    if len(markers) != 1 or _decode(markers[0].encode()) != expected_marker:
        _fail("TRACER_MISMATCH", "one active pinned PyTracer required")


def _intersection(
    method: _Method,
    statements: Sequence[int],
    excluded: Sequence[int],
    contexts: dict[int, list[str]],
    qualified: frozenset[str],
) -> MethodHit:
    for value in (*statements, *excluded, *contexts):
        _integer(value, 1)
    body = set(range(method.body_start, method.body_end + 1))
    executable = tuple(sorted(body.intersection(statements)))
    if not executable:
        _fail("EMPTY_BODY", method.key)
    if body.intersection(excluded):
        _fail("EXCLUDED_BODY", method.key)
    hit = tuple(line for line in executable if qualified.intersection(contexts.get(line, ())))
    contributing = tuple(
        sorted({context for line in hit for context in contexts[line] if context in qualified})
    )
    return MethodHit(
        method.key, method.path, method.body_start, method.body_end, executable, hit, contributing
    )


def _native(root: Path, run: Path, inventory: _Inventory) -> tuple[MethodHit, ...]:
    # Validate export encoding/version only;statement/hit decisions use public native APIs.
    audit = _decode(_read(run / "golden.coverage.json", 16 * _MIB))
    metadata = _object(audit.get("meta"))
    if _integer(metadata.get("format")) != 3 or _text(metadata.get("version")) != "7.16.2":
        _fail("UNSUPPORTED_VERSION", "native JSON format/version")
    try:
        # Constructor operands override ambient COVERAGE_FILE/DEBUG without changing
        # the parent's environment. Assessment must read the producer-owned database.
        cov = coverage.Coverage(
            config_file=str(run / "coverage.toml"), data_file=str(run / "golden.coverage"), debug=[]
        )
        cov.load()
        data = cov.get_data()
        if not data.has_arcs():
            _fail("NATIVE_ERROR", "branch data required")
        files: dict[str, str] = {}
        for filename in sorted(data.measured_files()):
            path = Path(filename)
            if not path.is_absolute() or not path.resolve().is_relative_to(root):
                _fail("INVALID_PATH", "foreign measured file " + filename)
            name = path.resolve().relative_to(root).as_posix()
            _path(root, name)
            if name.casefold() in files:
                _fail("INVALID_PATH", "measured filename collision " + name)
            files[name.casefold()] = filename
        for name in sorted(inventory.source_sha256):
            if name.casefold() not in files:
                _fail("MISSING_FILE", name)
        contexts = data.measured_contexts()
        if len(contexts) > 4096:
            _fail("BOUNDS", "native contexts")
        expected_contexts = {n.context for n in inventory.golden_nodes}
        if expected_contexts - contexts or contexts - expected_contexts - {""}:
            _fail("MISSING_CONTEXT", "exact qualified context set required")
        data.set_query_contexts(None)
        observations: list[MethodHit] = []
        for method in inventory.methods:
            filename = files[method.path.casefold()]
            _, statements, excluded, _, _ = cov.analysis2(filename)
            byline = data.contexts_by_lineno(filename)
            source_length = len((root / method.path).read_text(encoding="utf-8").splitlines())
            for line, values in byline.items():
                _integer(line, 1)
                if line > source_length:
                    _fail("NATIVE_ERROR", method.path + " native line outside source")
                if any(type(context) is not str or context not in contexts for context in values):
                    _fail("NATIVE_ERROR", method.path + " invalid native contexts")
            qualified = frozenset(
                n.context for n in inventory.golden_nodes if n.registry in method.registries
            )
            observations.append(_intersection(method, statements, excluded, byline, qualified))
        return tuple(observations)
    except (CoverageException, ValueError) as error:
        raise _EvidenceError("NATIVE_ERROR", "native coverage load/analysis failed") from error


def _unverified(error: _EvidenceError) -> ReplayCoverageResult:
    return ReplayCoverageResult("UNVERIFIED", error.freshness, error.code, error.detail, ())


def assess_run(project_root: Path, run_dir: Path) -> ReplayCoverageResult:
    """Read native evidence only;missing/stale evidence cannot become a passing result."""
    try:
        root, run = _location(project_root, run_dir)
        _packages()
        inventory = _inventory(root, verify_sources=False)
        descriptor = _evidence(root, run, inventory)
        _inventory(root)
        _registry(root, inventory)
        _selection(run, inventory, descriptor)
        methods = _native(root, run, inventory)
        # Revalidate bytes,packages and paths after native analysis;never publish a raced PASS.
        artifacts_after = _artifacts(run)
        if (
            all(value is not None for value in artifacts_after.values())
            and artifacts_after != descriptor["artifacts"]
        ):
            raise _EvidenceError("STALE_INPUT", "artifact changed during analysis", "STALE")
        if _evidence(root, run, inventory) != descriptor:
            raise _EvidenceError("STALE_INPUT", "descriptor changed during analysis", "STALE")
        failed = tuple(method.key for method in methods if not method.hit_lines)
        if failed:
            return ReplayCoverageResult("FAIL", "CURRENT", "ZERO_HIT", ", ".join(failed), methods)
        return ReplayCoverageResult(
            "PASS", "CURRENT", None, "35 registered bodies hit by8replays", methods
        )
    except _EvidenceError as error:
        return _unverified(error)
    except (OSError, UnicodeError) as error:
        return _unverified(
            _EvidenceError("MALFORMED_EVIDENCE", "evidence IO/encoding " + type(error).__name__)
        )


def _result_document(result: ReplayCoverageResult) -> dict[str, object]:
    return {"schema_version": 1, "gate": "G07", **asdict(result)}


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def run_gate(project_root: Path, run_dir: Path) -> ReplayCoverageResult:
    """Exclusive producer;subprocess failures and raw logs remain owned evidence."""
    owned = False
    interrupted = False
    run = run_dir
    try:
        root, run = _location(project_root, run_dir)
        if run.exists():
            _fail("INVALID_PATH", "run already exists " + str(run))
        packages = _packages()
        inventory = _inventory(root)
        _registry(root, inventory)
        try:
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
            ).stdout.strip()
        except subprocess.CalledProcessError as error:
            raise _EvidenceError("NATIVE_ERROR", "git baseline provenance unavailable") from error
        run.parent.mkdir(exist_ok=True)
        run.mkdir(exist_ok=False)
        owned = True
        (run / "temp").mkdir()
        before = _snapshot(root)
        config = (
            '[tool.coverage.run]\nbranch=true\ncore="pytrace"\n'
            'source=["src/engines","src/domain","src/contracts"]\n'
            'dynamic_context="test_function"\ndata_file='
            + json.dumps(str(run / "golden.coverage"))
            + "\n[tool.coverage.report]\nignore_errors=false\n"
        )
        (run / "coverage.toml").write_bytes(config.encode("utf-8"))
        recorded = _environment(root, run)
        environment = os.environ.copy()  # noqa: TID251 -- developer subprocess boundary;no parent mutation
        for key in tuple(environment):
            if key.upper().startswith("COVERAGE_") or key.upper() in (
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
            ):
                del environment[key]
        environment.update(recorded)
        # A boundary stopwatch measures tools,never simulation ticks.
        from time import perf_counter  # noqa: TID251

        phases: list[dict[str, object]] = []
        failed = False
        for name, argv in zip(_PHASES, _commands(run, inventory), strict=True):
            exit_code: int | None = None
            elapsed = 0.0
            if not failed:
                started = perf_counter()
                try:
                    child = subprocess.run(
                        argv,
                        cwd=root,
                        env=environment,
                        capture_output=True,
                        shell=False,
                        check=False,
                    )
                    exit_code = child.returncode
                    (run / (name + ".log")).write_bytes(
                        child.stdout + b"\n--- STDERR ---\n" + child.stderr
                    )
                except OSError as error:
                    (run / (name + ".log")).write_text(
                        "child launch failed: " + type(error).__name__, encoding="utf-8"
                    )
                except KeyboardInterrupt:
                    interrupted = True
                    (run / (name + ".log")).write_text("child interrupted", encoding="utf-8")
                elapsed = perf_counter() - started
                failed = exit_code != 0
            phases.append(
                {
                    "id": name,
                    "argv": argv,
                    "cwd": str(root),
                    "environment": recorded,
                    "exit_code": exit_code,
                    "elapsed_seconds": elapsed,
                }
            )
        after = _snapshot(root)
        descriptor = {
            "schema_version": 1,
            "run_id": run.name[6:],
            "project_root": str(root),
            "baseline_head": head,
            "python": {"executable": sys.executable, "version": sys.version.split()[0]},
            "packages": packages,
            "inputs_before": before,
            "inputs_after": after,
            "inventory_sha256": before[_INVENTORY],
            "config_sha256": _sha(config.encode()),
            "phases": phases,
            "artifacts": _artifacts(run),
        }
        _write_json(run / "run.json", descriptor)
        result = assess_run(root, run)
    except _EvidenceError as error:
        result = _unverified(error)
    except (OSError, UnicodeError) as error:
        result = _unverified(
            _EvidenceError("MALFORMED_EVIDENCE", "producer IO/encoding " + type(error).__name__)
        )
    if owned:
        try:
            _write_json(run / "result.json", _result_document(result))
        except OSError:
            return _unverified(
                _EvidenceError("ARTIFACT_MISSING", "could not write owned result.json")
            )
    if interrupted:
        raise KeyboardInterrupt
    return result


def pytest_sessionstart(session: pytest.Session) -> None:
    """Observe the actual in-flight tracer;do not mutate collection or outcomes."""
    trace = sys.gettrace()
    active = getattr(trace, "__self__", None)
    marker = {
        "module": type(active).__module__,
        "class": type(active).__name__,
        "version": coverage.__version__,
    }
    print("RS_G07_TRACER " + json.dumps(marker, sort_keys=True), flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "assess"))
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        if error.code == 0:
            return 0
        print(
            json.dumps(
                _result_document(_unverified(_EvidenceError("MALFORMED_EVIDENCE", "CLI arguments")))
            )
        )
        return 2
    result = (run_gate if args.command == "run" else assess_run)(args.project_root, args.run_dir)
    print(json.dumps(_result_document(result), sort_keys=True))
    return 0 if result.status == "PASS" else 1 if result.status == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
