# RS-OWN-001 — Data Ownership, Mutation and NPC Knowledge Review

REVIEW_COMPLETE2026-11-05;self-review of actual sources/registered metadata,not independent
certification or implementation of the proposals below. Primary7 design/integration support;
related2/3/4/5/6. [Order](../work_orders/RS-OWN-001_DATA_OWNERSHIP_REVIEW.md).
Baseline main421de09dd13ddd56377aee2279599969386f99b4 after ordinary PR39delivery;clean main/
origin equality and tested-tree equality verified before starting this review branch.
[Approved direction](../PRODUCT_DIRECTION_2026-11-05.md):complete authored base game plus
optional free-form NPC dialogue;API payment/access HOLD. Existing qualification holds remain.

## Findings and recommended decision

The current world slice has a coherent single-writer/atomic-commit foundation. A read-only
registered-metadata probe found8component families,30initial records,6engine bindings and
8command schemas. Actual manifest writers agree with every mutable FieldSpec owner. This
does not establish the broader target cognition/economy/history or its Unity integration.
No new demonstrated gameplay-state corruption is claimed by this audit.

| Priority | Evidence-backed finding | Consequence / disposition |
|---|---|---|
| High,target gap | Resident disposition is immutable local definition;checkpoint validation requires exact equality with elaborate_place. There is no mutable persona/belief/goal component in this world profile. | Do not mutate personality inside LocalDetail or treat generated prose as a belief update. Define separate owned mutable cognition/knowledge contracts before adding evolving NPCs. |
| High,integration hazard | Engine manifest permissions are enforced,but FieldSpec.consumers is not an enforced read allowlist. App context code can read a full CoreSnapshot;NPC privacy currently comes from a specific context projection. | Never treat storage location,consumer metadata or a prompt instruction as NPC knowledge authorization. Define an explicit subject/source/visibility projection before general retrieval. |
| High,target gap | World transcript is one player-owned ConversationRecord capped at4096exchanges. SQLite replay compacts after4096steps and receipts retain1024. | Replay is not an unlimited historical-memory ledger. Define durable important observations/claims and retention before promising lifelong memory or rebuilding a complete historical index. |
| High,integration hazard | Inventory is owned by world.supply;social reputation by world.social;fixed diplomacy is pinned catalog data. Separate quest/encounter demos are not part of this world bundle. | Combat loot,trade,authored quest rewards and diplomacy must not add competing writers or silently reuse unrelated profile state. Contract cross-owner requests and consequences first. |
| High,product/integration gap | Option C is approved,but this world's live-dialogue path has no complete authored campaign/state-aware scripted equivalent. Unity still uses ClientWorker/engine_bridge,not WorldWorker. | Establish the shared conversation/action/content contract before authored content expansion or world-to-Unity integration. Existing prepared quest dialogue is useful precedent,not a complete base game. |
| Medium,known performance limit | The original Tk+SQLite journey took 39.539s against a 30s target. Later wall-clock runs timed simulation and persistence within the same journey. | Keep the visible-window target open. The follow-up scopes the attribution and provides a reproducible probe. [RS-OWN-002](RS-OWN-002_CLAUDE_FEEDBACK_2026-11-06.md) |
| Deferred,infrastructure | No Qdrant integration/indexer/outbox/rebuild schema exists. Current world search is bounded lexical own-transcript selection. | No vector database implementation now. Benchmark actual recall/missed facts first;add a derived index only with ownership/visibility/rebuild contracts. |

These are distinct categories:missing product capabilities and future integration hazards are
not automatically bugs in an intentionally bounded prototype. Prior CI does not prove semantic
dialogue truth,art quality,commercial viability or release readiness.

## A. Actual owner / entity / storage map

All eight active component families use `state`,CORE storage and tierA. `world-transport-v1`
is selected by ordinary `--world`. Initial checkpoint contains30records,with only the starting
city's local detail materialized. Other cities already have supply state;their Resident data
is materialized on actual arrival. Catalog definitions and derived views are separate below.

