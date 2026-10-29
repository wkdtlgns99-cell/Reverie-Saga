# QT-F54 — NPC passage assistance execution

Order:[gate assistance](../work_orders/QT-F54_NPC_GATE_ASSISTANCE.md).
Status:LOCAL_ACCEPTED2026-10-25. Primary2internal calculation;related3/5/6/7.
Baseline72c2d58plus22accepted F49–53dirty paths;entry hashes under tmp/qtf54/entry.json.
Self-review only;CP06held,earlier independent patch rereview deferred. Local only.

## Implemented path

Explicit npc_aid/--npc-aid/REVERIE_UNITY_NPC_AID selects quest.harbor-cycle-aid-v1 on top
of the existing cycle mode. Existing state components/save envelope and supply rules are
unchanged. encounter.actions remains sole gate writer and receives its optional POST_TICK
activation from the existing two-second NpcActed wake. It reads its own NPC's directly heard
acceptance/report through registered memory views,opens a closed gate while awaiting the
report,and records the actual source-bound GateAssisted fact. No new timer/pending event.

Ordinary ClientSession/Worker/Tk/binary bridge,cycle isolated replay and Unity selection/
separate default save path are wired. New payload codecs are strict;the ordinary board
uses committed gate state and the Korean NPC opening message uses the actual fact.

## Real failures and repairs so far

- Initial compose used incorrect FieldFamily attribute names;corrected to canonical family
  equality. First compile rejected unsorted multi-subscriber pinned policies;sorting the
  descriptor's subscribers matches canonical event policy serialization. Logs retained.
- Initial unit checks incorrectly expected SchemaError from exact_fields(which raises
  ValueError),used the approved-catalog pin with a different unit content fixture,and
  compared separately constructed codec instances by identity. Corrected the precise error
  oracle,derived the unit fixture's frozen pin from actual HEAD source under tmp,and compare
  unchanged component schema identities. No existing tests/goldens altered.
- Initial real integration reproduced a postcommit projection failure for same-tick player
  close then NPC reopen:old EncounterPresenter required every gate fact's intermediate
  endpoint to equal final state. The variant now validates the actual ordered gate chain
  against the final committed endpoint and preserves the player/NPC intermediate cues.
  It also handles an earlier blocked-door move before a later NPC opening. Old-mode
  presenter behavior is unchanged;no fake read view or suppressed failure. Original
  new-first.log retains50PASS/1FAIL. Subsequent51PASS29.59s,then expanded57PASS33.77s.
- Strict types initially found two test narrowing/comparison errors;fixed the test code.
  Final strict213source files PASS;both Ruff configurations PASS. No blanket suppressions.

## Current evidence and outstanding acceptance

57new unit/integration cases PASS,including malformed wake/codec/selection,exact promise,
time boundary/no-op,partition equivalence,supply isolation,canonical replay,compacted accepted
checkpoint,real rollback/uncertain COMMIT,retry,old pins,previous-slot clone/restart,source
preservation,real pipe and withdrawn Tk callers. Five forged/incomplete gate chains and the
blocked-move/open projection are included. Original logs remain under tmp/qtf54/.

The added same-barrier report boundary is also qualified:report14and an in-flight aid
opening share the POST_TICK barrier;close15then wake16does not reopen. During adding this
test,a misplaced patch initially left the compact-checkpoint continuation in the new test
and raised NameError after its actual assertions. Restored both complete test bodies and
reran both:2PASS6.76s. This was a test-edit error;original log retained.

## Full regression and current-source requalification

Initial full2346cases:2267PASS/3FAIL/76setup ERROR in1428.11s(full.log). The76errors share
the manual G07fixture's intentional STALE_INPUT rejection of the changed encounter source.
Reviewed the existing6encounter public members and the new exact manifest read-tuple
generator;updated only their current source hash/ranges/nested identity in the runtime
inventory. All35obligations/8sources/8nodes,other29member rows,tool code/rejection checks
and historical authoring scopes preserved. The count oracle changes3→4for that explicitly
reviewed static generator. [Current source review](../work_orders/QT-F54_REPLAY_SCOPE.json).
The original8contexts prove public-body reachability,not the new optional aid branch.

