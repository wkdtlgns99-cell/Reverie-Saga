# QT-F76 — Exact immutable literal validation cost

Status:IMPLEMENTED_ENV_BLOCKED2026-10-27. Local self-review,not independent/native acceptance.
[Order](../work_orders/QT-F76_IMMUTABLE_LITERALS.md). Primary2performance support;related6/7.
Current V2 keeps legacy outer equality dispatch and omits seal only for identity-proven
None/bool/int after the existing depth guard. Strings/impostors still use seal;all other
source/recursion/keys/frozen/mutable checks unchanged. Earlier first-patch results below
are historical and explicitly superseded by the V2section. No state cache or canonical/schema/pins/codec/field change.

Baseline actual263source has56792exact-int no-op seal calls. Current delegating probe
removes those calls;all other observed type counts remain exact and state/source preserved.
Instrumented1.701943/1.639398s are diagnostic only,not qualified speedup or global2sproof.
Semantic47PASS0.71s before and47PASS0.61s after;Ruffboth/format55/strict251/pip PASS.
ASTnormalization restores only the literal branch;rest of module/110other production/
135prior non-scope/index/8engine witnesses unchanged. Current related/CI/parity/runtime/
shared-core full/final documentation qualification remains incomplete.

ENV-001:existing grimp3.17_rustgrimp.cp313-win_amd64.pyd is blocked by Windows application
control on canonical startup/fresh-process retry and runtime-cycle import gate. Installed
RECORD matches SHA2560f3aa7aee09e644563038c8b82001d437cbfe9043079fbb0f9d8af6314ad9e3c.
No corruption/missing-package repair inferred,no security/dependency/allowlist/relocation
or checker/test weakening. Prior graph evidence is historical,not a current command PASS.
No question while independent safe validation remains;required approved trust resolution
is recorded in [deferred](../DEFERRED_USER_DECISIONS.md). Preserve actual failed results.

Computer Use STOPPED/AWAY-001,fresh native/build NOT_RUN. CP06/D2/independent rereview/
global2s/MIN-SPEC/standalone/release OPEN. No agents/publication/dependency/timed wake.
Original goal ACTIVE;task not accepted. Exact jobs/resume:tmp/qtf76/resume.json.

## Superseded first optimization checks before the metaclass repair

Current232PASS62.80s(including47new),exact31boundary PASS10.50s. Both import commands
fail at ENV-001native startup;all remaining static/pip checks pass. All9modes match whole
stable game/update/descriptor/pin/core/protocol results,excluding only per-session
attachment_id/working_path. Eighteen actual mode checkpoint/replay body samples are
validated via durable read_segment and replay;before/current bytes match. Eight actual
7/263source query samples before/current/direct/framed preserve all outputs,actual
persisted bodies,state/protocol/source and quiet retry. Current long talk1.751639/1.735347s
and activity1.849208/1.807865s are slower than baseline1.622568/1.654594s and1.761732/
1.715186s(direct/framed). Keep all samples;no overall speedup claim.

Five alternating guard-only pairs on13actual records/1000iterations per sample isolate
lower local wall median0.0566971to0.0465299s(~17.9percent). CPUclock15.625msquantization
limits its25percent median estimate. This diagnostic does not qualify overall latency.
Initial parity setup wrongly used full-witness encode_fixture for retained witness=None;
only baseline-memory preparation failed before any pair/timing completed. Its database/
log retained;new runtime-pairs uses proper durable read_segment and actual checkpoint/
replay BLOBs. No product codec/test/golden changes or invented witnesses.

Targeted existing replay/G07will run on frozen current inputs independently of ENV-001;
whole shared-core full/import gate acceptance remains outstanding. Task still in progress.

## V2 metaclass repair and current evidence

First optimization incorrectly admitted PretendInt/PretendFrozenInt/PretendFrozenStr.
New semantic tests reproduce3FAIL0.32s against first optimization and3PASS0.18s against
original baseline. Repaired50PASS0.77s retains legacy outer equality dispatch and only
omits seal for identity-proven None/bool/int. No dataclass subclass newly admitted.
V2Ruffboth/format55/strict251PASS;235affectedPASS66.90s,31boundaryPASS11.18s. Unchanged
pip evidence reused;both native import failures remain without repeated retries.
Normalized module AST restores only local type binding/identity literal omission;
110other production/135prior non-scope/index/G07source witnesses preserved.
New delegating actual263query probe0literal calls/56792baseline,all other observed counts
EXACT,source/state/query bytes preserved;instrumented1.549716s is diagnostic only.
All9current-v2mode payloads/descriptors/pins/core/protocol/persisted bodies EXACT versus
unchanged baseline. Four current-v2query samples compare against unchanged baseline4,
all stable outputs/read-only state/source/retry/core/protocol/persisted bodies EXACT.

- short/direct:talk0.2968109s,activity0.2400341s.
- short/pipe:talk0.2744828s,activity0.2052281s.
- long/direct:talk1.6330913s,activity1.7308435s.
- long/pipe:talk1.5927913s,activity1.6605643s.

Five new alternating guard-only pairs on13actual records/1000fresh passes per sample:
wall median0.0596975to0.0528808s(11.4percent lower),component-only diagnostic.
CPUclock is coarse;no precise CPUgain or end-to-end/global2s/min-spec/native claim.
All original slower first-optimization samples remain retained as superseded evidence.
Current full will run once on frozen inputs,including the known native dependency test;
this is remaining semantic qualification,not a retry of failed import startup alone.
ENV-001continues to block acceptance. No test skips/security/dependency/checker changes.

Read-only Windows evidence:CodeIntegrity3077 policy VerifiedAndReputableDesktop,
PolicyID27555.1000.240208,status0xc0e90002;binary NotSigned and installed RECORD match.
Record match alone proves neither trusted publisher nor safety. Microsoft's
[Smart App Control overview](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/overview)
describes reputation/signing-based trust;no configuration guidance applied.

## Terminal complete current regression and remaining acceptance

Exec82669/PID28480TERMINAL1,one run:3123cases,3037PASS/86FAIL/0error/0skip,1452.18s
(wrapper1453.609685s). All86failures are tests/governance/test_dependency_contracts.py
with the same Windows-policy _rustgrimp startup. The checker did not evaluate graph
contracts;none is relabeled a product defect or successful graph result. Full JUnit/
per-case details/classification preserved in full-v2 and v2/full-classification.json.
All50new and168current replay/G07cases PASS. One existing record_property/xunit2warning
retained. All359frozen source/test/tool/config/docs/native inputs and actual index
preserved during run;only private reviewed index used. Reviewed encounter/watch blobs
3ca0453b58cbe6819c28abc234aafc67b0c034b7/c8309fa29819acf217f7962b3025bac6739dedfb.
Final7metadata documents follow terminal;all non-document inputs remain frozen hashes.

Current implementation/self-review is complete,but required successful full/import
qualification remains ENV_BLOCKED and task is NOT locally accepted. Preserve3037passing
case evidence and all failed gates;do not repeat unchanged full/native failures. Approved
external workstation trust resolution is required before retrying those gates. No security/
allowlist/dependency/checker/test/golden change or claim that RECORD hash proves safety.
All F76sessions terminal (59326,43571,82669;earlier diagnostics also terminal),no live jobs.
Final scope145/135prior non-scope/110other production/index/scene/links/document10/current
251Python closure is recorded by delivery.json,which is explicitly a blocked snapshot.
Original objective ACTIVE,unfinished;CP06/D2/independent/global2s/MIN-SPEC/standalone/
release remain OPEN. Fresh native/build NOT_RUN AWAY-001,Computer Use STOPPED.
