# QT-F48 — Cycle causal call links execution

Date:2026-10-23. Status:LOCAL_ACCEPTED. Executor/self-review:current Codex,not independent.
[Order](../work_orders/QT-F48_CYCLE_CALL_LINKS.md). Primary4retrieval support;related5/6/7.
D2OPEN,CP06held,earlier QT-R34–36patch rereview DEFERRED.

## Baseline and implementation

Clean main e782fa5380edf5119561213e7df7a3b977587351 includes merged PR15/F46–47.
PR15 exact-head push and PR CI both full2259PASS,boundaries31PASS and static PASS.
This request authorizes one new local implementation and verification,no new publication.

Cycle activity previously showed mixed bell/reply events without the actual originating
player-call link. It now enables existing F30causal collection in F47's same isolated
canonical replay. _answered_call follows request/echo/reply causal IDs,selected player/NPC
and same logical tick. Replay hashes and final core AND protocol still qualify the source.
No counters or simultaneous timestamps substitute for causal identity.

The existing call renderer is extracted into private _call_messages. Work-mode dialogue
retains its exact conversation-scoped output;cycle inspection requests the entire retained
segment instead. Actual response count covers all verified calls;the existing latest3cap
is independent of mixed8activity and persisted4supply anchors. Conversations do not erase
inspection history. Empty/checkpoint-only sources show explicit absence,not reconstructed
calls. Causal SaveError and ReplayFormatError map to NPC_ACTIVITY_SOURCE with cause retained;
existing session logging/worker failure projection/retry/polling remain active. Process
control propagates. No new CORE,save format,pins,wire,production Unity or live provider path.
F46conversation projection remains replay-free.

## Python and static verification

Reused repository .venv CPython3.13.12/Tk8.6,pinned dependencies;no installation/settings
change. README PYTHONPATH=src,PYTHONUTF8=1,PYTHONHASHSEED=0;default sys capture preserved.
Logs/evidence under ignored tmp/qtf48/.

| Command/selection | Actual result |
|---|---|
| New regression before implementation | exit1,1FAIL1.13s:actual call1missing after mixed activity eviction(red.log) |
| Initial new + F47 + existing F30call selection | exit1,33PASS/1FAIL30.83s:old F47test assumed no-inference text was final message;new call section intentionally follows it(initial.log) |
| New test_cycle_call_links.py | exit0,8PASS8.86s(new.log) |
| Final affected13integration modules | exit0,221PASS162.44s(affected.log) |
| Exact CI rulebook/boundary selection | exit0,31PASS9.16s(boundaries.log) |
| README shared Ruff and selective ruff-quality.toml | both exit0,PASS |
| README scoped format plus changed/new Python files | exit0,15already formatted |
| mypy --no-native-parser | exit0,206source files,PASS |
| Import Linter type-inclusive/runtime --no-cache | exit0,3+1contracts KEPT |
| pip check | exit0,no broken requirements |

F47test retains its exact original no-inference text at its section end(now third-from-last)
and adds the final empty-call assertion. No assertion/golden/check is removed or suppressed.
Final affected selection:cycle_call_links,cycle_self_activity,cycle_player_memory,npc_cycle,
npc_call_recollection,npc_work_recollection,npc_work_inspection,npc_self_activity,
npc_activity_return,npc_player_memory,client,engine_bridge,previous_slot_recovery.

New8cases cover old call surviving mixed8eviction,five-call count/latest3after conversation,
retry idempotence,checkpoint-only count5without call reconstruction then actualcall6,
previous/current restore and new-process branch isolation,one observed real replay with
snapshot/protocol/attachment/trace/source-byte guards,real missing causal request through
existing selector and worker error/retry/recovery,process-control propagation,actual binary
pipe and actual Tk display. Existing F30malformed-chain vectors and work dialogue protect
shared helpers;F47wrong-owner/hash/core/protocol/IO tests protect the new live path.

## Native and owned saves

Discovery found no running Unity editor. Reused installed
C:/ReverieSaga/tmp/unity-editor/6000.3.25f1/Editor/Unity.exe,one graphical editor5644,
cycle mode/fresh tmp/qtf48/native/game.sqlite,explicit retained-editor mode0. No restart,
install,login or security change. Computer Use inventory selected the returned Unity window;
verification used the registered editor harness,not injected UI scripts or a new hook.

- unity.log:123VERIFY_PASS,0VERIFY_FAIL;ENGINE_VERIFY_PASSED and RESULT/EDITOR_RETAINED/
  EDITOR_IDLE all code0. Existing cycle/current+previous save recovery/quest reward/player
  statement tests retained. Added actual calls32..36then talk37;inspection keeps34/35/36,
  total5,distinct supply/mixed sections,time/file bytes unchanged and exact reconnect result.
- Actual547x376 cycle-causal-calls.png inspected:heading,count5/latest3and full request/
  response times readable through ordinary dialogue focus. Matching response/history files
  retained in native/evidence/. Editor remains open/idle.
- readback.py/readback.json:exact9owned managed saves validated,isolated replay matched,
  query displayed independently expected latest3calls at34/35/36or explicit empty. Original
  file hashes unchanged. Inventory excludes lock sidecars and matches generated source,
  current/previous slots and3private clones;no user save accessed.
- Saved query mean612.830ms,max870.353ms across9queries,under TARGET2s. Tests separately
  observe exactly one replay;no regional/target-device performance inference.
- Scene restoration first rejected a CRLF-sensitive comparison before writing. Corrected
  the evidence comparison to normalize line endings,generated local IDs and trailing spaces;
  all other scene data identical. Restored entry bytes exactly,SHA256
  3157e6272f93a108ce80848f9d1352fdaa15f3ecae3e750e525763818b011b94.
  preservation.json qualifies269tracked source/test/content/Unity inputs unchanged after
  native execution. No production source change after qualification.

No fresh full regression or release rebuild:shared CORE and production Unity inputs are
unchanged. Historical PR15full2259and F40–44build remain revision-scoped;new app wiring
is qualified by these fresh affected/static/boundary/native/save checks. No other-device,
human UX,final-art,MIN-SPEC,standalone release or independent-review claim.

## Delivery

Actual-source/callers/error/read-only/retention acceptance PASS. Backlog,handoff and Korean
progress updated together,including PR15publication facts. Final diff/scope/UTF-8/local-link/
whitespace checks and rulebook document tests recorded under tmp/qtf48/delivery.json.
Existing backup stash/private files/frozen witnesses preserved. Local only;no commit,push,
PR,merge,agent,external send,provider call or automatic next task.

Publication follow-up2026-10-23:director explicitly authorizes F48commit/push/PR,
required CI and ordinary main merge/sync,then continued bounded work cycles. Local-only
statements above describe the implementation acceptance snapshot;Git owns actual state.
