# QT-F18 — Offline NPC Memory Comparison Acceptance

Date:2026-10-15 | State:LOCAL_ACCEPTED | Review:self,not independent.
Order:[QT-F18](../work_orders/QT-F18_MEMORY_COMPARISON.md). Primary4retrieval support,related6/7.
Director defers Claude and requests execution of the next eligible task. Broader D2remains open.

## Selected Scope and GOV-03 Entry Stop

Initially examined the existing READY GOV-03 order. Native enumeration of its same four factory
outputs finds27public methods,not the historical20. Added:EncounterActions/EncounterMovement
scenario_layout and the five Watch classes' inherited scenario_layout. The latter implementation
lives in domain/scenario.py,outside the old four-source inventory. Movement.manifest contains a
generator code object,which also invalidates the old blanket no-nested-code assumption. Evidence:
tmp/gov03/current-registry.json. These are scope/readiness gaps,not gameplay defects or G07results.
The order explicitly stops on changed registry/ranges;no gate/tool/config/coverage policy activated
or relaxed. Its current entry now records STALE_SCOPE. A bounded source/selection re-review remains
necessary;no automatic exemption or silent inventory regeneration. Original inventory preserved.

Selected independent D2step:compare already validated persisted NPC conversations. New explicit
developer CLI uses read_memory,existing full T0 query projections and publish_fresh. It produces
source-bound before/after snapshots plus added/removed/retained stable IDs. Different world/NPC/
player/quest/catalog rejects;different branches or reversed ticks remain valid comparisons.
The artifact reports snapshot differences,not forgetting,enemy observation or new game authority.
Both sources are rechecked before exclusive publication. Output has no local paths/API secrets.
Two reads do not prove a shared atomic instant across saves;the artifact is not an approval or
automatically accepted generation input. No new memory,CORE/save schema,wire,UI or provider work.

## Actual Verification

Current host reused project Python3.13.12 and pinned tools;no installations/version changes.

| Check | Actual result |
|---|---|
| Entry full baseline,pytest --basetemp .pytest_cache/gov03-baseline --junitxml tmp/gov03/baseline.xml | 1697PASS502.83s;collected before new files,not final combined suite |
| Initial comparison module | 16PASS/1FAIL13.30s;test wrongly expected load to change saved branch ID |
| Corrected comparison +query/export/check/memory/prepare modules | 67PASS38.53s |
| Final same six modules after stronger IO/corrupt-save assertions | 67PASS38.78s;17new cases included |
| Shared Ruff and selective Ruff | both PASS |
| Scoped Ruff format | 2files already formatted |
| Strict mypy --no-native-parser | PASS162source files |
| pip check | no broken requirements |
| Native import contracts | 3+1kept,0broken |
| Actual prior Unity-produced saves,network-forbidden standalone CLI | 3comparisons PASS;all3source SHA256 unchanged,API0 |

Final tests:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/integration/test_npc_memory_compare.py tests/integration/test_npc_memory_query.py tests/integration/test_npc_memory_export.py tests/integration/test_npc_memory_check.py tests/integration/test_npc_memory.py tests/adapters/test_npc_memory_prepare.py --basetemp .pytest_cache/qt-f18-acceptance --junitxml tmp/qt-f18/acceptance.xml
```

Independent expectations include empty/acceptance/report/wait/reverse cases,certainty and stable
IDs,real older-slot load,preserved saved branch ID,valid different-branch projection,exact context
types and five foreign identity fields. Real commits after either initial source read reproduce
NPC_CONTEXT_STALE before output. Existing output/pending/source alias/parent-file IO errors and
corrupt save preserve inputs. Network-blocked real subprocess exercises the registered module CLI.

Initial test expectation was corrected against load's contract:attachment/working path changes,
while saved protocol.branch_id is preserved. Current test asserts that exact retained identity and
separately exercises a validated different-branch projection. No production behavior changed to
satisfy this test. Initial new-test strict typing errors were repaired using typed replacements.
Initial import invocations omitted PYTHONPATH and could not find app;proper README environment
PYTHONPATH=src;. qualified both real contracts. Both initial and corrected logs retained.

## Real Retained Unity Saves

Used the existing accepted QT-F17 default run(default-8fc6de9a14dc43ea96ab04a05a5bb555),tracked
approved catalog/pin and source files only. No editor/player/build rerun or new native claim.

| Before → after | Ticks | Added / removed / retained |
|---|---|---|
| slot01 → original | 10 → 13 | 1report / 0 / 1acceptance |
| original → slot01 | 13 → 10 | 0 / 1report / 1acceptance |
| original → loaded | 13 → 12 | 0 / 0 / 2 |

Report certainty remains reported;no witnessed enemy defeat is invented. Sources retained original
SHA256 ff9f26de78c978186ebe447e2733d7693c409f1f09ddbe9bb35ef04803015a80,
slot83e0513bf4ad4e34c4cce7d98bf445a05cbb660f824f6443a34158259cb94925,
loaded5a315f026b09df2a0eebf35f4ff7dc84632533006cffee9b49b94319533074bf.
Witness:tmp/qt-f18/actual-unity-saves.json;fresh canonical comparison artifacts alongside it.

## Delivery and Limits

All228preexisting source/test/client/content/config inputs byte-identical to entry. Existing dirty
review-request/start/order files preserved. Entry/protected fingerprints,JUnit,static results and
actual-save witnesses live under tmp/qt-f18;baseline/registry probe under tmp/gov03. No ignored
evidence published,no secret/credential/usage-ledger access and no cleanup of old unique inputs.
README and three progress documents updated;new order/source/test/receipt remain local.

Final combined full suite,remote CI for this uncommitted addition,Linux/native Unity/live API and
independent inspection NOT_RUN. Baseline1697and affected67overlap;do not sum them. Earlier CI success
qualifies2f591f7,which excludes QT-F18. Claude V3deferred/incomplete;CP06release held. Existing final
English request still pins2f591f7;refresh it to include QT-F18when review is explicitly resumed.
GOV-03 remains unimplemented and requires current-scope re-review;no automatic next work or push.
