# CP03 — Verified Feedback and Repair Dispositions

Date:2026-10-13 | State:DONE for actual feedback/verified dispositions/scoped repair acceptance
Actual [feedback](RS-REVIEW-CP03_FEEDBACK.txt) is a static subset review:contract/receipt/domain/
app/engines/key tests and orchestration call-site grep. Reviewer did not run tests/Unity,read all
orchestration line by line,or inspect generated C#/Unity. Preserve these limits;no full independent
audit,external patch rereview or runtime execution claim. Original witness/ZIP remain unchanged.

| ID | Verified disposition / bounded action |
|---|---|
| F1 | CONFIRMED latent boot-validation gap. Constructor-skipping extensions fall back to LEGACY;nonlegacy descriptors originally allowed registration. Reproduced two missing expected boot errors. RegisteredStateIO now checks every typed ScenarioConsumer among engines,read-adapter delegates,command/delta/patch routes,presenters,payload/component codecs and checkpoint against the complete pinned definition before registration. Explicit INVALID_SCENARIO_BINDING,not assert. Comparing immutable canonical values rather than Python identity uses the existing rules document as authority and accepts equivalent frozen copies;legacy descriptors and extensions remain compatible. Nine constituent categories tested. No demonstrated wrong-world commit is inferred. |
| F2 | CONFIRMED bootstrap/pin mismatch. Default spec0+grove pin6 originally succeeded. Nonlegacy spec.initial_cell must now equal selected initial_cell;INVALID_INITIAL_STATE/SCENARIO_INITIAL_CELL before world creation. Client's correct selected start remains unchanged;legacy bootstrap overrides remain compatible. No save-format/pin migration. |
| F3 | CONFIRMED hard-coded wait name;optional legacy names are intentional compatibility. Added explicit selected actor_id in the live client caller and mapped wait name;standalone legacy defaults preserved. Custom traveler name tested against actual wait publication. Making names mandatory would break supported standalone/legacy callers without improving current live selection. |
| F4 | CONFIRMED exact-type constructor inconsistency. Frozen EncounterActions/Movement __post_init__ rejects None/subclass layout as SCENARIO_TYPE;typed scenario_layout property supplies boot guard. Other consumers retain existing exact-type validation. |
| F5 | INTENTIONAL display fallback. Programmatic layouts support lexical-role and noncentral-door tests outside the three CLI choices. Generic name affects no state/pins/selection. Keep fallback;test it with SQLite load/resume. Unknown CLI selector already rejects SCENARIO_SELECTION;no silent world reinterpretation. |

## Additional Test Gaps

Added56cases in tests/integration/test_cp03_repairs.py:all nine binding categories;constructor-
skipping legacy compatibility;default-grove mismatch;engine None/subclass;selected wait name;
legacy gate/NPC/actor rejection on both samples with exact diagnostic and unchanged CORE/protocol;
legacy↔harbor/grove resume/load preservation;bool/float/list across all four cells and walls;
oversize identities across all seven roles/IDs;real SQLite recovery with committed/uncommitted
uncertainty and unreadable proof on both samples;lexical role swap through save/load/resume.
Existing12scenario cases and all legacy goldens remain. No domain-outcome mocks.

Initial reproducer6FAIL1PASS0.96s→7PASS0.39s after source repair. Expanded test harness initially
left the noncommitting fault port armed for the follow-up normal command:2FAIL54PASS6.28s.
Restored the real store after recovery to test normal continuation and asserted COMMITTED,tick1,
reply1 and no repeated fault-port persist;production code was not changed to hide these failures.
Final focused133PASS38.46s;Ruff shared/selective,mypy107,imports3+1 PASS. Full/native acceptance
pending;record completion below only after actual required checks.

## Final Repair Acceptance

Full pytest with `--basetemp .pytest_cache/cp03-full-final --junitxml tmp/cp03-full-final.xml`:
exit0,1360PASS321.92s. Shared/selective Ruff,format16,strict mypy107,imports3+1 and
document/scope/hash checks PASS. Repair source scope:six existing Python files plus new56case test
module;old save/turn driver/pins/goldens/content/dependencies/CI and original review witness/ZIP untouched.

Current-source Unity runs under tmp/cp03-native:harbor11,grove11,legacy24,corrupt1 checks PASS,
all four editor exits0 and ENGINE_VERIFY_PASSED. Legacy Windows build89477040bytes PASS;
release verification hook ABSENT. Reused exact6000.3.25f1 editor/current-host license
success/active/signedIn=true. Raw logs/private saves remain ignored;repaired witness retains
sanitized views/checks/screenshot hashes. Editor-generated scene IDs restored to original clean
version after tests;no production scene change. Harbor120frames median1.660899ms/p952.124298ms;
grove120frames median1.676403ms/p952.1929ms. These are not release/device acceptance claims.

CP03 feedback/repair accepted for this first embedded segment. External review was the stated
static subset;patch external rereview NOT_RECEIVED,generated C#/Unity/orchestration full independent
inspection and new standalone/extracted-packet/remote CI qualification NOT_RUN or UNVERIFIED.
[Repaired witness](RS-REVIEW-CP03_REPAIR_INPUTS.json) and local
tmp/reviews/RS-REVIEW-CP03_REPAIRED_2026-10-13.zip preserve actual current inputs and acceptance.
Original witness SHA256 cee767ead9823af24dc512ab4f654996d448cd25f00da86b8a8e944e540b1002;
original ZIP SHA2564383eeeff280fe07ae0a27c46f1f430662e3e39145933ed239aa0cbc1c8a0d6b unchanged.

CP05 remains NOT_TRIGGERED:these are validation/presentation repairs under existing embedded
definitions and unchanged save format/compatibility pins. No new quest/memory mechanics,bulk
content,provider/agent/remote administration or publication. No automatic next task is authorized.
