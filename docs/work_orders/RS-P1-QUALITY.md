# RS-P1-QUALITY — Reliability to Playable Client

Status:ACCEPTED/DONE for all seven authorized items2026-10-07. Final1221tests280.39s PASS;self-review only. Remote CI/human visual/final renderer/device/release acceptance UNVERIFIED. No commit/push.

Authorization:director2026-10-07 requested highest-priority backlog entries,execution,and DONE marking after each accepted item. Executor/reviewer:Sol,self-review only. No commit/push/agent launch/dependency additions authorized.
Baseline:main b0f98e2;clean entry. Runtime:project .venv,CPython3.13.12;20 pinned dev packages. Fresh baseline1192tests264.73s PASS;final results are recorded separately below. Prior review diagnostics are not defect counts.

## Sequence / acceptance

| ID | Work | Acceptance |
|---|---|---|
| RS-P1-QUALITY-01 | Canonical quality/repair policy | Existing authority retained;precise scoped repair/evidence rules;document checks |
| RS-P1-QUALITY-02 | Root AGENTS entry | ≤40lines;valid authority/workflow links;no duplicate full rulebook |
| RS-DOC-002 | README refresh/create | Actual implemented systems/runtime/check commands;existing stale design-only content superseded by this approved order |
| RS-P1-QUALITY-03 | Selective Ruff + minimal Windows CI | Preserve accepted dependency controls/tool lock;qualified error checks;no blanket suppression;local native checks PASS;remote execution UNVERIFIED until a real run |
| RS-P1-QUALITY-04 | Work-order repair/acceptance loop | Canonical policy linked;baseline/failure classification,repair/retest,DONE gates;no new custom checker |
| RS-P1-QUALITY-05 | Bounded core cleanup | Static registry indexes;responsibility decomposition;existing constants/schema keys reused;unchanged save/pins/goldens;lint/strict types/dependency/full regression PASS |
| RS-CLIENT-001 | Thin playable client | Explicit input/projection boundary;existing movement/door/combat/rest/wait/NPC/save/load;real execution and tests;not final 3D/client/performance acceptance |

## Bounds / reads

Read root context/progress,engineering prompt quality/AP/B0/B1/B3/B5,MASTER Brain/client/product boundaries,work-order template,and actual edited sources/callers/tests. Current workspace is C:\ReverieSaga;historical spaced paths are provenance only. Preserve all existing task IDs/history.
Allowed documents:AGENTS,README,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO,prompt,work-order template,this order and README order. Allowed policy:pyproject/.github minimal workflow plus narrow diagnostic config if necessary. No lock/version changes.
Core paths:orchestration/turn.py,engines/encounter.py,contracts/encounter.py and task-specific tests. No serialization/state schema/rules values/order/fact semantics change. Inspect actual types before splitting;keep fresh views and save-before-head publication.
Client paths:selected NEW app client and typed boundary/adapter files plus NEW tests. Reuse watch/durable services;no new engine/LLM/assets/network service unless explicitly settled and needed for the prototype. Do not claim an interactive window or remote CI was verified without evidence.
Edge cases:invalid/rejected input leaves authoritative state unchanged;blocked movement/no-op actions retain specified consuming behavior;load replaces attachment/token;unknown/error results remain visible;EOF/normal exit closes storage. Derive tests from these requirements,not implementation output.
Stop for overlapping user changes,undefined public semantics,required new dependencies,destructive changes or missing verification after safe alternatives. Routine private choices/repairs within these bounds are authorized.

## Verification / evidence

Use explicit .venv Python;Ruff,strict mypy --no-native-parser,both native import-linter configs,pytest with owned ignored basetemp,and six existing golden nodes. Narrow selected checks must have positive/negative detection evidence. No custom checker or mass formatting/oracle rewrite.
Record each subtask acceptance here;update the three progress records immediately after it passes. Baseline is separate from final results. Refresh deferred GOV-03 source fingerprints before any later execution;do not rewrite historical inventories.

## Execution log

- Entry:existing rule authority and code-review corrections rechecked;root AGENTS/README/.github absent. Full1192 baseline started. All sequence items are pending acceptance;this order is not a completion claim.
- QUALITY-01/02/04 and DOC-002 DONE:canonical policy/router/template/README checked;strict UTF8,all local links,AGENTS≤40lines and git diff --check PASS. Strict mypy89files PASS. Documentation-only acceptance;full baseline still running,no new gameplay,no automatic-discovery execution claim.
- QUALITY-03 DONE:separate standard Ruff config extends shared controls and adds only E501/PT011 on changed core/replay/client paths. Initial97diagnostics (92E501+5PT011);after scoped formatting/precise assertions native checks PASS. Stdin negative qualified ReplayFormatError probe exits1/PT011;matched probe exits0. Shared lint,scoped formatter,mypy89files,both native dependency configs PASS. Minimal Windows Actions job preserves locked versions and runs the same gates;remote execution UNVERIFIED,no push. Fresh entry baseline1192tests264.73s PASS. Core/replay cleanup in progress;no stored golden/reference bytes edited.

