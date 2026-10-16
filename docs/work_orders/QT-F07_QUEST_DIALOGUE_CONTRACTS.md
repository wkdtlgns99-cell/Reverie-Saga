# QT-F07 — First Quest and Gemini Dialogue Contracts

Date:2026-10-13 | State:CP05-CONTRACT PASS_WITH_CORRECTIONS;verified corrections accepted.
Authority:[MASTER](../MASTER_GAME_ARCHITECTURE.md) §§2–3,7–9;
[engineering prompt](../ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md) A3/A5/A14/C-02;
[order](QT-F07_QUEST_DIALOGUE.md). Director explicitly requests execution and selects Gemini free API.
This is a proposed first implementation contract,not evidence of an existing quest/provider feature.

## 1. Bounded Decision

Add one opt-in harbor quest using the current harbor layout/combat/watch behavior.
Brain decides acceptance,goal completion and one-time reward. Gemini generates a four-line
Korean dialogue bundle only during an explicit preparation job. An approved hash-pinned
bundle is selected locally during gameplay;simulation,retry,recovery and replay never call Gemini.
The first sample reward is a recorded favor token,not money,an inventory item or faction standing.
It has value1 only after quest completion;future spending/economy requires another contract.

Do not add live conversational inference,free-form player commands,NPC memory/personality engines,
world travel,procedural quests,bulk template reuse,save-format migration,provider billing changes,
new dependencies or a central developer relay. Use the currently qualified harbor name only;
the quest and lines are new content,not a port of unqualified Quilltale quest templates.

## 2. State / Internal Rules

NEW frozen exact-type `domain.quest.QuestDefinition(layout:Scenario,quest_id:str)` validates
structure/exact IDs only;it never imports app. An app.quest factory checks equality with the
harbor layout. The only accepted first app definition has layout equal to `select_scenario("harbor").layout`,
quest_id=`quest:harbor-sentinel`,giver=layout.npc_id,target=layout.enemy_id,
actor=layout.actor_id,space=layout.space_id,reward_id=`favor:harbor-watch`,reward_amount=1.
Reject a Scenario subclass,wrong layout or wrong/non-exact ID with `QUEST_DEFINITION`.
Keep all six original role IDs and geometry unchanged;quest activation changes feature pins.

NEW `QuestRecord(entity_id:EntityId,stage:int)` implements ComponentRecord;
schema=`TypeKey("quest.progress",1)`,entity_id=quest_id. Stage is exact int,not bool/float/subclass:
0=not accepted,1=active,2=goal met/report available,3=completed/reward granted.
Only `quest.rules` owns the `stage` family in RESOLVE and POST_TICK. Range0..3,scale1,
unit=`quest_stage`,CORE/tier A. Exactly one quest record is appended to the ten watch records.
No separate reward flag/wallet creates a partial multi-field state:reward amount is derived as
`1 if stage == 3 else 0`. Stage3 is the durable one-time grant receipt,not a client-side credit.

NEW `QuestTalkCommand(npc_id:EntityId)` schema=`quest.talk/v1`.
Admission order is actor→exact payload codec→actorHP/dead→target→space/range→duration/overflow.
Declare reads encounter.hp.hp,trial.position.cell/space_id,watch.npc.cell/space_id.
Admission validates command actor/target against the selected definition,actorHP>0,
same space and Manhattan distance<=1 from giver. Same cell is permitted because the existing NPC
is nonblocking. Wrong actor→UNAUTHORIZED_ACTOR;wrong target→INVALID_TARGET;
dead actor→ACTOR_DEFEATED;out-of-range→OUT_OF_RANGE. Rejection changes no tick/revision/record.
Invalid external payload shape/unknown fields/exact-type failures follow existing schema errors;
an impossible registered read/definition is a CandidateError,not a normal player rejection.
Valid talk takes exactly1second;overflow follows existing INTEGER_OVERFLOW behavior.

