from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from adapters.generation_budget import GenerationBudget
from contracts.dialogue import GenerationError
from domain.canonical import canonical_json, decode_json, object_value

NOW = 1791849600000


def child_reserve(profile: Path, instant: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "from pathlib import Path; import sys; from adapters.generation_budget import GenerationBudget; "
            "from contracts.dialogue import GenerationError;\n"
            "try: print(GenerationBudget(Path(sys.argv[1])).reserve(now_ms=int(sys.argv[2])).number)\n"
            "except GenerationError as e: print(e.code)\n",
            str(profile),
            str(instant),
        ],
        cwd=Path(__file__).resolve().parents[2] / "src",
        capture_output=True,
        text=True,
        timeout=20,
    )


def test_real_process_lock_contention_and_restart_accounting(tmp_path: Path) -> None:
    budget = GenerationBudget(tmp_path)
    with budget.locked():
        blocked = child_reserve(tmp_path, NOW)
        assert blocked.returncode == 0 and blocked.stdout.strip() == "GENERATION_BUDGET_UNAVAILABLE"
    assert child_reserve(tmp_path, NOW).stdout.strip() == "1"
    assert child_reserve(tmp_path, NOW + 59999).stdout.strip() == "GENERATION_DEFERRED"
    assert child_reserve(tmp_path, NOW + 60000).stdout.strip() == "2"
    assert child_reserve(tmp_path, NOW + 120000).stdout.strip() == "3"
    data = object_value(decode_json((tmp_path / "budget.json").read_bytes()))
    assert (data["attempts"], data["tokens"]) == (3, 60000)


def test_reconcile_is_once_and_unknown_keeps_reservation(tmp_path: Path) -> None:
    budget = GenerationBudget(tmp_path)
    reservation = budget.reserve(now_ms=NOW)
    budget.reconcile(reservation, None)
    data = object_value(decode_json((tmp_path / "budget.json").read_bytes()))
    assert data["tokens"] == 20000
    budget.reconcile(reservation, 456)
    budget.reconcile(reservation, 456)
    assert object_value(decode_json((tmp_path / "budget.json").read_bytes()))["tokens"] == 456


def test_corrupt_ledger_fails_closed_and_future_clock_never_resets(tmp_path: Path) -> None:
    budget = GenerationBudget(tmp_path)
    budget.reserve(now_ms=NOW)
    with pytest.raises(GenerationError, match="GENERATION_DEFERRED"):
        budget.reserve(now_ms=NOW - 86400000)
    (tmp_path / "budget.json").write_bytes(b"corrupt")
    with pytest.raises(GenerationError, match="GENERATION_BUDGET_UNAVAILABLE"):
        budget.reserve(now_ms=NOW + 86400000)


@pytest.mark.parametrize("stale", (b"", b"partial", b'{"attempts":0,"tokens":0}'))
def test_stale_pending_recovery_preserves_committed_accounting(
    tmp_path: Path, stale: bytes
) -> None:
    budget = GenerationBudget(tmp_path)
    assert budget.reserve(now_ms=NOW).number == 1
    pending = tmp_path / "budget.pending"
    pending.write_bytes(stale)
    resumed = child_reserve(tmp_path, NOW + 60000)
    assert resumed.returncode == 0 and resumed.stdout.strip() == "2"
    assert not pending.exists()
    assert child_reserve(tmp_path, NOW + 120000).stdout.strip() == "3"
    data = object_value(decode_json((tmp_path / "budget.json").read_bytes()))
    assert (data["attempts"], data["tokens"]) == (3, 60000)


