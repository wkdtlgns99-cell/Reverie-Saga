# QT-F21 — Keep Unity Controls and History Reachable

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/reviewer:self;no delegation.
Director requests Git synchronization and the next bounded implementation.
Primary5(screen/presentation);related6existing save controls,7native integration.

| Field | Contract |
|---|---|
| goal/non_goals | Repair the existing short-viewport history starvation. Separate scrolling controls from scrolling history;retain readable text and all existing controls. No art/camera/gameplay/save/IPC/content change or human UX acceptance claim |
| baseline | Clean0e06577,tracking branch up to date after actual git pull --ff-only. Remote main has separate QT-F02history;do not merge/revert later implemented work. Entry screenshot1101x506 leaves only about45pixels for history. Preserve scene bytes SHA2563157e6272f93a108ce80848f9d1352fdaa15f3ecae3e750e525763818b011b94 |
| prerequisites/read_files | ENGINEERING_RULES,SESSION_HANDOFF,BACKLOG,GAME_SYSTEM_SUMMARY_KO,MASTER§2.2,engineering prompt checkpoint/language rules,numbered guide,workstation setup,work-order template,actual PlayRoom/LiveVerification/PlaytestBuild/BrainConnection and Unity/root README |
| allowed_edit_paths | MODIFY C:/ReverieSaga/clients/unity/Assets/Reverie/Scripts/PlayRoom.cs,LiveVerification.cs in the same directory;C:/ReverieSaga/clients/unity/README.md,docs/WORKSTATION_SETUP.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md. NEW this order,docs/reviews/QT-F21_EXECUTION_2026-10-16.md;owned tmp/qt-f21 |
| forbidden_paths | CORE/Python/save/protocol/approval/content/assets/camera/policies/dependencies/frozen evidence. Native-generated scene may only be restored after proving generated-ID equivalence to entry |
| public_contract | Existing controls and Send/InspectMemory/InspectRecentMemory/InspectSlot/Reconnect unchanged. New private rendering helpers/scroll state. Editor/development-only layout observation fields may support actual GUI verification;absent from release |
| behavior/ownership | UI-only rectangles in pixels. Panel margin12,width min380/available screen,height available screen. Title24;inner margin6,gaps6. Remaining space after title/history heading is60%controls,40%history. Controls scroll separately;incoming messages auto-scroll history only. Existing availability/busy/error gates and200message cap remain |
| edge_policy | For tiny/minimized screens clamp dimensions to nonnegative values;no negative GUI rectangle. Qualification target>=320x240;below target usable area best effort. Long Korean labels wrap;action buttons use at most3columns,or2below330inner pixels. Empty/pre-attach/error controls remain scrollable;history scrolling stays enabled while busy |
| examples | At1101x506:panel380x482,inner368wide,title24;available scroll space410 =>controls246,history164. At320x240:panel296x216,inner284wide,scroll space144 =>controls86,history58. Control bottom remains reachable via its own scrollbar;the narrow-screen example is arithmetic,not actual device qualification |
| algorithm_steps | Record entry evidence;implement bounded rectangles and extract control/history drawing;native check viewport separation,top/bottom scrolling and unchanged committed/save state;run existing normal/legacy/error native flows and release build;self-review and synchronize progress |
| wiring | Existing PlayRoom.OnGUI renders normal runtime. Existing LiveVerification observes real GUI after Repaint and captures top/bottom control scroll states without fabricating domain responses |
| performance | O(200messages+fixed controls),no per-frame IO/provider call. Reuse existing120frame native measurement;no new performance threshold/benchmark claim |
| baseline_commands | Git status/pull successful after permitted FETCH_HEAD access;Python3.13.12/Tk8.6/pip check and editor6000.3.25.14801824 verified. Restricted license query unavailable;permitted CLI active/signedIn=true |
| verification_commands | Existing README Ruff(shared/selective),scoped format,mypy/import/pip gates and affected client/bridge tests. Sequential actual editor Verify(default/old quest/legacy/harbor/grove/corrupt) and BuildAndVerify legacy using fresh owned saves;inspect captures and release-hook exclusion. Unchanged Python full1741PASS remains historical,reused rather than fresh full claim |
| test_responsibilities | LiveVerification:actual positive control/history bounds,gap,scroll range,bottom reachability,rendered captures,UI-only state/file preservation. Existing native actions independently check quest/reward/retry/load/reconnect/memory/slot/errors. No tests that merely match source formatting |
| acceptance | Separate nonoverlapping visible history at actual host viewport;controls bottom can be reached;no automatic history-to-controls jump. Native mode actions/build pass;actual image inspection;source contracts/scene preserved;three progress files agree |
| claude_checkpoints | NOT_TRIGGERED:bounded presentation repair under existing closed CP03/04/05contracts. V3full review remains deferred/incomplete;CP06release held;human UX/device/standalone qualification remains separate |
| stop_conditions | Overlapping user changes,changed domain/contracts,unavailable actual editor after safe retries,or generated scene changes beyond proven IDs;retain evidence and report limit |
| delivery | Local implementation/receipt/progress only;no commit/push/merge/reviewer call/agent/automatic next task |

Acceptance:[actual execution](../reviews/QT-F21_EXECUTION_2026-10-16.md):native307PASS/seven modes,
Windows build/hook absence,Python51PASS/static/imports PASS;actual1101x506captures inspected.
Narrow320x240/device/human UX/release not qualified;no broader game completion claim.