| Family / entity | Sole registered writer | Source / stored meaning |
|---|---|---|
| world.traveler / actor:world-player | world.walk / WorldWalker | Current city,foot-route progress,visited IDs;TravelerRecord in domain/world_travel.py. |
| world.journey / same player | world.walk / WorldWalker | Vehicle route/mode/progress/phase/cause;JourneyRecord in domain/world_transport.py. |
| world.settlement / each12place IDs | world.materialize / LocalMaterializer | LocalDetail or None;sites,resident identity/occupation/disposition/work hours. Not mutable NPC moods or autonomous personal inventories. |
| world.inventory / player | world.supply / WorldSupply | Gold and sorted item quantities;single player inventory,not a general multi-actor trade ledger. |
| world.supply / each12place IDs | world.supply / WorldSupply | Conserved market/warehouse stock,received/consumed/missed,repair stage/cargo accounting,treasury/resolution time. |
| world.supply-progress / player | world.supply / WorldSupply | Processed-tick watermark,required to equal CORE.tick. Derived processing state,not a second time authority. |
| world.conversation / player | world.conversation / WorldConversation | Bounded exchanges identified by speech/NPC/place IDs,utterance/reply times,model/context hash,proposal and speech progress. |
| world.social / player | world.social / WorldSocial | Selected ancestry/citizenship,18group reputation scores,once-credited supply places. Not each NPC's private interpersonal beliefs. |

Exact registration:[transport bundle](../../src/app/world_transport_registry.py),composing
[social](../../src/app/world_social_registry.py),[conversation](../../src/app/world_conversation_registry.py),
[supply](../../src/app/world_supply_registry.py),[population](../../src/app/world_population_registry.py)
and [walking](../../src/app/world_registry.py). Records are persisted by
[SqliteCommitStore](../../src/adapters/sqlite_store.py),not directly by these engines.

Other actual responsibilities:

- CORE.tick and pending event queue belong to the shared Driver/system clock/event machinery;
  `world.time` emits explicit wait facts and does not independently own the clock. Protocol
  branch/revision/streams/receipts belong to Driver;DurableSession owns its current attachment.
- Retained world/social/transport catalogs define geography,ancestry,organization membership,
  initial diplomacy,route rules and closure definitions. Registered rules/catalog fingerprints
  bind them to a save. Do not edit catalogs to simulate an in-game change or silently load a
  different definition version. SQLite state plus matching validated definitions/pins is the
  authority boundary;arbitrary SQLite rows or an index entry are not sufficient authority.
- Resident activity,available offers,social reaction,ConversationContext and memory rankings
  are derived read models. They have no independent mutation authority. Approved media stays
  in build assets/manifests;it is not duplicated into ordinary saves.
- Separate legacy quest profile:`quest.rules` owns quest stage;`quest.memory`/NpcQuestMemory
  owns one NPC's two source-bound accepted/reported evidence slots. Separate assistance mode:
  `encounter.actions` owns quest.assistance-memory,total count/latest4causes. These are real
  narrow features,not interchangeable stores for this world's free-form NPC memory.
  [Quest rules](../../src/engines/quest.py),[evidence writer](../../src/engines/npc_memory.py),
  [assistance contract](../../src/contracts/npc_assistance_memory.py).

## B. Single-writer enforcement and its limit

[Driver.validate_registry/_stage/_run_barrier](../../src/orchestration/turn.py) reject wrong
field owners,unregistered/wrong-owner reducers,undeclared reads/writes and duplicate barrier
targets. [Scheduler](../../src/orchestration/scheduler.py) rejects duplicate same-phase writers
and dependency cycles. Reducers can read/stage only their delta target;engines use declared
observed read views whose lifetime ends with the invocation. UI/provider output is not an
engine and cannot apply arbitrary patches through the registered command path.

FieldSpec.consumers is descriptive metadata,not an enforced read ACL:an in-memory audit probe
replaced all8consumer tuples with empty tuples;registered IO/checkpoint validation still passed
with identical pins. No production file/save was changed. Actual engine access is checked
against manifest.reads and admission-route reads. This observation does not show a current
NPC leak or permit hostile third-party engines;it prevents overstating the existing control.
Decide whether consumers is documentation or a separately enforced restriction before relying
on it for future privacy. Either choice still needs per-NPC/per-record visibility rules.

Proposed ownership rule:separate immutable identity/definitions,objective simulation facts,
NPC observations/claims and mutable attitudes. Assign one registered owner to each mutable
family. Quest/combat/dialogue may request supported transfers or social consequences;they
must not independently edit the inventory/reputation/knowledge tables. Exact new families,
field types/ranges and accepted operations require a bounded contract before implementation.

