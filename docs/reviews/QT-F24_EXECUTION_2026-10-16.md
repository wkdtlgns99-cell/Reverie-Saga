# QT-F24 — Unity Wait Duration Selection

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/review:self;not independent.
[Order](../work_orders/QT-F24_UNITY_WAIT_DURATION.md). Primary5;related2/7.

## Behavior

PlayRoom offers1/4/8/16second presets,default1,in the existing scrolling controls. Selection is
local-only and gated by attached/idle/healthy readiness;invalid indices reject without mutation.
BrainConnection.Send forwards invariant decimal seconds only for wait;all other intents still
send1. Canonical Python wait/event/commit/retry/save/validation rules and wire hash remain unchanged.
The local preset survives load/reconnect;new room starts at1. UI choices are not a new limit SSOT.

## Verification

Existing Windows CPython3.13.12 AMD64/Tk8.6,pip PASS;editor6000.3.25f1/file6000.3.25.14801824reused.
Restricted license query unavailable;permitted public read-only status active/signedIn=true.
No installation/login/license/security change. Fresh native working directories preserve old saves.

Python515PASS70.31s,exit0,no failures/errors/skips;includes9new actual-pipe cases and existing
watch-event integration coverage. All four presets advance exactly their seconds in one revision;
changed retry-envelope duration cannot replay again;save/load restore prior state. Wire malformed/
out-of-range values remain INVALID_REQUEST;zero remains INVALID_COMMAND with no time advance.

```powershell
$env:PYTHONPATH='src;.'; $env:PYTHONHASHSEED='0'; $env:PYTHONUTF8='1'
.venv/Scripts/python.exe -m pytest -q tests/integration/test_unity_wait_duration.py tests/integration/test_unity_slot_selection.py tests/integration/test_engine_bridge.py tests/integration/test_watch.py --basetemp .pytest_cache/qt-f24-focused --junitxml tmp/qt-f24/focused.xml
```

Both Ruff configs PASS,format13files PASS,mypy169files PASS,import contracts3+1kept0broken.
Default native128PASS:real UI→Brain wait16moves12→28,retry after selecting4stays28,slot08load/
reconnect restores12while retaining16. Input selections/busy/invalid/connecting guards preserve
state and selected slot. Seven modes:default128+memory128+old quest67+legacy73+harbor60+grove60+
corrupt3=519PASS,all editor exits0/no failed checks. Windows build/release-hook absence PASS.
Middle screenshot added after initial default run;explicit memory mode shows all four buttons
and selected16clearly. This capture-only addition changes no runtime or default test behavior.

Native artifacts:tmp/qt-f24/native/<case-run>/evidence,receipts/logs and native-summary.json.
Six actual selected-wait.json witnesses confirm waitT→T+16then slot load/reconnect restoreT.
Readback of24actual current/slot01/02/08files PASS,hashes unchanged by reads. Final current CORE
equals slot08;slot02is one tick later,slot01retains its pre-test hash. Quest vectors remain
slot01tick10/stage2/one memory,slot08tick12/stage3/two memories,slot02tick13/stage3/two memories.
Actual1101x506screen preserves368x246controls and368x164history;content594pixels,bottom scroll348.18.
Top/middle/bottom screenshots show the wait selector and remaining controls reachable.

Native Prepare only regenerated scene-local IDs/empty-name whitespace;normalized whole-scene
comparison passed before byte-exact restoration. Final scene SHA256
3157e6272f93a108ce80848f9d1352fdaa15f3ecae3e750e525763818b011b94matches entry.
Delivery checks:453entry files preserved outside declared paths,UTF8/links/fences/progress/diff PASS;
existing document entry guards qualify the final progress update. No new behavior/source test failures.

No Python production/shared CORE change:full suite NOT_RUN,prior1741historical. No live provider,
agent,commit/push/merge or independent rereview. V3stopped PARTIAL,CP06holds release;human UX,
other-device/narrow viewport/MIN-SPEC/standalone qualification remain separate.