- QUALITY-05 DONE:shared core regression1206tests274.33s PASS after all three production changes. Driver now separates command checking/admission/simulation/barrier staging/composition/preparation/persistence/presentation;static manifest/route/policy/adapter/presenter indexes only,no read-port cache. Encounter payload SCHEMA ClassVars preserve serialization;static manifests/domain STAMINA_MAX+REST_RECOVERY reused;exact-type dispatch and specified consuming no-ops retained. Scoped formatting is distinguishable from structural changes. Specific corruption tests initially exposed latest-receipt hash mismatch before intended state validation;negative in-memory witnesses were made self-consistent,not their errors relaxed. Focused encounter25tests14.20s PASS;earlier replay57tests43.57s PASS;final full run includes all latest changes. No stored fixture/reference/codec/pin edits;new client files were not collected by this core run. Self-review only.
- CLIENT-001 IN_PROGRESS:four new production modules (contracts/client +app/client_session/client_worker/client),one new integration test module. Native controller/withdrawn Tk tests15PASS4.67s. Initial two test expectations were incorrect against settled specifications:exact retry returns receipt/head without replaying cues;Bell increments replies,periodic wake increments NPC bells. Corrected the independently checked expectations and added exact no-cue/no-extra-replay-step assertions;no Brain behavior change. Reviewed queued-close join race and added explicit post-window worker join. Latest lint/types94files/scoped format9files/dependency3+1 contracts PASS;final1221-test regression running. No manual human visual/performance/crash qualification.
- CLIENT-001 DONE:final complete suite1221tests280.39s PASS;all latest client behavior included. Six explicit existing golden nodes6PASS3.37s. Help entry python -m app.client --help exits0. Native dependency configs analyze78files/487dependencies (3kept) and55files/306dependencies (1kept);0broken. Documentation9strict-UTF8 files/89prose links/fences/AGENTS32lines/diff checks PASS. Historical README output-data literals are not links relative to its work-order directory;the first document probe incorrectly included inline code and was corrected without rewriting history. Added why-comments for uncertain persistence/recovery boundaries after full run;no behavioral source change. All seven accepted;progress records synchronized. Final renderer/MIN-SPEC/human playtest/remote Actions UNVERIFIED;no new dependencies,agents,commit/push or fixtures rewritten.

### Final native commands / results

All executables use .venv/Scripts/python.exe;dependency CLI uses installed importlinter.cli:lint_imports_command because the generated Windows launcher is denied locally. PYTHONPATH=src;pytest temporary roots are owned ignored .pytest_cache directories.

| Invocation | Actual result |
|---|---|
| -m ruff check src tests | PASS |
| -m ruff check --config ruff-quality.toml src tests | PASS |
| -m ruff format --check (nine changed core/client/test files listed in README/CI) | PASS |
| -m mypy --no-native-parser | PASS94files |
| installed native import-linter CLI --config pyproject.toml --no-cache | 3kept/0broken |
| same CLI --config .importlinter-runtime.toml --no-cache | 1kept/0broken |
| -m pytest -q --basetemp .pytest_cache/quality-final-full | 1221PASS280.39s |
| six literal nodes from GOV input inventory,golden/core+trial+encounter/death+watch/passive | 6PASS3.37s |
| -m app.client --help | exit0 |

Final delivery recheck:shared/selective Ruff,9-file formatter and strict mypy94files PASS after comment/document finalization;9UTF8 documents/90prose links/fences/32line AGENTS/seven priority DONE rows and git diff --check PASS. The CRLF-conversion notice for the Korean companion is a Git warning,not a failed check.
Preservation:git diff --name-only on requirements-dev.lock,pyproject.toml,runtime import config,stored replay fixtures and CORE03/04 reference vectors returns empty. HEAD remains b0f98e2aa19c5db11d0c746226d4bf321b34dee8. Scope is20nonignored project files (10modified/10new);core formatting/structure and new client behavior are separately described for any later authorized commits. Next:thin-harness playtest,then a separately bounded small-segment order;do not expand into content/balance/final renderer work under this completed order.

## CLIENT-001 prototype boundary — settled before implementation

This is a playable diagnostic boundary harness,not final graphical-engine selection or §0.C HD-2D/MIN-SPEC qualification. Candidates for this bounded harness:stdlib Tk Canvas vs browser HTML/JSON viewer;Tk is locally available8.6,requires no new service/dependency and offers real native widget tests. Prefer Tk provisionally for this harness;future Godot/Unity/other HD-2D candidates remain open.
Topology:one process,one single-worker executor owns the entire DurableSession/SQLite lifetime. Tk main thread renders immutable ClientView/ClientUpdate projections and enqueues requests;it never executes simulation or save IO. No network/backend process or duplicate state owner.
Typed ClientAction maps movement/open/close/attack/rest/wait/bell to existing GameCommand payloads. New immutable DTOs are DERIVED presentation data only;no CORE schema,pins,codec or save format change. Brain decides admission,damage,time,blocked movement and no-op semantics;UI must not predict them.
Controller reads current protocol revision/active stream and current attachment for each new request. Retry keeps the exact previous command/token;successful load invalidates it. Save/load use the eight existing slots;show active working path after load,which preserves the original branch and uses a private clone. Resume requires the displayed active path;never overwrite an existing working file.
UI requirements:map/player/door/enemy/NPC display,HP/stamina/time,authoritative error/cue summaries,keyboard/buttons,slot save/load/retry,recovery and graceful close after queued work. Gate:real durable scenario+invalid input/immutable rejection+retry/load token+resume+native withdrawn Tk button/render/close tests;all gates PASS. Human visual playtest,final art/camera/gamepad/performance/crash/device/packaging qualification UNVERIFIED.
