# QT-F17 — Unity NPC Conversation Memory Inspection

Date:2026-10-15 | Status:LOCAL_ACCEPTED | Review:self,not independent Claude feedback.
[Order](../work_orders/QT-F17_UNITY_MEMORY_INSPECTION.md). Primary5;related2/6,7integration.
Director requests Unity wiring/tests and explicitly keeps Claude V3 pending.

## Implementation / Truth Boundary

EngineBridge registers exactly one new memory request after existing envelope/sequence/attachment
validation and routes it to QT-F16ClientWorker.inspect_memory. No gameplay command is submitted.
ClientRequest/ClientUpdate fields and all CORE/save/content schemas stay unchanged. Canonical
generate_wire updates only the generated C#schema hash from b7b08208... to
188504954814f58c87dba6dad0f63e996a4267c3fa8de15b2f35d7e86c5c1416;existing C#hash comparison
rejects a mismatched peer. No BrainConnection transport change or save migration is needed.

PlayRoom shows NPC conversation-memory button only in memory mode;CanInspectMemory shares its
ready/not-busy/no-failure gate with the public InspectMemory callback. Repeated click while busy
does nothing. Existing response/history/load/reset/reconnect shows the current attached branch.
Only already recorded conversations with this player are displayed,with game seconds:directly
heard acceptance and received completion report. Reports are explicitly not witnessed enemy death.
Unavailable memory remains a visible ordinary status;no provider call/private NPC knowledge added.

## Baseline / Device

HEAD:e32cf3e08a44d327b7ed091650bec7f74716676f. Entry includes all prior local QT-F16source/tests/
docs plus pause notes;fingerprints/status:tmp/qt-f17/entry.json. These are preserved,not reset.
Actual current host:Windows AMD64,Python3.13.12/Tk8.6/SQLite3.50.4 and installed editor6000.3.25f1/
e1dba0a9aba4,reported executable6000.3.25.14801824. Restricted public license CLI could not connect;
permitted same CLI confirmed active Personal/signed-in. No install/login/license/security change.
This is current-host evidence,not a second-device or final standalone qualification.

## Actual Python / Static Verification

Interpreter:.venv/Scripts/python.exe;cwd C:/ReverieSaga. Pytest uses PYTHONHASHSEED=0,
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1;native import CLI uses PYTHONPATH=C:/ReverieSaga/src.

| Check | Actual result |
|---|---|
| Baseline engine bridge+QT-F16inspection+memory-client route |29PASS15.56s;tmp/qt-f17/baseline.xml |
| New real pipe/binding tests |3PASS2.79s;tmp/qt-f17/new.xml |
| Final affected regression below |144PASS46.17s;0failure/error/skip;tmp/qt-f17/final.xml |
| Ruff shared +ruff-quality.toml |both exit0 |
| README format selection +engine_bridge and two new inspection modules |15files/exit0 |
| strict mypy --no-native-parser |159files/exit0 |
| Native import CLI:pyproject.toml and .importlinter-runtime.toml,--no-cache |3+1contracts KEPT/exit0 |
| pip check |no broken requirements/exit0 |

Final test command:`-m pytest -q tests/integration/test_engine_memory_inspection.py
tests/integration/test_client_memory_inspection.py tests/integration/test_client.py
tests/integration/test_memory_client_route.py tests/integration/test_engine_bridge.py
tests/integration/test_npc_memory.py tests/integration/test_quest.py tests/unit/test_client_text.py
tests/unit/test_engineering_rules.py tests/unit/test_narrative_catalog.py
--basetemp .pytest_cache/qt-f17-final --junitxml tmp/qt-f17/final.xml`.
Static actual argv/exits/timings/log hashes:tmp/qt-f17/static.json and individual logs.
New actual subprocess pipe uses existing network-forbidden memory harness;checks empty/acceptance/
unreported defeat/report,source byte/view/reward preservation,retry,no duplicate grant,older slot,
stale token/request rejection,continued input,new process resume,unavailable legacy and generated
binding equality. Existing native Tk/worker/process-control/failed projection/recovery tests retained.

## Actual Unity / Build Verification

