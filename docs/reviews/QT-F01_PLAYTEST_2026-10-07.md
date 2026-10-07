# QT-F01 — Thin Client Playtest

Date:2026-10-07 | State:DONE (feedback / next-order authoring) | Human feedback:RECORDED / original UX_NOT_ACCEPTED
Authorization:director requested backlog execution in order,starting with the first pending item. Scope:existing Tk harness playtest,not new gameplay/engine/assets/policy/commit/push.
References:[backlog](../../BACKLOG.md),[accepted client order](../work_orders/RS-P1-QUALITY.md),[run instructions](../../README.md).
Baseline:HEAD b0f98e2aa19c5db11d0c746226d4bf321b34dee8;existing dirty quality/client/document changes preserved. No production/test/config edits in this playtest.

## Fresh checks

Commands use `.venv/Scripts/python.exe` from `C:\ReverieSaga`.

| Check | Actual result |
|---|---|
| `-m pytest -q tests/integration/test_client.py --basetemp .pytest_cache/qt-f01-baseline` | Exit0;15PASS4.69s |
| `-m ruff check src tests` | Exit0;PASS |
| `-m ruff check --config ruff-quality.toml src tests` | Exit0;PASS |
| `-m app.client --help`,with `PYTHONPATH=C:\ReverieSaga\src` | Exit0;PASS |
| Existing integration-test coverage | Combat/rest/blocking/rejection,NPC/wait,save/load/retry/resume,real withdrawn Tk buttons/rendering,worker drain and protected invalid files |
| Full suite/types/dependency/replays | NOT_RUN this task;previous1221PASS is historical,not a fresh result |

One help invocation omitted PYTHONPATH and failed with ModuleNotFoundError;the documented environment resolved it without source changes.

## Actual window observations

- Isolated test root:`C:\ReverieSaga\tmp\playtest\qt-f01-17a79d8a`;no existing player save replaced. Local test saves/logs are not release assets.
- Sandboxed launches ran but were absent from the desktop helper's window inventory. Two idle task-owned processes were stopped;an approved unsandboxed launch exposed the real titled window. No security/settings/helper changes.
- Windows Computer Use returned one matching game window and captured its initial ATTACHED screen:3×3 map,player/wall/door/enemy/NPC,HP3/3,enemy5/5,stamina2/2,tick0,controls and active path. Initial Korean labels were visible/readable in the captured layout.
- A planned Right-key action was refused because user input was detected. Re-observation showed tick8/revision8,NPC bells4,charge3 and COMMITTED. User actions are unknown;this is not evidence that the agent executed the intended sequence. Automation stopped to avoid competing with the user.
- The visible process subsequently exited0 and the matching window disappeared. A fresh `controlled.sqlite` launch also exited0 before window selection;no interactive action coverage is claimed from it. No task-owned game process remained at the final process check.
- The director subsequently supplied usability feedback:the screen is too crude,lacks a bottom dialogue/action explanation panel identifying who attacked whom and what happened,and has no visual appeal. They asked about Unity/Unreal and modeling-AI integration. This is negative product feedback,not successful usability acceptance or a final engine/provider selection.

## Findings / next

- UX-01:the observed screen displays raw English status/schema identifiers such as COMMITTED and encounter.attack-cue. Candidate improvement:keep diagnostics available but add understandable Korean action/result/rejection explanations. This is a usability finding,not a proven simulation defect or authorization to change public contracts.
- No new simulation defect was established by the fresh tests/window observations. This does not prove bug-free behavior or human usability acceptance.
- Human feedback is now recorded;the exact manual action checklist remains UNVERIFIED. Requested direction:understandable bottom action/dialogue history plus an actual graphical vertical slice,not another claim that Tk circles qualify as the game's visual prototype.
- Entry source diagnosis:`app.client_session.ClientSession._publication` discarded cue payload details and kept only `schema.kind`;`app.client.PlayWindow._render` joined those names into one notice label. Existing `contracts.encounter.AttackCue` already carried actor/target and before/after HP/stamina. The subsequent action-log task now formats committed facts without a per-turn LLM or new combat rules.
- Order requirements to settle next:renderer-neutral bounded Korean action history and rejection/load/retry semantics;one provisional 3D client and typed Brain bridge;one tiny room with a few licensed/import-verified assets,low-resolution rendering and minimal movement/hit/defeat feedback. Choose one client engine,not both Unity and Unreal. Provider generation/export and runtime asset loading are separate stages;no purchase/install/API use implied by this feedback.
- Director follow-up:graphics may wait;record and immediately implement action explanations. [Bounded RS-CLIENT-002 order](../work_orders/RS-CLIENT-002_ACTION_LOG.md) authored and accepted,final1242PASS283.95s plus real desktop combat/save/load explanation checks. QT-F01 DONE means feedback/next-order work completed,not approval of the original or updated graphical UX. No bulk assets/new engine integration.
- Final HD-2D,camera/gamepad,3D assets,MIN-SPEC,release QA and remote CI remain UNVERIFIED/out of scope.
