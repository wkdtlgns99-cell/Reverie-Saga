Still reviewing CP04: BrainConnection.cs is read and I've noted a few issues. Next up are PlayRoom.cs, LiveVerification.cs, the build script, and the native evidence.Still on CP04: the ledger is the last data file to check (does it stretch the six-entry qualification to the other 320?), and then I'll write the report.# CP04 Review: First Native Unity / Narrative Sample

## 0. What I opened and ran

```yaml
review_type: independent source/document review + partial Python execution
not_legal_clearance: true
not_release_or_final_engine_clearance: true
archive: RS-REVIEW-CP04_2026-10-12.zip   # 176 files, all listed/opened by role
opened_in_full:
  - src/app/engine_bridge.py, src/app/engine_project.py, src/app/client_worker.py, src/app/client_session.py
  - src/contracts/client.py, src/contracts/narratives.py, src/adapters/narrative_catalog.py
  - clients/unity/Assets/Reverie/Scripts/{BrainConnection,PlayRoom,LiveVerification,Wire.Generated,CatalogPin.Generated}.cs
  - clients/unity/Assets/Reverie/Editor/PlaytestBuild.cs
  - content/narratives.json, content/narratives.manifest.json
  - docs/reference/QUILLTALE_SELECTION_LEDGER_2026-10-12.json (structure + aggregate checks, not all 326 rows)
  - docs/reviews/QT-F04_GENERATION_EVIDENCE_2026-10-12.json, docs/work_orders/QT-F04_GENERATION_TERMS.md
  - docs/work_orders/QT-F06_NARRATIVE_IMPORT.md, RS-CLIENT-003_NATIVE_EVIDENCE json, BACKLOG CP04 rows
  - tests/integration/test_engine_bridge.py, tests/unit/test_narrative_catalog.py
  - the screenshot PNG (viewed)
checks_actually_run:
  - SHA-256 + byte length of all 174 witness-listed files: ALL MATCH; request hash and screenshot hash match
  - new tests (test_narrative_catalog + test_engine_bridge): 15 PASS
  - governance tests with import-linter installed: 79 PASS
  - runnable subset (6 files excluded, see C-8): 296 passed / 84 failed, all failures trace to files absent from the bundle (C-8)
  - my own repro of bridge failure paths (corrupt working file, empty-slot load, retry/recover with nothing pending)
not_run:
  - Unity (editor/player), C# compile, any of the 17 native checks
  - mypy/ruff, tkinter client test, the 5 test files that need absent vectors
  - network fetch of pinned GitHub sources; provider-terms pages
  - baseline diff, so "Python modules/oracles/locks unchanged" is UNVERIFIED (no baseline in bundle)
```

C# findings are from source reading only. Where I reproduced the Python half, I say so.

## 1. Verdict

The bounded path is sound on its main claims. The renderer only sends string intents, and the Python side builds every command from a fixed table. Framing, decimal strings, request/attachment identity and cleanup are done carefully and tested on the Python side. I found no CORE-mutation violation.

There are, however, real defects in error visibility, schema-hash coverage, a latent frame/catalog coupling, the qualification guard and ledger labeling. Weak native oracles and an incomplete packet also limit what the "17 PASS" can prove.

## 2. Answers to Q1–Q6

| Q | Verdict | Basis |
|---|---|---|
| 1. CORE-only mutation / derived-view ownership | **Validated** (bounded) | `PlayRoom` calls only `brain.Send(intent)`. `engine_bridge.request` allows 16 fixed names, `slot0[1-8]`, and `seconds` 0–16. `ClientSession._payload` maps intents to commands. All state flows back as `asdict(ClientUpdate)` through the `wire()` whitelist. One observation: `working_path` (an absolute local path) is sent on every update. It isn't displayed, and I treat it as hygiene only. |
| 2. Frame/UTF-8/decimal/identity/threads/cleanup | **Mostly sound; 3 gaps** | Python: 4-byte BE length, 1..16 KiB request cap, strict decimal regex, monotonic request ids, stale-attachment gate, single-thread executor. C#: strict UTF-8 decode, 1 MiB cap, `ConcurrentQueue`s, single in-flight. A test confirms the child exits on stdin EOF. Gaps are C-1, C-3 and C-4. |
| 3. Load/failed-load/retry/reconnect | **Python semantics verified; Unity partly unverified** | I reproduced `load` on an empty slot (status `SAVE_NOT_FOUND`, view preserved) and `retry` with nothing pending (`NO_RETRY`). The Unity-side kill is tested only when idle, and the standalone player never launched. |
| 4. Generated C# / coordinates / evidence | **DTOs match; hash gap; evidence narrow** | `WireView` has 16 fields, `WireUpdate` 7, `WireNarrative` 4, matching the dataclasses. Coordinates `x = cell % width`, `z = -(cell / width)` are consistent with the camera. See C-5, C-6, C-15. |
| 5. Narrative schema/guard/ledger scope | **Boundary held; guard shallow; ledger over-labeled** | No mechanics fields. The loader rejects unknown fields and the six original fields are preserved. The guard and ledger issues are C-10, C-11 and C-12. |
| 6. Defects | See section 3. | |

