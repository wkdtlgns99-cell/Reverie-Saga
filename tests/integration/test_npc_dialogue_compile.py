from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from adapters.quest_dialogue import compile_dialogue, load_dialogue
from app.client_session import ClientSession
from app.headless import replay_runner
from app.npc_dialogue_compile import compile_preparation, draft_approval, main
from app.npc_dialogue_review import DialogueReview, review_preparation
from app.npc_memory import memory_bundle, read_memory
from app.npc_memory_brief import memory_brief
from contracts.dialogue import ARTIFACT_ID, MAX_DIALOGUE_BYTES, GenerationError, QuestContent
from contracts.persistence import SaveError
from contracts.replay import ReplayFixture
from tests.integration.test_npc_dialogue_review import prepared
from tests.integration.test_npc_memory import session_at
from tests.integration.test_quest import GOAL
from tests.unit.quest_fixtures import catalog, content


def approved(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    working, plan, preparation = prepared(tmp_path)
    selected = content()
    receipt = tmp_path / "approval.json"
    draft_approval(working, selected, selected.definition.layout.npc_id, plan, preparation, receipt)
    data = json.loads(receipt.read_bytes())
    data.update(
        decision="APPROVED",
        approved_by="automated-test-only",
        approved_utc="2026-10-14T00:00:00+00:00",
    )
    receipt.write_text(json.dumps(data), encoding="utf-8")
    return working, plan, preparation, receipt


def test_draft_is_bound_to_reviewed_input_but_never_an_approval(tmp_path: Path) -> None:
    working, plan, preparation = prepared(tmp_path)
    selected = content()
    npc, receipt = selected.definition.layout.npc_id, tmp_path / "pending.json"
    before = tuple(path.read_bytes() for path in (working, plan, preparation))
    review = review_preparation(working, selected, npc, plan, preparation)
    draft_approval(working, selected, npc, plan, preparation, receipt)
    data = json.loads(receipt.read_bytes())
    assert set(data) == {
        "artifact_id",
        "output_sha256",
        "brief_sha256",
        "decision",
        "approved_by",
        "approved_utc",
    }
    assert (
        data["decision"] == "PENDING" and data["approved_by"] == "" and data["approved_utc"] == ""
    )
    assert data["artifact_id"] == ARTIFACT_ID
    assert data["output_sha256"] == hashlib.sha256(review.generated.candidate).hexdigest()
    assert (
        data["brief_sha256"]
        == hashlib.sha256(memory_brief(review.context).text.encode()).hexdigest()
    )
    with pytest.raises(ValueError, match="DIALOGUE_APPROVAL"):
        compile_dialogue(review.generated.candidate, receipt.read_bytes())
    output = tmp_path / "catalog.json"
    with pytest.raises(GenerationError, match="NPC_DIALOGUE_APPROVAL_INVALID"):
        compile_preparation(working, selected, npc, plan, preparation, receipt, output)
    assert (
        not output.exists()
        and tuple(path.read_bytes() for path in (working, plan, preparation)) == before
    )


def test_compiled_catalog_plays_all_branches_saves_resumes_and_replays_offline(
    tmp_path: Path,
) -> None:
    working, plan, preparation, receipt = approved(tmp_path)
    original, output = content(), tmp_path / "new-catalog.json"
    before = tuple(path.read_bytes() for path in (working, plan, preparation, receipt))
    selected = compile_preparation(
        working, original, original.definition.layout.npc_id, plan, preparation, receipt, output
    )
    assert selected == load_dialogue(output, selected.catalog_sha256, original.definition)
    assert selected.dialogue == original.dialogue and selected.brief_sha256 != original.brief_sha256
    assert tuple(path.read_bytes() for path in (working, plan, preparation, receipt)) == before
    # Existing saves retain their original content pin;only a fresh game uses this catalog.
    with pytest.raises(SaveError, match="UNSUPPORTED_RULESET"):
        ClientSession(working, selected.definition.layout, quest_content=selected, npc_memory=True)
    assert working.read_bytes() == before[0]
    session = ClientSession(
        tmp_path / "new-game.sqlite",
        selected.definition.layout,
        quest_content=selected,
        npc_memory=True,
    )
    try:
        initial_core, initial_protocol = session.owner.snapshot(), session.owner.protocol()
        for index, action in enumerate(GOAL):
            result = session.act(action)
            assert result.status == "COMMITTED"
            if index == 1:
                assert result.quest_stage == 1 and selected.dialogue.text("offer") in "\n".join(
                    result.messages
                )
                reminder = session.act("talk")
                assert reminder.quest_stage == 1 and selected.dialogue.text(
                    "reminder"
                ) in "\n".join(reminder.messages)
        assert (result.quest_stage, result.quest_reward) == (2, 0)
        known = read_memory(session.owner.working_path, selected, selected.definition.layout.npc_id)
        assert [entry.kind for entry in known.entries] == ["accepted"]
        session.save("slot01")
        session.act("left")
        reported = session.act("talk")
        assert (reported.quest_stage, reported.quest_reward) == (3, 1)
        assert selected.dialogue.text("completion") in "\n".join(reported.messages)
        stable = session.owner.snapshot(), session.owner.protocol()
        assert (
            session.retry().quest_reward == 1
            and (session.owner.snapshot(), session.owner.protocol()) == stable
        )
        gratitude = session.act("talk")
        assert gratitude.quest_reward == 1 and selected.dialogue.text("gratitude") in "\n".join(
            gratitude.messages
        )
        trace = session.owner.retained_segment().trace
        assert (
            replay_runner(
                ReplayFixture(initial_core, initial_protocol, trace),
                bundles=(memory_bundle(selected),),
            ).run(trace)
            == ()
        )
        loaded = session.load("slot01")
        assert (loaded.quest_stage, loaded.quest_reward) == (2, 0)
        resumed_path = Path(loaded.working_path)
    finally:
        session.close()
    resumed = ClientSession(
        resumed_path, selected.definition.layout, quest_content=selected, npc_memory=True
    )
    try:
        assert resumed.update().quest_stage == 2
        resumed.act("left")
        assert resumed.act("talk").quest_reward == 1
        assert resumed.act("talk").quest_reward == 1
    finally:
        resumed.close()
    assert tuple(path.read_bytes() for path in (working, plan, preparation, receipt)) == before


@pytest.mark.parametrize(
    "damage",
    (
        "pending",
        "rejected",
        "blank_approver",
        "missing",
        "extra",
        "artifact",
        "output_hash",
        "brief_hash",
        "brief_shape",
        "no_timezone",
        "non_utc",
        "invalid_time",
        "duplicate",
        "oversize",
        "empty",
        "invalid_utf8",
    ),
)
def test_invalid_or_unbound_receipts_cannot_publish(tmp_path: Path, damage: str) -> None:
    working, plan, preparation, receipt = approved(tmp_path)
    data = json.loads(receipt.read_bytes())
    if damage in ("pending", "rejected"):
        data["decision"] = damage.upper()
    elif damage == "blank_approver":
        data["approved_by"] = " "
    elif damage == "missing":
        del data["approved_utc"]
    elif damage == "extra":
        data["extra"] = "invalid"
    elif damage == "artifact":
        data["artifact_id"] = "dialogue:foreign"
    elif damage in ("output_hash", "brief_hash"):
        data[damage.replace("_hash", "_sha256")] = "f" * 64
    elif damage == "brief_shape":
        data["brief_sha256"] = 0
    elif damage in ("no_timezone", "non_utc", "invalid_time"):
        data["approved_utc"] = {
            "no_timezone": "2026-10-14T00:00:00",
            "non_utc": "2026-10-14T00:00:00+09:00",
            "invalid_time": "invalid",
        }[damage]
    raw = json.dumps(data).encode()
    if damage == "duplicate":
        raw = raw[:-1] + b',"decision":"APPROVED"}'
    elif damage == "oversize":
        raw = b"x" * (MAX_DIALOGUE_BYTES + 1)
    elif damage == "empty":
        raw = b""
    elif damage == "invalid_utf8":
        raw = b"\xff"
    receipt.write_bytes(raw)
    selected, output = content(), tmp_path / "compiled.json"
    before = tuple(path.read_bytes() for path in (working, plan, preparation, receipt))
    with pytest.raises(GenerationError, match="NPC_DIALOGUE_APPROVAL_INVALID"):
        compile_preparation(
            working, selected, selected.definition.layout.npc_id, plan, preparation, receipt, output
        )
    assert not output.exists() and not output.with_name(output.name + ".pending").exists()
    assert tuple(path.read_bytes() for path in (working, plan, preparation, receipt)) == before


@pytest.mark.parametrize("mode", ("draft", "compile"))
def test_changed_source_and_missing_receipt_never_publish(tmp_path: Path, mode: str) -> None:
    working, plan, preparation, receipt = approved(tmp_path)
    selected, output = content(), tmp_path / "output.json"
    npc = selected.definition.layout.npc_id
    if mode == "compile":
        with pytest.raises(GenerationError, match="NPC_DIALOGUE_APPROVAL_UNAVAILABLE"):
            compile_preparation(
                working, selected, npc, plan, preparation, tmp_path / "missing.json", output
            )
    session = session_at(working, 0)
    try:
        assert session.act("wait").status == "COMMITTED"
    finally:
        session.close()
    with pytest.raises(GenerationError, match="NPC_CONTEXT_STALE"):
        if mode == "draft":
            draft_approval(working, selected, npc, plan, preparation, output)
        else:
            compile_preparation(working, selected, npc, plan, preparation, receipt, output)
    assert not output.exists()


@pytest.mark.parametrize("race", ("source", "preparation", "receipt"))
def test_repeat_read_prevents_changed_input_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, race: str
) -> None:
    from app.npc_dialogue_compile import _compile

    working, plan, preparation, receipt = approved(tmp_path)
    selected, output = content(), tmp_path / "output.json"
    session = session_at(working, 0)

    def compiling(
        review: DialogueReview, raw: bytes, original: QuestContent
    ) -> tuple[bytes, QuestContent]:
        result = _compile(review, raw, original)
        if race == "source":
            assert session.act("wait").status == "COMMITTED"
        elif race == "preparation":
            # Semantically identical envelope still changes the reviewed raw input identity.
            preparation.write_text(
                json.dumps(json.loads(preparation.read_bytes()), indent=2), encoding="utf-8"
            )
        else:
            receipt.write_text(
                json.dumps(json.loads(receipt.read_bytes()), indent=2), encoding="utf-8"
            )
        return result

    monkeypatch.setattr("app.npc_dialogue_compile._compile", compiling)
    code = (
        "NPC_CONTEXT_STALE"
        if race == "source"
        else "NPC_DIALOGUE_INPUT_CHANGED"
        if race == "preparation"
        else "NPC_DIALOGUE_APPROVAL_CHANGED"
    )
    try:
        with pytest.raises(GenerationError, match=code):
            compile_preparation(
                working,
                selected,
                selected.definition.layout.npc_id,
                plan,
                preparation,
                receipt,
                output,
            )
        assert not output.exists()
        if race == "source":
            assert session.owner.snapshot().tick == 12
    finally:
        session.close()


