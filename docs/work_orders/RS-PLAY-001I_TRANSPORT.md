# RS-PLAY-001I — Time-Summary Transport with Player-Controlled Interruptions

READY2026-11-05. QI01answered:stop on a journey problem and let the player choose the
response. Walking remains default;special transport summarizes elapsed time. Primary2;
related3/5/6/7. Executor:self-review,no agents. MASTER0.4/parentRS-PLAY-001 own product scope.

## Baseline / reads / prerequisites

HEAD0d954c7,branch codex/world-transport-20261105;five owned dirty preparation documents.
PR38ordinary merge,local/remote main equality/clean and tested/merged tree equality verified;
both final CI3986full/32boundaryPASS. No unfinished Hdelivery. Current Python3.13.12/.venv,
Tk8.6/SQLite3.50.4/Git reused,no dependencies installed. Read rulebook,handoff,backlog,Korean
progress,MASTER0.4,Sol template,numbered structure,READMEverification,workstation setup,
autonomous policy,and actual turn/admission/activation/state-IO/travel/time/population/supply/
social/conversation/worker/UI callers. Existing world roads10..65km,sea130..724km;320logical
seconds cost1.268sheadless/2.155sdurable. Naive per-second long journeys are unsuitable.

## Concrete data / ownership / public contract

NEW retained transport catalog binds world seed:carriage5m/s on existing road routes,ship8m/s
on sea routes. Public-service fare0 explicitly shown;no invented initial money/reward or
resource transfer. No rail route exists,so this slice does not advertise a train facility.
Maximum physical summary segment3600seconds;speeds/time never distorted for test speed.
Two explicit temporary checkpoint closures:starting road2500m fromp0-a,ticks[400,800);
first sea route2000m fromp0-b,ticks[0,3600). Reasons:road/harbor passage inspection. They
are transit availability events,not an invented bridge-physics/combat/supply blockade.
All route endpoints canonical sorted pairs;reverse boarding mirrors checkpoint position.

JourneyState(origin_id,destination_id,mode,progress_m,phase,started_tick,block_id):idle is
all empty/zero with phase idle;active phase outbound/blocked/returning has distinct adjacent
endpoints,correct route mode,0<=progress<distance and saved origin==Traveler.place_id.
Existing Traveler stays at origin during transit;on actual destination arrival alone set
place/visited and clear journey. Returning reaches origin with no new visit. No teleport.
started_tick<=CORE.tick;progress<=speed*(tick-started_tick). Block IDs reference this route's
catalog closure;no arbitrary cause. WorldWalker/TRAVEL_OWNER alone writes traveler+journey.
NEW SupplyProgressRecord(last simulated tick) owned by world.supply is a derivable processing
watermark,not a second clock;checkpoint equality to CORE.tick is mandatory.

TransportAction(operation,destination_id='',duration_seconds=1):board,advance,wait,resume,
return. Worker plans duration from current committed snapshot once;admission independently
recomputes exact plan and rejects a mismatched duration. RESOLVE recomputes from target minus
accepted duration;CORE bug is never ordinary rejection. Board/resume/return each1second;
advance min(3600,ceil(remaining_m/speed),next active checkpoint crossing time),minimum1.
At prospective crossing tick,closed means start<=tick<end:clamp exactly to checkpoint and
save blocked phase. Never cross then rewind. A closure opening exactly at crossing permits
passage. Encountering a newly closed checkpoint at current position costs1second to stop.
Wait only while blocked/closure active,up to min(3600,end-current);no movement or automatic
resumption. Resume only after closure clear;player then explicitly continues. Return changes
direction and physically traverses actual progress back to origin;closure behind the stopped
checkpoint does not block escape. Starting/reaching hostile destination rejects current
social policy;return remains possible. Reading/selecting map never boards/moves.

All IDs/types exact;no bool-as-int,unknown/missing/extra fields,duplicate/unsorted closures,
invalid route/kind/checkpoint/negative time. Reject INVALID_COMMAND,JOURNEY_DURATION,
JOURNEY_ACTIVE,JOURNEY_NOT_ACTIVE,JOURNEY_BLOCKED,JOURNEY_CLEAR,JOURNEY_NOT_BLOCKED,
WORLD_NOT_ADJACENT,WORLD_NOT_ON_ROUTE and SOCIAL_ENTRY_DENIED without state/time change.
Idle Journey cannot have remnants;blocked requires known cause and exact mirrored checkpoint.
Example10km carriage:board1s;500s movement reaches2500m attick501and stops;wait299s reaches
800without moving;resume1s;advance1500s arrives attick2301. Return from2500m costs500s plus
return decision1s. Test arrival rounding and reverse routes independently.

## Exact catch-up / no second simulator

