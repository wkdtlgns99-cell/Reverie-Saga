# QT-F36 — Tk wait Enter evidence

Date:2026-10-21 | Status:LOCAL_ACCEPTED | Self-review,not independent.
Order:[QT-F36](../work_orders/QT-F36_TK_WAIT_ENTER.md). Primary5input support;related2.

Baseline main d7f3217with F34/F35accepted dirty work(6modified/4new paths),preserved.
Actual checkout C:/Reverie Saga;local CPython3.13.12/Tk8.6reused. No tool installation,
Unity launch,agents,provider calls or publication.

Two production lines:add Return binding on wait_input to existing _send(wait),and show
Enter in its label. Existing button/worker/parser/canonical validation/busy checks own all
semantics;no new command,save format or CORE behavior. Focus scope is the wait Spinbox.

Actual mapped focused Tk smoke:`python tmp/qt-f36/smoke.py`,exit0. Synthesized real Tk
KeyPress-Return on the focused field. Input4advanced tick0to4;two key events before polling
kept the same pending Future and committed once. Inputs1and16then advanced ticks5and21.
Inputsabc/empty produced INVALID_INPUT;0/-1/17produced INVALID_COMMAND;all retained
view,working-save bytes and entered text. Return in the log Text produced no request or
state/file change. Owned temporary Tk/worker closed;script/save remain ignored under
tmp/qt-f36. No new committed tests for this small input convenience.

`python -m pytest -q tests/integration/test_client.py tests/unit/test_client_text.py
tests/unit/test_engineering_rules.py --basetemp .pytest_cache/f36-affected`:
66PASS17.15s/exit0. README shared/selective Ruff PASS,scoped format12PASS,mypy190PASS,
type-inclusive import contracts3PASS,runtime cycle contract1PASS. After synchronized delivery
edits:document/rulebook guards10PASS1.40s,diff whitespace and UTF-8 checks PASS.

Self-review:only seven F36allowed paths changed;earlier F34/F35source/tests/evidence
preserved. Changes remain local/uncommitted. Full regression,Unity,other-device,human UX
and release acceptance NOT_RUN;D2OPEN,CP06held.
