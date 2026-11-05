# RS-PLAY-001I — Transport Execution Evidence

LOCAL_ACCEPTANCE2026-11-05;publication/CI still pending at this snapshot. Self-review,not
independent/native/device/release qualification. Primary2;related3/5/6/7.
[READY contract](../work_orders/RS-PLAY-001I_TRANSPORT.md). Baseline0d954c7 on
codex/world-transport-20261105. No existing save migration,dependency install or agent.

## Delivered behavior and authority

New isolated world-transport-v1 profile and retained transport catalog compose the social
world. Walking remains default. Confirmed public-service boarding (fare0) starts physical
carriage5m/s/ship8m/s travel on existing adjacent routes. Segment<=3600game seconds;closures
stop at the actual checkpoint. Waiting does not resume;clearance,continuation and physical
return require player choice. ESC holds later segments;restart requires explicit continuation.
Only actual arrival changes visited/place and materializes local detail. No vehicle Walked
fact or invented rail facility. In-transit local actions and provider context are gated.

WorldWalker owns Journey and Traveler. Supply owns its derived processed-tick watermark;
checkpoint requires equality with CORE.tick. Catch-up enumerates canonical20/30second/expiry
boundaries and calls the existing supply rules;no second simulator or clock. In this isolated
profile only,proven no-op intermediate population/social nodes run at command endpoints;
there are no queued events/subscribers. Existing profiles retain their activations/manifests.

The actual shared loader capped all commands at16seconds. Supporting CORE changes are limited
to ExecutionLimits,strict pinned time_summary registration and per-schema admission/effect
bound selection. Normal16/17rejection remains;only TransportAction opts into<=3600. Distinct
TransportArrivalDelta preserves the old footstep delta/reducer semantics. Two components,
six payloads,registered codecs/adapters/reducers/patches/admissions/checkpoint policy.

Worker reuses the existing coordinator's exact command/recovery identity. A possibly committed
segment is never replanned on retry. Real SQLite rollback,uncertain commit and GUI acknowledgement
failure preserve original intent/duration and prevent duplicate travel. One worker Future per
segment keeps Tk polling/input live;processing wall time adds no second charge.

## Verification

- Canonical local full regression:4022PASS998.08s,exit0. Captured358source/test/config input
  hashes unchanged throughout the run. Later changes add five boundary tests and format only
  those test files;all163runtime-source inputs still match the full-run witness. Full CI must
  qualify the final test/document snapshot;do not relabel4022as a final4027local full run.
- Final new transport tests:41PASS17.79s (22unit,13registered integration,6actual Tk/worker).
  Includes nonperiodic expiry637/resolved supply/varied intervals,dual replay,wrong duration,
  normal17/summary3601bounds,hostile boarding/arrival,return allowance,in-transit action/context
  denial,slot/restart,ESC between chunks,explicit post-restart continuation and real recovery.
- Six earlier profiles (walking,timed,population,supply,conversation,social):immutable HEAD
  source witness created real saves;current code resumed all six with identical pins/core
  hashes/G-Hcontext hashes and unchanged save-file bytes. No old save rewrite/migration.
- Both Ruff configurations PASS;README scoped formatting plus new modules/tests21files PASS;
  strict mypy355files PASS;type-inclusive import contracts3/3 and runtime-cycle1/1 KEPT;
  pip check PASS. Final affected-world/metadata/document guards236PASS88.03s,exit0.

Private evidence:tmp/rs-play-001i/full.log/full.exit/full-input-check.json,runtime-reuse.json,
profiles-baseline.json/profiles-current.json,headless-throughput.json,gui-throughput.json,
profile-segment.txt and actual private saves. No keys/dialogue/save contents are published.

## Measured performance / limits

Current-host headless full carriage+724kmsea:35commands,tick93851,total20.979s,max0.823ssegment.
Actual Tk+SQLite same physical journey:35commands,tick93851,total39.539s,max1.787ssegment.
Segment<2sTARGET met;longest-journey total<30sTARGET remains OPEN,not silently waived or claimed
PASS. These are small-world/current-device results,not minimum-spec or dense-history guarantees.

An actual3600ssegment on a separate copy of the performance save was instrumented with cProfile;
original save bytes remained unchanged. Instrumentation timings are not production benchmarks.
It records18000canonical phase barriers;_simulate5.092s of5.676sinstrumented submit,including
repeated immutable snapshot validation/sorting;durable persistence0.390s. This identifies the
remaining per-second CORE barrier/snapshot cost as the main measured hot path. Broader CORE
optimization is deferred to a separately bounded order;no barrier,validation or outcome is
removed to meet a target. The UI continues polling while the owned worker processes segments.

Native Unity/C#compile/render/build,manual UX/art,other-device/MIN-SPEC,independent checkpoints
and release remain unqualified. Full parent project is incomplete. No new provider calls
were needed for transport;prior conversation evidence remains separately scoped.

## Reproductions and corrections

Initial metadata lacked an integer descriptor bound;bootstrap rejected it and explicit bounds
were added. A real500scommand exposed the shared16scap (TURN_LIMIT);the scoped pinned capability
above resolved it while retaining normal-command guards. The old one-foot arrival reducer
correctly rejected a vehicle arrival;the new distinct delta preserves that old contract.
GUI board-ack failure initially lost continuation intent (1FAIL/3PASS),fixed and covered by
the final suite. The new no-provider test's callback annotation initially failed strict types;
it now declares Never because invoking it always fails the test.

An arrival-policy fixture first altered a committed state under its old receipt,which correctly
failed "latest receipt does not match head" (1FAIL/12PASS). The final scenario explicitly uses
a synthetic initial checkpoint with a fresh protocol;no receipt guard is changed or forged.
The preservation audit first compared live tuple-valued dataclasses with JSON lists;serialized
values/hashes/files were already equal. Comparing the same JSON representation fixed that
audit-only false mismatch. No actual runtime/profile regression was hidden.

## Product decision record / next task

Director2026-11-05approved [Option C and adjusted sequencing](../PRODUCT_DIRECTION_2026-11-05.md).
MASTER/numbered guides/root companions now distinguish complete authored base requirements,
optional live dialogue and API payment/access HOLD. Existing dev keys remain test-only. This
is an authorized requirement record,not implementation of the authored base game or billing.
After ordinary transport merge and main synchronization,next is actual ownership/mutation/
visibility A–J review and ranked proposals. No Qdrant or graphical expansion starts here.

## Publication

Local acceptance and self-review complete,with the explicit nonblocking30stotal TARGET open. Pending scoped commit/PR,required final-head CI and ordinary main sync.