COREstill iterates canonical seconds/phase barriers. Source inspection found its execution
loader hard-caps every command at16seconds,not merely the old profiles. Required supporting
contract extension:retain that normal cap and all old17second rejection tests;introduce an
explicit pinned time_summary{maximum_seconds,commands} rule,only for named registered command
schemas,strict unique/nonempty<=32schemas and17..3600seconds. ExecutionLimits gains optional
summary_max_seconds=16/summary_commands=() and duration_limit(schema);ordinary defaults/pins
remain identical. Admission and effect fact-count/time-window validation select that schema's
bound. Unknown/duplicate/malformed/unregistered summary config rejects INVALID_EVENT_POLICY;
summary without enabled simulation rejects. This is a bounded new capability for this task,
not global cap weakening. Local FULLregression required after this supporting COREextension. Only this
new profile's POST_TICK activations run at admitted action endpoint:proven prior intermediate
work consists of supply periodic changes,derived resident activities/no new visit,and already
credited social state;no queued events/simulation subscribers exist. Supply engine opt-in
catch-up advances from its watermark to target,enumerating only20/30second periodic boundaries
plus scenario expiry,ordered expire/consume/receive/transfer using canonical advance_supply.
Reads each city once,writes final state once,updates watermark in same COMMIT. Equality with
literal one-second stepping is independently tested at start/end/period collisions,active/
resolved/expired incidents and deterministic varied intervals. No skipped observable event.
Materialization occurs on real final arrival;social merit checks after supply endpoint. All
known action schemas activate these endpoint nodes. Old profiles retain their manifests,
16second normal limit,codecs,pins,context bytes and per-second scheduling. New profile pins
TransportAction alone into a separate3600second summary limit;old command admissions retain their own16second/speech limits.

## Wiring / UI / persistence

New world-transport-v1 composes Hbundle;register two components,six payloads,admissions,
adapters/codecs/reducers/patches/checkpoint. Optional TransportRules selects profile/session
bootstrap;ordinary --world loads retained catalog and separate tmp/world-transport-play.
Gate in-transit local speech/social/supply/foot commands;allow recorded idle time/save/load.
Worker masks local residents/offers and generation refuses out-of-reach before provider call.
Board confirmation shows destination/mode/0fare/duration. One Future per summary segment;
auto-continue only for that explicitly confirmed journey,stop on problem/error/arrival/ESC.
After restart require explicit continuation. Interruption panel offers supported wait/resume/
return with exact terms;no automatic problem resolution. Slow time during consideration,
ESC stops further segments,processing wall time excluded. Keep exact confirmed request,
GameCommand,duration,key and attachment across rollback/uncertain COMMIT/render-ack failure;
retry must not re-plan after a possibly committed segment. Own all polling/shutdown resources.

## Exact edit scope

All relative paths below denote exact paths under C:/Reverie Saga/.
NEW:content/worlds/development-transport-v1.json;src/domain/world_transport.py;
src/contracts/world_transport.py;src/orchestration/world_transport.py;
src/orchestration/world_supply_progress.py;src/app/world_transport_registry.py;
src/app/world_transport.py;tests/unit/test_world_transport.py;
tests/integration/test_world_transport.py;tests/integration/test_world_transport_client.py;
docs/reviews/RS-PLAY-001I_EXECUTION_2026-11-05.md.
MODIFY:src/contracts/events.py;src/orchestration/serialization.py;src/orchestration/turn.py;
src/domain/world_supply.py;src/engines/world_supply.py;src/engines/world_travel.py;
src/app/world_catalog.py;src/app/world_session.py;src/app/world_worker.py;
src/app/world_client.py;src/orchestration/world_conversation_context.py;README.md;
docs/MASTER_GAME_ARCHITECTURE.md;BACKLOG.md;SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md;
this order;docs/reviews/RS-PLAY-001H_EXECUTION_2026-11-05.md(factual prior delivery only).
Ignored scratch:tmp/rs-play-001i for owned probes/audits/private saves. Forbidden:COREchanges
outside the three exact duration-selection/validation files above,
old content/save rewrites,reference repo,credentials,CI/guards weakening,new dependency/native/
ComputerUse/device/independent/release/administration changes.

## Acceptance / checks / performance / delivery

Implement domain/catch-up and independent tests,registered real admission/COMMIT/replay,
then worker/Tk/ordinary launch. Verify all modes/closure branches,foreign visits,world supply
counts/expiry,NPC activity,new-state validation,old-profile identity,save/load/restart and
exact rollback/uncertainty/ack recovery. Native/human/device acceptance remains separate.
Measure3600s segment TARGET<2swall and longest90500ssea TARGET<30s on this PC;UI stays live.
If missed,diagnose lawful bottleneck and report,never change speeds/clocks/outcomes or bypass
CORE. README environment/capture=sys,both Ruff/scoped format/strict mypy/import3+1/pip,
relevant tests/doc guards;required full CI twice at final head before ordinary PR/main sync.
CP01-05not newly triggered:bounded per-schema duration extension preserves deterministic
scheduler/barriers and earlier normal-command qualification;no new kernel/first client/quest/
native/import boundary. Existing independent-review holds are not declared satisfied;CP06release held.
Stop on evidenced contract contradiction,user overlap,unavailable qualification or a genuinely
new material decision. Ordinary publication already authorized;no permission re-ask. Complete
only after evidence,then next unanswered material backlog decision. Full parent not DONE here.

Director2026-11-05also authorizes recording the accepted product compromise/next review in
MASTER/root companions,docs/PRODUCT_DIRECTION_2026-11-05.md and numbered structure guides.
This delivery includes that decision record only;no base-game/billing runtime is implemented.
