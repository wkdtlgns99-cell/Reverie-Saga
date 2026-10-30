# QT-F89 — Tk previous-save controls

LOCAL_ACCEPTED2026-10-30;self-review,primary5presentation support;related6/7.
[Order](../work_orders/QT-F89_TK_PREVIOUS_SAVE.md). Publication remains pending below.

Entry clean main/origin-main0e8e133after ordinary F88PR20and policyPR21merges.
Reused this PC's CPython3.13.12/Tk8.6/.venv and pinned tools;no dependency/settings change.
Only production client.pychanges:two explicit buttons route to existing worker APIs,
one extra control row,existing busy/close lifecycle,and operation-specific pending text.
No backend,rules,format,pin,wire,native or existing test changes.

Independent selected-slot vector:save1then3,live5,damage latest;normal load rejects,
previous preview shows1without changing view/path/token/source bytes;explicit restore
loads1into a private branch,new token,history reset,retry cleared. Slot01and08both pass;
new action reaches3and a fresh ClientSession resumes that branch with original files exact.
Missing/corrupt previous never falls back;failed reads/loads preserve retry. Real Tk
callbacks/worker/SQLite also cover pending duplicate suppression,disabled controls,
Future failure/cancellation,next action,close,reach-mode saved support text and nonoverlap.

Baseline two actual Tk cases fail at missing previous-preview control,1.90s.
Initial new10run:8PASS/2FAIL6.35s because a new history oracle incorrectly required every
load message to contain the phrase previous-save;existing load also reports the private
working path. Corrected only the new oracle to assert tick1/reset history and source label;
no product/legacy-test workaround. Initial static findings in new tests:fixture alias export
and untyped lambda tuple;explicit fixture registration and Callable annotation fix both.

Affected selection(new,client,pending-query,previous-slot,F88support):123PASS/2environment
FAIL47.99s. Both failures are unchanged existing os.link cases denied by Windows sandbox
WinError5. Permitted unchanged rerun of both plus final new10:12PASS6.07s. Thus125distinct
affected cases qualified;all10new pass on final source. No skip/mock/security workaround.
Logs:ignored tmp/qtf89/affected.log;other commands recorded in this chat.

Static:both README Ruff checks PASS;changed production/new-test format2PASS;strict mypy
272files PASS;type-inclusive import contracts3PASS/runtime1PASS;pip check PASS.
Current-host actual Tk samples:slot01preview0.049909s/load0.141753s;
slot08preview0.046586s/load0.150430s. Single short fixtures,not global latency/MIN-SPEC.
No added synchronous IO/replay;one existing worker operation per click.

Shared CORE is unchanged;prior required CI3625PASSqualifies the entry baseline,not this
new head. New-head required full CI and merge/main sync remain mandatory before delivery.
Native Unity compile/editor/render/build NOT_RUN;independent/device/CP06/release holds remain.
Final exact unchanged CI boundary selection:31PASS5.18s using the twelve workflow node
paths. UTF8/local file links/whitespace/scope10paths PASS;production-only client.pyconfirmed.
Prior F88/policy publication metadata corrected in their receipt/order and root trio.

## Publication input snapshot

The director's standing rule authorizes scoped commit/push,PR,required latest-head CI,
ordinary merge and local main synchronization. This is the precommit acceptance record;
actual GitHub PR/jobs/refs own final publication status. Preserve final publication evidence
under ignored tmp/qtf89/publication. No further feature selection authorized.
