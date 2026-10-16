# QT-F02 — Unity Scenario Selection / Fresh Review Entry

Date:2026-10-15 | State:DONE/self+native acceptance;CP03 DEFERRED/feedback NOT_RECEIVED.
Executor:Sol;self/native review,not Claude acceptance. Baseline:main1ad2244 plus the existing
uncommitted first room unit/documents/CP03 artifacts;preserve all prior work and stash.
Prior runtime acceptance:1330fullPASS362.34s/38focusedPASS. Capture actual status before edits.

Authority:ENGINEERING_RULES,MASTER Brain/client ownership,canonical Claude procedure and
director's explicit2026-10-15 instruction to defer CP03 because Claude quota is exhausted and
proceed. Record CP03 DEFERRED/feedback NOT_RECEIVED. This one-time continuation covers only
the Unity presentation connection below,not broad world/content imports or CP05/06 waiver.

Reads:AGENTS/rulebook/handoff/backlog/Korean summary,WORKSTATION_SETUP,README,Unity README,
QT-F02_ROOM_BINDINGS,CP03 request/receipt,engine_bridge/engine_project,BrainConnection,
PlayRoom,LiveVerification,PlaytestBuild and existing engine-pipe tests/packet builder.
Prerequisites:unchanged accepted room definitions/rules/SQLite/wire DTOs;Python exact20pins;
native verification requires exact Unity6000.3.25f1/license on this host. Reuse approved setup.

## Scope and contracts

1. Review onboarding:canonical rule adds new-session entry;tools/build_cp04_packet.py adds
   --request (legacy default CP04 request),validates the included request,adds/hashes root
   START_REVIEW.md with opening prompt/read order/report format. Existing archive/witness
   outputs must reject before overwrite. Entry generation is metadata,not claimed review.
   Prior CP03 ZIP/witness/patch remain immutable;use distinct FRESH_SESSION snapshot/resume
   request for current inputs. No external dispatch or upload.
2. Bridge:EngineBridge and serve add keyword scenario:Scenario=LEGACY_SCENARIO;CLI --scenario
   defaults to legacy ID and resolves scenario_by_id before starting ClientWorker. Unknown
   identifier fails startup before working-save creation. Full framed response schema/hash,
   request sequencing/attachments/retry/quit behavior unchanged. Explicit selection survives
   C# reconnect by retaining the same selected ID;load still checks existing rules pins.
3. C# constants:generate WireScenarios.Legacy/Courtyard from the two Python Scenario IDs in
   app.engine_project.generate_wire;no hand-written duplicate ID definitions or wire DTO changes.
   Only Wire.Generated.cs is regenerated;catalog/qualification/manifest bytes remain unchanged.
4. PlayRoom reads REVERIE_UNITY_SCENARIO once before filesystem/process work;unset/empty means
   legacy. Exact generated IDs accepted;other strings throw UNKNOWN_SCENARIO before launch.
   Default working path legacy remains tmp/unity-play/game.sqlite;courtyard gets separate
   tmp/unity-play-courtyard/game.sqlite. Explicit REVERIE_UNITY_WORKING remains authoritative.
   BrainConnection passes the validated ID through quoted --scenario at process startup;
   reconnect/load retain current private working path and same ID. No runtime scenario switch.
   Existing fixed3x3/immutable-board guard remains intact.
5. Native verifier adds a courtyard path under existing editor/development-only guard;legacy
   flow assertions stay unchanged. Initial view6/wall7/door2/enemy0/NPC8;right stays6,up3,attack
   yields HP2/enemy3/stamina1;save/attack/load restores exact view,retry has no second attack;
   door path3→4→1,open2,move2;bell one response;disconnect/reconnect preserves selected world.
   Native invalid scenario creates no working save;release hook still absent in actual build.

