# QT-F71 — Prepared native retained-call expectations repair

Status:LOCAL_SOURCE_ACCEPTED2026-10-27. Local self-review;not independent/native acceptance.
[Order](../work_orders/QT-F71_CALL_RETENTION_EXPECTATIONS.md). Primary7end-to-end verification
support;related2/5/6. This repairs verification source,not game behavior.

## Cause and repair

F68CallAidFlow assumed loading a prior slot at head8also reset its retained checkpoint
to8and removed call8. Actual SqliteSlots.export/stage_load use a full SQLite backup.
The restored branch retains checkpoint0/call8;later calls9,12,13make total4at13and call25
makes total5at25. Only displayed rows are capped at3. F70read-only probe of the actual
owned F68saved branch25already confirmed checkpoint0/5replies and original bytes preserved.

Only two CallAidFlow argument sites now expect totals4/5and the existing default0source.
CallAidActivity helper,PatrolFlow,Run dispatch and other flow bodies remain byte-exact.
The current Unity usage paragraph now explains ordinary backup versus checkpoint-only
clones. Historical F68receipt/order are preserved;this disposition supersedes their
incorrect prepared-source retention interpretation,not their actual Python row evidence.

Existing test_call_native_scenario.read_activity now asserts independently supplied
confirmed totals1/2/4/5and the exact checkpoint0aid heading at its four existing queries.
All old scenario checks remain,including state/gate/cell,stock/preparation/use counts,
actual ordered calls/aid rows,retry quietness,prior preview,separate load,reconnect,
source-file bytes,retained conversation2,reward1and report25support suppression. Both
actual ClientSession and real framed child execute the full scenario;no mocked domain result.

## Actual qualification

- Entry:119F70delivery hashes verified;HEAD72c2d58/branch codex/cycle-call-recall-20261024,
  actual index0e05744b90eb694a97901c60b41da40dcc2bd4b8e63c0b36268559fe37b82574,
  staged empty;baseline and entry.json preserved in tmp/qtf71.
- Independent prepared-source oracle:before2mismatches/exit1,after0/exit0;both retained.
- Current affected tests/integration/test_call_native_scenario.py,test_npc_call_aid.py,
  test_call_support_plan.py:37PASS37.74s(wrapper38.22s),JUnit zero failures/errors/skips.
  Direct and real-pipe scenario both included. Job27085terminal0,all240check inputs preserved.
- Current README Ruffboth/format44/strict240PASS. Production Python110files unchanged;
  source test's other ASTexact after removing only declared total argument and two added
  assertions. Native exactly2declared call-site changes;other source unchanged.
- F70check input240has239unchanged and only the test-oracle delta. Reuse unchanged
  import3+1/pip and CI31inputs/results;document10is rerun after final current docs. F69full
  2803evidence has278of281unchanged inputs and3deltas:the native verifier,F70app presentation,
  this test oracle. No new whole regression or native success claim.
- First source-audit script expected2F69full deltas but the actual frozen inventory also
  includes LiveVerification.cs. Corrected to3with exact actual delta list;initial AssertionError
  and explanation retained. No product/test change or weakened criterion resulted.
- Final scope,prior non-scope paths,all production hashes,logical/byte index,scene,UTF8,
  local links,whitespace,diff check and document result:tmp/qtf71/delivery.json.

## Limits and continuation

Fresh C#compile/native/render/capture/Windows build NOT_RUN AWAY-001,Computer Use STOPPED.
The corrected source and Python scenario do not qualify native execution. F70short/long
runtime evidence remains historical unchanged-production evidence,not a new timing/native
claim. CP06held,D2/independent rereview/global2s/MIN-SPEC/standalone/release OPEN.
No new question,agent,publication,dependency or timed wake. Original unfinished goal ACTIVE;
continue the next bounded useful authorized NPC/world task after entry/usage/source checks.