## C. Facts,heard claims,beliefs and memory

CURRENT:PlayerSay records that an utterance was delivered. It does not establish the truth
of its contents. NpcReply records accepted speech/provenance;its text is not a world fact.
`proposal` only selects none/accept/collect/deliver;executing a supply action is separate.
The legacy quest context explicitly labels acceptance as observed and completion as reported;
it does not give that NPC direct knowledge of the enemy's death.

Example:player says "the mayor stole food". Current durable fact is the utterance received by
that addressed NPC. There is no implemented general theft fact,belief confidence,rumor spread
or trust update from this sentence. A reply referring to an unregistered office does not
create that facility;the prior Hreceipt records this actual semantic limitation.

PROPOSED:retain objective events separately from NPC-owned observations and claims,including
source identity/event,tick,subjects,observer,visibility and branch provenance. A belief can be
wrong while the observation "heard X say Y" is true. Rumor forwarding must preserve who heard
what from whom;it cannot upgrade the claim to witnessed truth. Mutable trust/emotion/goals
need their own owner and transition rules. No confidence values,decay rates,rumor cadence,
personality axes or generic semantic interpretation were selected by this review.

## D. Typed changes and causal propagation

CURRENT registered commands:Footstep,WorldWait,SupplyAction,PlayerSay,ContinueSpeech,NpcReply,
SocialAction,TransportAction. Admission checks actor,binding/reach,current revision and
supported action conditions. Engines return typed deltas/facts;registered reducers validate
and stage them. Text,embeddings and summaries cannot submit a raw authoritative outcome.

Concrete delivery chain:confirmed SupplyAction validates current city/NPC,cargo/stage,then
WorldSupply changes cargo/treasury/repair in RESOLVE. WorldSocial reads the resulting supply
stage in POST_TICK and credits reputation once. Both are published in the same COMMIT. Hearing
an NPC agree to deliver is not the transfer. A transport segment updates journey/arrival and
exact endpoint supply/time accounting through this same Driver.

Active world facts Walked,TimePassed,SupplyActed,SpeechAdvanced are all record_only with no
simulation subscribers. This is not a general rumor/off-screen event network. Legacy quest
memory does consume source-bound QuestAccepted/QuestCompleted events in its separate bundle.
Reuse typed events/request boundaries for later propagation;do not invent cross-engine calls.

## E. Transaction order,replay and idempotency

CURRENT sequence:decode/admit against current committed state → deterministic phased candidate
evaluation/staging → full candidate/effect/checkpoint validation → SQLite transaction with
components,pending,protocol receipts,replay and head → proven COMMIT → publish authoritative
in-memory head → presentation. Rendering failure after COMMIT cannot undo the game action.

SqliteCommitStore uses BEGIN IMMEDIATE and validates the previous durable head. Before COMMIT,
confirmed absence preserves the old state;after an uncertain result,recovery must prove the
exact previous or next checkpoint/receipt. Driver blocks ambiguous publication. Command IDs
bind branch/stream/sequence;payload fingerprint/revision prevent different-action reuse.
The coordinator retains exact confirmed command/duration/attachment across retry. Load swaps
the owned attachment and invalidates pending reply context. Accepted replies replay from saved
commands/content without a provider call. An external AI generation job is not a SQLite
transaction and cannot be rolled back as if speech had never been heard.

Sources:[Driver](../../src/orchestration/turn.py),[durable owner](../../src/app/durable.py),
[persistence projection](../../src/orchestration/persistence.py),
[conversation coordinator](../../src/app/world_conversation_worker.py).

## F. Cross-system effects without cycles

CURRENT same-phase nodes read the pre-barrier state even when dependencies order execution.
A dependency does not make a preceding node's staged writes visible inside the same barrier.
Use a later phase or an explicitly supported queued-event delivery when a consumer must see
new state. The actual supply/social chain above crosses RESOLVE→POST_TICK and does not rely
on an illegal same-phase write/read shortcut. Import contracts retain engine independence.

PROPOSED:one authoritative clock;off-screen work consumes validated time/event inputs. Choose
registered causal delivery and idempotent event identity for new memories/quests/economic
effects. Do not add a second scheduler,parallel database mutation service or an LLM coordinator
that owns game truth. Endpoint catch-up is qualified only for the current no-subscriber world
profile;adding observable intermediate events invalidates that proof and requires requalification.

