# RS-REVIEW-CP04 — First Native Unity / Narrative Sample

Date:2026-10-12 | Feedback:NOT_RECEIVED | Review requested:independent implementation review.
Director manually supplies this packet to Claude and pastes its reply unchanged. No provider API
calls were run. Review is not legal/release/final-engine clearance. Files/hash/byte-length witness
is RS-REVIEW-CP04_INPUTS.json;its final SHA is anchored in the director delivery outside this set.
The archive includes actual source,contracts/tests,Unity project and sanitized observed evidence.
Raw account/license/logs/private saves/build binaries are excluded. Included tests do not prove
Claude ran them;please label checks actually run vs document/source inspection.

Baseline HEAD:53071474bc9027749ac32b3189b9a6c7a062ab67;local reviewed implementation is uncommitted relative to that baseline.
Publication may later have a different Git HEAD;reviewed exact file hashes are authoritative.
Request/manifest/archive are excluded from the reviewed-file hash set to avoid circularity.
The witness separately hashes this request;archive SHA is delivered separately.

## Actual result / retained limits

Unity6000.3.25f1 signed editor installed and Personal license active. Real graphical room routes
commands through one private-pipe Python child and existing ClientWorker/durable CORE;scene
positions/UI reflect only derived DTOs. Python game modules/oracles/locks unchanged. Generated
DTO/schema hash and canonical decimal strings;bounded closed requests/attachment/request IDs;
full views in this provisional pipe route,not production TCP/diff/chunk/ACK.6adapted descriptive
catalog entries actually load/display. They do not create6worlds or executable quests/monster
abilities.326entry selection ledger is a review/queue artifact,not runtime import approval.

Final fresh editor build/play exit0,17checks PASS;actual PNG visually inspected. Current unsigned
standalone player build succeeds but Windows application control blocks launch. First player run
before repair exposed missing shader;real Resources material is now included/rebuilt. Standalone
runtime therefore UNVERIFIED. First native failure-load probe accidentally shared old slots and
failed;fresh-directory preflight and17PASS repair retained in receipt. Unity SearchDatabase
startup exception remains separate;intentional own-child kill produces expected visible error
before reconnect. No checks/oracles/security policies were weakened. Human UX,HD-2D art,
portable packaging,MIN-SPEC/full-world scenario generalization remain pending.

## Questions

1. Does actual PlayRoom→BrainConnection→engine_bridge→ClientWorker wiring preserve CORE-only
   mutation and derived-view ownership? Find a concrete violation or validate the bounded path.
2. Check frame/JSON/UTF8/decimal/schema/identity/attachment handling,stdout/thread/UI/timeout
   ownership and cleanup. Are any errors hidden,state partially applied,or processes orphaned?
3. Check load/failed-load/retry/disconnect/reconnect and history behavior against existing
   durable semantics and independently expected tests. Distinguish editor17checks from blocked
   standalone runtime and production lifecycle/packaging requirements.
4. Verify generated C# declarations match actual Python dataclasses;renderer coordinates/ranges
   and primitive material inclusion are correct. Does the measured/screenshot evidence support
   only the claims made? Report visual/input/performance limitations rather than assumed QA.
5. Check new frozen narrative schema/compiler qualification-dossier guard/hash-pinned loader,
   original6field/provenance preservation,and326ledger's explicit non-runtime scope. Identify
   accidental mechanics/old bindings or unqualified automatic import. CP03 still precedes bulk
   scenarios/content;6descriptions are a first sample only.
6. List actionable defects with file/line,independent reproduction/expected outcome and bounded
   fix. Classify confirmed defect/documentation/intentional prototype policy/false positive/
   unresolved external evidence. No blanket legal/copyright clearance.

## Reviewed dirty snapshot before packet creation