Public editor invocation per case:`Unity.exe -projectPath C:/ReverieSaga/clients/unity
-executeMethod ReverieSaga.PlaytestBuild.Verify -logFile <owned unique log>`;legacy uses
BuildAndVerify,corrupt uses VerifyCorrupt. Hidden graphical editor,not batch/null graphics;fresh
unique working paths under tmp/qt-f17/native. Script:tmp/qt-f17/native.ps1,adapted from retained
prior current-host harness. Cases run sequentially;actual summary:tmp/qt-f17/native-summary.json.

| Case / run suffix | Checks | Result |
|---|---:|---|
| default-8fc6de9a14dc43ea96ab04a05a5bb555 |46 |PASS/exit0 |
| memory-b9657e6ab1ad4362a6907e84e2929f75 |46 |PASS/exit0 |
| quest-25a222af369b4b5cbbbd68117ce04254 |17 |PASS/exit0 |
| legacy-3b2955da2e034de3866a57d925eb72dc |25 |PASS/exit0/build/hook absent |
| harbor-6cf2c57b4ca043f79a2ba6cc0ea4e30c |12 |PASS/exit0 |
| grove-10e5da26a2914f2db44bfa74234add07 |12 |PASS/exit0 |
| corrupt-bbb9b6e8162945ccbf4547db2e43a792 |1 |PASS/exit0 |

Total159VERIFY_PASS/0VERIFY_FAIL across seven completed runs. Memory-enabled runs add seven
phase inspections:empty,accepted,unreported,reported,loaded,reconnected,branch report. Each checks
enable/busy/double-click suppression,exact view/quest/reward/token/path/file hash preservation,
correct remembered game times/certainty and existing rendered history. Load clears newer report
history. Existing quest prose/retry/no-second-grant/continued play and reconnect checks still run.
Native verifier invokes the same callback as OnGUI,not an OS mouse click. Actual Game screenshot
default.../evidence/quest.png was visually inspected:readable Korean memory button/report shown.
BuildPipeline Windows build succeeds and release Assembly-CSharp excludes LiveVerification.

Both default and explicit-memory runs' original/slot/loaded saves independently read back using
retained read_native_memory.py:original accepted@2/report@12,tick13;slot accepted@2,tick10;
loaded accepted@2/report@12,tick12/favor1/reported certainty. All three hashes unchanged during
readback/offline preview,network forbidden/API0;per-run memory-readback.json retains evidence.

## Diagnostics / Scope / Limits

First default run996953021c674ad781727885985da7e9 reached3checks then new verifier File.ReadAllBytes
hit Windows sharing violation on the open SQLite file. It is not a query/gameplay defect:inspection
had not been sent. Exact owned editorPID2476 identified by executable+unique log,stopped,exit-1;
failed receipt/log retained. Verifier now opens a read-only FileStream with FileShare.ReadWrite|Delete,
preserving SQLite ownership. Entire default and remaining cases requalified on final source.
Existing SearchDatabase indexing/optional token-refresh diagnostics remain in native logs;not
compilation or VERIFY failures and not relabeled as clean logs.

Prepare rewrote only generated scene object/reference IDs and empty-name whitespace. Structural
normalization equality and entry hash checked,then exact original bytes restored;witness
tmp/qt-f17/scene-restoration.json. Editor-created _Recovery files absent at entry matched that
scene structurally;after provenance/no-reparse/absolute workspace containment checks,moved intact
under tmp/qt-f17/editor-recovery. No recovery evidence deleted and no scene/art/camera edit retained.
Prior QT-F16new files/source/pause notes remain intact;other tracked inputs protected by entry hashes.
Delivery checks:404entry files byte-identical,exact10allowed existing edits/3new files,13UTF8
deliverables/20added local links PASS,JUnit144cases/0failure/error/skip,HEAD unchanged and
git diff --check exit0. Witness:tmp/qt-f17/delivery-checks.json. Existing two QT-F16CRLF checkout
advisories remain informational;no project whitespace error or unrelated edit retained.

No shared CORE change;full suite not rerun. Linux,standalone executable launch,other-device,
human playtest/MIN-SPEC,new remote CI/Claude/live-provider NOT_RUN. No commit/push/agent/merge/
release/account administration. V3A–Ereview remains pending at published e32cf3e and excludes local
QT-F16/17;CP06release held. Existing memory is two scoped records,not broader NPC cognition.
