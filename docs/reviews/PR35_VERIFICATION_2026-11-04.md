# PR35 — Verification and CI Fixture Repair

2026-11-04;executor self-review;primary7integration support,related2/4/6.
[Order](../work_orders/PR35_VERIFY_AND_MERGE_2026-11-04.md).
Entry clean a4851050,base6b12f51,PR35Draft with no reviews or unresolved review threads.
Latest director request supersedes upload-only pause and explicitly authorizes ordinary
merge/main synchronization followed by remaining confirmed backlog work.

## Finding and repair

PR workflow41801640562/job126478583607failed full regression. The inclusive dependency
configuration requires world_travel,time,population,supply,conversation engines;its synthetic
fixture still created only eight older engine modules. All dependency probes then failed
before reaching their intended contract. Local unchanged allowed-dag reproduced1FAIL2.57s:
Module engines.world_travel does not exist.

Add all five modules to the literal fixture inventory. New ten forward/reverse probes
establish actual world-engine independence enforcement;five added missing-input probes
retain error-versus-violation distinction. Literal configuration/inventory equality catches
future registration drift. All existing probes/assertions and production restrictions remain.
No production,central schema,provider,CI workflow or dependency edit in this repair.

## Review and local qualification

Reviewed actual optional bundle registration,session/checkpoint selection,admission and
speech gate,engine ownership,delta/patch/checkpoint validation,context own-memory/revalidation,
provider request/strict output/cancellation/budget and supply-helper reuse. Accepted output
is stored through existing COMMIT and replay;ordinary world GUI still selects supply mode.
The Gworker/dialogue UI remains unfinished,truthfully tracked;foundation delivery is not
feature or parent D01-D07 acceptance. No new provider/native run or release claim.

- Dependency qualification plus conversation unit/provider/registered integration:
  python -m pytest -q tests/governance/test_dependency_contracts.py
  tests/unit/test_world_conversation.py tests/unit/test_world_conversation_provider.py
  tests/integration/test_world_conversation.py --basetemp .pytest_cache/pr35-qualified:
  130PASS97.11s. Canonical sys capture,Python3.13.12AMD64/Tk8.6/SQLite3.50.4 reused.
- Both all-source Ruff configurations PASS;strict mypy334files PASS;pip check PASS.
- Scoped formatting25files PASS;actual inclusive imports3/runtime sibling cycles1PASS,
  --no-cache. No install/global Git trust/security setting change.
- Git requires process/command-local exact C:/Reverie Saga trust due existing ownership.
  Fetch/switch required approved execution because sandbox cannot write .git/FETCH_HEAD.
  Clean branch switched to actual PR branch without resets or discarded changes.

Final document/boundary checks and published-head full CI/merge/main equality are pending
at this prepublication snapshot. Actual GitHub runs/merge commit own later remote evidence.
Existing independent/native/device/release/CP06holds retained;no agents.

## Published result

Final head83405ce;push41846021869/job126629610184:3935PASS805.22s,boundary32PASS5.89s.
PR41846030829/job126629642850:3935PASS1100.10s,boundary32PASS7.67s;all workflow steps
SUCCESS. PR head/base unchanged83405ce/6b12f51 before ordinary merge265fc4b8c18be6f640ee25c35421316cd983fac3.
Fresh fetch/fast-forward local main equals origin/main265fc4b,clean. No direct-main push.
Additional current-host world/travel/time/population/supply/actualTk57PASS20.20s with
unraisable warnings promoted to errors. Markdown543local references/11document guards PASS.
Foundation publication complete;Gfeature remains separate unfinished follow-up work.
