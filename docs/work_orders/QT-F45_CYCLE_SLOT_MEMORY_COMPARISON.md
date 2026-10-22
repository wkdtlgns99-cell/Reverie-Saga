# QT-F45 — Compare saved and current own work memory

Status:READY,2026-10-22. Executor:current Codex;self-review,not independent review.
Authority:director requests Git publication and the next implementation. F40–44 published
at6bc8b54 on codex/npc-cycle-batch-20261022;PR14 open against main bd8e9c7. Clean entry.
Goal:slot inspection compares the NPC's own bounded supply memories across saved/current
snapshots. Primary4retrieval support;related5screen/6save/7integration. D2 remains OPEN.
Non-goals:new NPC behavior,CORE/schema/pins/RNG/save/IPC changes,extra replay/IO,LLM,
checkpoint waiver,main merge or agents. F40–44 mechanics/evidence remain unchanged.

Prerequisites:F38quest memory comparison,F40–44cycle memories and real current/previous
slot recovery. Read:ENGINEERING_RULES,README verification,MASTER,numbered guide,
SESSION_HANDOFF/BACKLOG/GAME_SYSTEM_SUMMARY_KO,app.npc_memory_compare.slot_memory_messages,
app.npc_cycle.cycle_messages,ClientSession.inspect_slot,domain.npc_cycle,existing slot and
cycle integration tests,Unity LiveVerification.CycleFlow/SaveManagerFlow.
Tools:reuse .venv Python3.13.12/Tk8.6 and running Unity6000.3.25f1;verify process before use.

Allowed NEW absolute paths:C:/ReverieSaga/src/app/npc_cycle_compare.py,
C:/ReverieSaga/tests/unit/test_cycle_memory_comparison.py,
C:/ReverieSaga/tests/integration/test_cycle_slot_comparison.py,
C:/ReverieSaga/docs/reviews/QT-F45_EXECUTION_2026-10-22.md,this order.
Allowed MODIFY:C:/ReverieSaga/src/app/client_session.py,
C:/ReverieSaga/clients/unity/Assets/Reverie/Scripts/LiveVerification.cs,
C:/ReverieSaga/README.md,C:/ReverieSaga/BACKLOG.md,C:/ReverieSaga/SESSION_HANDOFF.md,
C:/ReverieSaga/GAME_SYSTEM_SUMMARY_KO.md. Generated private verification artifacts only
under tmp/. Forbidden:other production modules,CORE/contracts,private user saves,credentials,
frozen review witnesses,reference checkout and security/tooling settings.

## Contract and algorithm

New derived `cycle_slot_messages(saved:DurableCheckpoint,current:DurableCheckpoint,
npc_id:EntityId)->tuple[str,...]`. Validate exact checkpoint types,same world_id/pins,
one exact CycleRecord per selected owner in each snapshot,domain shape and existing
validate_checkpoint(record,world,tick). Validation must not reconstruct/fill absent memories.
Invalid input/shape/missing record→GenerationError NPC_CONTEXT_INPUT;different world/pins/
owner→NPC_MEMORY_COMPARISON_OWNER;shared identity with differing evidence→
NPC_MEMORY_COMPARISON_IDENTITY. Client maps logged comparison failures to existing
SAVE_INSPECT_FAILED and preserves state/retry/polling.

Identity is (causal source_event_id,within-wake sequence). Tick20has consume sequence0 and
prepare sequence1 sharing a wake;never collapse them. Compare only actually retained4+4
entries. Group common/current-only/saved-only,ascending(tick,sequence) within each group.
No source IDs in ordinary text. Reuse evidence_text for action/stock explanation,replace
its prefix with explicit comparison group label. Include both snapshot ticks,counts and
each retained/total count. Explicitly say snapshots/branches AND the latest-four retention
limit can explain one-sided entries;absence is not proof of forgetting or nonoccurrence.
If neither side has anchors,show an explicit empty message. Counters do not create entries.
No extra replay/database read or new command;one saved inspection plus committed current
snapshot reused. Existing saved summary remains;comparison appended only for cycle mode.

Independent settled vectors:
save10 retains4prepare/8prepare/10use (3);current20 retains12prepare/16prepare/20use/20prepare
(4),so common0/current-only4/saved-only3. Save16/current20→common2(12/16),current-only2
(20use/prepare),saved-only2(8prepare/10use). Same20→common4/0/0;save20/current0→0/0/4;
both0→0/0/0. Tie order use then prepare remains visible. Previous-save preview uses that
explicit snapshot;loading older state then inspecting a future slot labels both directions.

Steps:write typed pure comparison;wire ClientSession cycle branch with logged error mapping;
add independent boundary/identity/corruption/order tests and real session/worker/Tk/pipe
current/previous/rewind/reconnect/read-only source guards;extend the native evidence checker for the existing cycle flow
to assert captured comparison counts/ties and inspect its slot result. Measure slot query TARGET<2s
locally,report observed sample. Bounded work:two4entry maps,at most8comparison rows.

## Acceptance,verification and delivery

Require correct settled vectors/empty/tie/eviction/reversed time/errors,unchanged owner,
protocol,attachment,source bytes,retry and real callers;all non-cycle views unchanged.
Commands:README Ruff+quality,scoped format plus new files,mypy,imports3+1,pip;new unit/
integration tests plus existing cycle/work/slot/previous/client/engine bridge/quest memory
comparison affected selection;exact CI boundaries. Reuse full2216PASS on unchanged CORE;
PR head CI executes full current tree. Native current-cycle flow/actual small slot display,
save readback/replay/byte guards;reuse unchanged production C#/wire/scene build evidence
fromF44 (all Unity sources remain unchanged). Leave editor open.
Baseline commands:F40–44 full2216PASS836.87s,31boundaryPASS8.53s/static/native76/build PASS;
refresh actual Git head/status before edits. New tests PLANNED in the paths above.
Claude:NOT_APPLICABLE,pure read-only retrieval/presentation through existing boundaries;
CP06 held,earlier patch rereview DEFERRED. Stop on user overlap/unresolved identity contract
or evidenced unavailable validation after safe repairs. Update root progress trio and receipt
after acceptance,commit/push to the same PR14 under current publication instruction;do not
merge main. Report task/category,actual tests and PR status;no automatic further task.

Execution:LOCAL_ACCEPTED;[receipt](../reviews/QT-F45_EXECUTION_2026-10-22.md).
