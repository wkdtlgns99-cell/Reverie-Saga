# Proposed persistent memory of an NPC's own gate assistance

PROPOSED2026-11-01;director scope decision pending. Future implementation order:DRAFT.
This document changes no runtime,save,API,pin or review gate.
Primary2internal factual memory;6persistence;related3definitions,5inspection,7village flow.
[Preparation order](../work_orders/QT-F95_ASSISTANCE_MEMORY_CONTRACT.md).

## Evidence and intended outcome

Current [F56](../work_orders/QT-F56_NPC_ASSISTANCE_HISTORY.md) intentionally retrieves only
retained GateAssisted facts. Actual current source opens the gate at16;activity shows
that assistance. A legitimate checkpoint-only save at16retains the open gate and existing
quest/supply memories,but no assistance row. The query explicitly refuses to infer help
from the open gate. This is correct existing behavior and an unimplemented D2capability.
Actual probe receipts:tmp/qtf95/probe-result.json and repeated-result.json;not portable
test artifacts or proof of the proposed persistent component.

Proposed outcome:in a new explicit child mode,the NPC retains its latest four own gate
assistance anchors and an exact cumulative own-assistance count across compaction,
checkpoint/save/load/restart and ordinary uncertain-COMMIT recovery. Existing quest
conversation memory and supply work memory remain separate. Regional cognition,
relationships,five-level general memory,forgetting and generation remain outside this slice.

## Proposed data contract

All names/values below require approval and a refreshed implementation order before code.
These are feature-owned DTOs,not fields added to ClientView or the wire envelope.

| Item | Proposed exact definition |
|---|---|
| Entry | Frozen AssistanceEntry(tick:int,target_id:EntityId,source_kind:Literal["wake","answered_call"],cause_event_id:str) |
| State | Frozen AssistanceMemory(total_assists:int,entries:tuple[AssistanceEntry,...]) |
| Component | AssistanceMemoryRecord(entity_id:EntityId,state:AssistanceMemory),schema TypeKey("quest.assistance-memory",1);entity_id is the selected NPC |
| Family | FieldFamily("quest.assistance-memory","memory"),CORE/tierA,scale1,unit own_assistance_records,collection cap4 |
| Delta/patch | AssistanceMemoryDelta(entity_id,before:AssistanceMemory,after:AssistanceMemory),schema quest.assistance-memory-delta/1;AssistanceMemoryPatch(state:AssistanceMemory),schema quest.assistance-memory-patch/1 |
| Fresh state | total_assists0,entries();new-world initialization only |
| Scalars | Exact int,never bool;tick1..MAX_INT;total_assists0..MAX_INT,with total_assists<=current core tick. MAX_INT remains the canonical domain.primitives value |
| Owner/target | Exact namespaced strings;component selected NPC,entry target selected existing gate. Foreign owner/target rejected |
| Retention | len(entries)==min(total_assists,4);strictly increasing ticks;unique causes;oldest entry evicted only when fifth or later assistance is appended. Append increments total once |
| Causal anchor | Exact e1- followed by64lowercase hex. Stores the validated incoming wake/reply cause,not the emitted GateAssisted event ID. source_kind identifies which existing cause was selected |
| Entry identity | The immutable tuple(owner,target_id,source_kind,cause_event_id). No new separate persistent memory-ID/hash algorithm is needed |
| Codec | Exact fields state:{total_assists,entries:[{tick,target_id,source_kind,cause_event_id}]};reject unknown/missing/duplicate fields,wrong type/range/order/cap/owner/reference/source |
| Domain failures | Invalid DTO ->specific NPC_ASSISTANCE_MEMORY_INPUT/OWNER/ENTRIES/ORDER/SOURCE ValueError;invalid engine/reducer candidate ->existing CandidateError INVALID_FACT. External malformed save ->existing SAVE_CORRUPT/UNSUPPORTED_RULESET boundary;no fake success or generic ordinary player rejection |

On checkpoint validation,revalidate the exact immutable shape,selected owner/target,
tick<=core.tick,count/retention bounds and canonical cause identities using the checkpoint
world and the selected feature's existing producer/phase/wave/sequence contracts. Preserve
all current quest/supply/NPC/gate checkpoint checks. A checkpoint's memory is authoritative
state;an open gate without this component is never promoted into a memory.

## Proposed writer and atomicity

Use the existing successful assistance decision in
[EncounterActions._assist_gate](../../src/engines/encounter.py). In the new child mode,
append the memory delta alongside GateDelta and the existing GateAssisted emitted fact
in the same EngineResult. Owner:encounter.actions/POST_TICK. No new engine import,
event subscriber,phase,wave,pending event,COMMIT hook or storage sidecar.

The existing `_aid_source` validates routine wakes and actual answered replies and gives
answered replies priority when both are incoming. Its selected header.event_id is known
before emission and must equal GateAssisted.caused_by[0] in the committed publication.
Record source_kind wake for NpcActed or answered_call for WatchReplied. Do not claim that
the stored cause is the requested-call event,or reconstruct an evicted request chain.

This source choice is deliberate:ReadPort/EngineInvocation expose no world_id. The writer
need not extend them or predict its own not-yet-sealed event ID. Checkpoint validation can
use its existing full CoreSnapshot world metadata to verify the known causal event ID.
The actual EventQueue event-ID input is world,tick,phase,wave,producer_id,sequence;
producer_rank is not an identity input. Future tests must use the actual canonical rule.

