# QT-F84 — Protocol conversion cost on long verified NPC queries

LOCAL_ACCEPTED2026-10-29,self-review;2sTARGET OPEN. Primary2performance support;
related4retrieval,5wait,6save,7real direct/framed integration.
[Order](../work_orders/QT-F84_PROTOCOL_CONVERSION.md).

## Cause and implementation

F82's4misses were long-history talk/activity,not slot inspection. Actual owned tick132/
132step source activity4.758797s. Stdlib profile(with overhead)16.270s:Runner15.786s,
132submit12.405s,137validate_checkpoint9.130s,139decode_protocol5.383s,
36564encode_command4.894s. Every replay turn validates a growing receipt history;
repeated command codec conversions and recursive canonical ownership copies compound.

Only serialization.py production changes. Private payload/command conversion returns its
fresh owned document and fully roundtripped decoded payload/command. Native checkpoint
validation consumes those same-call results in the common protocol walker,while public
wire decoding still performs fresh registered command validation. Fingerprints use the
validated encoded document already produced by that call. Internal owned-payload consumers
avoid copying a DTO just sealed by the same operation. No cross-call memoization,skipped
replay/truncated records,validation bypass,format/pin/schema/engine/owner/phase change.
All immutability,exact-type,Unicode/depth,codec reencode/class,stream/receipt ownership,
order/caps/revisions/tick/head/hash checks,protocol equality and policy remain.

## Verification

New semantic8PASS on original source3.35s;83codec/protocol/metadata cases PASS before
final qualification. Ruffdefault/quality,strict264/import3+1/pip PASS. Permitted full
PYTHONPATH=src/PYTHONUTF8=1/PYTHONHASHSEED=0:3562PASS984.82s,exit0. Same canonical capture,
checks and goldens;no source mutation during full. Current full includes CI31/document10.
Final document/scope checks are separate delivery evidence. Default+11prior opt-in modes
whole outputs/core/protocol/SQL dumps match preserved main baseline exactly. Reach-mode
before/current short/long direct/framed all updates and full SQLite dumps also EXACT,
including state/source/retry guards. Only attachment_id/working_path are omitted from
cross-process update equality. Real child launcher selects preserved/current source via
PYTHONPATH;it never replaces domain outcomes. Provenance files record actual module/hash.

## Paired measurements

| Long query | Before seconds | Current seconds |
|---|---:|---:|
| direct talk |4.906821|3.691802|
| direct activity |4.763930|3.644262|
| framed talk |4.948312|3.726747|
| framed activity |4.762113|3.568566|

All12short/long talk/activity/slot samples:mean1.845204->1.427486s;
max4.948312->3.726747s. All4long talk/activity cases still exceed2sTARGET;
all12stay below10sdeadline. These are paired single samples,not global latency/MIN-SPEC
qualification. Residual replay still performs fresh simulation/checkpoint/receipt validation
for each step;its growing-history cost remains. Do not reinterpret this as2sacceptance.

Evidence:tmp/qtf84/profile2.log,activity.pstats,semantic-baseline.log,core2.log,full.log,
matrix-before/matrix-after(results/provenance/performance),timing-comparison.json,
parity-after/results.json. The initial profiling script shadowed stdlib profile and failed;
it was renamed before actual profiling,without production/source-save mutation.
An initial private stream DTO annotation was corrected before full/static acceptance.
Native/editor/compile/render/build NOT_RUN;CP06/independent/device/release holds retained.
No agents,commit/push/remote CI/security/dependency/goal action. One additional task is
now authorized;F85current next-action reply presentation is selected.