The other3failures were unchanged checkout-index tests:the real index still held old
uncommitted encounter bytes while the reviewed working inventory was current. A private
index and private object directory under tmp/qtf54contain HEAD plus the exact current
encounter source,with the real object store read-only as an alternate. Original false/true/
input autocrlf cases3PASS0.80s. Real index SHA256remains unchanged;no actual staging,
commit,reference update or publication. This qualifies prospective current-source Git
bytes and is not a claim that the unpublished real index or remote CI has passed.

Requalification of the whole affected G07module and the current58new aid cases:
168PASS419.59s(requalification.log). Its actual native Python coverage child independently
ran8replays PASS100.50s with the pinned PyTracer and all35positive public bodies. This is
Python replay qualification,not Unity verification. No negative check was removed/skipped.

Current collection2347,including one new report14case. Name-set closure plus230unchanged
frozen inputs and an AST comparison proving all prior aid tests unchanged establish
2347distinct qualified cases across the original full run and explicit reruns. Not one
clean single full invocation:original failures remain truthful. See python-qualification.json,
regression-lineage.json and qualification.py. Exact current CI boundary12node selection
expanded to31PASS16.33s. The first ad-hoc selector script incorrectly expected13nodes;
it stopped before tests,was corrected against the actual workflow,and its log is retained.

Both Ruff configurations,strict213files,imports3+1,pip and14scoped format files PASS.
Existing orchestration/encounter.py remains in its established style instead of reformatting
the entire facade;HEAD already fails whole-file formatting(legacy-format-baseline.log).
No former README/CIformat target or configured rule was removed or weakened.
All three prior memory/work/cycle pin sets remain byte-identical(compatibility.log).

## Measured current feature and remaining native work

One actual sample per operation,current host with concurrent gameplay:talk2=0.263414s,
NPC open4=0.088263s,read-only activity4=0.235496s,reopen6=0.078967s,return talk7=0.405231s.
All committed/query outcomes and query source-byte guards verified(latency.json).
These short samples meet2second TARGET;no Unity transport,distribution,MIN-SPEC or
long-history performance acceptance follows. F53's2second overrun remains OPEN.

Native159input manifest and exact original scene snapshot prepared. Installed editor
6000.3.25.14801824exists;current window inventory exposes no Unity editor. A game window
is active,and the director's Unity timing preference is pending after the earlier crash
concern. No Unity launched or UI input sent this task. Owned F54VerificationTrigger is
prepared under tmp only,not installed into Assets;no automatic run is armed.

Native aid/old-cycle/invalid-selection modes,actual screen,owned save readbacks,Windows
build and final delivery remain NOT_RUN/UNVERIFIED. Feature remains IN_PROGRESS;do not
claim local acceptance or advance a new feature before these criteria are met. Goal
actually confirmed ACTIVE after the director resumed it. CP06held;no agents/publication.

## Editor-free C# qualification while native timing is pending

Current-device process inspection confirmed a running game and no Unity editor;no process
was terminated or UI input sent. Reused the installed Unity NetCoreRuntime and Roslyn
4.3.1-3.22526.13(41a5af9d),with the project's actual cached editor/player/editor-tool
response files. Preserved defines,language9,reference assemblies,source generators,
analyzers and existing warning policy. Only output/ref-output paths moved to owned tmp;
editor-tool compilation additionally references the freshly compiled editor client and
an owned copy of the prepared F54trigger. Original response files unchanged.

- Client editor profile:PASS2.502051s,228reference/analyzer/additional inputs.
- Client nondevelopment player profile:PASS1.202135s,174inputs.
- Editor tools plus prepared trigger:PASS1.164906s,268inputs.

