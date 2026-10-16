# QT-F23 — Unity Save Slot Selection

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/review:self;not independent.
[Order](../work_orders/QT-F23_UNITY_SAVE_SLOT_SELECTION.md). Primary5;related6/7.

## Change

PlayRoom now exposes a four-column/eight-button selector(default slot01) in the existing controls
scroll region. Save/load/preview share the selected ID through BrainConnection.Send's existing
wire slot_id. The public selector validates indices0..7 and refuses changes while unattached,
busy,connecting or failed. Load/reconnect retain local selection;new component starts at01.
BrainConnection retains default slot01for existing callers and rejects invalid IDs before writing.
Canonical Python slot validation,wire/save/content pins and ownership/cleanup behavior unchanged.

## Qualification

Current host reuses Python3.13.12 AMD64/Tk8.6,pip check PASS,editor6000.3.25f1/file6000.3.25.14801824.
Restricted license status unavailable;permitted read-only CLI confirms active/signedIn=true.
No installation/login/license/security setting change. Native script uses fresh per-case save paths.

Initial Python selection22PASS5FAIL14.46s:four new assertions incorrectly expected INVALID_SLOT
inside update instead of the existing wire INVALID_REQUEST retaining ATTACHED;one existing hardlink
test was denied by the sandbox. Corrected only new test expectations against EngineBridge schema;
permitted targeted rerun46PASS24.02s,no skips/errors. Native/default117,memory117,old quest56,
legacy62,harbor49,grove49,corrupt2=452PASS;all7editor exits0/no failed checks. Windows build and
release-hook absence PASS. Exact logs/JUnit/receipts:tmp/qt-f23/native-summary.json and native/.

```powershell
$env:PYTHONPATH='src;.'; $env:PYTHONHASHSEED='0'; $env:PYTHONUTF8='1'
.venv/Scripts/python.exe -m pytest -q tests/integration/test_unity_slot_selection.py tests/integration/test_slot_preview.py tests/integration/test_engine_bridge.py tests/integration/test_memory_client_route.py tests/integration/test_recent_memory_clients.py --basetemp .pytest_cache/qt-f23-focused --junitxml tmp/qt-f23/focused.xml
```

Both Ruff configs PASS,format13files PASS,strict mypy168files PASS;imports3+1kept0broken.
Actual1101x506bottom capture inspected:01–08grid,selected slot08,preview/save/load controls and
164px history are visible. Native vectors save08@T/save02@T+1,preview each without changing current
view/file,load08restoresT,then reconnect retains08/loaded path. Slot01hash remains unchanged.
Quest vectors independently retain01@10,08@12,02@13;report memory remains factual,not eyewitness.
Readback of24actual files across6gameplay modes PASS,all file hashes unchanged by reads. Current
loaded CORE hashes match slot08;slot02is exactly one tick later;slot01hash remains the pre-test
hash. Quest modes:slot01tick10/stage2,slot08tick12/stage3,slot02tick13/stage3;memory counts1/2/2.
Actual selected-slot.json/layout.json/captures/final views and120-frame samples are retained per run.
At1101x506controls368x246/history368x164;content532pixels,bottom scroll285.60shows all slot controls.

Prepare regenerated only local scene IDs/empty-name whitespace;normalized whole-scene comparison
proved equivalence before exact entry bytes were restored. Final scene SHA256
3157e6272f93a108ce80848f9d1352fdaa15f3ecae3e750e525763818b011b94matches entry. Initial helper
readback used platform cp949 and failed decoding UTF8 evidence;explicit UTF8repaired the helper,
not game/source/evidence data. Generated-scene whitespace was removed by exact restoration.
Scope/UTF8/link/fence/progress/diff checks and existing entry guards qualify final delivery.

No shared CORE/Python production change:full suite NOT_RUN;prior1741is historical. No live API,
agent,commit/push/merge/release or independent rereview. V3stopped PARTIAL;CP06held. Human UX,
other-device/narrow viewport/MIN-SPEC/standalone release qualification remains separate.
