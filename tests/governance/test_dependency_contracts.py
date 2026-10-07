from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
import sys
import tomllib

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT_ROOT / "pyproject.toml"
RUNTIME_CONFIG = PROJECT_ROOT / ".importlinter-runtime.toml"
ROOTS = ("app", "adapters", "orchestration", "engines", "contracts", "domain")
ENGINE_MODULES = ("skeleton", "trial", "encounter", "watch")
CONTRACT_NAMES = (
    ("rs-layers", "Reverie Saga six internal layers"),
    ("rs-engines-independent", "Reverie Saga concrete engine modules are independent"),
    ("rs-core-no-external-effects",
     "Reverie Saga core avoids named SDK IO and developer-tool imports"),
    ("rs-siblings-acyclic", "Reverie Saga same-layer siblings have no runtime cycles"),
)
# Literal expectations were specified in the reviewed GOV-02 input inventory.
FORBIDDEN_ROOTS = (
    "aiohttp",
    "anthropic",
    "ast_serialize",
    "asyncio",
    "click",
    "colorama",
    "coverage",
    "ctypes",
    "datetime",
    "google",
    "godot",
    "grimp",
    "http",
    "httpx",
    "importlib",
    "importlinter",
    "iniconfig",
    "io",
    "librt",
    "markdown_it",
    "mdurl",
    "multiprocessing",
    "mypy",
    "mypy_extensions",
    "ollama",
    "openai",
    "os",
    "packaging",
    "pathlib",
    "pathspec",
    "pluggy",
    "production",
    "pygame",
    "pygments",
    "PySide6",
    "pytest",
    "pytest_mock",
    "random",
    "requests",
    "rich",
    "ruff",
    "secrets",
    "shutil",
    "socket",
    "sqlite3",
    "subprocess",
    "sys",
    "tempfile",
    "threading",
    "time",
    "tools",
    "typing_extensions",
    "unittest",
    "unity",
    "urllib",
    "uuid",
)


@dataclass(frozen=True)
class Probe:
    id: str
    changes: tuple[tuple[str, str], ...]
    exit_code: int
    broken: str | None


PROBES = (
    Probe("allowed-dag", (), 0, None),
    Probe("adapter-io", (("adapters/port.py", "import os\nimport pathlib\nimport sqlite3\n"),), 0, None),
    Probe("core-pure-stdlib", (("domain/value.py", "import dataclasses\nimport hashlib\nimport json\n"),), 0, None),
    Probe("reverse-layer", (("domain/value.py", "import app.entry\n"),), 1, "rs-layers"),
    Probe("indirect-reverse", (("domain/value.py", "import contracts.port\n"), ("contracts/port.py", "import app.entry\n"),), 1, "rs-layers"),
    Probe("direct-engine", (("engines/skeleton.py", "import engines.trial\n"),), 1, "rs-engines-independent"),
    Probe("indirect-engine", (("engines/skeleton.py", "import contracts.port\n"), ("contracts/port.py", "import engines.trial\n"),), 1, "rs-engines-independent"),
    Probe("type-only-reverse", (("domain/value.py", "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import app.entry\n"),), 1, "rs-layers"),
    Probe("core-indirect-io", (("engines/skeleton.py", "import contracts.port\n"), ("contracts/port.py", "import pathlib\n"),), 1, "rs-core-no-external-effects"),
    Probe("core-type-only-sdk", (("domain/value.py", "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import openai\n"),), 1, "rs-core-no-external-effects"),
    Probe("absent-forbidden-roots", (), 0, None),
    Probe("allowed-sibling-edge", (("domain/cycle_a.py", "import domain.cycle_b\n"), ("domain/cycle_b.py", "VALUE = 1\n"),), 0, None),
    Probe("allowed-type-only-sibling-cycle", (
        ("contracts/cycle_a.py", "from typing import TYPE_CHECKING\n"
         "if TYPE_CHECKING:\n    import contracts.cycle_b\n"),
        ("contracts/cycle_b.py", "import contracts.cycle_a\n"),
    ), 0, None),
)


