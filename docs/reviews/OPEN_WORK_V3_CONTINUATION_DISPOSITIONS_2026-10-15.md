# V3 Continuation — Findings and Repair Evidence

Date:2026-10-15 | State:CONTINUATION_RECEIVED_FULL_REVIEW_INCOMPLETE.
Source:[verbatim director-supplied continuation](OPEN_WORK_V3_CONTINUATION_FEEDBACK_2026-10-15.txt).
FeedbackSHA256 ae16945de827b5c266668037add0e6d00660678e0677751e38ffe5633b76cc85.
Review target3159c92251afc61cd3d30e5156020adac4937c5d;[first review](OPEN_WORK_V3_DISPOSITIONS_2026-10-15.md).
Order:[bounded follow-up](../work_orders/OPEN_WORK_V3_FOLLOWUP_2026-10-15.md).
Reviewer verdict PASS_WITH_CORRECTIONS only for actual inspected scope. Sol checks below are
executor validation,not an expansion of independent coverage. Primary7support;related6/4.

## Reviewer execution / inspected scope

Reviewer replaces inconsistent first counts:earlier Linux3.12.3/noTk1620passed/55excluded.
Continuation reports LinuxCPython3.13.12/Tk9.0/Xvfb,1675collected/1674passed/1failed/0errors/
0skipped,534.2s;folder counts1207integration+275unit+83governance+58replay+52adapters sum1675.
These are external reports,no raw JUnit supplied here. Scratch proposed F1repair reportedly passes;
original packet unchanged. Pinned versions installed without lock hash enforcement because Linux
wheels differed;do not portray this as the qualified hash-pinned Windows/Tk8.6 environment.
Ruff/shared+selective/scoped12format/imports3+1 PASS reported;Linuxmypy4Windows-only test constant
errors,win32-targeted mypy157PASS reported. No native Windows/Unity/live Gemini execution.

Inspected:quest/memory engines/domain/reducers,partial watch/serialization/turn,quest registry/
definitions/scenarios;complete Gemini transport/generation/budget,approved content hash bindings;
complete BrainConnection/PlaytestBuild,selected PlayRoom/bridge/session/worker and C#guards;
CP03/05dispositions and named repair code. Test execution does not establish body inspection.

## Findings / dispositions

| ID | Verification / classification | Disposition |
|---|---|---|
| F1 P3 test metadata portability | Existing test passes Windows3.13.12 but injects Windows-only st_file_attributes into stat_result on POSIX. External Linux3.13failure is consistent with platform-specific constructor fields. Production hardlink guard not implicated. Native probe shows unconditional omission on Windows produces attrs=None;real scratch proposed change FAILS with TypeError at reparse-bit check before hardlink validation | REPAIRED_TEST_ONLY:include extra metadata iff actual stat exposes the attribute;retain all native fields and force only st_nlink=2. Tighten exact INVALID_PATH hardlink diagnostic;retain unpatched save reopen/tick0. Windows save-slot module29PASS14.19s;native Linux repaired execution NOT_RUN locally |
| F2 P3 typed client error | Duplicate first V3-N1 maintenance note;reviewer explicitly says correct today | DEFERRED_NONBLOCKING,existing boundary-contract follow-up;no runtime change |
| F3 P3 reconciliation lock contention | Offline actual GenerationBudget OS-lock probe now reproduces post-response GENERATION_BUDGET_UNAVAILABLE:1stub response/0APIcalls,reservation20000retained/unsettled,no approved output. Uses fresh isolated test profile,not user accounting | CONFIRMED_AVAILABILITY_LIMITATION_NONBLOCKING:accounting stays conservative,job fails explicitly. Bounded reconcile retry/retaining returned response needs settled error/publication semantics and lock-duration contract;record next provider-budget follow-up. No extra send,ledger reset or policy change silently introduced |
| F4 P4 response growth | Whole narratives repeated and write_frame capacity exception outside request handler confirmed in source. Current CLI narrative loader caps admitted catalog64KiB,below1MiBframe;normal current oversize response not demonstrated | CONDITIONAL_EXTENSION_RISK:reassess whole-frame sizing/failure projection before catalog/protocol expansion;not a proved current normal-input defect or permission to weaken frame limits |
| F5 P4 cold-start deadline | BrainConnection Stopwatch begins at construction and awaiting deadline is10s;no slow-start/native reproduction supplied | UNVERIFIED_NONBLOCKING:retain D7cold-start/device measurement need before changing deadline/handshake semantics. Prior native checks are not minimum-spec latency proof |
| F6 P4 colocated preset pin | Expected dev-preset consistency check,not authenticity/trust-root claim;actual approval/catalog hashes match | INTENTIONAL_NO_CHANGE;no production signing/security claim |
| CP03-F1 missing undeclared consumer role | Reviewer raises extension hypothesis without wrong-world commit/reproducer;typed declared-consumer checks and built-in inheritance inspected only partly | UNVERIFIED_EXTENSION_RISK:verify generic versus scenario-dependent consumer obligations and9category tests before proposing mandatory-role semantics. Do not equate unmarked generic consumers with a proved wrong-world commit |
| CP03-F3 wait narration | Reviewer did not inspect actual application of selected name | STILL_NOT_INDEPENDENTLY_VERIFIED;first-party passing tests cannot fill this independent inspection gap |
| Budget directory fsync P4 | Reviewer notes absent directory fsync after replace,without crash repro/new contract | UNVERIFIED_DURABILITY_NOTE under future provider-accounting contract;not proof of under-accounting,do not silently add platform-specific durability guarantees |