`QuestRules` has a RESOLVE action activation for quest.talk and a POST_TICK every-tick activation,
both tier A/wave0. It reads quest.stage,actor/target encounter.hp and required position/NPC families
through registered ReadPort keys;it never imports or calls engines.encounter/watch.
All referenced families add quest.rules/system.admission/presenter consumers only in the new bundle.
No new RNG stream,wall clock,network,mutable dialogue state or delayed event is used in this engine.

RESOLVE talk transitions:

| Before | After | Spoken intent | Reward |
|---|---|---|---|
| 0 | 1 | offer | 0 |
| 1 | 1 | reminder | 0 |
| 2 | 3 | completion | 1,exactly once |
| 3 | 3 | gratitude | no additional grant |

POST_TICK,after RESOLVE phase staging,is the objective observation point.
If stage1 and selected targetHP==0,change stage1→2 and emit GoalMet. Otherwise emit no goal change.
Pre-acceptance defeat is allowed:stage0 can coexist with targetHP0;first talk stages0→1 in RESOLVE
and1→2 in POST_TICK. It offers the quest and displays a separate factual report-available notice;
the next talk reports/completes. Talk never infers completion from model prose or client flags.
Cross-family invariants belong only to QuestRules POST_TICK and QuestCheckpointPolicy,never
the family-confined reducer/net validator. Stage1 requires targetHP>0 and stage2/3 require
targetHP0 in every accepted checkpoint. A living actor is not required to retain
previous progress,so existing defeat/save behavior is preserved. No resurrection/reset in this slice.

NEW `QuestStageDelta(entity_id,before_stage,after_stage)` and `QuestStagePatch(stage)` have
schemas quest.stage-delta/quest.stage-patch v1;target=quest.progress.stage. Allowed transitions
are0→1,1→2,2→3;identity1→1/3→3 produces no delta. Codec accepts exact range0..3 and strictly
increasing endpoints,including0→2 for persisted composed diffs. Reducer.stage accepts single
steps only and checks exact old value. compose validates each single step and contiguous endpoints;
compose/validate_net accept net set{0→1,0→2,1→2,2→3} only. No identity,downgrade,0→3/1→3 net
diff is valid. Net validation reads only quest.progress.stage. Patch validates range/identity;
turn staging enforces transitions and COMMIT atomicity,checkpoint enforces cross-family invariants.

Facts,all `record_only`/PRESENT,producer quest.rules,version1:
- `QuestAccepted(quest_id,actor_id,npc_id)` from0→1.
- `GoalMet(quest_id,target_id)` from1→2.
- `QuestCompleted(quest_id,actor_id,npc_id,reward_id,amount)` from2→3,amount exactly1.
- `QuestSpoken(quest_id,npc_id,intent)` on every valid talk;intent is one of the table's four strings.
No subscriber mutates state from these presentation facts. Register codecs with exact fields/types,
IDs and producer/scope validation. Existing encounter.defeated stays record_only with no subscriber:
turning that old fact into a simulation event would change existing event semantics/goldens.

Facts follow actual phase/rank/emission order;emit transition fact before QuestSpoken within
RESOLVE;GoalMet follows in POST_TICK. Read-only QuestPresenter validates receipt/fact endpoints
before emitting QuestCue(quest_id,npc_id,intent),schema quest.cue/v1. Goal notices and reward amount
are deterministic UI text drawn from committed facts. Spoken prose comes from the approved bundle.
If presentation fails after COMMIT,retain truthful committed state and expose PRESENTATION_FAILED.
An aborted/uncertain commit never displays a newly awarded token or a successful completion line.

## 3. Content Boundary / Approval

NEW frozen contracts.dialogue records:
`DialogueLine(intent:str,text_ko:str)` and
`QuestDialogue(quest_id:str,npc_id:EntityId,lines:tuple[DialogueLine,...])`.
Require exactly four distinct intents in canonical lexical order
completion,gratitude,offer,reminder. Text exact str,NFC,nonempty/no control characters,
UTF-8<=1024bytes per line;total candidate<=16KiB. No interpolation/executable markup.
Exact types are required throughout;duplicate/extra/missing intent→DIALOGUE_INTENTS;
wrong ID→DIALOGUE_BINDING;bad text→DIALOGUE_TEXT;unknown fields→existing exact-fields rejection.