def _tree(root: Path) -> None:
    for package in ROOTS:
        directory = root / package
        directory.mkdir()
        if package != "adapters":
            (directory / "__init__.py").write_text("", encoding="utf-8")
    files = {
        "app/entry.py": "import adapters.port\n"
        "import engines.skeleton\nimport engines.trial\n"
        "import engines.encounter\nimport engines.watch\n",
        "adapters/port.py": "import orchestration.driver\n",
        "orchestration/driver.py": "import contracts.port\n",
        "contracts/port.py": "import domain.value\n",
        "domain/value.py": "VALUE = 1\n",
    }
    for module in ENGINE_MODULES:
        files[f"engines/{module}.py"] = "import contracts.port\nimport domain.value\n"
    for name, source in files.items():
        (root / name).write_text(source, encoding="utf-8")


def _native(root: Path, configuration: Path, label: str) -> subprocess.CompletedProcess[str]:
    # Use the installed console entry point, not a generated Windows launcher.
    # Windows Application Control can deny pip-generated .exe launchers.
    argv = [
        sys.executable, "-c",
        "from importlinter.cli import lint_imports_command; lint_imports_command()",
        "--config", str(configuration), "--no-cache",
    ]
    result = subprocess.run(
        argv, cwd=root, text=True, encoding="utf-8", capture_output=True, timeout=60,
    )
    (root / f"{label}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    (root / f"{label}.json").write_text(json.dumps({
        "argv": argv, "cwd": str(root), "exit_code": result.returncode,
        "config": str(configuration),
    }, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _run_probe(
    root: Path, monkeypatch: pytest.MonkeyPatch,
) -> tuple[subprocess.CompletedProcess[str], subprocess.CompletedProcess[str]]:
    type_config, runtime_config = root / "types.toml", root / "runtime.toml"
    type_config.write_bytes(CONFIG.read_bytes())
    runtime_config.write_bytes(RUNTIME_CONFIG.read_bytes())
    with monkeypatch.context() as scoped:
        scoped.setenv("PYTHONPATH", str(root))
        scoped.setenv("PYTHONIOENCODING", "utf-8")
        scoped.setenv("PYTHONHASHSEED", "0")
        scoped.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
        return (
            _native(root, type_config, "type-inclusive"),
            _native(root, runtime_config, "runtime-cycles"),
        )


def _expect(results: tuple[subprocess.CompletedProcess[str], ...], case: Probe) -> None:
    output = "\n".join(result.stdout + result.stderr for result in results)
    if case.broken is None:
        assert all(result.returncode == 0 for result in results), output
        assert "Contracts: 3 kept, 0 broken." in results[0].stdout, output
        assert "Contracts: 1 kept, 0 broken." in results[1].stdout, output
        for _, name in CONTRACT_NAMES:
            assert f"{name} KEPT" in output, output
    else:
        assert all(result.returncode in (0, case.exit_code) for result in results), output
        index = 1 if case.broken == "rs-siblings-acyclic" else 0
        assert results[index].returncode == case.exit_code, output
        name = dict(CONTRACT_NAMES)[case.broken]
        assert f"{name} BROKEN" in output, output
        assert "Broken contracts" in output, output
        assert "Traceback" not in output, output


@pytest.mark.parametrize("case", PROBES, ids=tuple(case.id for case in PROBES))
def test_dependency_specified_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: Probe,
) -> None:
    _tree(tmp_path)
    for name, source in case.changes:
        (tmp_path / name).write_text(source, encoding="utf-8")
    results = _run_probe(tmp_path, monkeypatch)
    _expect(results, case)
    output = "\n".join(result.stdout for result in results)
    if case.broken == "rs-layers":
        assert "domain" in output or "contracts" in output, output
        assert "app.entry" in output, output
    elif case.broken == "rs-engines-independent":
        assert "engines.skeleton" in output and "engines.trial" in output, output
    elif case.id == "core-indirect-io":
        assert "contracts.port" in output and "pathlib" in output, output
    elif case.id == "core-type-only-sdk":
        assert "domain.value" in output and "openai" in output, output


