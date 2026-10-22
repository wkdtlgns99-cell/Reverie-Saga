# QT-F45 — Cycle slot memory comparison

Status:LOCAL_ACCEPTED2026-10-22. Executor:self-review;not independent review.
[Order](../work_orders/QT-F45_CYCLE_SLOT_MEMORY_COMPARISON.md). Baseline6bc8b54,
PR14/codex/npc-cycle-batch-20261022. Director explicitly authorizes publication and this
next implementation. Primary4retrieval support;related5screen/6save/7integration.

## Result

Cycle-mode current/previous slot inspection now compares retained own work anchors by
(actual causal source ID,within-wake sequence). Both20-second actions remain distinct.
Common/current-only/saved-only rows remain chronological within each group. Header shows
both snapshot times;retained/cumulative counts and latest4 scope are explicit. Missing
entries are not presented as proof of forgetting or nonoccurrence. Existing quest memory
comparison stays separate;no IDs leak into ordinary text. Non-cycle views are unchanged.

New pure app projection validates owner/world/pins,record shape/canonical own anchors,
duplicates and conflicting shared identity. Existing ClientSession slot route logs rejection
and raises SAVE_INSPECT_FAILED;worker error projection and next-request recovery tested.
No additional replay/database read,new command,CORE/schema/pin/RNG/save/IPC change.

## Verification

- New22tests PASS9.78s. Initial strict-type check found the new Tk test using the generic
  _send route for slot_inspect,which is outside that route's typed request union. Replaced
  it with the actual slot_preview_button.invoke callback;no production workaround.
- Final affected238PASS82.85s/exit0,including all22new tests,cycle/work,quest-memory slot
  comparison,previous recovery,client/worker/Tk/pipe,bridge,memory differences and rulebook.
- Exact CI boundary selection31PASS9.81s/exit0. Shared/selective Ruff,scoped formatting,
  strict mypy203files,imports3+1,pip PASS;final document and whitespace checks PASS.
- Independent vectors:0/0→0/0/0;save10/current20→0common/4current-only/3saved-only;
  16/20→2/2/2;20/20→4/0/0;saved20/current0→0/0/4;20/32→2/2/2.
  Exact20-second use→prepare rows,empty scope,wrong types/world/pins/owner,missing record,
  conflicting source identity,corruption rejection,readonly/retry,rewind/future/previous,
  reconnect and logged error recovery qualified with real callers.
- Real slot query20iterations:mean87.065ms,max97.813ms,target<2000ms;state/protocol/source
  bytes unchanged. This is a local observed sample,not a device guarantee.
- Reused editor9524,6000.3.25f1;no editor restart. New native run76PASS0FAIL,exit/result/
  retained/idle0. Actual captured previous31/current33 response matches all9independent
  comparison lines:common3,current-only1,saved-only1,retention4/9vs4/8,and separate common
  use/prepare20anchors. No source IDs in text.
- Actual547x376ordinary-play slot manager inspected using its current-info button and
  scroll controls:current30/saved20,common3/current1/saved1,retention4/8vs4/7,full scope
  explanation readable. Summary/action captures saved;game time stayed30. Play stopped;
  editor remains open. All9native saves validate/replay/query/source-byte guards PASS.
- Scene normalization proved semantic equality before restoring original bytes. All65
  qualified CORE/Unity source paths unchanged. All baseline source/test hashes match
  except ClientSession's new read-only projection call. Preserves prior full2216PASS and
  F44Windows build89,489,696bytes/release-hook exclusion evidence for unchanged inputs.
  No fresh local full regression or Windows rebuild is claimed for F45;new/affected checks
  cover this derived app change. PR head CI runs the full current tree.

## Publication and evidence

F40–44 published at6bc8b54 in [PR14](https://github.com/wkdtlgns99-cell/Reverie-Saga/pull/14).
Its PR CI run39733797530/job119674690550 succeeded:2216PASS756.80s,boundary31PASS8.37s,
static/type/imports PASS. F45 publication follows in the same PR under the current user
instruction;Git/GitHub own the actual final commit/check state. No main merge authorized.

Ignored evidence:tmp/qt-f45/{affected.log,affected-exit.txt,ci-boundaries.log,native.log,
native-comparison.json,readback.json,native-save-identities.json,performance.json,
preservation.json,comparison-summary.png,comparison-actions.png,pr14-initial-ci.log}.
Native save/capture root:tmp/unity-verification/d4528b2a0d3b4c558f756739f1350bc5.
The first preservation-prefix selection used POSIX separators against Windows manifest
keys and selected0paths;corrected normalization and asserted nonempty coverage of all five
prefix groups before acceptance (65paths). No vacuous hash proof is accepted.

All scoped acceptance criteria PASS. D2 remains OPEN,CP06 held,earlier QT-R34–36 patch
rereview DEFERRED. No agents,new external review or automatic further implementation.
