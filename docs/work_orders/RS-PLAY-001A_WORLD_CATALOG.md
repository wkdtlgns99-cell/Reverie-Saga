# RS-PLAY-001A — Stable Large World Catalog

READY2026-11-04;self-review. Parent:RS-PLAY-001;primary3,related2/5/6/7.
Director requests a larger default world and one reusable development world,not new AI
generation on every test. Director confirms the initial profile6continents/6countries/12cities.
This supersedes all earlier proposed numeric profiles.

Baseline:HEAD9fdb95e;existing five dirty parent/planning documents preserved.
Read:MASTER D01-D03,domain/canonical.py,domain/scenario.py,app/scenarios.py,README verification.
Allowed NEW paths under C:/ReverieSaga:src/domain/world.py,src/app/world_catalog.py,
tests/unit/test_world.py,content/worlds/development-world-v1.json;this order;parent progress docs.
No other modules/reference/user files changed by this stage.

Contract:immutable Continent,Country,Place,Route,WorldCatalog,Resident,LocalDetail;
generate_world(seed_hex) -> WorldCatalog;elaborate_place(world,place_id) -> LocalDetail.
Exact built-in types;seed exactly64lowercase hex;bounded scale;unique stable IDs;canonical
ordered routes with distinct existing endpoints,positive distance and connected whole graph.
All countries belong to existing continents;all places to existing countries. Unknown IDs
reject explicitly. No wall clock,network,mutable global state or external random generator.
Use domain-separated SHA256 seed-derived identity/choices. Names are original generated
prototype labels,not v1 reuse. Neighbors are roads within continents and shipping links
between continents. Distance is integer kilometres;this stage does not adopt travel speed.
Local residents/sites derive from the pinned world seed and place identity;querying detail
does not change the catalog. Acceptance/persistence of visited detail belongs to next stage.

Wiring:app.world_catalog CLI loads the reusable catalog by default and inspects the chosen
place;explicit generation is separate. Later registered world travel consumes this same
catalog;do not claim this stage is completed gameplay or D01-D07 acceptance.
Save JSON uses exact fields,UTF8,canonical JSON and versioned format;unrecognized fields,
duplicate IDs,bad references,disconnected routes and invalid types reject rather than repair.
Existing saves unchanged. Tests must load the checked-in fixed world for ordinary scenarios;
separate generator tests may use other seeds locally with zero provider calls.

Acceptance:catalog counts/connectivity/identity/local detail stability/strict roundtrip and
malformed documents tested;CLI reads the same file without mutating it. Generation+validation
TARGET<2s for default catalog on current host;measure and report actual value.
Checks:both Ruff configs,format touched Python,strict mypy,engineering guards and scoped tests.
Checkpoint:none triggered by immutable local catalog;first integrated/native/release gates
retain their existing scope. This stage alone is not independently published as the parent's
completed playable feature. Continue registered movement,persistence and graphical integration.

## Current evidence

Implemented catalog/CLI/new20tests;engineering10also PASS1.22s. Both scoped Ruff,format3,
strict291PASS. Imports3+1passed before the final pure geography validation addition. Default
generate+validate0.000267s. All-file integration and final delivery remain parent work.
Local details define residents/sites only;this is not simulation or persisted visit acceptance.
