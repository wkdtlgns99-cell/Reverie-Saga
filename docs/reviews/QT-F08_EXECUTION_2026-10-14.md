# QT-F08 — NPC-Known Quest Context Acceptance

Date:2026-10-14 | Sol execution/self-review.
LOCAL_IMPLEMENTATION_ACCEPTED;LIVE_CONTEXT_GENERATION UNVERIFIED.
[Order/contracts](../work_orders/QT-F08_NPC_CONTEXT.md).
Classification:primary4(runtime AI),related3(data)/6(persistence). Director authorized selecting
and executing the next task. No autonomous following task or publication.

## Behavior and Wiring

New frozen contracts.npc_context.NpcQuestContext and app.npc_prepare provide a real preparation
CLI. Existing validate_save reads a consistent read-only SQLite transaction using the accepted
quest registry/pins;no owner/writer attachment,command,CORE memory component or save-format change.
Project only the harbor NPC's knowledge from validated quest progress:stage0 available,stage1/2
accepted,stage3 reported/favor1. Stage2 enemy defeat does not become NPC witness knowledge before
report. No enemy HP/location,world seed,save path,attachment/session secret or other NPC exported.
This is a bounded derived source projection,not episodic history or all five semantic memory levels.

Context binds world/branch/revision/tick/core hash/catalog hash. Source is re-read after optional
generation;changed state rejects NPC_CONTEXT_STALE before publication. Existing output/pending
sibling/dangling link reject before provider. Single exclusive canonical output:CONTEXT_ONLY or
NEEDS_REVIEW,never an approved content package. Raw candidate bytes/hash and nullable usage retained.
Any later acceptance must recheck source binding again;candidate publication is not atomic adoption
into a running world. Normal gameplay does not import/call this preparation entry point.

## Verification

- Final100focused tests PASS17.45s;30new cases. Actual command:`.venv/Scripts/python.exe -m pytest -q tests/unit/test_npc_context.py tests/integration/test_npc_context.py tests/adapters/test_npc_prepare.py tests/integration/test_quest.py tests/replay/test_quest.py tests/unit/test_dialogue.py tests/adapters/test_gemini_dialogue.py tests/adapters/test_generation_budget.py --basetemp .pytest_cache/qt-f08-qualified --junitxml tmp/qt-f08/qualified.xml`.
- Actual source/branch save/load/resume/exact retry,invalid owner/legacy/corrupt source,privacy,
  immutable/exact types,provider invalid text/usage,failure/exclusive output and stale-after-real-commit
  tested. Real standalone offline subprocess forbids all socket.* and urllib.Request audit events.
- Shared/selective Ruff PASS;strict mypy132files PASS;affected5files formatter PASS;Import Linter
  shared3/runtime1contracts kept. No test/golden/policy weakening,new library or runtime engine cycle.
- Prior1451full/native/build evidence retained for unchanged production inputs;new full regression,
  Unity/render/build,other-device/standalone launch NOT_RUN. Only two new production modules;
  existing Python/C#/CORE/DTO/save/pins are byte-unchanged. Focused checks cover new callers/boundaries.

Initial focused24PASS/1FAIL expected a new protocol branch ID on load. Actual accepted load clones
the working file while preserving saved protocol;repair that independently mistaken oracle:equal
snapshot yields equal context,then an action on the private copy changes its context while the
original remains unchanged. No save implementation/golden changed. Initial unused import and
mypy loop-variable/test-fixture argument issues repaired;final static results above.
The first owned live harness lacked root tests on PYTHONPATH and stopped before key/provider access;
the corrected invocation included root+src. This did not consume a HTTP reservation.

## Actual CLI / Live Attempt

Standalone offline CLI on a fresh owned test quest at tick9/stage2 generated
[context result](../../tmp/qt-f08/live-3a9fad15bd2c47a0b7546e288dd7b86c/npc-context.json),exit0.
Context565UTF8bytes,brief1346bytes;known_phase accepted/recorded_favor0/known_facts quest_accepted.
Source file SHA256 before/after identical. Source catalog/receipt are automated-test-only;
no Gemini candidate promoted or director production approval fabricated.

One primary-key live attempt used the existing shared tmp/gemini-profile budget. Final sanitized
CLI error GENERATION_BUDGET_EXHAUSTED,exit1,90.594s. No candidate published.
Before:one prior QT-F07 successful reservation452tokens. After:two reservations,settled only1,
tokens20452. The existing generator's timeout/transient retry path reached the daily cap before
another HTTP call;unknown consumption retains the conservative20000reservation. The exact initial
transport/provider code is not retained by the sanitized CLI;do not assert a specific DNS/TLS/HTTP
cause or Google's remote quota. [Sanitized attempt receipt](../../tmp/qt-f08/live-result.json).
No budget reset,spare-key rotation,paid fallback,additional HTTP request or fabricated success.
Earlier QT-F07 actual Gemini request PASS remains separate evidence,not a pass for this context job.

New live-context success is UNVERIFIED;retry only within the existing shared budget when it permits
and under authorized scope. Project billing/remaining remote quota,production content approval,
vector retrieval,long-term memory/relationship/BDI systems remain separate future qualification.
CP05 NOT_TRIGGERED here:derived read-only data only. The first authoritative memory addition still
needs its own complete contracts/checkpoint routing. Original review witnesses/ZIPs remain frozen.
HEAD unchanged;no agents,dependency/account change,remote CI,publication or unrelated cleanup.