## G. Save/load,recovery,retention and index rebuild

CURRENT SQLite tables:save_head,components,pending,streams,receipts,checkpoint,replay. Rows and
head/protocol/checkpoint are validated with hashes and registered schemas/pins. Save slots
load into a validated private branch/attachment;old source saves are preserved. Six earlier
world profiles were proven unchanged by I's immutable-source/save-byte witness.

Limits are deliberate:1024receipts,4096retained replay steps with checkpoint compaction,and
4096world exchanges globally across addressed NPCs. At the transcript cap,new speech rejects
DIALOGUE_HISTORY_FULL instead of silently forgetting. Current durable state and narrow permanent
anchors survive compaction;arbitrary old events absent from those records cannot be recovered
by installing Qdrant. A full objective-history archive/semantic retention policy is missing.

PROPOSED:define which durable facts/observations must survive before adding a derived index.
Build/rebuild it from those retained canonical records with world,branch,NPC/source identity,
record version and embedding/index version. Loading a different branch must select/rebuild its
own index scope. A crash or index failure after game COMMIT leaves committed game truth intact;
index recovery/fallback must report its actual freshness. No atomic SQLite+Qdrant transaction,
outbox,job ledger or migration is implemented/claimed here.

## H. NPC-specific visibility and information access

CURRENT [context projection](../../src/orchestration/world_conversation_context.py) includes
the addressed NPC's identity/disposition/activity/local environment,current player utterance,
own prior exchanges and selected public supply/social facts. Only courier/merchant roles get
warehouse/assignment facts in this prototype. Public organization standing is not another
resident's private incident history. Active journeys reject context before initializing a
provider. [retrieve_memories](../../src/domain/world_conversation.py) excludes other NPC IDs,
keeps recent2plus lexically relevant older records,with defaults6records/4096bytes. It does
not perform semantic vector search. Current identity/diplomacy values are treated as public;
disguises,secret citizenship and learned political knowledge are not implemented.

The app can inspect CoreSnapshot,so engine read capabilities alone do not enforce NPC privacy.
Prompt instructions are useful but do not enforce knowledge disclosure or factual natural
language. Structured output/context-hash/proposal validation protects command/state boundaries;
it does not prove every sentence is true. Re-ingesting old AI prose as objective history would
create a second,unjustified source of facts even though SQLite stored that utterance correctly.

PROPOSED:apply deterministic observer/source/branch visibility eligibility before retrieval,
then verify selected record provenance and current eligibility before constructing the prompt
and accepting a candidate. Do not send hidden global documents to a model and ask it to forget
them. Separate currently known public facts,private observations,heard claims and untrusted
speech in both scripted and free-form context. Wrong/stale branch,NPC,revision or source must
not become a private-memory hit. Exact permissions are a future contract,not selected lore.

## I. SQLite authority versus derived retrieval

CURRENT canonical game state,accepted utterances and source-bound evidence reside in validated
SQLite records/checkpoints with matching packaged definitions. Keyword rankings/context DTOs
are derived;Qdrant is absent. No vector record may change objective state or authenticate its
own content. Similarity is not proof,ownership or permission.

PROPOSED optional index contract:document IDs map to canonical retained record IDs and branch/
observer scope;embeddings/rankings/summaries carry version/freshness/provenance. Revalidate
retrieved content against SQLite/current definitions rather than trusting vector metadata
alone. Deleted/restricted/superseded records cease to be eligible even if an index update is
late. Use canonical retrieval without vectors when adequate;never require players to install
Docker/a database server. Add infrastructure only after recall/latency/retention evidence.

## J. Missing contracts and bounded next order

The better compromise keeps the current transaction kernel and solves the following contracts
before broad simulation/content or graphical integration. These are proposals,not new runtime
schemas or automatically approved balance/behavior changes.

