# RS-PUBLISH-001 — Per-task main synchronization

IN_PROGRESS2026-10-30;self-review,primary7workflow support;no gameplay change.
[Order](../work_orders/RS-PUBLISH-001_PER_TASK_MAIN.md).

Director grants standing delivery authority for each authorized coherent task:scoped
commit/push,PR,required latest-revision CI and checkpoint checks,ordinary merge,local
main fast-forward/equality/clean verification before beginning another task.
Related implementation/UI/tests/docs remain one task;unrelated completed tasks no longer
accumulate by default. No direct main push,bypass,agent,new automatic loop or release waiver.

F88PR20:https://github.com/wkdtlgns99-cell/Reverie-Saga/pull/20
Head21a707b99aeedac0d8cc40a1e535c62e67f35dd4;base4cc0004.
Required run41017530781in progress;no merge/success yet claimed.

Initial rulebook guard runs correctly rejected560/554/551word draft variants;shortened
wording without changing550word guard or other tests. Final results recorded below.
Existing local CPython3.13.12/Tk8.6 and installed tools reused;no install/config change.
GitHub CLI stored authentication failed;connected GitHub tools used for PR operations.

Local validation:existing rulebook10guards PASS1.03s;final rulebook549words.
Unchanged runtime/tests/CI;no gameplay tests required for this prose-only diff.
Remaining:scope/link audit,ordinary publication and local main synchronization.
