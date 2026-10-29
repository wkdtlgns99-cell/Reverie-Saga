# QT-F59 — Supply-prioritized NPC passage support

Status:LOCAL_ACCEPTED2026-10-26. Self-review,not independent acceptance.
[Order](../work_orders/QT-F59_NPC_SUPPLY_AID.md) owns scope/threshold/order/acceptance.
Primary2internal calculation;related3binding,5display,6save,7integration.

The new explicit npc_supply_aid variant requires the NPC's directly heard acceptance,
no heard completion report,and actual prior POST_TICK barrier stock>=2before the
existing gate owner opens the passage. Same-barrier preparation cannot satisfy readiness;
ordinary consumption may leave1after a valid opening at10. This is readiness,no stock
payment. The cycle owner,4/10timing,existing gate delta/fact/cue,reward and memory rules
remain unchanged. One canonical SUPPORT_STOCK_MIN,no inference from tick/counter/cache.

Ordinary ClientSession/Worker/Tk/binary pipe/Unity attach/load/reconnect and isolated
activity/recollection replay all retain exact selection. New feature identity and
separate Unity default save path reject cross-mode loads unchanged. Four previous
schema/rule byte pairs are exact. No component/payload/IPC/save-envelope/migration,
queued event,LLM,dependency,agent or publication was added. The new Korean mode label
states the two-item readiness condition;the board/messages show committed facts.

## Python and reviewed-source evidence

Selection baseline3FAIL0.69s. After selection-only wiring,real saved-source behavior
3FAIL2.82s demonstrates the premature4second opening;the actual threshold repairs it.
New3plus old30aid cases33PASS40.70s. New22unit PASS0.42s after fixture15FAIL/7PASS0.78s:
canonical component order and actual EngineResult field corrected. Expanded integration
26PASS/2FAIL28.69s;the two expected-code mismatches corrected to source-defined
UNSUPPORTED_RULESET,same2PASS1.48s with bytes preserved. Additional2close/report barrier
casesPASS5.28s. New52distinct cases are also all included in the passing current full.
Real branches/restart/compaction/manual openings/one wake/readiness/report/talk windows,
long-vs-partition replay,quiet retry,actual SQL rollback and uncertain durability,
invalid exact flags before allocation,and actual worker/Tk/framed callers are covered.
No domain outcomes are mocked;faults affect only the actual IO boundary.

Ruff both/format20/strict220/import3+1/pip PASS;exact CI31PASS11.22s.
Initial7test-type errors and subsequent5remain preserved in first/second logs. A repair
script's3of5pattern guard stopped before writing those sites/G07scope;the corrected
script bound the actual5. No production type suppression or weakened check. The shell
continued after that preparation error;later launchers explicitly stop on nonzero exit.

Current full2491PASS1398.93s,one invocation(session7067terminal0),all249frozen inputs
and current real index preserved throughout. JUnit confirms2491/no failures/errors/
skips and all52new cases. One existing record_property/xunit2metadata warning is
retained;no pytest/JUnit setting or test was changed to hide it. Final README adds only
usage documentation after the full;remaining248inputs and all runtime/test inputs stay
exact,with fresh document qualification. This is a current full,not relabeled F57proof.

[Reviewed G07scope](../work_orders/QT-F59_REPLAY_SCOPE.json):only encounter source hash,
six existing public ranges and one generator first_line refreshed after actual diff/
source review. All35public obligations,8sources/8nodes,29other members and4nested code
identities remain;tool/assessor/CI/goldens/coverage criteria unchanged. The full uses an
owned private index/object directory for the reviewed encounter blob,not real staging.
The full's real index10fae70a was byte-exact throughout that invocation. A final
historical byte guard later failed:current index0e05744b differs after full/native
cleanup. Real staged delta remains empty and HEAD72c2d58unchanged;logical index entries
match HEAD,with only the deliberately reviewed encounter blob differing from the
private evidence index. Exact writer/cause is UNVERIFIED(cache/stat refresh plausible).
Do not claim final historical byte equality. Original failed guard/script and both
hashes are retained in index-observation.json. No real staging/reset/index restore;
further reads use GIT_OPTIONAL_LOCKS=0. Current staged-entry hash is independently bound.


## Native,build and actual sources

