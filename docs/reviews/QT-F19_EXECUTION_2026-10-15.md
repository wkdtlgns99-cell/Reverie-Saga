# QT-F19 — Recent NPC Memory in Tk and Unity

Date:2026-10-15 | State:LOCAL_ACCEPTED | Executor/review:self,not independent.
Order:[QT-F19](../work_orders/QT-F19_RECENT_MEMORY_CLIENTS.md). Primary5;related4retrieval/6/7.
Director explicitly defers Claude and requests next implementation. Only the existing two scoped
player/NPC conversations are retrieved;broader D2cognition/world/memory remains open.

## Behavior and Live Wiring

Both memory-enabled clients now have the Korean **최근 대화 기억** control. It shows
at most one newest committed conversation using the same canonical(-observed_at,memory_id)ranking
as existing T0queries. Shared recent_evidence accepts only a validated exact NpcQuestMemoryRecord;
ClientSession reads its current owner snapshot and uses the same private formatter as full
inspection. Full chronological inspection and its existing public signature/results are unchanged.

ClientWorker serializes inspect_recent_memory on its existing owner executor. Before attach it
refuses without creating/opening a save;closing and unavailable modes remain explicit. Ordinary
faults are logged/projected with continued input,while process-control exceptions propagate.
Tk's actual new button shares busy/close gates with full inspection;wait/slot rows move only in
memory mode to prevent overlap. Unity shares CanInspectMemory and rejects repeated/cross-button
clicks while busy. Older load and reconnect always query the currently attached saved branch.

New bounded wire request memory_recent goes through existing envelope/sequence/attachment checks.
No request fields,ClientRequest/action enum,ClientUpdate/save DTO or authoritative protocol changes.
Wire.Generated.cs regenerated with generate_wire;schema pin changes from188504954814f58c87dba6dad0f63e996a4267c3fa8de15b2f35d7e86c5c1416
to58134983b3bf0132665cfe8b58aacdda5652ee6956beffbfa6dc8bbcaf3206ef. Generated equality and live
current-hash transport are verified;the existing C#schema mismatch guard remains intact. This does
not claim a separate native old-client binary test. No save/content hashes repinned or model calls.

## Python and Static Qualification

| Check | Actual result |
|---|---|
| Entry query/full-inspection/engine-inspection baseline | 29PASS10.91s |
| New recent-memory module | 12PASS7.30s |
| Affected client/worker/pipe/query/comparison/export/check/prepare/text modules | 161PASS76.02s |
| Current actual Tk button cases after helper typing repair | 2PASS3.10s,10deselected |
| Both Ruff configurations | PASS |
| Scoped format | 15files already formatted |
| Strict mypy --no-native-parser | PASS163source files |
| pip check | no broken requirements |
| Native import contracts | 3+1kept,0broken |

Initial mypy found two new-test calls passing save/load to the existing gameplay-action-only
_click helper. Replaced them with actual Tk save/load button invocations plus normal event pumping;
no source behavior or assertion weakened. The161case run had already loaded the earlier test body;
the two affected Tk cases were therefore rerun separately after this repair. Final static results
cover current bytes. Evidence:tmp/qt-f19/{baseline,new,affected,tk-final}.xml and static.json;
initial diagnostics retained in static-initial.json and original logs.

New independent assertions cover empty/accepted/unreported/reported states,the exact latest tick,
certainty/no invented eyewitness evidence,full inspection unchanged,no turn/reward/file/protocol/
retry changes,pre-attach/disabled/closing,owner-thread execution,ordinary failure and fatal
propagation,real binary pipe stale request/attachment rejection,older load/resume,and real Tk
busy/close/layout/continued gameplay. Existing query/export/compare tests verify unchanged T0order.

## Actual Unity Qualification

Reused installed Python3.13.12 AMD64/Tk8.6/SQLite3.50.4 and Unity6000.3.25f1(e1dba0a9aba4),file
version6000.3.25.14801824. Restricted CLI license query failed LICENSING_CLIENT_UNAVAILABLE;
permitted host query confirmed success/active/signedIn without modifying licensing/security.
Sequential native editor runs used fresh owned saves and existing PlaytestBuild entry points:

| Case | Passed checks |
|---|---:|
| Ordinary approved memory default | 74 |
| Explicit approved memory | 74 |
| Old quest without memory | 18 |
| Legacy +Windows build | 25 |
| Harbor | 12 |
| Grove | 12 |
| Corrupt save | 1 |
| Total | 216 |

All exit0/no VERIFY_FAIL. Windows build and RELEASE_VERIFICATION_HOOK_ABSENT passed. Native
verification exercises both full/recent actions at empty,accepted,unreported,reported,loaded,
reconnected and branch-report phases,including busy/cross-button suppression,correct visible
history,source hash/view/reward/attachment preservation and old-mode unavailability.
tmp/qt-f19/native-summary.json binds seven receipts/logs and their actual working paths.

Inspected actual default screenshot:
tmp/qt-f19/native/default-f1cea19d6d6a466781dc6cbe08eb35d9/evidence/quest.png.
Both memory controls render in Korean with the reported-memory text in the scrollable history.
No renderer/asset/camera changes. Final response contains only the recent report@12,tick12/favor1.

Read back original(tick13),slot01(tick10),loaded(tick12) from BOTH successful memory runs. Recent
selector equals existing EvidenceQuery(limit=1):slot gives acceptance@2,original/loaded give report@12.
All six source file SHA256 remain unchanged across readback;API0. Witness:
tmp/qt-f19/actual-memory-readback.json. This is actual saved-state readback,not synthesized UI data.

The existing native harness regenerated scene object IDs/empty-name whitespace. Verified complete
scene structure/reference equivalence against entry,retained generated copy,then restored EXACT
entry bytes;tmp/qt-f19/scene-restoration.json records both hashes. No scene edit retained. Existing
engine/domain/contracts/content/config/old QT-F18/review-request inputs preserved outside scope.

## Delivery and Limits

New source/test/order/receipt,README/Unity/setup and three progress updates remain local on
HEAD2f591f7. Prior local QT-F18and final-English-request edits are preserved;no commit/push,
provider/Claude call,agent,package install,remote settings or release action.
Current combined full suite/remote CI/Linux/other-device/standalone/human UX/independent inspection
NOT_RUN. Earlier full1697/remote CI and QT-F18results retain their original scopes;do not sum test
counts or present them as a new full run. Current affected/native inputs are qualified above.
Claude V3deferred/incomplete and CP06release held;future review request must include QT-F18/19.
GOV-03stale-scope hold and broader D2/D3/D4/D6/D7remain;no automatic next implementation.
