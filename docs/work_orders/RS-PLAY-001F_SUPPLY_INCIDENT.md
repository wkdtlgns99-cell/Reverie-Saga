# RS-PLAY-001F — Supply Disruption and Confirmed Delivery

READY2026-11-04;self-review;primary2/6,related3/4/5/7. Parent remains RS-PLAY-001.
Baseline50ef965clean on codex/world-social-play-20261104. Director accepts supply disruption
and delegates best testing approach:fixed representative regression plus deterministic seeded
timing/duration/place variants,not fresh live generation per test. No other incident types
are implied. Read living bundle,inventory/local codecs,world clock/worker/UI and MASTER D03/D06.

Allowed NEW C:/ReverieSaga paths:src/domain/world_supply.py,src/contracts/world_supply.py,
src/engines/world_supply.py,src/orchestration/world_supply.py,src/app/world_supply_registry.py,
src/app/world_supply.py,tests/unit/test_world_supply.py,tests/integration/test_world_supply.py;
MODIFY world_session.py,world_worker.py,world_client.py,world GUI tests/progress docs.
Actor/local2D/facility reach is later parent integration;current command reach is same city,
not while on a road. No teleportation or domain outcomes mocked to reach tests.

Each city owns SupplyState(stock0..3,warehouse0..6,stage0..3,claimed0..2,repair_used0..2,
received,consumed,missed,treasury0..15,resolved_tick). Initial stock3/warehouse6/treasury15,
other counters0. Conservation:9+received=stock+warehouse+consumed+claimed. Player holds
source-city item:supply-{place suffix},quantity=claimed-repair_used. Repair consumes the
delivered2crates;does not also add them to market. Reward5gold moves from city treasury,
once only. These are scoped prototype tuning,not final economy or entire-world goods simulation.

Default scenario targetplace:p0-a,start30/end630logical seconds;active[start,end) unless
resolved. Every20seconds warehouse receives1up to6,then if route open transfers1to market
up to3;every30seconds market consumes1or records unmet demand. Ordering:expire,consume,
receive,route transfer. Each tick evaluated once;no re-created goods on retry.
Expiry sets stage3unless resolved;previously collected crates remain player-owned with no
reward and no forced remote confiscation. Offers clearly describe deadline/terms.
Seed variants select an existing city,start30..90,duration300..900,all local SHA256 choices.

Typed SupplyAction(place_id,npc_id,operation):accept/collect/deliver. Authority:player,at the
city,not mid-road,actual stored local NPC. Merchant index1accepts/delivers;courier index0
collects. Accept only active stage0;collect only active stage1,warehouse>0,claimed<2,one crate;
deliver only active stage1 with both source-city crates. Deliver consumes2,stage2/resolved_tick,
treasury-5/playergold+5 atomically. Refusal/preview does not transfer anything. Revalidate at
confirmation,including deadline/current resources. Invalid commands preserve time/state.
All action durations1second initial tuning. Events and cues record actual actor/NPC/operation.

World supply engine owns supply+inventory deltas;POST_TICK updates all city aggregates,
RESOLVE handles confirmed actions. No cross-engine imports,COMMIT-only writes. Strict
records/codecs/read views/patches/reducers/checkpoints bind cities,resource conservation,
quest stage,reward and inventory. Supply profile has distinct pins;old profiles unchanged.
NPC activity override only while awake:blocked courier seeks alternative supply;low-stock
merchant restricts sales;stock0other residents queue for ration. Otherwise saved routine.

UI:query actual available offers,show NPC/terms/deadline/quantity/reward,confirm or refuse;
nonmodal consideration retains slow clock. Do not present this prepared action surface as
live free-form conversation completion. Live AI later proposes these same validated actions.
Tests:independent exact tick30/60/90/expiry/conservation/stages/resource failure/retry/
save/restart/replay/seeded variants/GUI refusal-confirmation,real SQLite failure preservation.
Checks Ruffboth/format/strict/imports/scoped regressions;full regression at parent delivery.
TARGETsupply action<2s current host;measure. No new checkpoint/native/release completion.

Delivery amendment2026-11-04:director says finish ONE feature and stop. Complete this
supply slice and its ordinary publication/main synchronization;do not start live dialogue,
local2D or transport. Parent D01-D07 remains incomplete and is to pause after this slice.
README/play instructions and GAME_SYSTEM_SUMMARY_KO.md are allowed delivery edits.
CP01-05 retain bounded historical closure;this opt-in registered supply extension uses
their existing validated command/COMMIT/store interfaces without shared CORE changes.
No new scheduled independent checkpoint trigger;CP06still holds release/public distribution.
Self-review and Tk evidence do not establish Unity/native/other-device/human UX acceptance.
