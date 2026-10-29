"""Independent G07 boundary cases and real native replay/coverage evidence."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import FrozenInstanceError
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import coverage
import pytest

from tools import replay_body_coverage as gate

ROOT = Path(__file__).resolve().parents[2]
_GOLDENS = (
    "tests/replay/test_golden.py::test_core_trace",
    "tests/replay/test_trial.py::test_trial_core_trace",
    "tests/replay/test_encounter.py::test_encounter_core_trace",
    "tests/replay/test_encounter.py::test_encounter_death_trace",
    "tests/replay/test_watch.py::test_watch_core_trace",
    "tests/replay/test_watch.py::test_watch_passive_trace",
    "tests/replay/test_quest.py::test_independent_vector_then_real_durable_offline_replay",
    "tests/integration/test_npc_memory.py::test_retry_repeat_save_load_resume_and_offline_replay",
)


def _json(path: Path) -> dict[str, object]:
    return gate._decode(path.read_bytes())


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, allow_nan=False), encoding="utf-8")


def _rows(value: object) -> list[dict[str, object]]:
    return [gate._object(v) for v in gate._array(value, 4096, nonempty=False)]


def _new_run(root: Path) -> Path:
    return root / ".pytest_cache" / ("gov03-" + secrets.token_hex(16))


def _env(root: Path) -> dict[str, str]:
    result = os.environ.copy()  # noqa: TID251 -- test subprocess boundary
    for key in tuple(result):
        if key.startswith("COVERAGE_") or key == "PYTEST_ADDOPTS":
            del result[key]
    result.update(
        PYTHONPATH=os.pathsep.join((str(root / "src"), str(root))),
        PYTHONHASHSEED="0",
        PYTHONUTF8="1",
        PYTHONIOENCODING="utf-8",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
    )
    return result


def _cli(
    root: Path, run: Path, command: str = "assess", *, poison: bool = False
) -> tuple[int, dict[str, object]]:
    environment = _env(root)
    if poison:
        environment.update(
            PYTEST_ADDOPTS="--not-a-valid-option",
            PYTEST_PLUGINS="missing_unapproved_plugin",
            COVERAGE_CORE="ctrace",
            COVERAGE_FILE=str(root / "foreign.coverage"),
        )
    child = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.replay_body_coverage",
            command,
            "--project-root",
            str(root),
            "--run-dir",
            str(run),
        ],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=240,
    )
    assert len(child.stdout.splitlines()) == 1, child.stdout + child.stderr
    return child.returncode, gate._decode(child.stdout.encode("utf-8"))


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


@pytest.fixture(scope="module")
def native_project(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("g07-native") / "workspace"
    root.mkdir()
    for folder in ("src", "tests", "tools", "content"):
        shutil.copytree(
            ROOT / folder,
            root / folder,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
    for name in (*gate._CONFIG_INPUTS, *gate._DOCUMENT_INPUTS):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    run = _new_run(root)
    before = gate._snapshot(root)
    code, result = _cli(root, run, "run", poison=True)
    assert (code, result["status"], result["freshness"], result["code"]) == (
        0,
        "PASS",
        "CURRENT",
        None,
    ), result
    assert gate._snapshot(root) == before
    return root, run


@pytest.fixture
def evidence(native_project: tuple[Path, Path]) -> Iterator[tuple[Path, Path]]:
    # Each mutation is confined to the independent copied project and fully restored.
    root, run = native_project
    before = {
        p: p.read_bytes() for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    }
    yield root, run
    for path in root.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts and path not in before:
            path.unlink()
    for path, body in before.items():
        if not path.exists() or path.read_bytes() != body:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)


def _bind(root: Path, run: Path, *, inputs: bool = False) -> None:
    descriptor = _json(run / "run.json")
    descriptor["artifacts"] = gate._artifacts(run)
    descriptor["config_sha256"] = hashlib.sha256((run / "coverage.toml").read_bytes()).hexdigest()
    if inputs:
        descriptor["inputs_before"] = descriptor["inputs_after"] = gate._snapshot(root)
        descriptor["inventory_sha256"] = hashlib.sha256(
            (root / gate._INVENTORY).read_bytes()
        ).hexdigest()
    _write(run / "run.json", descriptor)


def _expect(root: Path, run: Path, code: str, freshness: str = "UNKNOWN") -> None:
    exit_code, result = _cli(root, run)
    assert (
        exit_code,
        result["status"],
        result["freshness"],
        result["code"],
        result["methods"],
    ) == (2, "UNVERIFIED", freshness, code, []), result


def _method(start: int = 2, end: int = 5) -> gate._Method:
    return gate._Method(
        "toy.Engine.evaluate",
        "toy.Engine.evaluate",
        "src/toy.py",
        1,
        start,
        end,
        ("toy",),
        "toy.engine",
        (),
    )


@pytest.mark.parametrize(
    "statements,contexts,hits",
    (
        (
            (1, 2, 3, 4, 5),
            {2: ["golden"], 3: ["golden"], 4: ["golden"], 5: ["golden"]},
            (2, 3, 4, 5),
        ),
        ((1, 2, 3, 4, 5), {2: ["golden"], 3: ["golden"]}, (2, 3)),
        ((1, 2, 3, 4, 5), {1: ["golden"]}, ()),
        ((1, 2, 3, 4, 5), {2: [""]}, ()),
        ((1, 2, 3, 4, 5), {2: ["supplemental"]}, ()),
        ((1, 2, 3, 5), {4: ["golden"]}, ()),
    ),
)
def test_body_intersections(
    statements: tuple[int, ...],
    contexts: dict[int, list[str]],
    hits: tuple[int, ...],
) -> None:
    result = gate._intersection(_method(), statements, (), contexts, frozenset({"golden"}))
    assert result.hit_lines == hits
    assert result.golden_contexts == (("golden",) if hits else ())


def test_single_line_and_immutable_dtos() -> None:
    result = gate._intersection(
        _method(53, 53), (1, 53), (), {53: ["golden"]}, frozenset({"golden"})
    )
    assert (result.executable_lines, result.hit_lines) == ((53,), (53,))
    with pytest.raises(FrozenInstanceError):
        setattr(result, "key", "changed")
    with pytest.raises(FrozenInstanceError):
        setattr(
            gate.ReplayCoverageResult("PASS", "CURRENT", None, "ok", (result,)), "detail", "changed"
        )


@pytest.mark.parametrize(
    "statements,excluded,code", (((1,), (), "EMPTY_BODY"), ((2,), (3,), "EXCLUDED_BODY"))
)
def test_empty_and_excluded_body(
    statements: tuple[int, ...], excluded: tuple[int, ...], code: str
) -> None:
    with pytest.raises(gate._EvidenceError, match=code):
        gate._intersection(_method(), statements, excluded, {}, frozenset({"golden"}))


@pytest.mark.parametrize(
    "body", (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b" ", b"\xff", b"[]")
)
def test_strict_json(body: bytes) -> None:
    with pytest.raises(gate._EvidenceError, match="MALFORMED_EVIDENCE"):
        gate._decode(body)


@pytest.mark.parametrize(
    "value,code",
    ((True, "MALFORMED_EVIDENCE"), (0, "BOUNDS"), (-1, "BOUNDS"), (1_000_001, "BOUNDS")),
)
def test_line_bounds(value: object, code: str) -> None:
    with pytest.raises(gate._EvidenceError, match=code):
        gate._integer(value, 1)
    assert gate._integer(1, 1) == 1 and gate._integer(1_000_000, 1) == 1_000_000


def test_scalar_caps() -> None:
    assert len(gate._text("a" * 4096)) == 4096
    assert len(gate._array([0] * 128, 128)) == 128
    assert gate._integer(16 * 1024**2, 0, 16 * 1024**2) == 16 * 1024**2
    for action in (
        lambda: gate._text("a" * 4097),
        lambda: gate._array([0] * 129, 128),
        lambda: gate._integer(16 * 1024**2 + 1, 0, 16 * 1024**2),
    ):
        with pytest.raises(gate._EvidenceError, match="BOUNDS"):
            action()


@pytest.mark.parametrize(
    "name",
    ("../escape", "/absolute", "C:/outside", "//host/share", "a\\b", "a//b", "./a", "a/../b"),
)
def test_invalid_relative_paths(name: str) -> None:
    with pytest.raises(gate._EvidenceError, match="INVALID_PATH"):
        gate._relative(name)


def test_case_collisions() -> None:
    with pytest.raises(gate._EvidenceError, match="INVALID_PATH"):
        gate._hash_map({"src/a.py": "0" * 64, "src/A.py": "0" * 64})


@pytest.mark.parametrize("mode", ("called", "import-only", "excluded"))
def test_native_toy(tmp_path: Path, mode: str) -> None:
    # Independent literal branch/body oracle:definitions never establish execution.
    (tmp_path / "toy.py").write_text(
        "def choose(flag):\n    if flag:\n        return 1\n    else:\n        return 2\n",
        encoding="utf-8",
    )
    if mode == "excluded":
        (tmp_path / "toy.py").write_text(
            "def choose(flag):\n    if flag:  # pragma: no cover\n        return 1\n    else:\n        return 2\n",
            encoding="utf-8",
        )
    (tmp_path / "test_toy.py").write_text(
        "from toy import choose\ndef test_choice():\n"
        + (
            "    assert choose(True) == 1\n    assert choose(False) == 2\n"
            if mode != "import-only"
            else "    assert callable(choose)\n"
        ),
        encoding="utf-8",
    )
    config = tmp_path / "coverage.toml"
    config.write_text(
        '[tool.coverage.run]\nbranch=true\ncore="pytrace"\nsource=["toy"]\n'
        'dynamic_context="test_function"\ndata_file=' + json.dumps(str(tmp_path / "data")),
        encoding="utf-8",
    )
    child = subprocess.run(
        [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--rcfile",
            str(config),
            "-m",
            "pytest",
            "-q",
            "test_toy.py",
        ],
        cwd=tmp_path,
        env=_env(tmp_path),
        capture_output=True,
        timeout=60,
    )
    (tmp_path / "native.log").write_bytes(child.stdout + child.stderr)
    assert child.returncode == 0, child.stdout + child.stderr
    cov = coverage.Coverage(config_file=str(config))
    cov.load()
    _, statements, excluded, _, _ = cov.analysis2(str(tmp_path / "toy.py"))
    data = cov.get_data()
    assert data.has_arcs()
    if mode == "excluded":
        assert 2 in excluded and 3 in excluded
        return
    result = gate._intersection(
        _method(),
        statements,
        excluded,
        data.contexts_by_lineno(str(tmp_path / "toy.py")),
        frozenset({"test_toy.test_choice"}),
    )
    assert result.hit_lines == ((2, 3, 5) if mode == "called" else ())


def test_real_cli_scope_and_read_only(native_project: tuple[Path, Path]) -> None:
    root, run = native_project
    before = _tree_hashes(root)
    code, result = _cli(root, run)
    assert code == 0 and result["status"] == "PASS"
    assert _tree_hashes(root) == before
    rows = _rows(result["methods"])
    assert len(rows) == 35 and all(row["hit_lines"] for row in rows)
    assert len({gate._text(row["key"]).rsplit(".", 1)[0] for row in rows}) == 12
    assert len({row["path"] for row in rows}) == 8
    for key in (
        "engines.trial.Movement.evaluate",
        "engines.encounter.EncounterMovement.evaluate",
        "engines.quest.QuestRules.quest_content",
        "engines.npc_memory.NpcQuestMemory.quest_content",
        "engines.watch.WatchNpc.scenario_layout",
    ):
        assert any(row["key"] == key and row["hit_lines"] for row in rows)
    descriptor = _json(run / "run.json")
    assert descriptor["inputs_before"] == descriptor["inputs_after"]
    assert [
        gate._text(row["node_id"]) for row in _rows(_json(root / gate._INVENTORY)["golden_nodes"])
    ] == list(_GOLDENS)
    assert set(gate._DOCUMENT_INPUTS) <= set(gate._object(descriptor["inputs_before"]))
    assert (
        sum(
            len(gate._array(row["nested_code"], 256, nonempty=False))
            for row in _rows(_json(root / gate._INVENTORY)["methods"])
        )
        == 4
    )


def test_existing_run_preserves_bytes(native_project: tuple[Path, Path]) -> None:
    root, run = native_project
    before = _tree_hashes(run)
    code, result = _cli(root, run, "run")
    assert (code, result["code"]) == (2, "INVALID_PATH")
    assert _tree_hashes(run) == before


@pytest.mark.parametrize(
    "name",
    (
        "src/engines/quest.py",
        "src/domain/scenario.py",
        "src/contracts/dialogue.py",
        "pyproject.toml",
        "tests/replay/fixtures/trial_v1.json",
        "tools/__init__.py",
        "content/dialogue/harbor-memory-v1.json",
        *gate._DOCUMENT_INPUTS,
    ),
)
def test_input_drift(evidence: tuple[Path, Path], name: str) -> None:
    root, run = evidence
    path = root / name
    path.write_bytes(path.read_bytes() + b"\n")
    _expect(root, run, "STALE_INPUT", "STALE")


@pytest.mark.parametrize("operation", ("add", "delete"))
def test_input_set_drift(evidence: tuple[Path, Path], operation: str) -> None:
    root, run = evidence
    path = root / "content/added.json" if operation == "add" else root / "tools/__init__.py"
    if operation == "add":
        path.write_bytes(b"{}")
    else:
        path.unlink()
    _expect(root, run, "STALE_INPUT", "STALE")


def test_delivery_docs_do_not_invalidate(evidence: tuple[Path, Path]) -> None:
    root, run = evidence
    (root / "docs/note.md").write_text("delivery-only", encoding="utf-8")
    code, result = _cli(root, run)
    assert code == 0 and result["status"] == "PASS"


@pytest.mark.parametrize(
    "mode,code",
    (
        ("missing", "ARTIFACT_MISSING"),
        ("hash", "ARTIFACT_HASH"),
        ("large", "BOUNDS"),
        ("descriptor-large", "BOUNDS"),
        ("duplicate", "MALFORMED_EVIDENCE"),
        ("unknown", "MALFORMED_EVIDENCE"),
        ("bool", "MALFORMED_EVIDENCE"),
        ("hex", "MALFORMED_EVIDENCE"),
        ("version", "UNSUPPORTED_VERSION"),
    ),
)
def test_evidence_rejections(evidence: tuple[Path, Path], mode: str, code: str) -> None:
    root, run = evidence
    if mode == "missing":
        (run / "golden.coverage").unlink()
    elif mode == "hash":
        path = run / "json.log"
        path.write_bytes(path.read_bytes() + b"different")
    elif mode == "large":
        with (run / "json.log").open("r+b") as stream:  # noqa: TID251 -- owned evidence fixture
            stream.truncate(16 * 1024**2 + 1)
    elif mode == "descriptor-large":
        (run / "run.json").write_bytes(b" " * (4 * 1024**2 + 1))
    elif mode == "duplicate":
        (run / "run.json").write_bytes(b'{"schema_version":1,"schema_version":1}')
    else:
        descriptor = _json(run / "run.json")
        if mode == "unknown":
            descriptor["extra"] = 1
        elif mode == "bool":
            descriptor["schema_version"] = True
        elif mode == "hex":
            descriptor["baseline_head"] = "g" * 40
        elif mode == "version":
            descriptor["schema_version"] = 99
        _write(run / "run.json", descriptor)
    _expect(root, run, code)


@pytest.mark.parametrize("mode", ("omit", "extra", "duplicate"))
def test_collection_selection(evidence: tuple[Path, Path], mode: str) -> None:
    root, run = evidence
    lines = list(_GOLDENS)
    if mode == "omit":
        lines.pop()
    elif mode == "extra":
        lines.append("tests/replay/test_extra.py::test_extra")
    else:
        lines.append(lines[0])
    (run / "collect.log").write_text("\n".join(lines), encoding="utf-8")
    _bind(root, run)
    _expect(root, run, "SELECTION_MISMATCH")


@pytest.mark.parametrize(
    "mode,code",
    (
        ("omit", "SELECTION_MISMATCH"),
        ("extra", "SELECTION_MISMATCH"),
        ("duplicate", "SELECTION_MISMATCH"),
        ("zero", "REPLAY_FAILED"),
        ("failure", "REPLAY_FAILED"),
        ("error", "REPLAY_FAILED"),
        ("skipped", "REPLAY_FAILED"),
        ("dtd", "MALFORMED_EVIDENCE"),
    ),
)
def test_junit_outcomes(evidence: tuple[Path, Path], mode: str, code: str) -> None:
    root, run = evidence
    path = run / "golden.junit.xml"
    tree = ET.fromstring(path.read_bytes())
    suite = tree.find("testsuite")
    assert suite is not None
    cases = suite.findall("testcase")
    if mode == "omit":
        suite.remove(cases[-1])
    elif mode == "extra":
        ET.SubElement(suite, "testcase", {"classname": "extra", "name": "test_extra"})
    elif mode == "duplicate":
        suite.append(ET.fromstring(ET.tostring(cases[0])))
    elif mode == "zero":
        suite.set("tests", "0")
    elif mode in ("failure", "error", "skipped"):
        ET.SubElement(cases[0], mode)
    path.write_bytes(ET.tostring(tree))
    if mode == "dtd":
        path.write_bytes(b'<!DOCTYPE x [<!ENTITY x "bad">]>' + path.read_bytes())
    _bind(root, run)
    _expect(root, run, code)


@pytest.mark.parametrize(
    "mode,code",
    (
        ("xpass", "REPLAY_FAILED"),
        ("exit", "REPLAY_FAILED"),
        ("tracer", "TRACER_MISMATCH"),
        ("double-tracer", "TRACER_MISMATCH"),
        ("argv", "MALFORMED_EVIDENCE"),
        ("env", "MALFORMED_EVIDENCE"),
        ("packages", "UNSUPPORTED_VERSION"),
        ("config", "MALFORMED_EVIDENCE"),
    ),
)
def test_phase_provenance(evidence: tuple[Path, Path], mode: str, code: str) -> None:
    root, run = evidence
    if mode in ("xpass", "tracer", "double-tracer"):
        path = run / "golden.log"
        body = path.read_text(encoding="utf-8")
        if mode == "xpass":
            body += "\n1 xpassed\n"
        elif mode == "tracer":
            body = body.replace('"PyTracer"', '"CTracer"')
        else:
            body += "\n" + next(
                line for line in body.splitlines() if line.startswith("RS_G07_TRACER ")
            )
        path.write_text(body, encoding="utf-8")
        _bind(root, run)
    elif mode == "config":
        path = run / "coverage.toml"
        path.write_text(path.read_text() + "\n[tool.coverage.json]\npretty_print=true\n")
        _bind(root, run)
    else:
        descriptor = _json(run / "run.json")
        phases = _rows(descriptor["phases"])
        if mode == "exit":
            phases[1]["exit_code"] = 1
        elif mode == "argv":
            phases[1]["argv"] = ["foreign-python"]
        elif mode == "env":
            gate._object(phases[1]["environment"])["PYTHONHASHSEED"] = "random"
        else:
            gate._object(descriptor["packages"])["coverage"] = "0.0"
        _write(run / "run.json", descriptor)
    _expect(root, run, code)


@pytest.mark.parametrize(
    "mode,code",
    (
        ("omit", "INVENTORY_MISMATCH"),
        ("extra", "INVENTORY_MISMATCH"),
        ("foreign", "INVENTORY_MISMATCH"),
        ("inverted", "INVALID_RANGE"),
        ("range", "INVALID_RANGE"),
        ("nested", "INVALID_RANGE"),
        ("getter-owner", "INVENTORY_MISMATCH"),
    ),
)
def test_registry_inventory(evidence: tuple[Path, Path], mode: str, code: str) -> None:
    root, run = evidence
    path = root / gate._INVENTORY
    inventory = _json(path)
    methods = _rows(inventory["methods"])
    if mode == "omit":
        methods.pop()
    elif mode == "extra":
        methods.append({**methods[-1], "key": "engines.zz.Extra.evaluate"})
    elif mode == "foreign":
        methods[0]["implementation"] = "foreign.Engine.evaluate"
    elif mode == "inverted":
        methods[0]["body_end"] = 1
    elif mode == "range":
        methods[0]["body_start"] = gate._integer(methods[0]["body_start"]) + 1
    elif mode == "nested":
        nested = next(row for row in methods if row["nested_code"])
        nested["nested_code"] = []
    else:
        row = next(row for row in methods if row["key"] == "engines.watch.WatchNpc.scenario_layout")
        row["registries"] = ["watch_bundle"]
    inventory["methods"] = methods
    _write(path, inventory)
    _bind(root, run, inputs=True)
    _expect(root, run, code)


def _change_native(run: Path, mode: str) -> None:
    original = coverage.CoverageData(basename=str(run / "golden.coverage"))
    original.read()
    output_path = run / "altered.coverage"
    result = coverage.CoverageData(basename=str(output_path))
    for context in sorted(original.measured_contexts()):
        if mode == "missing-context" and context.endswith("test_watch_passive_trace"):
            continue
        original.set_query_contexts(["^" + re.escape(context) + "$"])
        actual_context = (
            "foreign.supplemental"
            if mode == "foreign-context" and context.endswith("test_watch_passive_trace")
            else context
        )
        result.set_context(actual_context)
        for filename in sorted(original.measured_files()):
            if mode == "missing-file" and filename.replace("\\", "/").endswith(
                "src/contracts/dialogue.py"
            ):
                continue
            if mode == "no-branch":
                result.add_lines({filename: original.lines(filename) or []})
            else:
                arcs = original.arcs(filename) or []
                if (
                    mode == "zero"
                    and filename.replace("\\", "/").endswith("src/domain/scenario.py")
                    and context
                ):
                    # Independent reviewed single-line getter oracle:line140.
                    moved = [arc for arc in arcs if 140 in arc]
                    result.set_context("")
                    result.add_arcs({filename: moved})
                    result.set_context(actual_context)
                    arcs = [arc for arc in arcs if 140 not in arc]
                result.add_arcs({filename: arcs})
    result.write()
    output_path.replace(run / "golden.coverage")


@pytest.mark.parametrize(
    "mode,code",
    (
        ("missing-context", "MISSING_CONTEXT"),
        ("foreign-context", "MISSING_CONTEXT"),
        ("missing-file", "MISSING_FILE"),
        ("no-branch", "NATIVE_ERROR"),
        ("malformed", "NATIVE_ERROR"),
    ),
)
def test_native_rejections(evidence: tuple[Path, Path], mode: str, code: str) -> None:
    root, run = evidence
    if mode == "malformed":
        (run / "golden.coverage").write_bytes(b"not a database")
    else:
        _change_native(run, mode)
    _bind(root, run)
    _expect(root, run, code)


def test_zero_hit_is_cli_one(evidence: tuple[Path, Path]) -> None:
    root, run = evidence
    assert (root / "src/domain/scenario.py").read_text().splitlines()[
        139
    ].strip() == "return self._layout"
    _change_native(run, "zero")
    _bind(root, run)
    code, result = _cli(root, run)
    assert (code, result["status"], result["freshness"], result["code"]) == (
        1,
        "FAIL",
        "CURRENT",
        "ZERO_HIT",
    ), result
    assert len(_rows(result["methods"])) == 35
    assert "scenario_layout" in gate._text(result["detail"])


def test_actual_failed_child_keeps_evidence(evidence: tuple[Path, Path]) -> None:
    root, _ = evidence
    (root / "tests/replay/test_golden.py").write_bytes(b"def broken syntax\n")
    run = _new_run(root)
    code, result = _cli(root, run, "run")
    assert code == 2 and result["status"] == "UNVERIFIED"
    descriptor = _json(run / "run.json")
    phases = _rows(descriptor["phases"])
    assert phases[0]["exit_code"] != 0 and phases[1]["exit_code"] is None
    artifacts = gate._object(descriptor["artifacts"])
    assert artifacts["golden.coverage"] is None and artifacts["golden.junit.xml"] is None
    assert (run / "collect.log").stat().st_size > 0 and (run / "result.json").is_file()


@pytest.mark.parametrize("kind", ("<lambda>", "helper"))
def test_unreviewed_nested_callable(evidence: tuple[Path, Path], kind: str) -> None:
    root, run = evidence
    path = root / gate._INVENTORY
    inventory = _json(path)
    methods = _rows(inventory["methods"])
    row = next(row for row in methods if row["key"] == "engines.skeleton.Stepper.evaluate")
    row["nested_code"] = [
        {
            "name": kind,
            "first_line": row["body_start"],
            "qualname": "Stepper.evaluate.<locals>." + kind,
            "policy": gate._NESTED_POLICY,
        }
    ]
    inventory["methods"] = methods
    _write(path, inventory)
    _bind(root, run, inputs=True)
    _expect(root, run, "INVALID_RANGE")


@pytest.mark.parametrize("mode", ("six-only", "extra-memory-context"))
def test_current_eight_contexts_are_mandatory(evidence: tuple[Path, Path], mode: str) -> None:
    root, run = evidence
    if mode == "six-only":
        (run / "collect.log").write_text("\n".join(_GOLDENS[:6]), encoding="utf-8")
        _bind(root, run)
        _expect(root, run, "SELECTION_MISMATCH")
    else:
        data = coverage.CoverageData(basename=str(run / "golden.coverage"))
        data.read()
        data.set_context("tests.integration.test_npc_memory.test_unapproved_extra")
        data.add_arcs({str(root / "src/engines/npc_memory.py"): [(30, 31)]})
        data.write()
        _bind(root, run)
        _expect(root, run, "MISSING_CONTEXT")


def test_error_precedence_missing_before_stale(evidence: tuple[Path, Path]) -> None:
    root, run = evidence
    path = root / "src/domain/scenario.py"
    path.write_bytes(path.read_bytes() + b"\n")
    (run / "golden.coverage").unlink()
    _expect(root, run, "ARTIFACT_MISSING")


def test_foreign_native_file(evidence: tuple[Path, Path]) -> None:
    root, run = evidence
    data = coverage.CoverageData(basename=str(run / "golden.coverage"))
    data.read()
    data.set_context("")
    data.add_arcs({str(root.parent / "foreign.py"): [(1, 2)]})
    data.write()
    _bind(root, run)
    _expect(root, run, "INVALID_PATH")


@pytest.mark.parametrize(
    "old,new", (("branch=true", "branch=1"), ("ignore_errors=false", "ignore_errors=0"))
)
def test_config_requires_exact_boolean_types(
    evidence: tuple[Path, Path], old: str, new: str
) -> None:
    root, run = evidence
    path = run / "coverage.toml"
    path.write_bytes(path.read_bytes().replace(old.encode(), new.encode()))
    _bind(root, run)
    _expect(root, run, "MALFORMED_EVIDENCE")


def test_invalid_factory_content_returns_typed_error(evidence: tuple[Path, Path]) -> None:
    root, _ = evidence
    (root / "content/dialogue/harbor-memory-v1.json").write_bytes(b"{}")
    code, result = _cli(root, _new_run(root), "run")
    assert (code, result["status"], result["code"]) == (2, "UNVERIFIED", "INVENTORY_MISMATCH")


@pytest.mark.parametrize(
    "body,code",
    (
        (b" ", "MALFORMED_EVIDENCE"),
        (b"\xff", "MALFORMED_EVIDENCE"),
        (b'{"meta":{"format":2,"version":"7.16.2"}}', "UNSUPPORTED_VERSION"),
        (b'{"meta":{"format":3,"version":"0.0"}}', "UNSUPPORTED_VERSION"),
    ),
)
def test_native_json_audit_version(evidence: tuple[Path, Path], body: bytes, code: str) -> None:
    root, run = evidence
    (run / "golden.coverage.json").write_bytes(body)
    _bind(root, run)
    _expect(root, run, code)


@pytest.mark.parametrize(
    "name", ("../json.log", "/json.log", "C:/json.log", "//host/share/json.log")
)
def test_descriptor_artifact_path_rejection(evidence: tuple[Path, Path], name: str) -> None:
    root, run = evidence
    descriptor = _json(run / "run.json")
    artifacts = gate._object(descriptor["artifacts"])
    artifacts[name] = artifacts.pop("json.log")
    _write(run / "run.json", descriptor)
    _expect(root, run, "INVALID_PATH")


def test_invalid_run_and_missing_evidence(tmp_path: Path) -> None:
    assert gate.assess_run(ROOT, tmp_path).code == "INVALID_PATH"
    assert gate.assess_run(ROOT, _new_run(ROOT)).code == "ARTIFACT_MISSING"


def test_symlink_rejection(tmp_path: Path, record_property: Callable[[str, object], None]) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "linked"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as error:
        record_property("symlink_capability", "UNAVAILABLE " + type(error).__name__)
        assert getattr(error, "winerror", None) == 1314
        return
    with pytest.raises(gate._EvidenceError, match="INVALID_PATH"):
        gate._reject_links(link)