## Actual local repair and checks

Only tests/integration/test_save_slots.py changed:conditional stat_result extra fields plus a more
specific rejection assertion. No test deletion/skip/xfail,production guard/formula/golden/schema/
budget/provider/C#/permission/dependency change. Worktree already had first-review document edits;
those were preserved. Original test/production hashes and dirty inventory recorded in
tmp/v3-continuation-20261015/entry.json. Current raw review preserved byte-for-byte.

Observed native proposed unconditional removal in isolated scratch:1FAIL0.68s,TypeError at
sqlite_store.safe_path(None & FILE_ATTRIBUTE_REPARSE_POINT). Correct conditional repair:whole
save-slot module29PASS14.19s. Whole-suite rerun not required for this test-only fixture edit;
prior local/remote1675PASS apply to published3159c92,not a new full run of the repair.
Shared/selective Ruff PASS,strict mypy157PASS. Existing file's unscoped legacy formatting kept;
new hunk follows scoped style. Final exact target1PASS0.57s,both Ruff configs/strict mypy157PASS.
Linux repaired result remains NOT_RUN here;external Linux replay and independent patch rereview
remain separate from native Windows verification. No new platform/runtime install or live API.

## Coverage still missing — independent review must continue

1. Remaining engines:skeleton/trial/encounter and watch beyond first60lines;turn.py beyond first140;
   scheduler/read_views/persistence/replay/events/rng;golden vectors/fixtures;feature_registry,
   npc_memory application wiring and headless.
2. Dialogue approval path:app npc_prepare/dialogue_prepare/npc_memory_*/npc_dialogue_* modules,
   adapters/quest_dialogue,contracts/dialogue and npc_context;actual compile/approval path beyond hashes.
3. Unity/save boundary:LiveVerification,Wire.Generated,remaining PlayRoom rendering,Unity README/
   ProjectVersion;durable/save_slots/remaining sqlite_store/contracts/client. No native Unity claims.
4. CP03/05original feedback,repair orders,input manifests and most actual regression assertions;
   CP03-F3 selected wait narration remains unverified. Disposition-only reading is insufficient.
5. MASTER/v2.6authority documents and platform/hash-closure limits remain explicit.

This continuation improves coverage but does not finish V3. Next priority is complete authoritative
engines/turn/scheduler/read-view path,then remaining dialogue approval and durable/client code,
followed by original repair evidence/assertions. Keep CP01–05closed/CP06release held;no blanket
archive retirement or content/rights/billing/merge approval. No automatic next feature,provider/
reviewer call,agent or publication inferred from this feedback.
