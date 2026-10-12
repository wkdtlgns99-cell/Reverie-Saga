# RS-CLIENT-003 / QT-F06 Execution — 2026-10-12

Baseline:main53071474bc9027749ac32b3189b9a6c7a062ab67,clean210tracked files.
Director resumed unfinished engine/content implementation and completed Unity browser login.
Self-review/native evidence only;CP04 external feedback NOT_RECEIVED.

## Result

Unity6000.3.25f1 installed from the official signed Windows editor installer;installation exit0.
Official Unity CLI1.0.0-beta.13 downloaded against publisher manifest SHA256
9a63636402d8a087e9b67621f31b15fbe0f48eba130a91bdefb88b68aa717b20.
Login exit0;Personal activation success;status active=true/signedIn=true. No account identifiers,
license serials or tokens are published. No Unity/UE5 connector found;public editor methods
provide repeatable direct edit/build/play/log/capture access. UE5 was not selected or installed.

Live path:PlayRoom → BrainConnection → engine_bridge → ClientWorker → existing durable
session/CORE. No existing engine,CORE,save schema,oracle or dependency lock changed.
Transport and generation contract:[executable order](../work_orders/RS-CLIENT-003_ENGINE_PLAYTEST.md).
The real scene has camera,tiles,wall,door,player,NPC and enemy geometry;Korean controls/history,
actual HP/time/projections and descriptive catalog browser. No LLM executes a game turn.

## Native acceptance

Final fresh run:tmp/unity-final-fresh.log,editor process exit0;ENGINE_BUILD_PASSED and
ENGINE_VERIFY_PASSED,17VERIFY_PASS/0VERIFY_FAIL. Compiled Windows player89,480,783bytes
(build report totalSize,not executable length). Native graphical editor checks:

1. Six hash-pinned narratives load;actor starts at0.
2. Missing save slot load preserves the entire public view.
3. Wait advances tick0→1;NPC call commits one reply.
4. Wall blocks0→1;closed door blocks3→4;open permits4→7.
5. Attack gives actorHP2/enemyHP3/stamina1.
6. Save/alter/load restores the complete view;exact retry repeats no effects.
7. Rest/attack kills enemy;enemy cell8 becomes passable.
8. Kill this test's Brain child;visible disconnect;reconnect resumes committed loaded branch;
   new input works without losing state.
9. Actual screenshot written and visually inspected;120frame sample recorded.

Final-view fields:actor8,actorHP1,enemyHP0,stamina0,tick14,revision14,NPC replies1.
Frame sample on Intel UHD Graphics750:median1.695104ms,p95=2.588903ms,120frames.
This is an editor placeholder observation,not laptop identity or release MIN-SPEC certification.
Previous handoff laptop specification does not describe the observed current GPU.
[Actual screenshot](assets/RS-CLIENT-003_playroom_2026-10-12.png).

Python:final focused15PASS2.59s;strict mypy103files PASS;shared/selective Ruff PASS,
format18targets PASS;type-inclusive dependency3/runtime-cycle1 contracts PASS.
Initial full1284PASS338.96s included all old golden/replay tests;one later qualification test
and compiler dossier guard require the final full run recorded in the delivery addendum.

## Failures retained / bounded repairs

- First package resolve failed:inputlegacy is not a bundled package. Removed the nonexistent
  dependency after inspecting installed built-ins;screen-capture module included explicitly.
- First strict types failed on IO/BinaryIO annotations;fixed declared stream interface.
- First batch capture stalled:WaitForEndOfFrame cannot run in editor batch mode. Graphical
  editor run captured an actual image;no fabricated rendering or skipped semantic assertions.
- Initial Windows-player run failed because Shader.Find's unreferenced shader was stripped.
  Added a real Resources material with built-in shader dependency;rebuilt successfully.
- Final unsigned standalone player was blocked by Windows application-control policy.
  This is an OS execution denial,not an auto-review rejection. No policy bypass or false player PASS.
- A fresh-room failure-load probe initially shared earlier slot files;it loaded a real old slot
  and correctly failed7checks. Added empty-directory verification preflight and reran in a
  fresh parent:17PASS. No old saves or checks were removed/weakened.
- Compiler qualification guard had a local variable collision/partial rename;strict mypy and
  focused tests caught it;fixed and reran103types/15tests PASS. Original dossier unchanged.
- Unity SearchDatabase startup IndexOutOfRange remains a recorded editor indexing issue,
  not an application source exception. Intentional Brain-disconnect exception is expected
  fault-probe evidence. Interpreter launcher-location notice persists before successful runs.

## Content acceptance

[QT-F06](../work_orders/QT-F06_NARRATIVE_IMPORT.md):new frozen4field narrative contract,
strict hash-pinned compiler/loader and actual Unity consumer;6sample descriptions imported.
Original candidate dossier still runtime_imported=false because it is the historical reference;
current import lives in content/narratives.json plus its manifest. The compiler checks the
QT-F04 qualification dossier SHA;unqualified edits cannot be automatically published.

[Per-entry ledger](../reference/QUILLTALE_SELECTION_LEDGER_2026-10-12.json):326source records
(215settlements/82creatures/14facilities/15quests),selected text/hash,excluded source fields,
source raw-byte hashes,disposition and duplicate links. All selected text inspected in this
self-review;keyword search was supplemental,not a rights detector.6SAMPLE_IMPORTED,
319ADAPTATION_QUEUE_CP03,1distinctive weapon-field/domain combination requires rewrite.
Two settlement descriptions are identical and flagged for consolidation. Creature descriptions
need appearance-only adaptation;some contain effects,stats or encounter transformations.
Facility services and supernatural-world rules remain text,not executable promises.
Whole legacy templates/stats/formulas/effects/bindings/code remain excluded.

Read-only reference276files,15dirty lines and HEAD3c50c34f unchanged against the entry baseline.
Original prompts/per-entry provider split remain unrecorded;director/consumer terms testimony
is qualified evidence,not exclusive copyright/noninfringement certification.

## Remaining acceptance

RS-CLIENT-003 implemented native prototype READY_FOR_REVIEW;CP04 packet ready,feedback pending.
QT-F06 compiler/sample/326ledger scope accepted;bulk adaptations/scenario generalization await
QT-F02/CP03. Standalone OS launch,portable packaging,full-world gameplay and human UX acceptance
remain open. CP02/old witnesses/archives/pins/core goldens are preserved.

## Final delivery addendum

Final full regression1285PASS305.69s after qualification guard repair;no skips/oracle changes.
Unity-generated YAML trailing whitespace normalized after native acceptance;field values and
C# sources unchanged. Final review witness/ZIP refreshed after synchronized delivery documents.