The scheduler currently routes same-phase simulated emissions as late;POST_TICK source
cannot simply acquire another POST_TICK subscriber. The proposed same-result delta avoids
changing that barrier. Gate state,memory and protocol either commit together or retain
their previous state together. Failed validation/staging/persistence must not publish a
remembered action;uncertain persistence must retain actual recovery evidence. Exact retry
reuses the existing committed result and never appends again.

No record for player open/close,already-open gate,unheard quest,insufficient prior stock,
far NPC,same-phase arrival,stopped-after-report aid or aborted/rejected commands. Existing
aid range/supply/wake/call priority,cost,reward and movement rules remain unchanged.

## Proposed compatibility and live consumers

| Boundary | Proposed scope |
|---|---|
| Opt-in identity | New child feature quest.harbor-assistance-memory-v1 built from the existing reach-aid bundle;distinct schema/rules pins and the actual compiled schedule fingerprint (which may match its parent). No new central client DTO fields |
| Selection | Explicit --npc-assistance-memory flag and app option npc_assistance_memory:bool=False,requiring npc_reach_aid=True. Exact flag hierarchy validated before resource IO. Future order must freeze actual entry paths;not an implemented CLI flag |
| Old saves/modes | Existing13modes and their pins/bytes/outcomes unchanged. Never silently repin,upgrade or add missing records to old saves. Old/child selection mismatch remains unsupported and source-preserving |
| New checkpoint/load | New child codec/policy restores its own component,retained entries,total and branch-local identity. Existing SQLite schema/envelope and actual atomic commit/slot/recovery mechanisms remain owners |
| Inspection | Existing talk/activity/slot message tuples show labelled persistent own assistance,total and latest4anchors. Keep the retained3event history explicitly separate;no duplicate count or claim that missing older detail means forgetting |
| Client wiring | Registered ClientSession ->worker ->Tk and framed bridge/CLI;current ClientView/WireEnvelope remain unchanged. Native Unity option/render/build qualification stays held and must not be inferred from Python/source checks |

Prospective files (PLANNED,not a runtime edit allowlist):new feature-owned domain,
contracts,orchestration and app assistance-memory modules;existing
engines/encounter.py decision/manifest,bootstrap/feature selection,ClientSession/query,
worker/Tk/headless/bridge/CLI routing and relevant qualification metadata. A future READY
order must enumerate exact actual paths,signatures,registration and tests after approval.
No generic memory framework,central registry rewrite,engine-to-engine import or unrelated
format/ownership refactor is part of this proposal.

## Independent acceptance vectors — planned,not executed

| Vector | Required proposed result |
|---|---|
| Fresh new mode | total0,empty entries;old quest/supply components identical in meaning |
| Actual first routine aid16 | total1;entry tick16,target selected gate,source_kind wake,cause equal actual GateAssisted.caused_by[0] |
| Actual current repeated source | Existing source produces aid16/20/24/28/32. Proposed state at32:total5,retained ticks20/24/28/32;the current source probe establishes events only |
| Compaction at16or32 | Aid memories/counters preserved without retained GateAssisted bodies;query read-only. Old modes still explicitly report their retained-history limit |
| Player open/already open/no eligible aid | No new record or total increment |
| Call+routine in one tick | Existing selected answered-call cause recorded once;max1aid/memory per tick;no second record from the wake |
| Prior barrier | Far prior NPC/same-phase arrival or insufficient prior stock yields no aid/memory;qualifying prior pose/stock can yield both atomically |
| Retry/report/load/restart | Retry no increment;completion report stops future aid but preserves own memories;restore uses selected branch,not current/future/global history |
| Invalid fields/foreign world or target/causes | Precise errors and unchanged owner/source;cannot accept bool ints,duplicate/out-of-order/future/oversized entries or old-mode pins |
| Abort/rollback/uncertain COMMIT | Gate+memory+protocol share actual durability outcome and truthful recovery;no postcommit fake rollback or extra retry action |
| Actual callers | Direct/worker/Tk/framed/CLI agree;pending/error/recovery/input/poll/close remain usable. Saved/current/previous inspection and exact source bytes qualified |
| Regressions/performance | Full shared CORE/replay/goldens,strict types,lint,imports/dependencies and exact source/pin/old-output parity. New query bookkeeping O(4);measure2sTARGET/10sdeadline with short/long sources,no unmeasured device claim |

## Decision required

Director approval is requested for this new optional persisted own-assistance component,
four-anchor retention,cumulative count,validated causal-source binding and explicit child
mode compatibility boundary. Approval permits authoring a refreshed implementation order;
it does not certify implementation,tests,native execution,independent review or release.

The automatic goal explicitly retains public/save-contract limits.
[ENGINEERING_RULES](../../ENGINEERING_RULES.md#delivery) requires explicit authorization for
further public/save-format changes outside an authorized task. This preparation neither
grants that authority nor fabricates it. Future implementation must evaluate the existing
checkpoint procedure against its actual scope;do not reopen closed checkpoints,create a
new gate or waive held review without authority. Until a decision,implementation is DRAFT.