Reused editor28252with its original2026-10-26 14:08:52creation;zero new editor launch.
Installed Python3.13.12/Tk8.6/Unity6000.3.25f1 reused,no install/security/license change.
Fresh supply1=65,old aid1=63,cycle1=153and two invalid-selection cases3+3:287PASS0FAIL.
Each stage starts once and has actual PASSED/result0/retained0/idle0. New native flow
checks2/4/6/8closed,10open/finalstock1,12prepare-without-early-open,14reopening,real
ordinary-talk rows10/14,slot rewind/reconnect,report/reward once and ready-but-stopped
support at36. Gate GameObject,state and query/retry/source preservation agree.
Actual642x456new open/return/completed and old cycle-return captures were inspected.
The initial desktop was occluded by other apps;it is not unobstructed/manual UX proof.

All17current managed sources(4supply+4aid+9cycle) validate/replay/query and independently
recovered GateAssisted facts PASS. Fresh copies qualify current-talk supply/assistance
windows and quiet retry/committed bytes;all originals remain byte-exact.
Readback talk mean0.832055s,max1.342226s(short native sources).
Fresh Windows build89,491,744bytes:
`tmp/unity-builds/52200bb5592942c3b72876bcfdd52d8a/ReverieSaga.exe`.
Actual PE metadata confirms PlayRoom present and LiveVerification,
get_GateOpenForVerification,IsolatePhysicalInputForVerification absent.
DLL SHA256:e3d1b91c767de250f9165e14798a44416e35ff1e0f2023ec357596e0ab66ec7c.
No standalone launch/release acceptance is claimed.

An initial activation observation timed out;the same editor/stage was observed,never
restarted. Later activation succeeded. To restore while the desktop may be occluded,
the existing owned temporary Editor harness gained a public OpenScene cleanup branch.
It rejects a dirty scene,restores original bytes,opens the actual path and checks
clean state/root count1/SHA. The already-consumed build1remained selected until a new
compiled READY marker was observed;the early readiness guard performed no stage write.
Then restore1ran once. No production/oracle/CORE source was changed for cleanup.
Original scene SHA3157e6272f93a108ce80848f9d1352fdaa15f3ecae3e750e525763818b011b94,
actual active path/root1/hash confirmed by the public Editor API. All159native inputs
preserved;exact trigger/meta/stage removed. The later screen observation was stopped
by the human's physical Escape. Post-cleanup desktop observation is UNVERIFIED;the
independently proven API reload/disk restoration are not screen proof. No further
Computer Use calls/native relaunch occurred after that stop;authorized headless work
continued on the active goal. No repeat permission question was sent.

## Actual current-host performance

Three fresh direct samples and one actual framed sequence per source:
talk → activity → quiet retry → wait16 → activity → quiet retry. Exact normalized
updates/core/protocol and source bytes match across direct samples and actual transport;
only attachment/path identity is normalized. Same independent actual-help anchors and
supply deltas are checked. This is not a pre/post optimization comparison:different
mode histories/pins have different legitimate facts.

| Source | Direct talk median(s) | Actual framed talk(s) | Framed wait16(s) |
|---|---:|---:|---:|
| short-supply | 0.340024 | 0.335430 | 0.130412 |
| long-supply | 1.829589 | 1.542033 | 0.154271 |
| long-old-aid | 2.059624 | 1.766838 | 0.164679 |

New long-supply direct talk1.763–1.853s;post-wait activity1.737–1.873s. Old aid direct
talk median2.060/max2.078s and post-wait activity median2.012/max2.056s still exceed the
2sTARGET. All accepted measured operations are below10sdeadline. Long-history2s/MIN-SPEC/
whole-device/whole-job-peak qualification remains OPEN;no universal performance claim.

The first measurement's nested immutable wire update failed standard JSON metadata
encoding after the owned short copy reached26. It is a measurement-writer error,not
production failure. Original script/log/committed copy/hash are retained,its timings
LOST/not counted. Canonical JSON conversion fixes metadata only;the accepted samples
use explicitly named fresh measurements-v2copies. No commands were replayed on the
failed committed copy,which remains byte-exact. Full/native were not rerun for it.

## Delivery

Self-review confirms actual prior-barrier reads,sole writers,strict selected-source
validation,current committed talk windows,real registered callers and durable failure
truth. No test/environment-specific production branch. Scope67paths/44prior non-scope
paths preserved. Final document/scope/UTF8/links/whitespace evidence is in delivery.json.
Earlier failures,previous orders/receipts and user sources remain preserved. All F59jobs
terminal;no duplicate full/native stages. Goal ACTIVE;next bounded authorized file/Python
work may proceed while Computer Use remains stopped. CP06held,D2/independent patch
rereview/long-talk target OPEN. Local only,no commit/push/PR/merge/release/agents.