## 3. Findings

Severity is my judgment. Class is one of: DEFECT, DOC, PACKET, LATENT, POLICY, UNVERIFIED.

| ID | Sev | Class | Location | Finding | Bounded fix | Acceptance check |
|---|---|---|---|---|---|---|
| C-1 | Med | DEFECT | `PlayRoom.cs` `Update()` | `if (!reply.has_view …) throw "No playable view"` runs before `reply.error` and `messages` are read. **I reproduced the Python half:** a corrupt working file yields `has_view=false`, `status=SAVE_CORRUPT`, and a clear Korean message. The Unity UI will therefore show only "No playable view". | On `!has_view`, put `update.status` and `update.messages` into `failure`. Check `error` first. | Native check with a corrupt file in a fresh directory: `room.Failure` contains `SAVE_CORRUPT`. |
| C-3 | Low | DEFECT | `engine_bridge.serve` + `BrainConnection.Poll` | `INVALID_REQUEST` is sent with `request_id "0"`. C# expects the in-flight id, so it reports "Unexpected response identity" and disposes (kills) the child. The real code is hidden. Python's malformed-JSON test checks the code but not this C# consequence. | Echo the parsed id when available, or have C# treat id `"0"` with a non-empty `error` as a protocol error and show it. | A malformed-request test whose C# side shows `INVALID_REQUEST` and keeps the process alive. |
| C-4 | Low | LATENT / UNVERIFIED | `BrainConnection.Poll`/`Dispose` | The 10 s timeout calls `Dispose()` on the main thread, which can block about 10 s (`WaitForExit(5000)` + `WaitAll(5000)`). The native `disconnect_visible` check kills only an **idle** child. A kill during an in-flight commit is untested at the Unity level, and the UI exposes no `recover` (bridge supports it, `Label()` throws on it). | Dispose off-thread or with a shorter bound. Add a kill-while-awaiting check. Decide whether `recover` must be exposed after a kill. | Native check: kill during an in-flight `attack`, reconnect, view equals the pre- or post-commit state, never a duplicate. |
| C-5 | Low | LATENT | `PlayRoom.Apply` | The board (width, height, walls) is built once from the first view. Later views' size or walls are ignored, and `Position()` uses the new width. The camera is fixed at `orthographicSize 4`, though bounds up to 64×64 pass validation. Fine for the fixed 3×3 room. | Assert later width/height equal the first, or rebuild. Document the limit. | A view with different dimensions fails visibly or rebuilds. |
| C-6 | Low | DOC | `LiveVerification.cs` | Weak oracles. `failed_load_preserves_state` passes for any status except `LOADED`, so it doesn't assert `SAVE_NOT_FOUND`. `input_after_reconnect` sends `wait` and asserts `actor_cell == "8"`, which `wait` doesn't change, so it doesn't prove the command ran. | Assert `status == SAVE_NOT_FOUND`. Assert `tick` increments after reconnect. | A build that drops `wait` fails `input_after_reconnect`. |
| C-7 | Low | DEFECT (hygiene) | `LiveVerification.cs` | A `RuntimeInitializeOnLoadMethod` hook is compiled into player builds, activated by env `REVERIE_UNITY_VERIFY=1`. It kills a process by PID and writes files. A test hook ships in the player. | Guard with `UNITY_EDITOR \|\| DEVELOPMENT_BUILD`. | Release build contains no verification hook. |
| C-8 | Med | PACKET | whole archive | The request promises "actual source, contracts/tests", but required test inputs are absent: `tests/replay/fixtures/{encounter,skeleton}_v1.json`, `docs/work_orders/*_REFERENCE_VECTORS.json`, `docs/ENGINEERING_ENFORCEMENT.md`. Five test files fail at collection, and a further 84 tests fail in the subset I ran. `tkinter` is also needed for `test_client.py`. The 1285-PASS claim can't be reproduced from the bundle. | Add the missing files to the allowlist (or list them as excluded with reasons) and document `tkinter`/`import-linter` as prerequisites. | A fresh unzip + `pytest` has no `FileNotFoundError`. |
| C-9 | Med | DOC | evidence JSON `source_file_raw_sha256`; ledger `source_files[].raw_sha256` | These hold the **LF-normalized** hashes from QT-F04 (e.g. `594ae8b9…`). The dossier's recorded hashes for settlement, quest and monster are different. Unless "raw" means git-blob bytes, the label is wrong. This is a recurrence of the earlier D-1 theme. | Add a legend or rename: `git_blob_sha256`, `worktree_sha256`, `normalized_lf_sha256`. | For each of the 4 files, all three hashes are listed with the transform and reproducible. |
| C-10 | Med | DOC / scope | ledger `entries[*].generator`, `terms_scope` | All 326 entries carry "GPT/Gemini collectively…" and "QT-F04 consumer-web terms…". QT-F04's decision scope is the six named selections only, with "no blanket corpus". The 320 queued/rewrite entries read as covered. | Set `terms_scope` for the 320 to `NOT_QUALIFIED (QT-F04 covers 6 only)` or add `qualification: NONE`. | Count of entries claiming qualification equals 6. |
| C-11 | Med | DEFECT (guard) | `engine_project.build_sample` | The "qualification guard" checks only `sha256(dossier) == evidence.candidate_dossier_sha256`. It doesn't read the evidence rows (per-candidate `QUALIFIED_…`, candidate-id set, `decision_scope`). The manifest's `qualification` and `approval` strings are hard-coded constants, not derived from evidence. The guard proves "this dossier version was inspected", not "these entries are qualified". The test covers only a one-byte dossier edit. (By code reading; not executed.) | Require each of the six ids to have `qualification == QUALIFIED_FOR_FUTURE_NARRATIVE_ADAPTATION` in the evidence and copy that value. Fail on any other id. | Mutating one evidence row's qualification (dossier hash unchanged) makes `build_sample` fail. |
| C-12 | Low | DOC | dossier/evidence `runtime_imported: false` | Six entries are now loaded and displayed from the compiled catalog. The flag is true for the dossier but can read as stale. | One line: "dossier is not consumed at runtime; `content/narratives.json` is." | Wording present in QT-F06 and the inventory. |
| C-14 | Low | LATENT | `engine_bridge.py` | The full narrative catalog is re-sent in every response, and `MAX_CATALOG_BYTES` (1 MiB) equals `MAX_FRAME` (1 MiB). A near-cap catalog plus view would exceed the frame, and `write_frame` raises `RESPONSE_CAPACITY` outside the inner `try`, which ends the session (exit 1). Harmless at 6 entries. | Send the catalog once (attach only) or cap it well below the frame. | A max-size-catalog test passes or fails with a visible error. |
| C-15 | Low | DEFECT | `engine_bridge.py` `SCHEMA_HASH` | The hash covers request fields, request names, `ClientView` fields and `Narrative` fields. It does **not** cover `ClientUpdate` fields or the response keys, so adding an update field changes `Wire.Generated.cs` but not the runtime hash. `generate_wire()` also maps tuple fields by hard-coded name, not by type. The repo-level `generate_wire() == file` test catches repo drift only. | Include update/response fields in the hash. Map by type. | Adding a `ClientUpdate` field changes `SCHEMA_HASH`. |