All159native source/package/settings inputs and the original scene remain unchanged.
Actual compiler/host/response/dependency/output hashes and logs are bound in
tmp/qtf54/csharp/result.json. No Unity editor/player was started,and client assemblies
were not executed. The trigger remains outside Assets and no stage is armed.

An owned small metadata reader uses the installed Unity Mono/Cecil0.11.1to inspect the
fresh DLLs without executing their code. Editor DLL contains LiveVerification and the
GateOpenForVerification observer;nondevelopment player DLL excludes both,while retaining
the ordinary NpcAidEnabled property. Editor-tool DLL contains PlaytestBuild and the exact
prepared F54VerificationTrigger. All3metadata checks PASS(metadata-result.json).

This is supporting5/7compilation and conditional-code qualification,not native gameplay,
asset import,screen input,Windows player build or release acceptance. Those original
criteria remain pending;do not substitute this evidence for them. Python passes reused
for unchanged inputs,without another full regression. Automatic goal remains ACTIVE.

## Source-readback tool preparation

Prepared owned tmp/qtf54/readback_source.py for explicit selected saves and fresh isolated
continuations. It validates the selected mode pins,replays the retained segment,queries
activity,and checks a new ordinary talk's supply difference against the existing independent
closed-form counter oracle. Exact retry must commit no new facts or bytes. Original source
bytes are preserved. Lock databases and existing output directories are rejected;no glob
can turn zero saves into success. Native stage/log/save-count qualification remains separate.

Tool qualification used the existing Python-created aid source at7and the historical F52
cycle source at30,not new F54native evidence. Both replay/activity/new-talk/retry/source
guards PASS. New talks at8and32reported1/0and6/3prepared/used;talk0.480/0.666s are tool
probe samples only. Wrong aid selection rejects UNSUPPORTED_RULESET before creating an
output directory and preserves source bytes. Native159inputs and original scene unchanged.
Evidence:tmp/qtf54/readback-tool/qualification.json and its two final result.json files.

Initial tool probes exposed two helper assumptions:retry status was incorrectly expected
to be RETRY instead of COMMITTED,and approach routing required the NPC cell instead of
the actual adjacent talk range. Corrected only the tool and reran both representatives
with fresh output directories;earlier probe outputs remain. No production input changed.
All required native F54flows/screen/build criteria remain NOT_RUN,not accepted by this tool.

## Native timing dependency / automatic goal blocked

After independent preparation completed,the same timing dependency persisted across three
consecutive goal turns. Previous turn was a verified wait on live Sephiria30764for45.023s;
current permitted read-only process query again found that process and no Unity editor.
Its actual45.025s WaitForExit returned false,session58178terminal0. No new timing answer
arrived. No game/editor process was closed or UI input sent. Pending native flow/screens/
saves/build cannot be accepted from the compiler or historical readbacks.

update_goal(status=blocked)returned BLOCKED. This is an execution dependency,not feature
completion or a user-requested pause. No game-exit watcher or scheduled wake-up is armed.
Explicit resume must revalidate current processes/timing and goal state before launching
one editor and continuing the prepared native stages. All production inputs remain frozen.

## Native acceptance after director timing choice

Director answered "지금 Unity 검증도 진행". Fresh window inventory then exposed no Unity
editor or Sephiria game window. Reused installed6000.3.25f1,started one editor36260at
16:57:46KST,and retained/reused it throughout. Actual goal later returned ACTIVE;the prior
blocked state is superseded. No game/Steam process was terminated and no other app was
controlled. [Computer Use skill](C:/Users/wkdtl/.codex/plugins/cache/openai-bundled/computer-use/26.1016.62342/skills/computer-use/SKILL.md)
was used for editor observation/input only. No new dependency,license or security change.