@pytest.mark.parametrize("external", FORBIDDEN_ROOTS)
def test_dependency_external_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, external: str,
) -> None:
    _tree(tmp_path)
    (tmp_path / "engines/skeleton.py").write_text(f"import {external}\n", encoding="utf-8")
    results = _run_probe(tmp_path, monkeypatch)
    _expect(results, Probe("direct-external", (), 1, "rs-core-no-external-effects"))
    assert f"engines.skeleton -> {external}" in results[0].stdout, results[0].stdout


@pytest.mark.parametrize("package", ROOTS)
def test_dependency_sibling_runtime_cycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, package: str,
) -> None:
    _tree(tmp_path)
    (tmp_path / package / "cycle_a.py").write_text(
        f"import {package}.cycle_b\n", encoding="utf-8",
    )
    (tmp_path / package / "cycle_b.py").write_text(
        f"import {package}.cycle_a\n", encoding="utf-8",
    )
    results = _run_probe(tmp_path, monkeypatch)
    _expect(results, Probe("runtime-cycle", (), 1, "rs-siblings-acyclic"))
    assert f"No cycles are allowed in {package}." in results[1].stdout, results[1].stdout


@pytest.mark.parametrize("missing", ("adapters", "engines.watch"))
def test_dependency_missing_required_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing: str,
) -> None:
    _tree(tmp_path)
    if missing == "adapters":
        # Only the two known disposable fixture paths are removed.
        (tmp_path / "adapters/port.py").unlink()
        (tmp_path / "adapters").rmdir()
    else:
        (tmp_path / "engines/watch.py").unlink()
    results = _run_probe(tmp_path, monkeypatch)
    output = "\n".join(result.stdout + result.stderr for result in results)
    assert any(result.returncode != 0 for result in results), output
    assert missing in output, output
    assert "does not exist" in output or "Could not find package" in output, output
    assert "BROKEN" not in output, output


def test_dependency_configuration_keeps_type_and_runtime_scopes() -> None:
    inclusive = tomllib.loads(CONFIG.read_text(encoding="utf-8"))["tool"]["importlinter"]
    runtime = tomllib.loads(RUNTIME_CONFIG.read_text(encoding="utf-8"))["tool"]["importlinter"]
    assert inclusive["exclude_type_checking_imports"] is False
    assert inclusive["include_external_packages"] is True
    assert runtime["exclude_type_checking_imports"] is True
    assert inclusive["root_packages"] == runtime["root_packages"] == list(ROOTS)
    assert {c["id"] for c in inclusive["contracts"]} == {
        "rs-layers", "rs-engines-independent", "rs-core-no-external-effects",
    }
    assert [c["id"] for c in runtime["contracts"]] == ["rs-siblings-acyclic"]
    forbidden = inclusive["contracts"][-1]
    assert forbidden["source_modules"] == ["domain", "contracts", "engines"]
    assert forbidden["forbidden_modules"] == list(FORBIDDEN_ROOTS)
    assert forbidden["allow_indirect_imports"] is False
    assert forbidden["as_packages"] is True


def test_dependency_actual_source_graph(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as scoped:
        scoped.setenv("PYTHONPATH", str(PROJECT_ROOT / "src"))
        scoped.setenv("PYTHONIOENCODING", "utf-8")
        scoped.setenv("PYTHONHASHSEED", "0")
        results = (
            _native(tmp_path, CONFIG, "actual-types"),
            _native(tmp_path, RUNTIME_CONFIG, "actual-runtime"),
        )
    _expect(results, Probe("actual-source", (), 0, None))
