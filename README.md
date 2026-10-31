# Reverie Saga

AI-produced HD-2D/2.5D graphical turn-based RPG in development.
Current prototype:Python deterministic rules,3x3rooms,combat/NPC events,one quest,two NPC conversation
records,SQLite save/load/recovery/replay,Tk and provisional Unity. [Current status](BACKLOG.md).

## Runtime

Commands run from `C:\Reverie Saga` in PowerShell. Reuse local `.venv`;for another computer
follow [workstation setup](docs/WORKSTATION_SETUP.md). Git excludes tools,licenses,keys and private saves.
Validated host:CPython3.13.12 x64,Tk8.6;Ruff/mypy target3.12syntax,not tested3.12runtime support.

Fresh environment only:
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
$env:PYTHONPATH = "$PWD/src"
```

## Play the prototype

Basic Tk room:
```powershell
$env:PYTHONPATH = "$PWD/src"
.\.venv\Scripts\python.exe -m app.client --working tmp/client/game.sqlite
```

A new path creates a game;an existing path resumes it. WASD/arrows/buttons move;stand beside
doors/enemies/NPCs to interact. Rest restores stamina,not HP. Add `--scenario harbor` or
`--scenario grove` with a separate working path for the other embedded rooms.

In Tk,press Return or keypad Enter while editing the wait-time field to run the existing wait action.
The accepted range remains1–16game seconds;invalid input keeps the current progress.
Repeated identical invalid-text errors occupy one adjacent log entry,so they do not evict gameplay history.

Approved harbor quest+NPC memory:
```powershell
$taskDialoguePin=(Get-Content -LiteralPath content/dialogue/harbor-memory-v1.sha256 -Raw).Trim()
.\.venv\Scripts\python.exe -m app.client --working tmp/client-harbor-memory/game.sqlite --scenario harbor --quest-catalog content/dialogue/harbor-memory-v1.json --quest-sha256 $taskDialoguePin --npc-memory
```

| Control / state | Behavior |
|---|---|
| Quest | Accept→defeat→report→one favor;ordinary turns use prepared approved text without API calls |
| NPC memory | Full/recent conversation inspection;reported evidence remains distinguished from direct observation |
| Slot info | Preview saved metadata;current stats/retry remain current |
| Save/load | slot01..slot08;load creates a private branch and clears later display history. Resume using displayed working path and original scenario/catalog/memory selectors |
| History/retry | Latest200lines,not persisted display history;exact retry does not repeat gameplay or narration |
| Close | Drains accepted work;SQLite/session remains owned by worker thread |

Tk history follows new output while at the bottom. Scroll up to keep reading the same
retained record as messages arrive;evicted records yield to the oldest remaining record.
Click `최신 기록으로` beside the history heading to return to the bottom and follow new output.
Loading a save resets history and returns to the latest output.

Tk also offers **이전 저장 정보** and **이전 저장 불러오기** for the selected slot
(QT-F89). Preview keeps the current game unchanged;explicit previous loading continues
in a separate working file and preserves both saved generations. Missing or damaged
previous saves report an error without falling back to the latest save.
[Evidence](docs/reviews/QT-F89_EXECUTION_2026-10-30.md).

In compact Tk windows,the map and controls share a scrollable region while status,
working-path information and history remain below it (QT-F90). Use the play-region
scrollbars or mouse wheel to reach controls;history scrolls independently. Wait-time
and slot fields keep their own wheel behavior. Basic/reach-mode geometry is qualified
at900x600and900x768on the current PC,not final renderer/device UX acceptance.
[Evidence](docs/reviews/QT-F90_EXECUTION_2026-10-30.md).

In NPC-memory modes,selected-slot information also compares that slot's memories with
the current game:shared,current-only and saved-only conversations,with their actual times.
Differences describe save/branch history,not NPC forgetting;received reports remain distinct
from witnessed events. Inspection does not load a branch or advance the game.

Successful harbor NPC conversations include committed activity counts in the action log.
They use the restored save's current state;exact command retries do not repeat the line.
The bounded return/report/save/restart route and its limits are recorded in
[QT-F25](docs/reviews/QT-F25_EXECUTION_2026-10-16.md).

## Unity graphical prototype

[Unity play/build/native verification](clients/unity/README.md):editor6000.3.25f1.
No-selector Unity starts the approved harbor-memory preset in a catalog-pin-specific save directory;
explicit legacy/scenario/quest selectors preserve their existing modes.
Independent control/history scrolling is qualified at1101x506on the observed host.
Human UX,final art/camera/engine,gamepad,MIN-SPEC,portable standalone and other-device acceptance remain open.

## First quest / prepared Gemini dialogue

[CLI workflows](docs/CLI_WORKFLOWS.md) contain key loading,explicit preparation,offline review/approval/
compilation,NPC context,query export/check/comparison and plan-based generation.
Normal play needs no key/network. New generated content stays NEEDS_REVIEW until actual director approval;
existing games retain their content pins. [Current qualification limits](BACKLOG.md#qt-f07-deferred-qualification).

## Verification

Unity **저장 관리** opens a dedicated slot01–08 panel with current/previous save
inspection and explicit previous-save loading. Overwriting a valid slot retains one
previous save. Loading either version continues in a private working branch and preserves
both source files;corrupt latest saves never trigger automatic fallback. Inspect the
previous version,then choose **이전 저장 불러오기** when recovery is wanted. Missing or
invalid backups report their own errors. The panel blocks movement keys while polling
continues;Escape closes it. Selection and panel mode survive load/reconnect.
[Contract](docs/work_orders/QT-F39_SAVE_MANAGER_RECOVERY.md).

QT-F28 adds an explicit harbor NPC work mode. It prepares one communal supply at logical
seconds4/8/12,then stops at capacity3. Travel/combat time counts;wall time does not.
Talk shows committed stock;NPC activity and slot preview remain read-only. No player inventory
or extra quest reward is granted. Existing modes/saves are never upgraded.

```powershell
$questPin = (Get-Content content/dialogue/harbor-memory-v1.sha256 -Raw).Trim()
$env:PYTHONPATH = "$PWD/src"
.\.venv\Scripts\python.exe -m app.client --scenario harbor --working tmp/npc-work/game.sqlite --quest-catalog content/dialogue/harbor-memory-v1.json --quest-sha256 $questPin --npc-memory --npc-work
```

Use a fresh work path;an older memory save intentionally rejects with UNSUPPORTED_RULESET.
[Work contract](docs/work_orders/QT-F28_NPC_PROVISIONS.md).

QT-F40–44 adds a separate optional supply-cycle mode. In the command above use a fresh
`tmp/npc-cycle/game.sqlite` and replace `--npc-work` with `--npc-cycle` (keep `--npc-memory`).
The NPC uses one communal supply every10 logical seconds and prepares one every4 up to3;
at a tie it uses before preparing. Player rewards are unchanged. The latest four actual own
work memories and cumulative counts persist across checkpoint,save/load and reconnect.
Talk/activity show those stored anchors;slot previews explicitly label saved memories.
The header shows the selected mode. Old work/memory saves retain their original identities;
cycle mode rejects them unchanged. [Batch contract](docs/work_orders/QT-F40_44_NPC_CYCLE_BATCH.md).

QT-F45 cycle-mode slot previews also compare current/saved own work memories by actual
causal source and within-wake sequence. Common/current-only/saved-only groups preserve both
consume/prepare actions at a tied second. Each snapshot retains only its latest four own
actions;the view labels that scope and cumulative totals. Missing entries do not prove an
action never occurred or that the NPC forgot. Current/previous previews remain read-only.
[Comparison contract](docs/work_orders/QT-F45_CYCLE_SLOT_MEMORY_COMPARISON.md).

QT-F46 cycle-mode conversations also recall the newest persistent player quest statement:
the heard promise or received completion report,with its original game time. Enemy defeat
alone does not become a received report or eyewitness memory. Restoring an older save
selects that branch's memories;retry adds no duplicate context. This reuses existing
committed anchors without another player-memory replay or live API call.
[Recall contract](docs/work_orders/QT-F46_CYCLE_PLAYER_MEMORY.md).

QT-F49 cycle-mode talk additionally recalls verified answered player calls after the
previous retained conversation. It counts all confirmed replies in that range and shows
the latest three request/reply times through one isolated replay. A compacted save with
no retained call events reports that limit even when its cumulative reply count is nonzero.
Retry adds no duplicate recall. [Call contract](docs/work_orders/QT-F49_CYCLE_CALL_RECALL.md).

QT-F50 cycle-mode talk also summarizes confirmed supply preparation/use counts since the
previous retained conversation. The comparison uses committed counter snapshots in that
same verified replay;the recent-four detailed memories remain separate. Without a previous
retained talk,the summary explicitly starts at the source checkpoint and never attributes
older counter values to that range. [Change contract](docs/work_orders/QT-F50_CYCLE_RETURN_CHANGE.md).

QT-F47 cycle-mode **NPC 활동 기록** keeps those persistent supply memories and also shows
the selected save segment's latest eight bell/reply events,verified through one isolated
replay. It labels the source checkpoint boundary;missing retained events are never rebuilt
from cumulative counters. Inspection advances no time and preserves source files/retry.
[Activity contract](docs/work_orders/QT-F47_CYCLE_SELF_ACTIVITY.md).

QT-F48 extends cycle-mode activity inspection with the actual player-call/response links:
the total verified responses in the retained segment and their latest three request/reply
times. These details survive eviction from the mixed eight-event list and are not reset
by a conversation. Checkpoint-only history never reconstructs missing calls from counters.
The same single isolated replay verifies all activity sections;inspection remains read-only.
[Call-link contract](docs/work_orders/QT-F48_CYCLE_CALL_LINKS.md).

QT-F29 work-mode dialogue also recalls the NPC's verified production since the previous
retained conversation. Work is collected separately from frequent bell events,so those
events do not hide production. Only actual retained facts are recalled;missing earlier
history is labeled as the current saved segment. Same-turn production is included once;
retry adds no duplicate recall. This adds no new save/rules/wire format or live API call.

QT-F30 adds answered-player-call recollection to that same work-mode return dialogue.
It follows actual request→echo→response event identities,shows the range's confirmed
response count and most recent3,and survives save/load/reconnect. Frequent periodic bells
cannot hide these calls;missing checkpoint history is never reconstructed from counters.
Work and call context share one verified replay. [Contract](docs/work_orders/QT-F30_NPC_CALL_RECOLLECTION.md).

QT-F31 return context also selects the newest persistent player statement:the heard quest
promise or received completion report,with its original time. Objective enemy defeat alone
does not become a received report or eyewitness memory. These existing CORE anchors survive
retained-trace truncation;work/call evidence keeps its explicitly retained-history boundary.
[Contract](docs/work_orders/QT-F31_NPC_PLAYER_MEMORY.md).

QT-F32 Unity **대화 크게 보기** expands NPC history within the existing window. The fixed
header button or Escape restores controls;movement keys are suppressed while reading.
This is local presentation only,preserving turns/save data and ongoing response polling.
[Contract](docs/work_orders/QT-F32_DIALOGUE_FOCUS.md).

QT-F51 keeps the controls,dialogue and save-manager panel opaque so world geometry cannot
show through its text. Panel size,scrolling and input behavior stay the same.
[Readability repair](docs/work_orders/QT-F51_PANEL_OCCLUSION.md).

QT-F52 Unity history keeps the retained text being read when new responses arrive.
At the bottom it follows new output;**최신 기록** returns there explicitly. Loading a
save resets history to the loaded branch. [Reading behavior](docs/work_orders/QT-F52_HISTORY_READING.md).

QT-F54 adds explicit `--npc-aid` with `--npc-memory --npc-cycle` and the approved harbor
catalog. After hearing the player's quest acceptance,the NPC opens the passage at its
next two-second wake until hearing the completion report. Closing remains available;
an active NPC may reopen at the next wake. The NPC uses its saved conversation evidence,
not unreported enemy defeats. Supply/reward rules and old modes remain unchanged.
This variant has distinct pins;use a new working save. Load/restart/retrieval retain it.
[Contract and verification state](docs/work_orders/QT-F54_NPC_GATE_ASSISTANCE.md).

QT-F59 adds supply-prioritized aid with `--npc-supply-aid` in both Python clients.
It requires `--npc-memory --npc-cycle --npc-aid` and the approved harbor content.
The NPC waits for at least2communal items at its prior action barrier before opening
the passage. This readiness condition spends no stock;the ordinary4/10supply cycle
continues. In a fresh down1/talk2source,stock reaches2at8and the NPC opens at10;
ordinary consumption at10leaves1. Same-barrier preparation is considered at the next
wake. New mode/save identity;select a fresh working path rather than repinning saves.
Unity accepts `REVERIE_UNITY_NPC_SUPPLY_AID=1` with the same parent flags;unset/0keeps
prior modes,invalid values reject before creating a Brain/save. Its default path is
`tmp/unity-play/harbor-cycle-supply-aid/<catalog-pin>/game.sqlite`.
[Contract/status](docs/work_orders/QT-F59_NPC_SUPPLY_AID.md).

QT-F56 aid-mode **NPC 활동 기록** appends confirmed gate openings from the selected
retained save segment:total count and latest3actual NPC assistance facts,oldest first.
Bells and player-opened gates do not establish assistance. Loading an earlier branch
restores its records;compacted-away events are explicitly unavailable. This uses the
same verified read-only replay and adds no permanent memory or save field.
[Contract/status](docs/work_orders/QT-F56_NPC_ASSISTANCE_HISTORY.md).

QT-F58 aid-mode ordinary talk recalls only actual NPC openings after its previous retained
conversation(or explicit checkpoint),with total and latest3details. Same-talk wake
assistance is included;retry does not repeat it. Current local qualification:347affected Python checks,216native checks,13source-preserving
save readbacks and a fresh Windows build pass;standalone/release acceptance stays held.
[Contract/status](docs/work_orders/QT-F58_ASSISTANCE_RECOLLECTION.md).

QT-F33 work-mode **NPC 활동 기록** keeps a separate retained production section after
the unchanged mixed recent8activities. Repeated bells cannot hide verified work4/8/12;
the final line shows current committed stock. A compacted checkpoint may retain stock
without old work events:the display states that limit instead of inventing history.
Inspection shares one isolated replay,advances no time,and preserves saves/retry identity.
[Contract](docs/work_orders/QT-F33_NPC_WORK_INSPECTION.md).

Use the applicable order for affected tests;shared CORE changes require full regression.
The environment setup below applies to all commands,including both import checks.
```powershell
$env:PYTHONPATH = "$PWD/src"
$env:PYTHONHASHSEED = '0'
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff check --config ruff-quality.toml src tests
.\.venv\Scripts\python.exe -m ruff format --check src/orchestration/turn.py src/contracts/encounter.py src/engines/encounter.py tests/replay/test_encounter.py src/contracts/client.py src/app/client.py src/app/client_session.py src/app/client_worker.py src/app/client_text.py tests/integration/test_client.py tests/unit/test_client_text.py tests/unit/test_engineering_rules.py
.\.venv\Scripts\python.exe -m mypy --no-native-parser
.\.venv\Scripts\python.exe -c "from importlinter.cli import lint_imports_command; lint_imports_command()" --config pyproject.toml --no-cache
.\.venv\Scripts\python.exe -c "from importlinter.cli import lint_imports_command; lint_imports_command()" --config .importlinter-runtime.toml --no-cache
New-Item -ItemType Directory -Path .pytest_cache -Force -ErrorAction Stop | Out-Null
if (-not (Test-Path -LiteralPath .pytest_cache -PathType Container)) { throw 'Pytest temporary parent is not a directory' }
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/local-run
```

Shared imports include TYPE_CHECKING;runtime imports exclude it. Both checks are required.
Pytest uses `--capture=sys` from pyproject.toml. Keep this default for Windows Tk tests:
descriptor capture replaces native standard handles between test phases and reproduced
false missing-Tcl-file errors. Python output remains captured;subprocess checks capture their
own output explicitly. Do not retry,skip,copy Tcl libraries or override with `--capture=fd`.
Root-cause evidence:[RS-TK-001](docs/reviews/RS-TK-001_EXECUTION_2026-10-16.md).
Source mode uses PYTHONPATH;the project is not an installable package.
[CI](.github/workflows/checks.yml) owns the exact named boundary selection;
[enforcement map](docs/ENGINEERING_ENFORCEMENT.md) distinguishes active/deferred guards.
For a broader local boundary run:
```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/unit/test_engineering_rules.py tests/integration/test_client.py tests/integration/test_save_slots.py tests/integration/test_durable_turn.py --basetemp .pytest_cache/local-boundaries
```

## Navigation

| Need | Read |
|---|---|
| Agent/session entry | [AGENTS](AGENTS.md)→[rules](ENGINEERING_RULES.md),[handoff](SESSION_HANDOFF.md),[backlog](BACKLOG.md) |
| Product/architecture | [MASTER](docs/MASTER_GAME_ARCHITECTURE.md),[engineering prompt](docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md),[numbered structure](docs/GAME_STRUCTURE_GUIDE_EN.md) |
| Task contracts/evidence | [order template](docs/prompts/SOL_CODING_WORK_ORDER.md),docs/work_orders/,docs/reviews/ |
| Human progress | [Korean companion](GAME_SYSTEM_SUMMARY_KO.md) |
| Past commands/results | [README snapshot](docs/history/README_2026-10-16.md);historical instructions are non-operative |

## PR09 Integration

Preserve the courtyard room and its V1 rules/save identity through the shared current layout path.
Original [room evidence](docs/reviews/QT-F02_ROOM_BINDINGS_2026-10-15.md) and
[Unity evidence](docs/reviews/QT-F02_UNITY_SELECTION_2026-10-15.md) remain historical;
[PR08 repair](docs/reviews/PR08_CI_REPAIR_2026-10-16.md) records current integration acceptance.

### Opt-in answered-call support (QT-F65)

Add `--npc-call-aid` to the existing Python memory/cycle/aid/supply-aid flags.
With the Unity approved harbor preset,set `REVERIE_UNITY_NPC_CYCLE=1`,
`REVERIE_UNITY_NPC_AID=1`,`REVERIE_UNITY_NPC_SUPPLY_AID=1` and
`REVERIE_UNITY_NPC_CALL_AID=1` (work mode unset/0). Invalid values reject before
startup. The NPC may open the passage after an actual answered call,including odd
seconds,when previously available communal stock is at least2and the NPC has heard
acceptance without a completion report. Support spends no stock;routine supply
preparation/consumption continues. The default Unity save directory is the distinct
`tmp/unity-play/harbor-call-aid/<catalog-sha256>/game.sqlite`;older mode saves retain
their pins and reject incompatible selection without overwrite. Existing bell action,
save format and wire envelope are reused. Fresh native/build qualification is deferred
under AWAY-001 while Computer Use remains stopped;Python verification is separate.


### Opt-in conversation-aware patrol (QT-F73)

Add `--npc-talk-pause` to the existing approved harbor memory/cycle/aid/supply-aid/
call-aid/patrol selection. An actual admitted conversation holds the NPC's current
position for that turn;the next actual wake without a conversation resumes ordinary
patrol. Rejected talk creates no lasting pause. Supply,aid and reward rules are unchanged.
This variant has distinct rules pins;use its own fresh working file rather than repinning
older saves. All seven prior modes keep their existing descriptors and behavior.
Unity source accepts `REVERIE_UNITY_NPC_TALK_PAUSE=1` with the same parent flags;unset/0
keeps the prior selection,other values reject before child/save creation. Its distinct
default directory is `tmp/unity-play/harbor-talk-patrol/<catalog-pin>/game.sqlite`.
Current Python/runtime scope is locally accepted with one2950PASSfull run;fresh native/build qualification remains
NOT_RUN under AWAY-001 while Computer Use is stopped.
[Contract and current evidence](docs/work_orders/QT-F73_TALK_PAUSE_PATROL.md).


### Opt-in quest-aware patrol (QT-F74)

Add `--npc-quest-patrol` to the approved harbor memory/cycle/aid/supply-aid/call-aid/
patrol/talk-pause selection,using a fresh working file. This variant waits at the original
work point until the NPC hears acceptance,patrols while its own acceptance remains
unreported,and returns home after hearing the completion report. Enemy defeat alone
cannot change its own knowledge. Talk holds that turn;an occupied home delays the return
until a later wake after the player leaves. Once home,it stays. Supply/aid/reward rules
and saved memory fields remain unchanged. Talk/activity show the derived current goal;
the plan does not invent historical movements or promise an arrival time.

The distinct feature is `quest.harbor-quest-patrol-v1`;all eight older modes retain their
rules identity. Incompatible saves reject without overwrite. Unity source accepts
`REVERIE_UNITY_NPC_QUEST_PATROL=1` with all parent flags and uses
`tmp/unity-play/harbor-quest-patrol/<catalog-pin>/game.sqlite`;unset/0keeps the prior
selection,other values reject before child/save creation. Current Python/runtime/source
scope is locally accepted with one3031PASSfull run;one2sactivity-target miss remains
recorded/global2sOPEN. Fresh Unity/native/build remains NOT_RUN AWAY-001.
[Contract](docs/work_orders/QT-F74_QUEST_PATROL.md);
[current execution](docs/reviews/QT-F74_EXECUTION_2026-10-27.md).


### Saved/current quest patrol plan preview (QT-F75)

In the existing quest-aware patrol mode,slot preview now labels the current plan and
the selected save's plan before the physical-position comparison. Equal positions can
have different heard quest knowledge;reported NPCs can still be waiting to return.
Previous-save inspection and loaded-branch reconnect retain their actual selected times.
The preview neither loads a save nor changes either source. Existing eight modes,
authoritative rules,pins,save format and wire are unchanged. Current Python/query scope
is locally accepted with42new in239affected plus static/CI31;unchanged F74engine full
3031is reused,not a new F75whole run. Fresh Unity/layout/build remains NOT_RUN AWAY-001.
[Contract](docs/work_orders/QT-F75_QUEST_PATROL_SLOT.md);[evidence](docs/reviews/QT-F75_EXECUTION_2026-10-27.md).


### Immutable validation cost experiment (QT-F76,ENV_BLOCKED)

Identity-proven None/bool/int omit redundant scalar sealing after the original depth
and legacy type-equality dispatch;Unicode/container/record/codec/field validation stays.
Three newly caught custom-metaclass regressions are repaired:baseline3PASS/first3FAIL,
repaired50new/235affected/31boundary PASS. Both Ruffconfigs/format55/strict251 PASS.
V2all9modes and actual saved-source direct/framed results/persisted bytes match baseline;
all superseded timings retained,no overall speedup/global2sclaim. Existing import checker
native startup remains Windows-policy blocked (ENV-001),not a source graph PASS.
One complete current regression:3123cases/3037PASS/86FAIL/0error/0skip in1452.18s. All86
failures are the existing dependency-checker native startup block;new50/replay-G07168
PASS,all359frozen inputs/index preserved. Required successful full/import qualification
remains unresolved;no skip/security/checker change or local acceptance.
[Scope](docs/work_orders/QT-F76_IMMUTABLE_LITERALS.md);
[actual evidence](docs/reviews/QT-F76_EXECUTION_2026-10-27.md).


### Answered-call patrol hold (QT-F77checkpoint)

Add `--npc-call-pause` after the existing quest-patrol parent chain to opt in. The NPC
holds its cell only during an actual answered call,then follows the existing quest goal
at the next actual wake;occupied targets still wait. No persistent pause or new save/IPC
schema. Distinct feature `quest.harbor-call-pause-v1` rejects incompatible existing saves.
Current82new in535related/31boundary/168replay-G07 and both Ruffconfigs/format57/strict253
PASS;old9stable outputs/persisted bytes remain exact. Required import/successful full
qualification remains ENV-001blocked;new-mode long-source performance is unverified.
Unity selection/verifier source prepared only,fresh native/build NOT_RUN AWAY-001.
The historical2026-10-27checkpoint paused development;the human resumed it2026-10-29.
[Checkpoint memo](docs/reviews/DEVELOPMENT_CHECKPOINT_2026-10-27.md),
[scope](docs/work_orders/QT-F77_CALL_PAUSE_PATROL.md),
[evidence](docs/reviews/QT-F77_EXECUTION_2026-10-27.md).


### Supply readiness before NPC patrol (QT-F80)

The explicit `--npc-ready-patrol` option requires `--npc-call-pause` and its entire
existing parent chain. Use a new `tmp/npc-ready-patrol/game.sqlite` working path;
older modes/saves keep their existing rules and intentionally reject cross-mode loading.
After hearing acceptance,the NPC prefers its original work point while the selected
gate is closed and its own support supplies are below the existing2-unit requirement.
Actual talk/call holds and occupied targets still apply. Supply production/use,aid cost,
quest rewards and logical time retain their existing rules. Newly prepared supplies in
the same POSTphase affect the next action decision,not an earlier read in that phase.
Talk/activity and saved/current next-action rows use each snapshot's own stock and gate.

Python qualification passes current792affected/31boundary/168replay-G07cases,old10mode
whole parity and actual new-mode7/264direct/framed query/source preservation. Native source
is prepared;fresh native execution/build is NOT_RUN AWAY-001. ENV-001required imports/
successful full remain unresolved,so status is IMPLEMENTED_ENV_BLOCKED.
[Scope](docs/work_orders/QT-F80_READY_PATROL.md),[evidence](docs/reviews/QT-F80_EXECUTION_2026-10-29.md).


### Previous conversation-end patrol plan (QT-F81)

In existing ready-patrol mode,talk adds the prior retained conversation-end next-action
projection beside the current one. Activity lists the latest two retained conversation-end
projections. These use each verified snapshot's own stock/gate/occupancy,not the current
state applied to history. They describe a committed conversation-end plan,not an executed
past action. A compact checkpoint with no retained conversations explicitly has no older
plan snapshots,even if its authoritative memory contains past talks. No new flag/save
format/state/pins/extra replay/IO/cache. Current362affected/35new/CI31/old10parity/
new11declared-row-only parity/actual original-source queries pass;native and ENV-001
required current import/successful full gates remain held (IMPLEMENTED_ENV_BLOCKED). [Order](docs/work_orders/QT-F81_CONVERSATION_PATROL_PLAN.md).


### Physical NPC passage assistance (QT-F82)

Add `--npc-reach-aid` to either client CLI with `--npc-ready-patrol` and all its parents.
Use a new working file (for example `tmp/npc-reach-aid/game.sqlite`);existing saves retain
their rules identity and are never repinned. Missing parent/non-bool API selections reject
`NPC_REACH_AID_CONTENT` before save/thread creation. The new identity is
`quest.harbor-reach-aid-v1`. The NPC needs prior committed stock of at least two and a
position adjacent to the passage;arrival during the same phase cannot qualify early.
Talk/activity and selected-save comparison describe each snapshot's actual position.
[Contract](docs/work_orders/QT-F82_REACH_GATE_AID.md),
[verification](docs/reviews/QT-F82_EXECUTION_2026-10-29.md).


Reach-mode answered calls also show the existing support plan labelled as current state
after the response (QT-F83). Exact retries produce no additional plan;the presentation
neither infers past failure reasons nor changes assistance timing or stored state.
[Contract](docs/work_orders/QT-F83_CALL_SUPPORT_FEEDBACK.md),
[evidence](docs/reviews/QT-F83_EXECUTION_2026-10-29.md).


### Verified-query conversion cost (QT-F84)

Checkpoint validation reuses freshly owned command conversion results within that one
operation,without persistent caches,skipping replay or truncating history. Paired12query
samples preserve complete outputs and SQLite dumps:mean1.845204->1.427486s,
max4.948312->3.726747s. All4long talk/activity samples still exceed the2sTARGET;
all12remain below the10sdeadline. This is measured improvement,not global latency or
minimum-spec acceptance. [Evidence](docs/reviews/QT-F84_EXECUTION_2026-10-29.md).

Reach-mode answered calls now also present the existing current next-patrol-step plan
(QT-F85),including occupied-target waits. This shares the current support snapshot and
neither promises a future event nor adds a replay/query/state change. Exact retries add
no plan. [Evidence](docs/reviews/QT-F85_EXECUTION_2026-10-29.md).

QT-F86qualifies the same12query samples below2s on the current host:maximum1.833s;
three extra repetitions of each formerly slow case also pass,maximum1.952s. Complete
outputs/storage remain identical;full3599PASS. This supersedes the F84sample misses,
not global history/device/minimum-spec performance. [Evidence](docs/reviews/QT-F86_EXECUTION_2026-10-29.md).

The Python player now identifies pending dialogue,activity,memory and slot inspections
(QT-F87). Readonly queries explain time/progress preservation;the actual result replaces
the pending text. Existing input/error/cancel/close handling remains active.
[Evidence](docs/reviews/QT-F87_EXECUTION_2026-10-29.md).

Reach-aid talk also recalls the support plan at the previous retained conversation end
(QT-F88);activity lists the latest two. Each projection uses its own verified stock,
NPC position and gate state. These describe past plans,not executed aid;compact saves
without retained conversation events explicitly lack older projections. Existing modes,
save formats and game rules stay unchanged.
[Evidence](docs/reviews/QT-F88_EXECUTION_2026-10-29.md).

Keyboard focus in the scrollable Tk play area now reveals the focused control on both
axes when needed (QT-F91). Native Tab/reverse-Tab traversal and Space activation retain
their existing commands. History,other windows and input editing remain independent.
[Evidence](docs/reviews/QT-F91_EXECUTION_2026-10-30.md).

In narrow Tk windows,Shift+mouse wheel scrolls the play region horizontally (QT-F92).
Ordinary wheel input still scrolls vertically;wait/slot inputs and history retain their
own wheel handling. Scrolling changes no game time or saved state.
[Evidence](docs/reviews/QT-F92_EXECUTION_2026-10-31.md).

Tk movement accepts WASD with Shift or CapsLock enabled (QT-F93). Ctrl/Alt combinations
do not issue movement commands. Arrow controls and native wait/slot/history input remain
unchanged. [Evidence](docs/reviews/QT-F93_EXECUTION_2026-11-01.md).
