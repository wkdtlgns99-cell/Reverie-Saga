# QT-F35 — Latest-history button evidence

Date:2026-10-21 | Status:LOCAL_ACCEPTED | Self-review,not independent.
Order:[QT-F35](../work_orders/QT-F35_TK_LOG_LATEST.md). Primary5screen support;related4.

Baseline main d7f3217with accepted F34dirty work(6modified/2new paths),all preserved.
Actual checkout C:/Reverie Saga;reused CPython3.13.12/Tk8.6. No installations,Unity,
agents,external calls or publication.

Replaced the existing heading Label placement with a shared heading frame and the
최신 기록으로 ttk.Button. Callback only calls Text.see(end). It remains available during
pending gameplay because it does not submit or modify commands. Existing F34tail detection
then resumes following output. No history persistence or gameplay/state behavior changed.

Actual mapped Tk smoke:`python tmp/qt-f35/smoke.py`,exit0. Asserted the button is mapped
and correctly labeled,short-history/repeated clicks are harmless,80records can be read
above the tail and returned to bottom1.0,ClientView/last_update/history/save bytes stay
equal during scrolling,and the same pending Future survives clicks during an actual wait.
After the real wait,tick1and automatic tail following both qualified. Temporary script/save
owned under ignored tmp/qt-f35;ordinary test teardown closed its own Tk/worker.

`python -m pytest -q tests/integration/test_client.py tests/unit/test_client_text.py
tests/unit/test_engineering_rules.py --basetemp .pytest_cache/f35-affected`:
66PASS17.05s/exit0. Includes existing F34reading/eviction/tail/load and worker/failure guards.
No committed tests added for this small UI addition;native smoke verifies the new control.

README shared/selective Ruff PASS,scoped formatting12PASS,strict mypy190PASS,
type-inclusive dependency contracts3PASS,runtime cycle contract1PASS. Final delivery
document guards/diff/UTF-8 checked after synchronized documentation edits.

Self-review:only F35's seven allowed paths were changed in this increment;F34's test
and two evidence/order files remain intact. No full regression,Unity,other-device,
human UX or release qualification is claimed. D2OPEN;CP06held. Local/uncommitted only.