@pytest.mark.parametrize(
    "mode,target",
    (("draft", "output"), ("draft", "pending"), ("compile", "output"), ("compile", "pending")),
)
def test_occupied_output_precedes_input_reads(tmp_path: Path, mode: str, target: str) -> None:
    selected, output = content(), tmp_path / "output.json"
    occupied = output if target == "output" else output.with_name(output.name + ".pending")
    occupied.write_bytes(b"existing")
    with pytest.raises(GenerationError, match="GENERATION_TARGET_EXISTS"):
        if mode == "draft":
            draft_approval(
                tmp_path / "missing.sqlite",
                selected,
                selected.definition.layout.npc_id,
                tmp_path / "missing.json",
                tmp_path / "missing-prep.json",
                output,
            )
        else:
            compile_preparation(
                tmp_path / "missing.sqlite",
                selected,
                selected.definition.layout.npc_id,
                tmp_path / "missing.json",
                tmp_path / "missing-prep.json",
                tmp_path / "missing-receipt.json",
                output,
            )
    assert occupied.read_bytes() == b"existing"


def test_standalone_draft_then_explicit_test_receipt_compile_has_no_network(tmp_path: Path) -> None:
    working, plan, preparation = prepared(tmp_path)
    selected, catalog_path = content(), tmp_path / "source-catalog.json"
    catalog_path.write_bytes(catalog())
    guard = tmp_path / "guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        "import sys\ndef guard(event,args):\n if event.startswith('socket.') or event=='urllib.Request': raise RuntimeError('NETWORK_FORBIDDEN')\nsys.addaudithook(guard)\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env.pop("GEMINI_API_KEY", None)
    env["PYTHONPATH"] = os.pathsep.join(
        (str(guard), str(Path(__file__).resolve().parents[2] / "src"))
    )
    common = [
        sys.executable,
        "-m",
        "app.npc_dialogue_compile",
        "--working",
        str(working),
        "--quest-catalog",
        str(catalog_path),
        "--quest-sha256",
        selected.catalog_sha256,
        "--plan",
        str(plan),
        "--preparation",
        str(preparation),
    ]
    receipt, output = tmp_path / "draft.json", tmp_path / "compiled.json"
    before = tuple(path.read_bytes() for path in (working, plan, preparation, catalog_path))
    drafted = subprocess.run(
        [*common, "--draft-approval", "--output", str(receipt)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert drafted.returncode == 0 and "DIALOGUE_APPROVAL_DRAFT_PENDING" in drafted.stdout
    refused = subprocess.run(
        [*common, "--receipt", str(receipt), "--output", str(output)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert (
        refused.returncode == 1
        and "NPC_DIALOGUE_APPROVAL_INVALID" in refused.stderr
        and not output.exists()
    )
    # Explicit diagnostic approval;this is not director testimony or production acceptance.
    data = json.loads(receipt.read_bytes())
    data.update(
        decision="APPROVED",
        approved_by="automated-test-only",
        approved_utc="2026-10-14T00:00:00+00:00",
    )
    receipt.write_text(json.dumps(data), encoding="utf-8")
    compiled = subprocess.run(
        [*common, "--receipt", str(receipt), "--output", str(output)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert compiled.returncode == 0 and "COMPILED_APPROVED_DIALOGUE" in compiled.stdout
    loaded = load_dialogue(
        output, hashlib.sha256(output.read_bytes()).hexdigest(), selected.definition
    )
    assert loaded.dialogue == selected.dialogue
    assert tuple(path.read_bytes() for path in (working, plan, preparation, catalog_path)) == before


@pytest.mark.parametrize("mode", ("draft", "compile"))
def test_publication_failure_preserves_inputs_and_cleans_owned_pending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], mode: str
) -> None:
    working, plan, preparation, receipt = approved(tmp_path)
    selected, catalog_path, output = content(), tmp_path / "source.json", tmp_path / "output.json"
    catalog_path.write_bytes(catalog())
    before = tuple(
        path.read_bytes() for path in (working, plan, preparation, receipt, catalog_path)
    )

    def unavailable(fd: int) -> None:
        raise OSError("diagnostic fsync failure")

    monkeypatch.setattr("adapters.quest_dialogue.os.fsync", unavailable)
    args = [
        "--working",
        str(working),
        "--quest-catalog",
        str(catalog_path),
        "--quest-sha256",
        selected.catalog_sha256,
        "--plan",
        str(plan),
        "--preparation",
        str(preparation),
        "--output",
        str(output),
    ]
    assert (
        main([*args, "--draft-approval"] if mode == "draft" else [*args, "--receipt", str(receipt)])
        == 1
    )
    assert capsys.readouterr().err.strip() == "NPC_DIALOGUE_COMPILE_INPUT"
    assert not output.exists() and not output.with_name(output.name + ".pending").exists()
    assert (
        tuple(path.read_bytes() for path in (working, plan, preparation, receipt, catalog_path))
        == before
    )


@pytest.mark.parametrize("flags", ((), ("--draft-approval", "--receipt", "missing.json")))
def test_cli_conflicting_modes_fail_before_input_reads(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], flags: tuple[str, ...]
) -> None:
    output = tmp_path / "output.json"
    assert (
        main(
            [
                "--working",
                "missing.sqlite",
                "--quest-catalog",
                "missing.json",
                "--quest-sha256",
                "0" * 64,
                "--plan",
                "missing.json",
                "--preparation",
                "missing.json",
                "--output",
                str(output),
                *flags,
            ]
        )
        == 1
    )
    assert capsys.readouterr().err.strip() == "GENERATION_INPUT" and not output.exists()