Gemini output document has exactly format,quest_id,npc_id,lines;
format=`reverie-quest-dialogue-candidate/v1`;line objects have exactly intent,text_ko.
It cannot contain stage,reward,stats,commands,conditions,approval or save mutations.
Model schema conformance is insufficient:local decoder applies these checks independently.
Natural-language factual accuracy cannot be proven by JSON validation. Candidate remains
NEEDS_REVIEW until the director approves its exact hash and checks each intent's permitted claims.
Offer/reminder cannot claim a kill or granted reward;completion describes the actual single
favor grant;gratitude cannot promise another grant. Factual UI always supplies authoritative counts.

Candidate artifact metadata,kept separately from model output,has exact fields:
artifact_id=`dialogue:harbor-sentinel-v1`,provider,model,brief_sha256,output_sha256,
created_utc,validation_status,approval_status,usage. SHA256 fields are lowercase64hex.
provider=`gemini` only for a real API response;offline examples use provider=`codex-example`.
created_utc is ISO UTC;validation_status=VALIDATED/REJECTED;approval_status=NEEDS_REVIEW/APPROVED.
usage records attempts and prompt/output/total token counts as exact nonnegative ints or null
when provider metadata is missing;null means unknown,never zero. No key/raw private log is recorded.

Approval receipt exact fields artifact_id,output_sha256,brief_sha256,decision,approved_by,approved_utc;
decision=APPROVED and the exact two hashes are required for compilation. This local receipt is a
director-authorization record,not a cryptographic signature or permission a model can grant itself.
Changing bytes/brief invalidates approval. No auto-approved label from Gemini is accepted.

Trust boundary clarification (CP05 integration review2026-10-14):compilation compares the receipt's
output_sha256 to the exact raw candidate bytes,not their canonical JSON reencoding. The originating
brief is external provenance;compile checks its anchor's format but has no brief input to recompute
it. A director approving a different brief must issue a new exact receipt/pin. Runtime load checks
the externally selected trusted full catalog SHA256 and the bounded canonical schema;it cannot
authenticate reviewer identity or reconstruct original raw output/brief from the compiled catalog.
The two provenance anchors alone are not proof of authenticated approval. Unity's environment
path/hash selectors have the same local-harness authority;choosing a new hash chooses new trusted
input. This is not a hostile-user content authorization boundary.

`compile_dialogue(candidate:bytes,receipt:bytes)->bytes` validates receipt and binding and writes
an immutable canonical catalog with format=`reverie-quest-dialogue/v1`,candidate document and
approved provenance. `load_dialogue(path:Path,expected_sha256:str,definition:QuestDefinition)->QuestContent` bounds reads16KiB,
verifies full file SHA256 then exact schema/receipt. Open/read/write/replace failure is explicit;
generation/compile outputs use a fresh target and temporary sibling+atomic rename without replacing
an existing approved artifact. Failure cleans only job-owned temporary files;prior artifact unchanged.
Candidate generation never opens the gameplay database or swaps a running session's content.

`QuestContent` and runtime-checkable `QuestConsumer` live in contracts.dialogue,not domain.
Content is frozen and holds definition,dialogue and canonical behavioral catalog bytes/hash.
compile/load live in adapters.quest_dialogue;metadata timestamps remain strings in contracts.
Only definition,the four texts and approval anchors artifact_id/output_sha256/brief_sha256 are
embedded in rules. created_utc,approved_by,usage and other provenance remain a sidecar,so
nonbehavioral provenance changes do not invalidate saves. All static quest consumers expose bound
definition/content metadata for boot
validation:extend the existing RegisteredStateIO boot-binding check with a specific typed
QuestConsumer metadata protocol and compare definition/layout/catalog hash with rules.quest/
rules.dialogue whenever the quest extension is present. Include engines,wrapped read adapters,
admission routes,reducers,patches,presenters,codecs and checkpoint policy;missing/skipped constructor
or mismatched static metadata raises BootstrapError INVALID_QUEST_BINDING before registration.
Determine quest presence from actual registered quest engine/schema/presenter roles,events and
field families before checking optional document keys. Require declaration/presence agreement;
removing rules.quest cannot disable validation or leak an uninitialized consumer into the scenario guard.
quest_bundle declares the exact required quest consumer roles by registered engine/schema/
presenter/checkpoint category. The boot checker first requires each role to expose QuestConsumer,
then compares its definition/catalog hash;it cannot skip a missing protocol property. Base watch
consumers retain ScenarioConsumer. Test a registered quest consumer with no binding property.
No default legacy fallback for a missing quest binding is accepted. Dialogue changes therefore
change feature pins/world identity and require a fresh game;midgame bundle replacement is rejected.
This first bounded compatibility choice stores accepted texts/approval hash anchors in existing
rules fingerprints,not runtime-package rows or a new SQLite format. The existing pin contract
requires the exact artifact at resume/replay;it is not embedded into every save as duplicated blobs.