## 4. Evidence vs claims (Q4)

I viewed the screenshot (1101×506; hash matches the witness). It supports these claims:

- Korean text renders.
- The 3×3 board draws.
- The HUD matches the final view (HP 1 / enemy 0 / stamina 0, tick 14, 7 bells).
- The imported catalog description is displayed.
- The NPC and player sit at cells 6 and 8.

It does not show the enemy (hidden at hp 0), the closed door, or any input path, and it is a single final-state frame. Wall and floor are only weakly distinguished.

The performance figures are editor-only, 120 frames on a 9-tile scene (median 1.7 ms, p95 2.6 ms), and are labeled as such. They support no claim beyond "the prototype scene is trivially cheap". They are not MIN-SPEC evidence. The standalone player's launch is `BLOCKED_WINDOWS_APPLICATION_CONTROL`, so standalone runtime is UNVERIFIED, as the request says.

## 5. Intentional policy and false positives

- Full views each response, the private-pipe route (not TCP/diff/ACK), and the Windows-only `.venv/Scripts/python.exe` path are provisional and documented.
- The repo-relative layout (`Application.dataPath/../../..`) ties the player to `tmp/unity-build/`. Packaging is pending, as stated.
- `reply.error != ""` is treated as session-fatal. That's acceptable for a prototype, but it means the bridge's recoverable error paths (`STALE_*`) are unreachable from this client.
- The SearchDatabase startup exception is a separate Unity issue and I have no evidence either way.
- **False positive:** `activeInputHandler: 0` means the legacy Input Manager, so `Input.GetKeyDown` is valid.
- **False positive:** the ledger's 326 = 215 + 82 + 14 + 15 matches, and its entries are unique and carry no mechanics in `selected_fields`.

## 6. Rights and external evidence (no clearance)

- The six qualifications rest on director testimony, self-review and provider-term reading. I did not fetch the provider pages and make no copyright, non-infringement or ownership finding.
- QT-F04 says "AI-expanded details with reported structural inspiration". That reliance on testimony is unverifiable from the bundle.
- CP03 still precedes bulk scenarios or content, as your own documents state.

## 7. Suggested status line

`CP04: independent source review RECEIVED (C# by reading only; Unity not run). Hash witness PASS; new tests 15 PASS. Findings C-1,C-3–C-12,C-14,C-15 open; C-8 packet gaps. CORE-only mutation path validated. Standalone runtime, rights, CP03 unchanged. Not DONE until C-1/C-11 repaired and findings dispositioned.`