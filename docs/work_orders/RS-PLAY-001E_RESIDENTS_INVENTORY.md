# RS-PLAY-001E — Saved Local Residents and Inventory

READY2026-11-04;self-review;primary2/6,related3/5/7. Parent RS-PLAY-001 remains active.
Baseline9fdb95e+001A-Ddirty inputs. Read world/world_travel records and codecs,timed bundle,
world session/worker/client,MASTER D02/D03/D05,README checks and workstation Tk instructions.

Allowed NEW C:/ReverieSaga paths:src/domain/world_population.py,
src/contracts/world_population.py,src/engines/world_population.py,
src/orchestration/world_population.py,src/app/world_population_registry.py,
tests/integration/test_world_population.py;MODIFY world_session.py,world_worker.py,
world_client.py,world_time order,world GUI tests/progress docs. No existing kernel changes.

Each catalog city has an initially dormant SettlementRecord(state:LocalDetail|None).
Only the starting city is materialized at bootstrap. POST_TICK materializes the player's
committed destination after arrival,using the pinned local-v1 recipe,then stores the complete
resident definitions/sites. No map selection materialization,no live provider call. Return,
save/load/restart preserve the same accepted definitions. Four named prototype residents per
materialized city are a representative set,not a claim of whole-city population density.
Ordinary activity derives from saved work hours/workplace plus logical time. Day origin08:00,
24hour day;work interval[start,end),awake nonwork06:00-22:00market,otherwisehome/sleep.
No social incident,production formula or deception is inferred before the current product
answer. Querying an NPC's activity does not mutate their definitions or advance time.

InventoryRecord stores exact immutable InventoryState(gold:int,items:tuple[(id,count),...]),
initial gold0/items empty;no unapproved starting grant. Integers exact,no bool,nonnegative
gold,signed63-bit cap;item counts positive,IDs namespace-validated,sorted unique,max128stacks.
This is actual persisted empty inventory,not a fabricated panel. Future trade/reward writes
must use a separately defined owner/typed command;this stage does not invent those mechanics.

New living-world bundle extends timed world,distinct feature/schema/rule pins. Keep foot
and timed modes intact. Bootstrap contains exact12settlement records,oneinventory,one traveler,
canonically sorted. Checkpoint requires detail exactly for visited places,correct static
definition/owner binding. Local materializer owns settlement state,onlyNone→accepted recipe
transition;COMMIT-only delta/patch/reducer. Inventory is bootstrap-owned/read-only until trade.
Strict codecs/observed immutable views;reject unknown/missing fields/IDs and bad nested data.

UI shows current-city resident activity from committed state and opens real inventory in a
nonmodal panel. Opening/reading inventory preserves1/10clock;ESC remains explicit global
pause. App worker projects records and current activity;no sidecar authoritative gameplay.
Default living-mode work path distinct from older prototype saves;no silent migration.

Tests:initial/dormant/arrival/return/materialization+movement atomicity,exact schedule
boundaries/nextday,restart/slots,invalid records,source preservation,actual GUI inventory
clock/ESC/current residents. TARGETnew projections<2s on current host;measure scope.
Verify Ruffboth/format/strict/imports/relevant tests;full regression at parent delivery.
No new checkpoint triggered by this bounded layer;independent/native/release gates remain.
Director subsequently accepts first supply disruption and delegates best test approach.
Keep fixed regression plus deterministic seeded variants,not per-test live generation.
Incident response is the next bounded integration,not claimed here.

Current-host evidence:population+actualGUI27PASS5.04s,all-sourceRuffboth/strict316/import3+1PASS.
No source-domain outcome mocks;actual registered arrival/SQLite/slot/restart and Tk used.
Only ordinary routine/no-incident behavior accepted at this stage;parent remains incomplete.

Final affected149PASS22.06s under Tk warning-as-error;format10PASS. Work continues on
codex/world-social-play-20261104 with an intermediate local checkpoint,not parent/main
completion. No full regression or live-provider qualification yet.