def test_existing_exhausted_profile_continues_without_reset(tmp_path: Path) -> None:
    ledger = tmp_path / "budget.json"
    ledger.write_bytes(
        b'{"attempts":2,"day":"2026-10-13","next_ms":1791849720000,"settled":[1],"tokens":20452}'
    )
    reservation = GenerationBudget(tmp_path).reserve(now_ms=NOW + 120000)
    assert reservation.number == 3
    data = object_value(decode_json(ledger.read_bytes()))
    assert (data["attempts"], data["tokens"], data["settled"]) == (3, 40452, (1,))
    resumed = GenerationBudget(tmp_path)
    resumed.reconcile(reservation, 650)
    resumed.reconcile(reservation, 650)
    data = object_value(decode_json(ledger.read_bytes()))
    assert (data["attempts"], data["tokens"], data["settled"]) == (3, 21102, (1, 3))
    with pytest.raises(GenerationError, match="GENERATION_DEFERRED"):
        resumed.reserve(now_ms=NOW + 179999)
    assert resumed.reserve(now_ms=NOW + 180000).number == 4


def test_crashed_writer_pending_is_recovered_under_real_process_lock(tmp_path: Path) -> None:
    budget = GenerationBudget(tmp_path)
    reservation = budget.reserve(now_ms=NOW)
    committed = (tmp_path / "budget.json").read_bytes()
    crashed = subprocess.run(
        [
            sys.executable,
            "-c",
            "from pathlib import Path; import os,sys; "
            "from adapters.generation_budget import GenerationBudget;\n"
            "b=GenerationBudget(Path(sys.argv[1]))\n"
            "with b.locked():\n"
            " (b.profile/'budget.pending').write_bytes(b'partial')\n"
            " os._exit(7)\n",
            str(tmp_path),
        ],
        cwd=Path(__file__).resolve().parents[2] / "src",
        capture_output=True,
        timeout=20,
    )
    assert crashed.returncode == 7
    assert (tmp_path / "budget.json").read_bytes() == committed
    budget.reconcile(reservation, 456)
    budget.reconcile(reservation, 456)
    data = object_value(decode_json((tmp_path / "budget.json").read_bytes()))
    assert (data["attempts"], data["tokens"], data["settled"]) == (1, 456, (1,))
    assert not (tmp_path / "budget.pending").exists()


def test_pending_cleanup_failure_and_corrupt_ledger_preserve_committed_bytes(
    tmp_path: Path,
) -> None:
    budget = GenerationBudget(tmp_path)
    budget.reserve(now_ms=NOW)
    ledger = tmp_path / "budget.json"
    committed = ledger.read_bytes()
    pending = tmp_path / "budget.pending"
    pending.mkdir()
    with pytest.raises(GenerationError, match="GENERATION_BUDGET_UNAVAILABLE"):
        budget.reserve(now_ms=NOW + 60000)
    assert pending.is_dir() and ledger.read_bytes() == committed
    pending.rmdir()
    pending.write_bytes(b"stale")
    ledger.write_bytes(b"corrupt")
    with pytest.raises(GenerationError, match="GENERATION_BUDGET_UNAVAILABLE"):
        budget.reserve(now_ms=NOW + 60000)
    assert ledger.read_bytes() == b"corrupt" and pending.read_bytes() == b"stale"


def test_full_day_accounting_fits_and_rollover_retains_spacing(tmp_path: Path) -> None:
    ledger = tmp_path / "budget.json"
    ledger.write_bytes(
        canonical_json(
            {
                "day": "2026-10-13",
                "attempts": 1440,
                "tokens": 144000,
                "next_ms": NOW + 86400000 + 30000,
                "settled": tuple(range(1, 1441)),
            }
        )
    )
    assert len(ledger.read_bytes()) > 4096
    budget = GenerationBudget(tmp_path)
    with pytest.raises(GenerationError, match="GENERATION_DEFERRED"):
        budget.reserve(now_ms=NOW + 86400000)
    reservation = budget.reserve(now_ms=NOW + 86400000 + 30000)
    assert (reservation.day, reservation.number) == ("2026-10-14", 1)
    data = object_value(decode_json(ledger.read_bytes()))
    assert (data["attempts"], data["tokens"], data["settled"]) == (1, 20000, ())
