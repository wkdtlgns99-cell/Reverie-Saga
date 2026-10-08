"""Qualify the small instruction entry and existing standard-tool safeguards."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "document,pattern",
    [
        (
            "docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md",
            r"The current working project is `([^`]+)`",
        ),
        ("docs/MASTER_GAME_ARCHITECTURE.md", r"^- Workspace: `([^`]+)`"),
    ],
)
def test_current_workspace_authorities_agree(document: str, pattern: str) -> None:
    text = (ROOT / document).read_text(encoding="utf-8")
    current = re.search(pattern, text, re.MULTILINE)
    assert current is not None, f"Current workspace declaration missing: {document}"
    assert current[1] == r"C:\ReverieSaga"
    handoff = (ROOT / "SESSION_HANDOFF.md").read_text(encoding="utf-8")
    assert "Current workspace `C:\\ReverieSaga`" in handoff


def test_each_turn_entry_routes_to_existing_rulebook() -> None:
    entry = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "MUST read [ENGINEERING_RULES.md](ENGINEERING_RULES.md) from disk" in entry
    assert "at the start of EVERY assistant turn" in entry
    assert (ROOT / "ENGINEERING_RULES.md").is_file()
    prompt = (ROOT / "docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md").read_text(
        encoding="utf-8"
    )
    assert "## Implementation Quality and Repair Loop — Director Rule 2026-10-07" in prompt
    assert "[ENGINEERING_RULES.md](../ENGINEERING_RULES.md)" in prompt


def test_rulebook_is_bounded_and_has_the_operational_sections() -> None:
    book = (ROOT / "ENGINEERING_RULES.md").read_text(encoding="utf-8")
    assert len(book.split()) <= 550, "Keep the every-turn input compact; link detailed contracts"
    sections = re.findall(r"^## (.+)$", book, re.MULTILINE)
    assert sections == [
        "Preflight",
        "Implementation",
        "Verification",
        "Failure Handling",
        "Delivery",
    ]
    for section in re.split(r"^## .+$", book, flags=re.MULTILINE)[1:]:
        assert section.strip(), "An empty stage cannot guide execution"


def test_rulebook_local_references_resolve() -> None:
    book = (ROOT / "ENGINEERING_RULES.md").read_text(encoding="utf-8")
    targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", book)
    assert targets, "Contract and enforcement references must remain discoverable"
    for target in targets:
        path, _, anchor = target.partition("#")
        document = ROOT / path
        assert document.is_file(), f"Missing rulebook reference: {target}"
        if anchor:
            headings = re.findall(r"^#+ (.+)$", document.read_text(encoding="utf-8"), re.MULTILINE)
            slugs = {
                re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-") for heading in headings
            }
            assert anchor in slugs, f"Missing rulebook section: {target}"


@pytest.mark.parametrize(
    "config,filename,invalid,valid,code",
    [
        (
            "pyproject.toml",
            "src/adapters/_rules_probe.py",
            "try:\n    int('invalid')\nexcept Exception:\n    pass\n",
            "try:\n    int('invalid')\nexcept ValueError:\n    raise\n",
            "S110",
        ),
        (
            "pyproject.toml",
            "src/engines/_rules_probe.py",
            "import random\nvalue = random.random()\n",
            "value = 1\n",
            "TID251",
        ),
        (
            "pyproject.toml",
            "src/contracts/_rules_probe.py",
            "from typing import Any\ndef convert(value: Any) -> int:\n    return 1\n",
            "def convert(value: int) -> int:\n    return value\n",
            "ANN401",
        ),
        (
            "pyproject.toml",
            "src/engines/_rules_probe.py",
            "value = 0\ndef mutate() -> None:\n    global value\n    value = 1\n",
            "def calculate(value: int) -> int:\n    return value + 1\n",
            "PLW0603",
        ),
        (
            "ruff-quality.toml",
            "tests/integration/test_client.py",
            "import pytest\nwith pytest.raises(ValueError):\n    int('invalid')\n",
            "import pytest\nwith pytest.raises(ValueError, match='invalid literal'):\n"
            "    int('invalid')\n",
            "PT011",
        ),
    ],
)
def test_standard_lint_detects_invalid_and_accepts_valid_input(
    config: str, filename: str, invalid: str, valid: str, code: str
) -> None:
    command = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "--config",
        str(ROOT / config),
        "--no-cache",
        "--stdin-filename",
        filename,
        "-",
    ]
    rejected = subprocess.run(
        command, input=invalid, text=True, capture_output=True, cwd=ROOT, timeout=15
    )
    assert rejected.returncode == 1, rejected.stdout + rejected.stderr
    assert re.search(rf"\b{code}\b", rejected.stdout), rejected.stdout
    accepted = subprocess.run(
        command, input=valid, text=True, capture_output=True, cwd=ROOT, timeout=15
    )
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
