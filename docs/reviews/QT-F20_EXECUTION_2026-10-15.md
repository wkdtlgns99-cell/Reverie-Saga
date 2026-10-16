# QT-F20 — Save Slot Preview Qualification

Date:2026-10-15 | State:LOCAL_ACCEPTED | Executor/review:self,not independent.
Order:[QT-F20](../work_orders/QT-F20_SAVE_SLOT_PREVIEW.md). Primary6;related5/7.
Director keeps Claude review deferred and requests next implementation.

## Behavior and Ownership

SqliteSlots.inspect reuses exact slot-name/path/alias validation,current-store health validation,
read-only checkpoint decoding and the existing busy guard. It creates no temporary/clone/output
file and does not fall back to a previous slot generation. Missing/corrupt/incompatible/indirect
paths retain their established SaveError diagnostics;ordinary unwrapped SQLite/OS read failures
become SAVE_INSPECT_FAILED with busy cleared in finally. Unexpected programming exceptions are
not reclassified as gameplay success. DurableSession.inspect_slot uses its existing operation/
closed/quarantine guards without swapping the owner,token,store or read views.

ClientSession displays saved logical time/revision,quest stage/favor and registered NPC-memory
count/report presence as explicitly saved messages. Its ClientUpdate view/reward/path/token still
describe the current game. Preview never becomes a command or overwrites retry. Shared Korean
quest labels are reused by Tk. Memory count appears only when that feature is registered;the
completion evidence is explicitly the player's report,not witnessed enemy defeat.

ClientWorker.inspect_slot serializes the read on its owner executor;pre-attach returns
SLOT_INSPECTION_UNAVAILABLE without creating a game. Existing closing/error/Future behavior applies.
Tk uses the actual selected slot;Unity's button explicitly labels slot01to match its existing
prototype save/load controls. Both share input/busy/close handling. Unity's full/recent memory
buttons occupy one row to preserve history space. Current player stats are never replaced by saved
preview values. Preview is a point-in-time read,not a lock binding a later separate load.

The bounded slot_inspect request uses existing slot_id and normal sequence/attachment validation.
Wire.Generated.cs is regenerated canonically:58134983b3bf0132665cfe8b58aacdda5652ee6956beffbfa6dc8bbcaf3206ef
→a342a2f3bb5ca4123243cc52450cbf12c46661e4f18737095e222beb6e87212f. No ClientRequest/action,
ClientUpdate/save DTO,CORE/protocol/content/approval or migration semantics changed.

## Verification Recorded So Far

- Entry save-slot/SQLite recovery/durable baseline:79PASS126.58s.
- Restricted new module:12PASS/1FAIL twice due to environment setup;real hardlink creation denied WinError5.
  Initially tried an open working save,then the more representative closed exported slot. Both
  restricted attempts refused before the guard could be exercised;logs retained,not hidden.
- Same13case snapshot on the permitted host:13PASS7.17s,including actual hardlink rejection.
  No skip,synthetic link metadata or weakened path policy. Owned alias removed afterward.
- Added real commit/absent uncertainty variants:2PASS1.31s,13deselected. Both refuse preview until
  recovery is proved and preserve the actual persisted state/slot without pretending rollback.
- Initial strict typing found nominal EntityId/variable-tuple annotation issues;fixed explicitly.
  Initial lint found one unused test import and a Korean display-width line;fixed without changing
  runtime AST. Verified AST equality around the formatting-only repair. Original formatting outside
  the two small storage/owner additions was preserved;no bulk formatting retained.
- Host Python3.13.12/Tk8.6/SQLite3.50.4/editor6000.3.25.14801824 reused. Host CLI confirms
  success/active/signedIn;no install/license/security settings change.

## Final Qualification

