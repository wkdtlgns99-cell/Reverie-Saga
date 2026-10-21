# QT-F34 — Tk history reading evidence

Date:2026-10-21 | Status:LOCAL_ACCEPTED | Self-review,not independent.
Order:[QT-F34](../work_orders/QT-F34_TK_LOG_READING.md). Primary5screen support;related4/6.

Baseline clean main d7f3217 after PR12merge/local synchronization. Actual checkout
C:/Reverie Saga. Reused local CPython3.13.12/Tk8.6;no installation or Unity execution.

Existing _append_messages unconditionally called see(end). Actual mapped Tk reproduction:
80records/top40/+1 moved the visible record39to71;200records/top40/+2 moved39to192.
Before fix:new reading tests2FAIL,existing tail/load behavior1PASS (2.56s).

Implementation captures tail visibility and top logical line before rebuilding Text.
Deque eviction shifts the saved line index;an evicted anchor selects the oldest retained
record. Empty/reset history follows latest output. No new state,save writes,worker requests,
contracts or dependencies. Wrapped rows may align to their logical record's beginning;
pixel-level scroll preservation is not claimed.

Verification,all exit0 with normal sys capture:

- `python -m pytest -q tests/integration/test_client.py tests/unit/test_client_text.py
  tests/unit/test_engineering_rules.py --basetemp .pytest_cache/f34-affected`:
  65PASS16.42s,including3new cases at that point.
- Added the oldest-record eviction boundary;final `pytest -q tests/integration/test_client.py
  -k 'new_log_preserves or log_follows_tail' --basetemp .pytest_cache/f34-edge-final`:
  4PASS3.38s. This overlaps the earlier3new cases;66distinct affected cases qualified overall.
  Actual mapped widgets cover append,empty append,bounded eviction,tail following and real
  save/load history reset. Read-only append preserves ClientView and working-save bytes.
- Shared/selective Ruff PASS;changed-file format2PASS;strict mypy190files PASS.
- Type-inclusive dependency contracts3PASS;runtime cycle contract1PASS.

After all delivery edits:shared/selective Ruff PASS,README scoped format12PASS,strict
mypy190PASS,document/rulebook guards10PASS1.41s and git diff --check PASS. Self-review:
only the8allowed paths changed;three progress documents agree with local acceptance and
the earlier actual PR12merge. Production diff is9lines in the existing Tk append method.
Shared CORE unchanged;earlier successful PR12full CI remains historical evidence,not a new
full run for this patch. Unity,other-device,pixel-perfect/human UX and release acceptance
NOT_RUN. D2OPEN;CP06held. No commit/push/PR/merge for this increment.