Allowed MODIFY under C:/Reverie Saga:canonical v2.6 prompt;SOL_CODING_WORK_ORDER;
tools/build_cp04_packet.py;src/app/engine_bridge.py;src/app/engine_project.py;
clients/unity/Assets/Reverie/Scripts/{Wire.Generated,BrainConnection,PlayRoom,LiveVerification}.cs;
clients/unity/Assets/Reverie/Editor/PlaytestBuild.cs;README.md;clients/unity/README.md;
docs/WORKSTATION_SETUP.md;BACKLOG.md;SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md.
Allowed NEW:this order;tests/integration/test_review_packet.py;
tests/integration/test_unity_scenario.py;docs/reviews/QT-F02_UNITY_SELECTION_2026-10-15.md;
docs/reviews/RS-REVIEW-CP03_RESUME_REQUEST.md;distinct fresh-session witness/ZIP/digest under
docs/reviews or ignored tmp/reviews. Local tools/logs/builds/private saves stay ignored.
Editor-owned scene/settings rewrites may be restored only to captured pre-run bytes,never
over unrelated edits;do not retain incidental scene/settings churn as a feature change.
Forbidden:CORE/domain/engine/save-format/rule/pin changes,legacy test weakening,old review
artifact rewrites,reference/candidate/compiled narrative changes,security-policy changes,
dependencies/upgrades except approved missing editor prerequisite;agents/commit/push.

## Verification and delivery

Independent tests:actual builder ZIP has correct request-specific root entry and manifest
hashes,and cannot overwrite an existing output;actual pipe child selects courtyard/retries/
reopens/loads with correct views and preserves legacy default;invalid CLI selection leaves
no save. Native Unity uses real Brain,rendered positions/state and reconnect;test actual pin.
Empty/invalid IDs follow explicit defaults/rejection above;no target/cardinality/geometry
changes. Tick,integer-string framing,record bounds,ordering and mutation ownership unchanged.
Performance:no new per-turn IO/catalog work;one startup selection,existing capacities.
Run focused new+engine-bridge/catalog/scenario suites,Ruff/format,strict mypy/imports and
document checks. Reuse prior full1330 evidence for unchanged CORE;run native editor/build
for C# changes. Unavailable native verification stays NOT_RUN/UNVERIFIED,not DONE.
Installation:official signed pinned installer into owned tmp/unity-editor/6000.3.25f1;
older locally installed6000.3.4f1/6000.3.9f1 remain untouched. Record actual setup/license.
Acceptance:review onboarding automated and qualified;Python/C# startup/reconnect wiring;
native evidence/limitations;CP03 deferral and synchronized handoff/backlog/Korean summary.
Stop:unresolved semantics,overlapping edits,unavailable login/license or failed native tools
after safe alternatives;complete independent work and report exact blocker. No bypasses.
Delivery:brief Korean changes/tests/next position;CP03 deferred,never falsely DONE.

Execution:[receipt](../reviews/QT-F02_UNITY_SELECTION_2026-10-15.md):75focusedPASS28.12s,
Ruff/format5/mypy108/imports3+1 PASS;exact editor installed and C#editor/release compile PASS.
Actual graphical launch exits198(no valid license),so native acceptance and release build
remain NOT_RUN. Director asked to activate Hub;resume courtyard,legacy,invalid selection and
release checks with fresh paths. New-session packet behavior accepted;no automatic next task.

Latest resume supersedes that license blocker:director configured Hub;Program Files pinned
editor opened the existing project,recognized Personal and completed initial import/script
compilation. Gameplay/build checks remain pending;open editor has an Untitled scene.

Final native acceptance supersedes pending status:director requested play/build completion;
actual courtyard17/default24/invalid3/corrupt1=45PASS,all exit0. Windows release build PASS,
verification type absent in emitted assembly;standalone startup/save/shutdown smoke PASS.
Scene restored to captured pre-run bytes,all39non-code inputs match. Receipt retains native
commands/run IDs/expected faults and small-viewport UI overlap/human-UX limits. No source
repair needed;earlier75focused/1330CORE evidence reused for unchanged inputs. Unit DONE,
parent IN_PROGRESS;CP03 remains deferred and broader expansion held. No automatic next task.

Subsequent director request explicitly authorizes recording and publishing the completed
session's task-related changes,excluding further independent review. This supersedes the
earlier no-commit/push restriction only for [this delivery](../reviews/SESSION_2026-10-15.md);
use protected-main PR/check/ordinary-merge flow,no settings bypass. CP03 remains deferred.