```text
M .gitignore
 M BACKLOG.md
 M GAME_SYSTEM_SUMMARY_KO.md
 M README.md
 M SESSION_HANDOFF.md
 M docs/work_orders/RS-CLIENT-003_ENGINE_PLAYTEST.md
?? clients/unity/Assets/Reverie.meta
?? clients/unity/Assets/Reverie/Editor.meta
?? clients/unity/Assets/Reverie/Editor/PlaytestBuild.cs
?? clients/unity/Assets/Reverie/Editor/PlaytestBuild.cs.meta
?? clients/unity/Assets/Reverie/Resources.meta
?? clients/unity/Assets/Reverie/Resources/Placeholder.mat
?? clients/unity/Assets/Reverie/Resources/Placeholder.mat.meta
?? clients/unity/Assets/Reverie/Scenes.meta
?? clients/unity/Assets/Reverie/Scenes/PlayRoom.unity
?? clients/unity/Assets/Reverie/Scenes/PlayRoom.unity.meta
?? clients/unity/Assets/Reverie/Scripts.meta
?? clients/unity/Assets/Reverie/Scripts/BrainConnection.cs
?? clients/unity/Assets/Reverie/Scripts/BrainConnection.cs.meta
?? clients/unity/Assets/Reverie/Scripts/CatalogPin.Generated.cs
?? clients/unity/Assets/Reverie/Scripts/CatalogPin.Generated.cs.meta
?? clients/unity/Assets/Reverie/Scripts/LiveVerification.cs
?? clients/unity/Assets/Reverie/Scripts/LiveVerification.cs.meta
?? clients/unity/Assets/Reverie/Scripts/PlayRoom.cs
?? clients/unity/Assets/Reverie/Scripts/PlayRoom.cs.meta
?? clients/unity/Assets/Reverie/Scripts/Wire.Generated.cs
?? clients/unity/Assets/Reverie/Scripts/Wire.Generated.cs.meta
?? clients/unity/Packages/manifest.json
?? clients/unity/Packages/packages-lock.json
?? clients/unity/ProjectSettings/AudioManager.asset
?? clients/unity/ProjectSettings/ClusterInputManager.asset
?? clients/unity/ProjectSettings/DynamicsManager.asset
?? clients/unity/ProjectSettings/EditorBuildSettings.asset
?? clients/unity/ProjectSettings/EditorSettings.asset
?? clients/unity/ProjectSettings/GraphicsSettings.asset
?? clients/unity/ProjectSettings/InputManager.asset
?? clients/unity/ProjectSettings/MemorySettings.asset
?? clients/unity/ProjectSettings/MultiplayerManager.asset
?? clients/unity/ProjectSettings/NavMeshAreas.asset
?? clients/unity/ProjectSettings/PackageManagerSettings.asset
?? clients/unity/ProjectSettings/Physics2DSettings.asset
?? clients/unity/ProjectSettings/PresetManager.asset
?? clients/unity/ProjectSettings/ProjectSettings.asset
?? clients/unity/ProjectSettings/ProjectVersion.txt
?? clients/unity/ProjectSettings/QualitySettings.asset
?? clients/unity/ProjectSettings/SceneTemplateSettings.json
?? clients/unity/ProjectSettings/TagManager.asset
?? clients/unity/ProjectSettings/TimeManager.asset
?? clients/unity/ProjectSettings/UnityConnectSettings.asset
?? clients/unity/ProjectSettings/VFXManager.asset
?? clients/unity/ProjectSettings/VersionControlSettings.asset
?? clients/unity/README.md
?? content/narratives.json
?? content/narratives.manifest.json
?? docs/reference/QUILLTALE_SELECTION_LEDGER_2026-10-12.json
?? docs/reviews/RS-CLIENT-003_EXECUTION_2026-10-12.md
?? docs/reviews/RS-CLIENT-003_NATIVE_EVIDENCE_2026-10-12.json
?? docs/reviews/assets/RS-CLIENT-003_playroom_2026-10-12.png
?? docs/work_orders/QT-F06_NARRATIVE_IMPORT.md
?? src/adapters/narrative_catalog.py
?? src/app/engine_bridge.py
?? src/app/engine_project.py
?? src/contracts/narratives.py
?? tests/integration/test_engine_bridge.py
?? tests/unit/test_narrative_catalog.py
```

Current dispositions/packet are not independent feedback. After manual feedback,verify each
finding,repair/retest valid defects,and close CP04 only under the canonical director checkpoint
procedure. Held downstream:final engine decision/bulk assets. QT-F02/CP03 remain separate.