## 4. Gemini Free-API Preparation Contract

Director selected Gemini free API in chat. Model default=`gemini-3.5-flash-lite`;
current official [pricing](https://ai.google.dev/gemini-api/docs/pricing) lists free standard text
input/output;[structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
lists JSON Schema support. Checked2026-10-13;not a guarantee of this account's access/quota or tier.
Free-only scope:never enable billing,change tier,switch to paid/alternate models or use paid tools.
Free account/project selection must be confirmed before a live qualification call;provider headers
cannot establish billing tier. Project RPM/RPD/TPM remain UNVERIFIED until the director supplies
current AI Studio limits;no free-turn/day capacity claim. The player supplies their own key for
any later shipped runtime generation;current task is an explicit developer preparation CLI.

NEW `DialogueGenerator.generate(brief:DialogueBrief)->GeneratedDialogue` Protocol in contracts,
implemented only by adapters.gemini_dialogue. Definition/brief include approved harbor label,
giver's limited knowledge,the four situations,and exact reward description. They contain no
WorldState,private NPC thoughts,saves,user history,filesystem paths or credentials.
This first job pre-generates all four branches instead of sending the live mutable world to Gemini.

Use stdlib HTTPS REST,one nonstreaming POST to fixed
`https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent`.
Key comes from GEMINI_API_KEY at app boundary and x-goog-api-key header,never URL/CLI argument.
No custom origin,redirect,tool/search grounding,file upload/URL retrieval or automatic model fallback.
GenerateContent remains documented though labeled legacy;qualification must verify the selected
model/endpoint combination and record modelVersion if returned. No SDK/dependency installation.
Request has contents(parts(text=brief)) and generationConfig(responseMimeType=application/json,
responseJsonSchema=local four-intent schema,maxOutputTokens=2048,candidateCount=1,
thinkingConfig.thinkingLevel=MINIMAL).
Response text must come from exactly one STOP candidate,with text parts only;join parts in order.
Reject missing/blocked/non-STOP/truncated/tool response as GENERATION_OUTPUT,then locally decode
candidate. Bounded network envelope<=256KiB,prompt UTF-8<=4096bytes,candidate<=16KiB.
Out-of-order/duplicate intents remain explicit GENERATION_OUTPUT,with no output-normalizing sort
or automatic retry. Returned usage is reconciled once and that attempt stays consumed;the raw
output-byte provenance and exact local candidate-order contract remain intact.
Never log the HTTP request body/headers or raw provider error body;sanitize status/code only.

Explicit live CLI flags --live,--free-tier-confirmed,--free-data-use-confirmed and a configured key
are required;free-service data-use acknowledgement is linked to
[official terms](https://ai.google.dev/gemini-api/terms). Offline
validation is default and calls no provider. Missing key→GENERATION_KEY_MISSING;missing free-tier
confirmation→GENERATION_TIER_UNVERIFIED;offline invocation without candidate→GENERATION_INPUT.
Paid-project credentials cannot be detected reliably;the confirmation is supplied by the director,
not fabricated from the existence of a key. This turn observed GEMINI_API_KEY absent,not its value.

Director2026-10-14 explicitly removed local daily call/token ceilings;[superseding order](GEMINI_DAILY_LIMIT_REMOVAL.md).
Maximum2HTTP attempts per explicit job;minimum60seconds between attempts across processes.
Reserve20000accounting tokens per attempt before I/O;retain reservation when usage is missing,
otherwise reconcile upward/downward to provider total usage. Daily counters are accounting only,
not provider quotas;no daily exhaustion rejection. Existing profiles continue without reset.
OS-level msvcrt/fcntl cross-process locking and an atomic local ledger prevent parallel jobs
bypassing limits;test with real spawned processes. Failure to lock or
persist reservation→GENERATION_BUDGET_UNAVAILABLE and zero new HTTP call. Use a fresh ignored
generation-profile directory;never place the ledger/credential in a game save or packet.
While holding the exclusive profile lock,the writer removes only its reserved budget.pending
path left by a crash before fsync/atomic publication. budget.json remains authoritative;unpublished
pending bytes never reset counters or repay an attempt. Cleanup failure/corrupt ledger fails closed.
The lock remains nonblocking;contention reports BUDGET_UNAVAILABLE and consumes no attempt.
Measured provider usage beyond reservation is recorded truthfully without a local daily stop.
Actual cloud billing,remote activity from other apps and exact remaining quota cannot be inferred.

Explicit ProxyHandler({}) and a no-redirect handler disable ambient proxies/redirects.
Run the transport in an owned killable subprocess;parent communicate deadline60s covers
DNS/startup/connect/read and always kill/reap on timeout/cancellation. Per-I/O timeout30s;
response-read deadline60s;two60s attempts plus at most60s retry delay give job latency
TARGET<=180s plus bounded process scheduling overhead,measured separately from turns.
HTTP429→GENERATION_DEFERRED immediately,no automatic
retry. HTTP500/502/503/504 or network timeout→at most one retry after60s with a successful reservation.
If that reservation fails,preserve the initial provider/transport code with local failure as cause.
401/403→GENERATION_AUTH;other4xx→GENERATION_REJECTED;oversize/schema/blocked response→
GENERATION_OUTPUT without retry. Cancellation/process-control exceptions propagate and do not
publish an artifact;reserved attempts remain consumed. No UI/main gameplay thread blocks on this job.
Quota/service failure preserves all prior approved files. An existing approved catalog remains
usable offline;without one,quest startup reports QUEST_CONTENT_UNAVAILABLE rather than pretend
Gemini generated anything. A Codex-authored test example is never relabeled as Gemini output.

## 5. Wiring / Compatibility

`quest_bundle(content:QuestContent)->FeatureBundle` composes watch_bundle(harbor layout),adds
quest registration/field specs/codecs/adapters/reducer/patch/presenter and rules/schema literals.
Feature_id=`quest.harbor-v1`. Keep watch_bundle/legacy/harbor/grove pins exactly unchanged.
`bootstrap_quest(spec:WatchBootstrapSpec,content:QuestContent)->HeadlessSession` validates content,
constructs the existing ten-record/watch-genesis world plus stage0 record using the new bundle,
and derives world ID from new pins. app.watch._bootstrap accepts an optional merged bundle and
extra initial record tuple;default preserves old bytes. RegisteredStateIO still receives exactly
one merged FeatureBundle,whose rules retain the scenario key. Do not patch a finished session.

`QuestCheckpointPolicy` selects records by exact schema/entity keys,removes only the unique quest
record and delegates the remaining ten to WatchCheckpointPolicy. This avoids slicing assumptions:
quest.progress sorts before trial/watch components. Reject missing/duplicate/extra records,
stage2/3 with living target,invalid schema/role bindings or noncanonical order. Keep existing
watch clock/charge/replies/genesis invariants and save uncertainty behavior.

`ClientSession(path,layout=LEGACY,*,quest_content:QuestContent|None=None)` and ClientWorker use
one immutable content selection across create/resume/load/retry/recover. Quest content requires
the harbor layout;defaultNone keeps current behavior. Add action talk;no client completion switch.
Tk/bridge opt-in:--scenario harbor --quest-catalog PATH --quest-sha256 HASH;both quest options
required together,wrong selector/content rejected before owner attachment. Default stays unchanged.
Unity local harness receives catalog path/hash before Brain start and displays a Korean talk button,
quest stage and favor count. Player UI does not display keys,API flags or engineering schema IDs.
DTO trailing defaults in ClientUpdate:quest_id="",quest_stage=-1,quest_reward=0,dialogue_sha256="";
stage is an int sentinel(-1=no quest);wire exports canonical decimal strings as for existing ints.
fact_messages/turn_messages receive optional QuestContent and handle every quest fact explicitly;
missing dialogue at an impossible registered quest presenter is an explicit presentation error.
wire exporter generates matching C# types and schema fingerprint;all request dispatchers add talk.
Unity reconnect/load retains catalog selection and current loaded working branch.

State/text save compatibility:old saves remain playable with their old watch bundle;new quest
saves require exact quest bundle/approved content and reject old/wrong text pins through existing
UNSUPPORTED_RULESET/UNSUPPORTED_SCHEMA paths before owner swap. No silent migration/replacement.
Same seed/pinned content/command trace gives identical stages/reward/facts/core hash offline.
Retries of the exact report return original receipt,no duplicate reward/line/tick;new talk after
completion can consume a turn and display gratitude but produces no second grant. Load restores
stage/reward and clears display history;resume uses the exact required bundle. Recover only
publishes the actual persisted endpoint. Display log is still not authoritative/persisted.

## 6. Independently Derived Acceptance Vector

Fresh quest harbor:cell0,actorHP3,targetHP5,stamina2,stage0,reward0,tick0.
Down(cell3,tick1);talk(stage1,tick2,offer);open(tick3);right(cell4,tick4);
down(cell7,tick5);attack(tick6,HP2/3,stamina1);attack(tick7,HP1/1,stamina0);
rest(tick8,stamina1);attack(tick9,HP1/0,stamina0,stage2,reward0).
Left(cell6,tick10);talk(tick11,stage3,reward1,completion);retry(tick11,stage3,reward1,
no duplicate line);new talk(tick12,stage3,reward1,gratitude).
Each valid action advances revision once;watch wakes=tick//2,charge=min(3,tick),next wake=next even tick.
First talk from initialcell0→OUT_OF_RANGE,tick0/state unchanged. Wrong old NPC/actor IDs likewise reject.

Additional planned independent checks:goal killed before acceptance;save/load/resume at every
stage;exact/wrong catalog hash;wrong scenario and old/new pins both directions;precommit failure
and uncertain committed report recovery;postcommit renderer failure;malformed candidate with
stage/reward/approval extra fields;forged/mismatched approval hashes;all four intent omissions/
duplicates/text/exact-type/byte limits;provider401/429/503/timeout/cancel/oversize/non-STOP;
budget locking/reservation across two adapter workers;network-call count zero during real offline
quest play/replay;real bridge/Tk/Unity talk/load/retry/reconnect and release-hook absence.
Adapter transport fakes belong only in tests/adapters;domain outcomes use real registered Brain.

## 7. Checkpoint / Status

CP05-CONTRACT is triggered by the first authoritative quest progress/reward persistence.
Actual Claude PASS_WITH_CORRECTIONS received;H1/H2 and M1–M7/low findings verified and repaired
in this contract and [dispositions](../reviews/RS-REVIEW-CP05_CONTRACT_DISPOSITIONS.md).
Contract implementation hold is released only after recorded correction checks;no patch external
rereview claim. CP05-INTEGRATION remains a separate future pass after the first implementation's
native/full evidence;larger quest/memory/world integration is held until its repair/retests pass.
This document and offline examples are review inputs,not a contract pass,provider call or gameplay
acceptance. Human content approval,free-project verification and API qualification remain distinct.
Thought-token usage is recorded separately (nullable if absent) and included in total token budget.
Set thinkingConfig.thinkingLevel=MINIMAL for this selected model;qualification must verify
support and STOP output. Unsupported config never silently falls back to a different model/config.