| Fresh native stage | PASS | FAIL | Evidence |
|---|---:|---:|---|
| aid1 |36|0|Actual next-wake opening,blocked move before opening,visible gate GameObject,odd/even closes,retry,previous-slot rewind,reconnect,replayed activity,combat/report and no later reopening |
| cycle1 |153|0|Unchanged prior mode,stock/memories/calls,read-only queries,opaque panels,history reading position,slots and recovery |
| invalid-aid |3|0|Missing cycle prerequisite rejects before working save allocation |
| invalid-aid-selection |3|0|Invalid environment value rejects before working save allocation |

All four stages independently contain ENGINE_VERIFY_PASSED,RESULT0,RETAINED0and IDLE0.
Total195PASS0FAIL;native-stages.json and unity.log retain exact stage boundaries. The
owned temporary trigger was adjusted to keep watching explicit new stage names,with
SessionState preventing duplicate runs. Editing that owned trigger during the first import
caused a worker modification-time Import Error Code4;an explicit Refresh reimported and
compiled it successfully. This transient tool/import failure remains in the original log;
it is not a gameplay failure or a hidden restart. No production source changed.

Inspected actual642x500engine captures npc-gate-aid-open/completed.png:the first contains
the blocked-door message followed by the factual NPC-opening message;the completed source
shows later retained NPC activity. Registered checks independently observe the actual gate
GameObject and mode label,including loaded closed/open states. Desktop observation was
partly occluded by the director's video window. A separate fresh manual1probe accepted a
real S key,committed move0→3at tick1,and was stopped with Ctrl+P. One coordinate button
probe committed no action;do not claim manual button or unobstructed desktop acceptance.
The video was not moved/closed. This extra probe does not replace the four native stages.

All13exact managed native saves(4aid+9cycle,excluding lock databases)validate/replay/query
and preserve original bytes. Fresh isolated continuations verify new ordinary talk supply
deltas and exact quiet retry. Aid source ticks8/8/30/30have gate open/open/closed/closed;
their talks at9or31report2/0or2/2prepared/used. Current/previous slots and loaded working
branches retain the selected variant. Mean talk0.926417s,max1.395317s over13probes;these
current-host short samples do not close F53long-history latency or MIN-SPEC qualification.
readback-{aid1,cycle1}.json/log and native-readback/ retain sources/results. The extra
manual1working save is separate from the13automated acceptance sources.

Same-editor fresh Windows build PASS89,491,232bytes at
tmp/unity-builds/c89664a1a6a74aa5a89f873f1e3ddccf/ReverieSaga.exe. Actual BuildPipeline
success and RELEASE_VERIFICATION_HOOK_ABSENT recorded;independent Cecil inspection of
that built client DLL confirms ordinary NpcAidEnabled retained and LiveVerification/
GateOpenForVerification absent(build-metadata.log,build-result.json). No standalone
launch,release approval or public distribution is claimed;CP06remains held.

Disarmed/deleted only the owned stage/Editor trigger and its meta,retaining exact trigger
copies under tmp. Restored original PlayRoom.unity byte-exact and accepted Reload in the
editor;all159native input hashes match entry. Editor36260remains open,idle,out of Play
mode;no second editor or stage is armed. Python production inputs remain frozen,so earlier
2347distinct qualifications/static checks remain applicable without another full run.

Self-review rechecked actual source/callers:one gate writer,prior-barrier direct memory,
strict codecs,pins,read consumers,presenter chain ordering and final endpoint,all public
client/retrieval selections and conditional player exclusions. Canonical read_record
validates accepted/report order before the engine uses the single-entry accepted state;
no unreported defeat inference,additional authoritative cache or pending event was added.
Final root progress trio/order synchronized;final document/scope receipts under tmp/qtf54.
Local acceptance only;no commit/push/PR/merge/agent/release. D2and deferred independent patch
rereview remain open. Automatic goal remains ACTIVE for the next authorized bounded work.
