# QT-F99 — Canonical selection scalar validation

LOCAL_ACCEPTED2026-11-03;self-review,primary2performance support;related5/6/7.
[Order](../work_orders/QT-F99_CANONICAL_SELECTION.md).

## Entry and measured scope

Fresh Git/local inspection:clean main/origin-main dbcd288b5030008ee32faef9dc77aebac58e248d,
0ahead/behind,no untracked files. F98PR31already merged;no overlapping work. Reused this
PC's existing Python3.13.12/Tk8.6 and pinned tools. No install,global setting or other-device
qualification. New scoped branch codex/qt-f99-canonical-selection-20261103.

Own child-mode SQLite fixture:264commands,tick276. Read-only activity4.320988s,39messages,
source bytes unchanged. Profile12.978s includes profiler overhead,not product latency.
Verified replay remains264commands;command encoding37092calls and select35508calls.
Repeated validation is required;neither replay skipping nor cross-call caching is adopted.

Only production change:CanonicalDocument.select calls existing _checked_text(key) after
the existing isinstance(str) rejection,instead of seal(key). The removed generic wrapper
and scalar dispatch already led to that same helper at depth0. No validation is removed.
String subclasses still receive fresh NFC/UTF8 validation before source lookup;lookup
ordering,KeyError identity,owned values,canonical bytes and selected-subtree height stay.
No engine,contract,save-format,public API,IO,CI,dependency or native change.

## Semantic verification

New11cases independently cover empty/duplicate/reordered selectors,literal ASCII/control/
Unicode bytes,non-string and non-NFC errors before lookup,surrogate error details,missing
key identity/precedence,hostile str subclasses,fresh encode rejection,caller alias ownership
and exact nesting32 after shallow subtree selection. New cases plus existing canonical/
keys/owned/protocol suites PASS96in2.49s on unchanged baseline before the production edit.
Final affected132PASS23.90s includes actual assistance-memory slots/clients and replay.
Both Ruff configurations PASS;strict288files PASS. Existing tests/goldens unchanged.

## Measurement integrity

Preliminary isolated private-method probe showed small improvement;it is feasibility only.
Initial probe compared fresh attachment nonces and failed. Diagnostic established only
attachment_id differed;the corrected probe validates the token inside each attachment.

Actual qualification uses separate baseline/current processes with imported module paths
and SHA256 proofs. Real framed child startup asserts its selected source and records its
own proof. Complete public updates and complete SQLite dumps are compared across variants
and channels;only per-attachment nonce and per-case working path are normalized. Within
each attachment the token is preserved. Read-only activity preserves bytes;talk retry
preserves state/protocol/bytes and emits exactly the existing already-processed notice.
Frozen activity/talk sources remain byte-identical throughout the matrix.

First owned harness failed because script-directory imports omitted the repository root.
Second failed on baseline because it wrongly expected an empty retry message;the existing
client deliberately emits an already-processed notice. Only the owned harness was fixed;
failed logs/data are retained under tmp/qtf99. No product/test/check bypass or regression
is inferred from these harness errors. Final qualification/result follows below.

Framed decoding owns JSON arrays as tuples,so the harness's list comparison also rejected
the correct baseline notice. Corrected the comparison to tuple form and regenerated only
the missing six framed-talk samples in fresh paths. Eighteen already valid matrix samples
are reused with unchanged source proofs,inputs and output/SQL checks. An owned helper also
initially read UTF8 through cp949 before its environment assignment;fixed the invocation
ordering. These are harness failures,not product failures or accepted failed measurements.

Final source-bound matrix:three alternating baseline/current pairs for each query/channel,
24timed queries. All complete updates/SQL EXACT and frozen sources unchanged. Medians:

| Channel/query | Baseline seconds | Current seconds | Improvement |
|---|---:|---:|---:|
| direct activity |4.380592|4.326795|1.2281%|
| direct talk |4.698147|4.511856|3.9652%|
| framed activity |4.303779|4.253721|1.1631%|
| framed talk |4.484640|4.453398|0.6966%|

All samples<10sdeadline;2sTARGET remains OPEN. Small current-PC improvement,not a
general-device/MIN-SPEC claim. Preserve individual observations,proofs and parity in
tmp/qtf99/qualification.json,pairs3/pairs4 and qualification5.log. Unprofiled measurement,
source isolation and complete persisted-state equality qualify the one-line dispatch
removal;no new gameplay capability is claimed.

Native Unity compile/editor/render/build NOT_RUN. Independent/device/CP06/release holds
retained;no new automatic goal,agent or next feature follows from this receipt.

## Final local acceptance and publication input

Full shared-domain regression including goldens:3785PASS765.86s,exit0. All293frozen
source/test/config inputs unchanged before/after. Canonical capture=sys retained;approved
execution permits actual loopback/hardlinks without changing tests or host settings.
Exact twelve-node selection from unchanged CI:31PASS5.13s. Both Ruff configs/strict288/
README formatting plus canonical/new test14/imports3+1/pip PASS. Nine-path scope,UTF8,
Markdown local references and diff whitespace PASS. Self-review confirms one production
line only;new independent tests exercise baseline semantics rather than an implementation
mirror. Root backlog/handoff/Korean progress updated together. F98prior publication
metadata now records actual both-check success,PR31merge and local main equality.

Actual PR/jobs/refs own later publication. Standing/current user authorization covers scoped
commit/push,PR,both latest-head required full checks,ordinary merge and local main
fast-forward equality/clean verification. Preserve actual evidence in ignored
tmp/qtf99/publication/result.json. Finish one F99task;no further feature/goal/agent launch.
