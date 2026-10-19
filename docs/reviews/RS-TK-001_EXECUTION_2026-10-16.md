# RS-TK-001 — Windows Tk capture diagnosis

Date:2026-10-16 | Executor/self-review | Baseline:b2876a7.
Order:[RS-TK-001](../work_orders/RS-TK-001_RUNTIME_CAPTURE_2026-10-16.md).
State:LOCAL_ACCEPTED. Current-host targeted/static and combined final regression PASS.

## Cause and repair

Pytest's default fd capture replaces process descriptors at setup/call/teardown boundaries.
Windows Tcl retains standard-channel OS handles on its thread across interpreter lifetimes.
An old numeric handle can subsequently name another file. Tcl8.6.15's
[OpenFileChannel](https://github.com/tcltk/tcl/blob/core-8-6-15/win/tclWinChan.c#L1294)
returns an existing channel for the same handle,or NULL for different permissions without
setting a new errno. This explains varying real file paths and stale `No error`/ENOENT messages.
[Pytest capture contracts](https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html)
distinguish descriptor replacement from Python sys capture.

Native C-API diagnostic using the already installed tcl86t.dll observed cached Tcl stdout688
versus current CRT stdout924 after capture phases;12cases under fd produced10PASS/2Tcl failures.
Identical sys run observed192/192 through all12cases and12PASS3.39s. These numeric handles are
run-specific evidence,not constants. The stale handle was measured;the precise failing
CreateFile/permissions collision is inferred from that evidence and upstream source,not a
recorded native debugger stack. Local scripts/logs:tmp/test_tk_handles.py,tmp/tk-handles*.log.

Set pytest's canonical default to `--capture=sys`;local and CI commands inherit it.
All assertions,real widgets,workers,saves and original installation remain. No retry,skip,
Tcl copy,global environment workaround,dependency/security change or runtime behavior change.
Python output remains captured. Existing subprocess checks explicitly collect their output;
no capfd fixture consumers exist. Twenty independent test cases cross capture phases and
exercise actual attach/action/close. Failed original window attach now includes last_update.

## Reproduction and qualification

All commands use .venv/Scripts/python.exe and original installed Tcl files,without
TCL_LIBRARY/TK_LIBRARY. Base CPython3.13.12 AMD64/Tcl/Tk8.6;pip check PASS.

| Run | Actual result |
|---|---|
| Four original client modules,fd default |69PASS/1FAIL/1ERROR46.82s;init.tcl/treeview.tcl reads failed |
| Minimal root-only30lifetimes,fd |29PASS/1FAIL8.06s |
| Same30lifetimes,sys |30PASS7.97s |
| Standalone100lifetimes |100PASS;no pytest descriptor phases |
| New actual client20lifetimes,explicit fd negative reproduction |18PASS/2FAIL12.74s;menubutton.tcl failure retained |
| Original four modules,sys |71PASS49.96s |
| All six Tk modules plus new20cases,restricted |120PASS/1hardlink permission failure94.08s;second independently launched overlapping run same120/1in93.59s;no Tk failure. Avoid that redundant run pattern |
| Same121cases,permitted host |121PASS78.84s;actual hardlink guard exercised,no skip |
| Ruff shared/selective,format13files,strict mypy176files,imports3+1,pip |PASS |
| Final integrated RS-TK-001+QT-F25full regression,permitted host |1971PASS1092.70s(18:12),exit0;original installation,no Tcl/callback errors or warnings |

Logs are ignored tmp/tk-*.log;original failing logs retained. The restricted hardlink failure
is environmental and distinct from Tcl initialization. The approved host run passed unchanged.

PR8's historical remote `view is None` setup failure did not record its underlying update.
Its exact cause cannot be reconstructed from that assertion. Do not relabel it as proven Tcl
handle failure;current attach diagnostics and20new real-attach cases cover future occurrences.
Remote execution of this repair and another-device qualification are NOT_RUN. Historical
1896/1error and PR8full1943/1failure/2errors remain historical failures,not rewritten passes.
Unity editor16520 retained;no restart or native run required for Python test capture.

Final command/evidence:[QT-F25receipt](QT-F25_EXECUTION_2026-10-16.md),
tmp/tk-f25-full.log. Final static qualification:shared/selective Ruff,format14files,
strict mypy177files,imports3+1 PASS. Eight pinned replay sources and approved catalog
raw hashes match unchanged inputs. Other-host/remote/native-new-line limits remain explicit.
