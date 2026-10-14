# QT-F02 — Bounded Scenario and Content Generalization

Date:2026-10-13 (Asia/Seoul) | Executor/reviewer:Sol;self-review only
State:DONE for first embedded generalization;CP03 actual subset feedback/scoped repair accepted
Authorization:director subsequently requested the remaining design,code and verification in chat.
Current coding contract:[embedded scenarios](QT-F02_SCENARIO_CONTRACTS.md);supersedes the
historical authoring-only scope/DRAFT below. No publication or further bulk/world expansion.

Authority:[turn rules](../../ENGINEERING_RULES.md),[MASTER](../MASTER_GAME_ARCHITECTURE.md)
§§1–3,[engineering prompt](../ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md),
[coding template](../prompts/SOL_CODING_WORK_ORDER.md),[A10](../../architecture/BLOCK_05.md#a10-typed-schemas--content-pipeline).
Status/dependencies:[BACKLOG](../../BACKLOG.md);human progress:[Korean companion](../../GAME_SYSTEM_SUMMARY_KO.md).

## 1. Observed Baseline

HEAD:`1ad22446d48c50b8b72a6d3af8de3c9d775134ea`;entry tree clean,288tracked files.
Current-host Python probe:CPython3.13.12,exit0. No fresh gameplay/native/remote CI evidence.
Refresh HEAD,status and input hashes before design or implementation;do not overwrite intervening work.

| Actual source | Fixed coupling / live consumer |
|---|---|
| `src/app/client_session.py` `_payload`, `ClientSession.update`, `act` | Gate/enemy/NPC/actor/map IDs selected from constants;creates/resumes only watch bundle |
| `src/app/watch.py` `_bootstrap` | Fixed ten records;3×3 map,wall1,gate4,enemy8,NPC6;genesis wake addresses fixed NPC |
| `src/app/encounter_registry.py`, `src/app/watch_registry.py` | Fixed fields/ranges,feature documents and fingerprints;NPC cell restricted to6 |
| `src/engines/encounter.py`, `src/engines/watch.py` | Actions/events address fixed roles;watch wake/reply/lantern consumers are coupled |
| `src/orchestration/encounter.py`, `src/orchestration/watch.py` | Codecs/admission/reducers/presenters/checkpoints enforce IDs,topology and event provenance |
| `src/app/client_text.py` `NAMES` | Committed-fact narration has a fixed ID→Korean role table |
| `src/app/client_worker.py` → `src/app/engine_bridge.py` | Single owner worker;private-pipe requests expose actions,not scenario/target selection |
| `src/contracts/client.py` → Unity `PlayRoom.cs` | One actor/gate/enemy/NPC projection;no generic entity collection |
| `src/contracts/narratives.py`, `src/adapters/narrative_catalog.py`, `content/narratives.json` | Six immutable descriptions displayed through the bridge;no gameplay spawn/effect contract |

These are intentional accepted prototype restrictions,not defects to fix by relaxing validators.
Changing bootstrap positions alone is insufficient:registry,codec,checkpoint and presenter contracts
must agree. [CORE-03](RS-P1-CORE_03_INTERACTION_COMBAT.md),
[CORE-04](RS-P1-CORE_04_EVENTS_NPC.md) and [CORE-05](RS-P1-CORE_05_DURABILITY_SAVE.md)
retain the accepted v1 contracts and literal replay expectations.

Entry worktree SHA256 witnesses,not Git blob hashes:

| Path | SHA256 |
|---|---|
| src/app/client_session.py | f321f43ed089ab6f068ea13785091aa04124e7454715f3315382c778898749e8 |
| src/app/watch.py | 73a0c1aa8ea5ed7fd369b666dd32192131a5f1ef61a2d68fe8d8e1a2a2bbdce6 |
| src/app/encounter_registry.py | 9a514ba3724df1da51c0fbf506660a58c2a107a3f8e310f1e5a0a024f17af1df |
| src/app/watch_registry.py | 73e98a8410d893093dccf3f1a6b6d6a7a9fc2094460538b36f5f119e9a3f1c93 |
| src/orchestration/encounter.py | dfe5d672b20b9b4a93f38f19ed978055d1be1bd2ab8d3f31fe4a14ff6d6e778a |
| src/orchestration/watch.py | 268ebb0214090404dfe6b333e22e706ca270b227e6cde69da8331601932ab138 |
| src/app/engine_bridge.py | 8aaa6922f94674714f3a3626ab8e6a207f0ab5bae29dd49a02e1631632f79667 |
| src/contracts/narratives.py | 9f87b7da551f38fed2d7e734ce0261bed4c86ee7816bc4950b12653bb36e45a1 |
| content/narratives.json | 5b5927c5a354a06bfea69eaf36a005b87ca5c211c2d35e155c1ef3be4d9eac5e |

## 2. Complete Authoring Work Order — Historical Snapshot

| Field | Contract / result |
|---|---|
| task_id/title | QT-F02;author the first bounded scenario-generalization order |
| status/executor/review | Authoring DONE;Sol/self-review;runtime DRAFT until §4 contracts are complete |
| goal/non_goals | Define two independently playable configurations through one registered path;exclude bulk content,new combat balance,quest consequences,NPC cognition,world travel,art and release |
| baseline | §1 exact HEAD/clean tree/source witnesses;refresh before execution |
| prerequisites | CORE integration,CP01/CP02/CP04,CLIENT-003 and QT-F06 accepted for their recorded scopes;these do not qualify new gameplay schemas |
| read_files | §1 actual sources/callers;AGENTS/ENGINEERING_RULES/BACKLOG/SESSION_HANDOFF/GAME_SYSTEM_SUMMARY_KO;MASTER §§1–3;prompt format/reuse/checkpoints;BLOCK1 ownership,BLOCK4 A7/A9,BLOCK5 A10;CORE-03/04/05;QT-F06;CLIENT-003;CP01 dispositions/CP04 repair |
| allowed_edit_paths | NEW `C:/ReverieSaga/docs/work_orders/QT-F02_SCENARIO_GENERALIZATION.md`;MODIFY `C:/ReverieSaga/BACKLOG.md`,`C:/ReverieSaga/SESSION_HANDOFF.md`,`C:/ReverieSaga/GAME_SYSTEM_SUMMARY_KO.md` |
| forbidden_paths | All other tracked files;reference C:/Quilltale;runtime/tests/accepted content,original review witnesses/ZIPs,goldens,architecture authority,pins,CI and remote settings |
| public_contract | Documentation only;no function,DTO,wire,component,save-format or feature-registration change;runtime additions require §4 |
| behavior | Inventory live fixed bindings;define staged scope and required contract decisions;link original semantics;keep authoring/runtime/review states distinct |
| edge_policy | Empty/zero/negative/duplicates/invalid IDs/missing fields/order/error decisions for runtime are required in §4;numeric behavior here NOT_APPLICABLE because documents do not execute domain input |
| examples | Two changed labels alone→FAIL generalization;two independent IDs/layouts with the same accepted rules and correct load/replay→candidate acceptance;unqualified source entry→excluded from both samples |
| algorithm_steps | Read authoritative entry and sources;capture baseline;trace fixed bindings through callers;write §3–5;update all three progress documents;validate links/UTF8/scope/hashes/diff |
| wiring | BACKLOG→this order→actual sources/checkpoints;handoff/current Korean next-step reference same scope;no new runtime registration |
| performance | NOT_APPLICABLE for document behavior;runtime measurements remain NOT_RUN;A10 cache/chunk targets are not measured results |
| baseline_commands | `git status --porcelain=v1` empty;`git rev-parse HEAD` §1 SHA;`.venv/Scripts/python.exe --version` 3.13.12/exit0;source inspection only |
| verification_commands | `git diff --check`;UTF8/local-link/fragment/fence validation for four delivery files;source witness rehash;exact changed-file inventory/unchanged HEAD |
| test_responsibilities | No new runtime tests for documentation;§5 defines future behavioral responsibilities;reuse prior evidence only as historical |
| acceptance | All template fields present;actual sources exist;§4 unresolved semantics explicitly DRAFT;two-sample/compatibility/review criteria concrete;four-file scope/progress consistency/document checks PASS |
| claude_checkpoints | Authoring does not trigger CP03/CP05;future triggers and held downstream steps in §6;no external provider call/upload |
| stop_conditions | Intervening overlapping user edits;missing source evidence;attempt to promote incomplete runtime contract to READY;report actual cause before dependent changes |
| delivery | Brief Korean result,files and actual checks;local documentation only;no commit/push/PR/dependency/agent/remote administration in this task |

## 3. First Playable Scope

- Exactly two small,independent scenarios;one player,one door,one enemy,one watch NPC and one
  lantern per scenario. Retain3×3/1000mm cells and existing combat/time rules for this first stage.
  Vary role IDs and legal object/wall positions;do not require a larger map or multiple same-role actors.
- Configuration A and B must share one implementation and registration path. No branch on scenario
  name,content name or special enemy ID inside simulation. The old fixed prototype remains a
  compatibility case,not the test oracle for new traces.
- New-game selection chooses one validated immutable configuration before owner creation.
  Resume/load use saved accepted pins;UI selection cannot rewrite an existing world.
- Names/descriptions may bind only the six accepted QT-F06 narratives after category/reference
  validation. Fresh mechanical IDs/topology are authored for this project;source narrative IDs
  never become legacy entity bindings. The319queued+1rewrite-required entries remain held.
- Player actions:move,open/close,attack,rest,wait,bell;save/load/retry/recovery continue through
  the authoritative owner. A short action sequence that reaches the door/enemy/NPC is sufficient
  for each sample. Quest descriptions stay descriptive;no reward/status/neglect consequence is implied.
- First client remains provisional Unity;Tk regression behavior must remain qualified. Client
  geometry/labels follow committed projections and accepted definitions;client collision decides no outcomes.

## 4. Contract Completion Before Runtime READY — Authoring Gap Inventory

At authoring,the architecture supplied general rules but no complete scenario payload/schema.
The following gap inventory is now resolved for the embedded first stage by the linked contract;
external gameplay packages and major save/quest/memory changes remain later scopes.
Develop them together in a bounded contract-design stage before producing a READY coding order.

| Contract gap | Required concrete decision / artifact |
|---|---|
| Scenario definition | Frozen concrete DTO and compiler schema:scenario/version IDs;actor/space/gate/enemy/NPC/lantern roles;cells/walls/initial values;narrative references. Exact field types/defaults/ranges/cardinality/ownership and type/version registry;versioned feature documents. Suggested NEW contract artifact:`docs/work_orders/QT-F02_SCENARIO_CONTRACTS.md`;path is PLANNED,not present |
| Role resolution | Named public signatures and a single immutable binding source available to admission/engines/codecs/reducers/presenters/client. No engine I/O or sibling-engine imports;declare every read/consumer in FieldSpec/manifests. Entity identity distinct from player-facing description |
| Geometry / overlap | Derive coordinates from map record,not fixed WIDTH;define wall ordering,uniqueness and legal start cells,door/enemy/NPC overlaps,open-door occupancy and defeated-body movement. Initial HP/stamina and all arithmetic retain current constants;do not copy source stats |
| NPC events | Define binding of each wake/request/echo/reply/charge to selected roles,queue cardinality/next wake and cause provenance;retain period2/echo1/charge cap3/wait1..16. No added memories/goals or changed wake behavior |
| Accepted packages | Exact package/catalog/hash/dependency fields,compiler/load signatures and durable accepted-package path. Distinguish existing display-only narrative pin from authoritative scenario pin;persist dependencies before reference;missing/hash-mismatched definition explicitly fails before publication |
| Compatibility | Select exact type/schema/rules fingerprints and versioned feature path without widening old v1 validators. Specify old-save selection,scenario-save resume/load and package-unavailable errors. No automatic migration or rewrite;any format/migration change requires CP05 contract review and an explicit bounded order |
| Input / projection | Exact bootstrap/new-game selector and client request/projection signatures;how identities/labels survive load,retry,reconnect. Update generated wire bindings from canonical Python source,never edit generated C# as separate authority. No hot scenario switching |
| Error priority / boundary | Exact diagnostic codes/paths and priority for unknown/duplicate keys,wrong exact types,bool as int,missing IDs/cross-links,invalid cell,overlap,package rejection,wrong compatibility pin. Failure preserves files,attachment,CORE/protocol and displayed input/history as applicable |
| Samples / vectors | Two literal legal role/layout configurations and independently derived normal/blocked/attack/NPC/load/replay traces. Include cells→mm,HP/stamina/tick,count/queue/hash expectations and rejection preservation;no copied v1 goldens |
| Edit / verification scope | Exact absolute NEW/MODIFY paths and symbols after contract resolution;select existing owned routes/helpers first. Name actual test nodes/native scenarios,commands,performance measurements and public readers before coding READY |

Contract-design acceptance:every row complete,all source consumers accounted for,independent
vectors hand-derived,existing accepted contracts preserved and no unresolved version/ownership/error
semantics. Runtime DRAFT is a contract-readiness state,not a fabricated environment blocker.
The next authorized design task may edit this order plus its NEW contract artifact/progress;
it must establish its own concrete allowed paths/baseline. This routing grants no runtime authority.

## 5. Future Implementation / Acceptance Sequence

1. Complete §4 contracts and exact coding edit scope;refresh baseline and verify current-host
   tools through [workstation setup](../WORKSTATION_SETUP.md). Existing device evidence does not
   qualify another machine. Resolve CP05 applicability before any changed save/quest contract.
2. Implement typed definition/compiler/reader and role binding with one registered bootstrap path.
   Validate packages before new-game creation;pin accepted data for save/replay. Existing rejected
   package/codec/lifecycle risks from [CP01](../reviews/RS-REVIEW-CP01_DISPOSITIONS.md) must be
   assessed against actual new consumers,not automatically escalated into a structural rewrite.
3. Register admission,engines,reducers/codecs,checkpoint validation and presenters consistently.
   Run two independent headless scenarios;prove no old-target leakage or mutation before COMMIT.
4. Wire worker,committed-fact Korean narration,bridge/generated DTOs and Unity projection.
   Select each scenario in a fresh owned working directory;verify gameplay and its own load/resume.
5. Execute necessary focused normal/boundary/error/integration/replay tests;shared CORE changes
   require full regression. Run [README verification commands](../../README.md#verification),plus
   affected formatter targets and [Unity native workflow](../../clients/unity/README.md#generate--verify--build)
   extended with actual two-scenario cases. The existing fixed-room verifier alone cannot qualify B.
6. Record actual CP03 packet and await feedback before further scenario/world/bulk expansion.

Future test responsibilities (PLANNED;exact new nodes/paths assigned at contract completion):

- Definition/compiler:exact types and integer wire strings,closed fields,empty/boundary values,
  duplicate/reference errors,hash/qualification checks,deterministic output,failed publication preservation.
- Headless integration:both role/layout configurations through registered real callers,gate/occupied
  movement,attack/rest/death and invalid target,wait/wake/bell/echo chains. Swap all role IDs between
  legal fixtures;results follow definitions rather than old constants. Same-rules label-only edits
  cannot change authoritative outcomes unless explicitly included in a pinned package identity.
- Persistence/replay:save midcombat,before NPC wake,load and continue;wake/attack occurs once;
  exact retry uses prior fingerprint;bad/missing package and wrong pins preserve old owner.
  Frozen accepted package plus seed/trace reproduces state,protocol,events and relevant hashes.
- Client/native:projected cells/labels/tick/HP/counts match both Brain sessions;load resets history,
  failure preserves it;reconnect uses loaded branch;request failure/input polling/shutdown remain usable.
- Compatibility:original prototype and original replay goldens unchanged;accepted old saves remain
  explicitly supported or explicitly rejected according to approved policy,never silently reinterpreted.

Completion requires actual source,registered consumers,two independent live samples,focused and
required full checks,save/load/replay/error preservation,portable evidence and checkpoint dispositions.
Performance remains UNVERIFIED until cold/warm load memory/time and actual client frame samples
are recorded;use existing A10/A13 targets and declare device/scenario/method,not new unsupported numbers.

## 6. Checkpoints and Holds

- CP03:trigger after first generalized two-scenario playable segment and native acceptance;
  hold further scenario/world/bulk imports. Packet includes refreshed HEAD/diff/hashes,contracts,
  actual callers/tests,independent vectors,logs/screenshots and save/replay limitations. Obtain
  actual Claude feedback,validate dispositions,repair/retest before DONE. No automatic provider call.
- CP05:conditional preimplementation contract review if §4 changes save format/compatibility or
  introduces major quest/NPC-memory semantics;postimplementation review remains separately required
  under the [checkpoint register](../../BACKLOG.md#claude-checkpoints-and-defect-repair--2026-10-07).
  The first scope excludes new quest/memory mechanics;scenario-package persistence still needs an
  explicit applicability decision. Do not assume the existing empty-package format already supports it.
- CP04 retains accepted prototype status;final engine/bulk art decisions remain separate.
  No checkpoint is closed by this authoring delivery.

## 7. Authoring Acceptance — 2026-10-13

Source inventory and clean entry baseline recorded;all22required template fields present.
`.venv/Scripts/python.exe -` document audit:exit0;4UTF8 files/balanced fences,
160local links/10fragments,9unchanged source SHA256 witnesses,exact4-file delivery scope and
unchanged HEAD PASS. `git diff --check`:exit0. Actual diff self-reviewed against authoring scope
and existing contract/checkpoint limits. Python printed the preexisting launcher-location diagnostic
before completing the audit;no environment repair needed for this successful document check.
Runtime remains DRAFT because §4 contracts are not settled. Two scenarios are acceptance scope,
not implemented worlds. Gameplay/Unity/full tests/remote CI NOT_RUN for this document-only task.
No publication.

## 8. Implementation / Native Acceptance — 2026-10-13

Director subsequently authorized remaining design/code/tests. [Embedded contract](QT-F02_SCENARIO_CONTRACTS.md)
resolves §4 for this first scope without new save format/package storage. [Actual receipt](../reviews/QT-F02_EXECUTION_2026-10-13.md):
1304full/332focused/47native checks/build/hook-absence and required static/document checks PASS.
Two independent live scenarios,legacy compatibility and old-target/wrong-save rejection verified.
[CP03 packet](../reviews/RS-REVIEW-CP03_REQUEST.md) prepared;actual feedback NOT_RECEIVED.
Parent remains READY_FOR_REVIEW;further world/bulk expansion held. No publication.

## 9. CP03 Feedback / Repair Acceptance — 2026-10-13

Actual static subset feedback received;[verified dispositions/repairs](../reviews/RS-REVIEW-CP03_DISPOSITIONS_2026-10-13.md)
accepted:1360full/133focused/47native/build/static checks PASS. F1–F4 repaired;F5 generic
programmatic display label intentional. Original witness/ZIP preserved,repaired witness separate.
QT-F02/CP03 DONE for this first embedded scope only;external packages/world/quest/bulk and release
remain later authorized orders. No full independent/runtime/C# or external patch rereview claim.