| Check | Actual result |
|---|---|
| Full pytest,hashseed0,host environment | 1741PASS513.95s;15new slot-preview cases included |
| Current saved-memory/real-pipe/Tk display cases | 4PASS7.56s,11deselected |
| Shared and selective Ruff | both PASS |
| Scoped format | 14files already formatted |
| Strict mypy --no-native-parser | PASS164source files |
| pip check | no broken requirements |
| Native import contracts | 3+1kept,0broken |

The full run includes the retained local QT-F18/19work as well as QT-F20. Do not add overlapping
baseline/new/focused results to1741. A formatting-only repair during the full run preserved the
runtime AST exactly;removing an unused test import changed no assertions. The four current display
cases were rechecked separately;no new game semantics were introduced after full collection.

```powershell
$env:PYTHONHASHSEED='0'
$env:PYTHONPATH='src;.'
$env:PYTHONUTF8='1'
.venv/Scripts/python.exe -m pytest -q --basetemp .pytest_cache/qt-f20-full --junitxml tmp/qt-f20/full.xml
```

Raw commands/logs/JUnit/static evidence live under tmp/qt-f20. No tests skipped or weakened.
Actual cases cover latest generation/overwrite,missing/corrupt/invalid/hardlinked slots,closed/
busy/uncertain guards,real read failure and cleanup,source/file/identity/retry preservation,no
clones,owner-worker routing,selected Tk slot,real pipe stale IDs and loaded-branch resume.

## Actual Unity and Saved-State Evidence

Sequential native editor verification used fresh owned saves and the installed pinned editor:

| Mode | Passed checks |
|---|---:|
| Ordinary approved memory default | 84 |
| Explicit memory | 84 |
| Old quest without memory | 28 |
| Legacy +Windows build | 34 |
| Harbor | 21 |
| Grove | 21 |
| Corrupt save | 1 |
| Total | 273 |

All seven exit0/no VERIFY_FAIL. Windows build and RELEASE_VERIFICATION_HOOK_ABSENT passed.
Native checks exercise actual preview readiness,busy/cross-button suppression,missing-slot status,
saved metadata/history,working/slot file hashes and current view/reward/attachment preservation.
Existing gameplay,retry,load,reconnect,full/recent memory and corrupt-save flows still pass.
Witness:tmp/qt-f20/native-summary.json and its seven raw receipts/logs.

Inspected actual default screenshot:
tmp/qt-f20/native/default-33f10b120f394d9eae63aacf463b637b/evidence/quest.png.
The slot01button and saved-memory text are visible in the existing scrollable history;current
stats show tick12/favor1 while the saved preview reports tick10/favor0. Full response/independent
SQLite readback confirms all three preview messages;no human UX/release approval is inferred.

Read original/slot/loaded files from default,explicit memory and old quest modes:9actual saves.
Validated times13/10/12,stored quest stage2/favor0 versus current stage3/favor1,and,where registered,
only one acceptance@2memory in slot01with no report. Old quest mode omits a memory line. All nine
file SHA256 remain unchanged across readback;API0. tmp/qt-f20/actual-slot-readback.json binds
metadata to exact source hashes rather than treating UI text as storage proof.

The existing build harness regenerated only scene IDs/empty-name whitespace. Proved complete
structure/reference equivalence,retained generated copy and restored EXACT entry scene bytes;
tmp/qt-f20/scene-restoration.json records hashes. No asset/camera/renderer/scene edit retained.

## Delivery and Limits

All out-of-scope entry inputs,including previous QT-F18/19tests/receipts and final English request,
are preserved. New source/test/order/receipt,README/setup and three progress notes remain local
on HEAD2f591f7. No commit/push,provider/Claude call,agents,dependency/configuration/CI/settings or
approval changes. Current remote CI,Linux,other-device,standalone launch and independent review
NOT_RUN. Native editor/build qualification is not human UX or public-distribution acceptance.
Claude V3remains deferred/incomplete;CP06release held. Future review request must include
QT-F18/19/20and the new full evidence;older2f591f7CI does not cover these local additions.
Broader D2/D3/D4/D6/D7and GOV-03stale-scope hold remain;no automatic next implementation.
