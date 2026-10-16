# QT-F22 — Retained Working Save Inventory

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/review:self,not independent.
[Order](../work_orders/QT-F22_SAVE_CLONE_INVENTORY.md). Primary6 storage support;related7.

## Behavior

New explicit `python -m app.save_inventory` reads the supplied existing working save and exact
`.loaded-[0-9a-f]{32}.sqlite` names in its parent. Sorted rows show filename,saved logical tick,
revision,branch and whether the path equals the caller-supplied current path. Invalid candidates
retain their actual save diagnostic and null metadata. No global liveness/orphan/ownership claim.
No startup cleanup,delete,load,attachment/sidecar creation,game creation or limit/pin change.

Canonical safe_path+validate_save enforce existing path/type/size/schema/pin checks. Scan is
nonrecursive,capped at64candidate names;sidecars/slots/lookalikes are ignored. Input modes reuse
legacy/harbor/grove and original quest/memory bundle wiring. Catalog/hash pair and memory/quest
combination errors reject before save access. Per-file snapshots do not promise an atomic whole
directory view or that a later separate resume succeeds. Invalid current save fails the command.

## Verification

Host/environment and shared checks:[R1receipt](RS-V3-R1_EXECUTION_2026-10-16.md).
Initial inventory selection:12PASS3FAIL10.42s;new tests incorrectly expected SAVE_CORRUPT for
directory/missing/wrong-pin inputs. These are test-oracle mistakes,not legacy production defects.
Existing safe_path/classify_file and orchestration.persistence.decode_checkpoint specify exact
INVALID_PATH,SAVE_NOT_FOUND,UNSUPPORTED_RULESET;preserved these contracts and corrected expectations.
Intermediate affected run:60PASS1FAIL29.08s;remaining wrong-pin test expectation corrected against
the existing pin check and save-slot oracle. No existing production/test semantics changed.

Final affected selection:225PASS156.65s,exit0,no failures/errors/skips. A first invocation named nonexistent test_npc_dialogue_preview.py
and collected no tests;corrected selection uses actual test_npc_dialogue_plan.py:

```powershell
$env:PYTHONPATH='src;.'; $env:PYTHONHASHSEED='0'; $env:PYTHONUTF8='1'
.venv/Scripts/python.exe -m pytest -q tests/adapters tests/integration/test_save_inventory.py tests/integration/test_save_slots.py tests/integration/test_durable_turn.py tests/integration/test_npc_context.py tests/integration/test_npc_dialogue_plan.py tests/integration/test_npc_dialogue_review.py tests/integration/test_npc_dialogue_compile.py --basetemp .pytest_cache/v3-r1-f22-qualified --junitxml tmp/v3-r1/combined.xml
```

Inventory tests create real saved branches across sessions,prove resumed ticks,current markers,
unchanged save/sidecar/tree bytes and unchanged eight-clone refusal. Standalone subprocess CLI
covers all five original modes. Corruption,foreign rules,directory,real hardlink,disappearance,
over-cap,current missing,scan failure/invalid-mode rejection and process-control are covered.
Tools/CLI routes are developer support;no new graphical UI or ordinary-player cleanup capability.
Full1741and native307remain historical evidence,not a new full/native acceptance claim.

Acceptance PASS:affected225,17new inventory cases,15new HTTP cases;counts overlap preceding runs.
Ruff both/format16/mypy167/pip/import3+1 PASS;documentation UTF8/links/fences/feedback text,
440baseline-file preservation and git diff --check PASS. Three progress docs agree.
No source/provider/CORE/save schema/Unity/config/dependency changes beyond separate R1repair.
No commit/push/merge/agent/provider call. Existing release and partial-review limits remain.
