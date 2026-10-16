# QT-F21 — Compact Unity Interface Qualification

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/reviewer:self,not independent.
Order:[QT-F21](../work_orders/QT-F21_COMPACT_UNITY_UI.md). Primary5;related6/7.

## Baseline and Change

Actual Git pull --ff-only completed after restricted FETCH_HEAD access was retried with permission.
Current branch codex/open-work-closure-20261014 remains0e06577,matching its remote tracking head.
Remote main advanced separately tocec6869(QT-F02);no branch switch/merge/reset/publication.
Entry tree was clean. The retained QT-F20screen1101x506has about45pixels left for history after
fixed-height controls and narrative text. This is the short-viewport failure witness,not a new
failing automated baseline test.

PlayRoom.OnGUI now gives controls60%and history40%of the available scroll area,with a fixed title
and separate history heading. Upper controls scroll independently;existing incoming messages
only move history. At the actual1101x506render,controls are368x246at18,48;history368x164at18,324.
All actions retain their existing handlers/gates;action rows use at most3columns(or2below330pixels).
CORE/Python/save/protocol/content/camera/assets unchanged. Editor/development layout observations
and captures are excluded from release together with LiveVerification.

## Qualification

Current host reuses Python3.13.12 AMD64/Tk8.6,pip check PASS and installed
editor6000.3.25f1/file6000.3.25.14801824. Restricted license query returned unavailable;
permitted CLI status confirms active/signedIn=true. No install/login/license/security change.

Native default93+explicit memory93+old quest32+legacy38+harbor25+grove25+corrupt1=307PASS,
all seven editor exits0/no failed checks. Windows build and release-hook absence PASS.
Actual default top/bottom screenshots were inspected:upper scrollbar reaches save/load/retry/
recovery and narrative text while history remains visible. Measured controls content438pixels,
bottom scroll191.73. Native assertions preserve current view/working-file hash and verify that
an actual recent-memory response does not move the scrolled controls. Existing native flows
exercise actual Brain commands/reward/retry/load/reconnect/memory/slot operations.

Existing Python client/pipe/memory/slot and rulebook selection:51PASS24.08s,exit0,no skips.
Both Ruff configs PASS;README's12format targets PASS;strict mypy164source files PASS;
pip check PASS;import contracts3+1kept. Initial import checks lacked PYTHONPATH and could not
find app;both passed after applying README's source-path setup,no source/config repair.

```powershell
$env:PYTHONHASHSEED='0'; $env:PYTHONUTF8='1'; $env:PYTHONPATH='src;.'
.venv/Scripts/python.exe -m pytest -q tests/integration/test_engine_bridge.py tests/integration/test_memory_client_route.py tests/integration/test_recent_memory_clients.py tests/integration/test_slot_preview.py tests/unit/test_engineering_rules.py --basetemp .pytest_cache/qt-f21-focused --junitxml tmp/qt-f21/focused.xml
```

Native commands use the documented pinned editor with -executeMethod
ReverieSaga.PlaytestBuild.Verify(normal modes),BuildAndVerify(legacy),VerifyCorrupt(corrupt),
fresh explicit REVERIE_UNITY_WORKING and existing scenario/catalog/memory selectors.
The owned tmp/qt-f21/native.ps1 records exact arguments,exit/check counts and paths per run.
Six gameplay runs retain120frame measurements:median1.613499–1.956604ms,p951.882299–2.482001ms
on observed Intel UHD750. These are editor samples,not MIN-SPEC/final-release acceptance.

Native Prepare regenerated only local scene IDs and empty-name whitespace;normalized full-scene
comparison proved equivalence before restoring exact entry bytes. Final scene SHA256
3157e6272f93a108ce80848f9d1352fdaa15f3ecae3e750e525763818b011b94matches entry.
tmp/qt-f21/native-summary.json retains every receipt and restoration hashes. Final source diff
contains only the two intended C#files;Python/CORE/wire/content/camera/assets unchanged.
Raw evidence:tmp/qt-f21/native and its per-run receipts/captures/layout/performance JSON.
Narrow320x240example remains arithmetic only,not an actual viewport/device qualification.
Full1741PASS/QT-F20is historical unchanged-Python evidence,not a fresh full run.
Claude V3remains deferred/incomplete;CP06held,human UX/release/other-device acceptance open.
No commit/push/merge/agent/provider call or automatic next task.
