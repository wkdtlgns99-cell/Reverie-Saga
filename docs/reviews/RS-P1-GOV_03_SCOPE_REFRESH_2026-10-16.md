# GOV-03R — Scope and Native Replay Qualification

Date:2026-10-16 | State:LOCAL_ACCEPTED | Review:self;not independent.
[Order](../work_orders/RS-P1-GOV_03_SCOPE_REFRESH_2026-10-16.md),
[current implementation order](../work_orders/RS-P1-GOV_03_CURRENT_IMPLEMENTATION.md),
[reviewed scope/native observations](../work_orders/RS-P1-GOV_03_SCOPE_2026-10-16.json).
Primary7 engineering verification support;no gameplay/runtime gate change.

## Finding and Resolution

Old20methods assumed four factories/four source files/six goldens and no nested code objects.
Current same four factories contain27methods;all six current production factories,including
quest_bundle/memory_bundle,contain35methods/12classes/8resolved files. Inherited getters resolve
to domain/scenario.py and contracts/dialogue.py,which engines-only measurement would miss.
Keys use concrete class identity,not engine_id or shared implementation identity.

Three existing generator expressions were reviewed in Movement.manifest,QuestRules.manifest,
QuestRules.evaluate. Future acceptance admits only these exact source-bound entries within their
enclosing bodies;no general nested-function exemption/weaker body condition. New schema2runtime
manifest,8trace mapping and current implementation order resolve old scope assumptions.

## Actual Evidence

Existing Windows CPython3.13.12,coverage7.16.2,pytest9.1.1,pip check PASS;no install/config change.
Production binding sites,method bodies and selected fixture/vector/replay assertions inspected.
Exact8nodes collected;covered tests8PASS,zero failures/errors/skips,exact JUnit names;active
coverage.pytracer.PyTracer7.16.2observed. Native branch data/contexts verified with public coverage
APIs;all35have positive native statement/body/qualified-context intersections. Original six alone
provide no qualified hit for15current obligations;none are exempted. No supplemental context fills
a hole. Same-line shared implementation hits do not prove every object invocation/branch/access.

Actual subprocess phases:collect0.688s,golden52.955s,json1.085s,all exits0. Raw config/logs/JUnit/
binary data/context JSON/descriptor retained at
tmp/gov03-refresh/native-5d3b93c5e9ae4f43b9663ff467440249. Tracked scope binds actual SHA256/sizes,
source/script/package/input hashes and observations. Source/test/config input sets match before/
after;factory content additionally bound by entry/final hashes. Raw evidence remains ignored and
must be available/hash-current for future reuse;tracked summaries cannot recreate missing data.

Full-suite collection1787tests0.64s,not executed as full suite. Existing runtime/tests/fixtures,
old inventories,locks/config/UI unchanged. Permanent producer/assessor and negative gate tests
remain unimplemented;G07 NOT_ACTIVE,parent GOV IN_PROGRESS. New order READYfor later explicit work.

Delivery checks:456entry-file preservation outside declared notes;JSON counts/ranges/source/hash/
node/context/artifact consistency,UTF8/links/fences/progress/diff and existing entry guards.
No new full/static/native Unity run required for this docs/probe-only scope;previous checks remain
historical. CP01–05unchanged,V3stopped PARTIAL,CP06held;no live provider/agent/commit/push/CI/release/
cleanup or independent-review claim. Timing3s/all11/hardware remain unqualified.
