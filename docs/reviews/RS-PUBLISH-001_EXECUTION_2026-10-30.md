# RS-PUBLISH-001 — Per-task main synchronization

DONE2026-10-30;self-review,primary7workflow support;no gameplay change.
[Order](../work_orders/RS-PUBLISH-001_PER_TASK_MAIN.md).

Director grants standing delivery authority for each authorized coherent task:scoped
commit/push,PR,required latest-revision CI and checkpoint checks,ordinary merge,local
main fast-forward/equality/clean verification before beginning another task.
Related implementation/UI/tests/docs remain one task;unrelated completed tasks no longer
accumulate by default. No direct main push,bypass,agent,new automatic loop or release waiver.

F88PR20:https://github.com/wkdtlgns99-cell/Reverie-Saga/pull/20
Head21a707b99aeedac0d8cc40a1e535c62e67f35dd4;base4cc0004.
Required run41017530781SUCCESS:full3625PASS1131.51s,boundaries31PASS7.96s.
F88merged at bca720dbcd5f4b44efe71d31b98854579b1fc95d;local main equality/clean verified.
Current-PC F88new18PASS14.18s;native remains NOT_RUN.

Draft word counts560/554/551exceeded the existing550word bound;actual guard runs
rejected554and551. Shortened wording without changing the guard or other tests. Final results recorded below.
Existing local CPython3.13.12/Tk8.6 and installed tools reused;no install/config change.
GitHub CLI stored authentication failed;connected GitHub tools used for PR operations.

Local validation:existing rulebook10guards PASS1.03s;final rulebook549words.
Unchanged runtime/tests/CI;no gameplay tests required for this prose-only diff.
UTF8/local file links/whitespace/scope7files PASS. Policy commitb04a2f9published as PR21;
required run41018000274SUCCESS:full3625PASS1067.68s,boundaries31PASS7.37s.
Ordinary PR21merge0e8e133c5141e87b2770b624a85437ab6c13617f;fetched/fast-forwarded
local main equals origin/main,0ahead/behind,clean worktree before F89branch creation.
All acceptance criteria PASS. No runtime/protection/CI/dependency/agent/release change.
