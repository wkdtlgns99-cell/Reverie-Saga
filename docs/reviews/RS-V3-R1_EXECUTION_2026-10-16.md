# RS-V3-R1 — HTTP Framing Repair

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/review:self;not independent patch rereview.
[Order](../work_orders/RS-V3-R1_HTTP_TRANSPORT.md). Primary4 AI preparation support;related7.

## Reproduction and Repair

Host:Windows,CPython3.13.12 AMD64,pytest9.1.1,SQLite3.50.4;existing environment reused,pip check PASS.
Actual loopback socket server sends malformed status and truncated chunked-body bytes through
urllib's real HTTP parser. Before repair:2FAIL0.43s;BadStatusLine escapes opener.open and
IncompleteRead escapes response.read. Baseline:tmp/v3-r1/native-baseline.xml.
Initial restricted loopback run instead hit2server accept timeouts20.436s;qualified permitted
rerun distinguishes environment failure from the reproduced production defect.

Only production change:import HTTPException and translate it to GENERATION_TRANSIENT from None.
HTTPError remains first with its existing status-specific classification;other network timeout/
OS diagnostics remain unchanged. Main now serializes the error instead of exiting abnormally;
parent transport recognizes it and existing GeminiDialogue permits one budgeted retry.
HTTPException subclasses that also inherit OSError follow transient classification;both remain
eligible for the existing bounded retry. Endpoint/proxy/redirect/deadline/output/credential policy
and authoritative game state unchanged. No TLS/provider incident or live Gemini call was induced.

## Checks

- Initial fixed transport+existing module:22PASS1.02s,including actual child→parent→retry recovery.
- Expanded final regressions:225PASS156.65s,exit0,no failures/errors/skips;tmp/v3-r1/combined.xml.
- Actual faulty-then-valid response tests verify two zero-exit children and final usage260;
  failed attempt retains20000conservative tokens,ledger total20260. Two faults stop at two
  attempts,total40000;no third call. Read failures close owned responses;KeyboardInterrupt
  propagates. Eight actual HTTP status cases preserve auth/deferred/rejected/transient codes.
- Both Ruff configurations PASS,strict mypy167files PASS,format16files PASS,import contracts3+1
  kept0broken. Source/test inputs unchanged since these passing checks.

Exact final selection is recorded in the QT-F22receipt;affected checks share one run and counts
must not be added to earlier overlaps. Full CORE/native/remote CI NOT_RUN:no CORE/Unity change.
Current Claude V3inspection stopped PARTIAL by director;CP01–05bounded closures retained,CP06held.
Delivery check compares440original packet files against its manifest:no unexpected changes,
including byte-identical prior F21runtime/docs,RS-DOC-005archives/README and authorities.
UTF8/fences/local links/feedback text preservation and git diff --check PASS. Progress docs agree.
No commit/push/agents/live provider call. New work is local accepted only.