| Order | Bounded deliverable | Required acceptance before dependent implementation |
|---|---|---|
| O1 | Shared base/optional-dialogue ownership contract | Same objective state/quest/inventory action paths in both modes;scripted content is visibly authored,AI is optional;provider failure/cancellation cannot block main progression or silently charge money. Identify immutable persona vs mutable per-NPC records and actual writers. |
| O2 | Durable observation/claim/visibility and retention contract | Exact observer/source IDs,tick/branch visibility,truth-vs-heard distinction,capacity/retirement/important anchors,save version and deterministic updates. Material belief/rumor/trust behavior needs director clarification;do not guess numeric rules. |
| O3 | Tiny integrated text-play proof under those contracts | Two NPCs with different knowledge,one real quest/resource consequence,one heard false claim that does not become objective truth;scripted path without provider and optional AI path,save/restart/branch/replay/retry tests. Reuse current fixtures/resources where valid,not a new general framework. |
| O4 | Versioned world-to-client command/state bridge,then tiny graphics qualification | Actual current-world commands/committed snapshots,attachment/retry/provenance/error/sequence rules and asset binding IDs. Existing engine_bridge/Unity wire only carries earlier ClientWorker modes. No native/C#qualification is claimed or auto-resumed. |
| O5 | Measured expansion | Qualify total-system graphics+provider/local inference,retained-memory retrieval and CORE hot paths;only then choose Qdrant,bulk assets or broader off-screen simulation. Retain30stransport TARGET and device/release holds. |

Required later tests:writer conflict and undeclared access;no private cross-NPC or cross-branch
retrieval;heard false claim versus witnessed event;one confirmed transfer with multiple legal
consequences in one COMMIT;failure before/after COMMIT;exact retries;save/load and derived-index
rebuild after deletion/compaction;scripted/optional AI progression equivalence;stale response
rejection;unsupported prose creates no gameplay entity. These augment existing narrow tests;
they are not falsely reported as implemented by this documentation.

No migration is applied by this review. New cognition/history/visibility families will change
schema/rules/schedule pins:choose an isolated new profile or an explicitly versioned migration
with old-save preservation tests. Changing catalog files to force old saves to load is not a
migration. API billing remains HOLD;no commercial infrastructure is a prerequisite for O1/O2.

## Verification and delivery status

- Source/registered-metadata inspection and an in-memory owner probe verified the exact A map.
  Private witness:tmp/rs-own-001/metadata.py/metadata.json. Empty-consumers probe qualified the
  narrow Bfinding without changing production code or saves.
- Focused existing ownership/read-view/metadata/memory/context/durability/replay checks:
  90PASS25.43s,exit0. Existing cases cover sealed/expired views,writer conflicts,same-phase
  visibility,own-memory filtering/source certainty,atomic delivery,retry/recovery and replay.
  No new gameplay behavior was introduced to make these pass.
- Unchanged-runtime baseline full CI:PR39run42038935289/job1272842958134027PASS812.69s,
  push42038877403/job1272840950724027PASS913.52s;each32boundaryPASS,all steps terminal success.
  New review changes documentation only;no new runtime behavior/performance result is inferred.
- Document guards11PASS4.63s;584local links resolve;A–J section coverage verified;diff
  whitespace clean. Git comparison to421de09 confirms no src/tests/content/config/CI changes.
  Private witness: `tmp/rs-own-001/document-check.json`.
- PR40 merged `dc4e0dee50b8d06d34b28c7bfb60d86cbb8de05d` from tested head `ef15309`.
  The [PR run](https://github.com/wkdtlgns99-cell/Reverie-Saga/actions/runs/42043864344)
  passed 4027 full and 32 boundary tests in 1126.19s and 9.27s respectively.
  The [push run](https://github.com/wkdtlgns99-cell/Reverie-Saga/actions/runs/42043806471)
  passed 4027 full and 32 boundary tests in 830.65s and 6.15s respectively.
  Local and remote main matched after fetch and fast-forward. Tested and merged trees matched
  `23bfb32a141fe18369cad6c7572940df968939de`. [PR40 delivery record](https://github.com/wkdtlgns99-cell/Reverie-Saga/pull/40)

Independent/native/human UX/device/release qualifications remain open. See the [Claude feedback disposition](RS-OWN-002_CLAUDE_FEEDBACK_2026-11-06.md) for the subsequent source and evidence checks.

No source/test/content/credential/provider/billing/native change. No external reviewer/provider
call or agent;ordinary authorized PR publication is recorded separately.
Completing this review does not complete the full project or authorize an uncontracted runtime
expansion. The next step is O1/O2 contract work within the approved direction,with only materially
unsettled player-experience decisions brought back to the director.
