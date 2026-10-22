# QT-F47 — Cycle self-activity execution

Date:2026-10-23. Status:LOCAL_ACCEPTED. Executor/self-review:current Codex,not independent.
[Order](../work_orders/QT-F47_CYCLE_SELF_ACTIVITY.md). Primary4retrieval support;related5/6/7.
D2OPEN,CP06held,earlier patch rereview DEFERRED.

## Inputs and implementation

Entry main6dc918e plus9F46dirty paths. Entry diff and F46delivery manifest retained under
tmp/qtf47/;F46test/order/receipt preserved. No Git publication or source rollback.
Installed .venv CPython3.13.12/Tk8.6 and pinned Unity6000.3.25f1 reused;no dependency install.

ClientSession.inspect_activity now uses cycle_activity_messages inside the existing
source-read/error boundary. Private _ActivityFactory selects the existing cycle bundle
for exactly one canonical isolated replay. Final core AND protocol must match the live
committed checkpoint. Existing memory/work factory defaults and conversation recall stay
unchanged. There is no new authoritative calculation,storage,feature/catalog pin,wire,
content,LLM call or game command.

Existing cycle_messages prefix remains exact,including current supply and latest4real
own-action anchors. A separate source-checkpoint heading and latest8mixed bell/reply
events follow. Existing event-ID tie ordering is reused. Frequent bells cannot evict the
separate supply memories. Checkpoint-only sources show persisted supply but explicitly
decline to reconstruct missing bells/replies from counters. Wrong owner/missing cycle/
replay/head mismatch rejects as NPC_ACTIVITY_SOURCE;IO errors log and preserve live state.
Worker polling/retry continue;process-control propagates.

## Verification

Environment for commands:README PYTHONPATH=src,PYTHONUTF8=1,PYTHONHASHSEED=0 where applicable.
Retained logs/artifacts:tmp/qtf47/.

| Command/selection | Actual result |
|---|---|
| pytest new test_cycle_activity_retains_bells_and_persisted_supply_readonly,before implementation | exit1,1FAIL2.70s;cycle inspection omitted all8expected bell rows(red.log) |
| pytest test_cycle_self_activity.py | exit0,13PASS19.62s(new.log) |
| pytest affected activity/work/call/cycle/cycle-player/slot/client/bridge selection | exit0,161PASS261.72s(affected.log),includes the13new cases |
| exact CI rulebook/integration boundaries | exit0,31PASS23.01s(boundaries.log),process-only exact safe.directory,no global Git change |
| README shared Ruff and ruff-quality.toml src/tests | both exit0,PASS |
| README scoped format plus npc_activity/new test | exit0,14already formatted |
| mypy --no-native-parser | exit0,205source files,PASS |
| Import Linter type-inclusive/runtime --no-cache | exit0,3+1contracts KEPT |
| pip check | exit0,no broken requirements |

New tests independently settle bell2..16,caps6..20/26..40,distinct same-tick reply/bell,
same-tick20use/prepare,empty checkpoint16with count8but no events,continuation18/20,
current/previous restore/restart/source bytes,corrupt trace/wrong owner/stale core/protocol/
missing cycle,IO failure/retry/polling/process control and actual binary-pipe/Tk consumers.
Representatives:16second query225.713ms,40second query500.656ms,under TARGET2s.

## Native verification and unavailable editor recovery

Original editor34400 remains open/responding. Windows Computer Use selected its real
returned window;capture timed out. Fresh window selection/activation recovery failed with
`no monitor found for window`;no further UI input attempted. Temporary editor-only trigger
was added to invoke the existing Verify Current Selection menu through ExecuteMenuItem,
but the idle editor did not refresh it:unchanged log,no F47marker/path. Removed the owned
trigger and its optional .meta without execution;no persistent test hook remains.

Used documented unavailable-editor isolation fallback:156byte-identical Assets/Packages/
ProjectSettings/src/content input files copied under tmp/qtf47/native-root;local junction
reuses the repository .venv. No copied credentials/private saves/new installation. Original
scene/source/editor preserved;only isolated project preparation writes its own scene/settings.
Both runs use installed6000.3.25f1 graphical Verify with explicit automated exit mode.

- First isolated editor36356:109PASS/0FAIL,ENGINE_VERIFY_PASSED and RESULTcode0.
  It exited before a later OS exit-handle lookup;that lookup failed(process absent),so
  its OS exit code is NOT_CAPTURED rather than inferred from application logs.
- Same unchanged snapshot,second fresh owned save,editor27308:109PASS/0FAIL and actual
  waited process exit0. Repeated solely to close the required automated-exit evidence gap;
  no tests/sources were changed. Logs unity.log / unity-exit-qualified.log;native-exit.txt=0.
- Native checks preserve supply anchors and assert each actual bell6..20,source boundary,
  explicit genesis empty state,pending duplicate guard,read-only query,retry/load/reconnect,
  separate player-memory context and current/previous save recovery. Extra checks protect
  the added section;counts are per run,not218distinct assertions.
- Actual642x500 cycle-tie-memory.png inspected:bell8..20 text readable through ordinary
  dialogue history. Matching response/history contain both sections and source heading.
- readback.py / readback.json:all18owned managed saves across both runs validate,isolated
  replay/query match and source bytes remain exact;lock sidecars excluded. Prefix unchanged,
  supply<=4/activity<=8,and original156input hashes preserved. Actual saved-query samples
  mean812.758ms/max1550.763ms,under TARGET2s;not regional-world or target-device performance.
- Original scene SHA2563157e6272f93a108ce80848f9d1352fdaa15f3ecae3e750e525763818b011b94
  unchanged. Original editor34400retained;both isolated editors exited. Zero original-editor
  restarts. Temporary trigger absent;isolated copy/evidence retained under owned tmp/.

No fresh full regression or Windows release build. Historical F40–44full2216PASS/build
evidence remains scoped to unchanged authoritative/Unity production sources;new app wiring
is qualified by this affected/static/native evidence. No other-device,human UX,MIN-SPEC,
final-art,independent-review or release claim.

## Delivery

Acceptance PASS for settled examples,registered callers,read-only ownership,error handling,
retention boundaries,replay,source preservation and local performance target. Progress trio
updated together. Final UTF-8/local-link/whitespace/scope and F46frozen-file preservation
checks PASS;delivery.json records the combined13dirty paths(F47touches10).
No commit,push,PR,merge,agent,external send or automatic next implementation.
