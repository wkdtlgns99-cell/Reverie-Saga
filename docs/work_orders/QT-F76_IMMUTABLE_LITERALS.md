# QT-F76 — Avoid redundant sealing of exact immutable literals

Status:IMPLEMENTED_ENV_BLOCKED2026-10-27. Local self-review,not independent/native acceptance.
Authority:explicit human go;original supported goal ACTIVE after quota reset. Primary2
performance support,related6/7;no new NPC cognition/gameplay claim.

| Field | Contract |
|---|---|
| goal/non_goals | Reduce redundant canonical conversion while preserving every accepted/rejected immutable record and every canonical byte/error. No state cache,codec/checkpoint/registry validation removal,new canonical API/schema/save/pins/engine/feature/DTO/wire/dependency/provider/governance/native change |
| baseline | HEAD72c2d588d7f64c3e113cf462af35fb673bf82582,branch codex/cycle-call-recall-20261024. All141F75delivery hashes/index verified,staged empty,no live jobs;tmp/qtf76/entry.json/baseline111sources. F74profile contains108863immutable calls,78113seal calls from it/0.094136instrumented seconds of4.257338query. Fresh delegating probe of the same263source observes56792exact-int no-op seal calls;query/source preserved. Probe1.701943s is instrumented,not qualification or speedup evidence |
| prerequisites/read_files | ENGINEERING_RULES/handoff/backlog/Korean guide/MASTER2Brain/Body+performance/v2.6immutable-CORE-serialization boundaries/Sol template/setup/README/AUTONOMOUS_EXECUTION/deferred/F74profile/F75delivery;actual serialization._immutable/_component_fields/_decode_payload/encode_core/validate_checkpoint,domain.canonical.seal/_convert,registered fixtures/F61codec validation/F67metadata tests |
| MODIFY absolute paths | C:/Reverie Saga/src/orchestration/serialization.py;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md;C:/Reverie Saga/README.md;C:/Reverie Saga/docs/DEFERRED_USER_DECISIONS.md;this order |
| NEW absolute paths | C:/Reverie Saga/tests/unit/test_immutable_literals.py;C:/Reverie Saga/tests/integration/test_immutable_validation.py;C:/Reverie Saga/docs/work_orders/QT-F76_IMMUTABLE_LITERALS.md;C:/Reverie Saga/docs/reviews/QT-F76_EXECUTION_2026-10-27.md;owned ignored tmp/qtf76 |
| forbidden_paths | All other production/domain/contracts/engines/CORE/checkpoint/codecs/readview classes/old tests/goldens/G07inventory-tool-scope/C#/scene/governance/old orders-receipts/user files/reference. No agents/publication/commit/push/dependency/window/native/build |
| public_contract | Existing _immutable(value:object,depth:int=0)->None private signature/result/error contract unchanged. No new API or external behavior. All state/payload codecs,field ranges/types/identity/canonical roundtrip/adapter/checkpoint rules still run fresh through existing callers |
| behavior/ownership | Keep depth>32 rejection first. Exact None/bool/int are already immutable and accepted by seal for all integer magnitudes;return directly instead of calling seal with depth0. Exact str still calls existing seal for NFC/strictUTF8. Preserve legacy outer type-equality dispatch,including canonical rejection of metaclass impostors. All tuple/MappingProxyType/frozen dataclass recursion and unsupported mutable/nonfrozen/subclass cases remain byte-exact source. No value/result cached across calls |
| edge_policy | 0/negative/huge exact integers remain valid immutability literals;integer field bounds and bool-as-integer rejection remain later declared checks. Int/str subclasses are not newly admitted. Depth32valid/33reject even for literals/empty containers;depth error precedes leaf error as before. Every sibling still visited;literal prefix cannot hide later mutable/Unicode error. Mapping keys still use original seal,including existing error precedence;no new key/schema policy. Frozen dataclass values still validated freshly,no metadata/state cache |
| examples | None/False/True/0/-1/2**200 ->None;exact NFC text ->None,non-NFC ->ValueError non-NFC string,surrogate ->UnicodeEncodeError. Tuple(0,mutable-list) rejects unsupported child. A valid frozen record then an invalid sibling record still fails without mutating input. Gauge valueTrue/10/-10still INVALID_COMPONENT despite immutable primitive acceptance. Depth33literal rejects record nesting exceeds32 |
| algorithm_steps | Capture actual baseline work without production edits. New semantic boundary/registered IO tests must pass on baseline and current;this is an equivalence optimization,not a manufactured correctness failure. Bind runtime type once,preserve original outer equality dispatch,and omit seal only for identity-proven None/bool/int;all remaining outer-branch values still seal. No other source changes. Verify literal no-op calls eliminated in one delegating query probe,strings/owned source/output/state preserved. Static/affected/full/9mode/schema+rules+pin+state+protocol+persisted-segment parity and actual before/current direct/framed timing;retain every sample |
| wiring | Existing RegisteredStateIO record/payload encode/decode and checkpoint paths call _immutable;do not add a separate disconnected fast path. Real client/replay/query/durability/worker/framed/Tk paths qualified by current related/full suites and actual saved-source comparisons |
| performance | Baseline actual263query56792no-op int sealing calls;current must remove those redundant calls without changing results. Keep fresh recursion/codec/Unicode validation. Measure same short7/long263source talk/activity before/current direct/framed once per sample,target2s/existing10sdeadline;global2sOPEN until separately proven. This local guard is not the sole replay bottleneck;no inferred cross-mode speedup/min-spec claim |
| baseline_commands | F75hash/index PASS;F74pstats reused,one delegating actual query probe/source preservation PASS. New semantic unit/integration baseline expected PASS before edit,then unchanged acceptance after edit. Preserve logs and exact inputs |
| verification_commands | README Ruffboth/scopedformat55/strict source mypy251/import3+1/pip/new+immutable/codec/metadata/registeredIO/durability/replay/memory-client related tests/exactCI31/document10. Old9stable complete game outputs/descriptors/pins/core/protocol exact,excluding only attachment_id/working_path. Actual persisted segment bytes/checkpoint+trace readback and short/long direct/framed outputs/retry/source/timings. Shared serialization change requires one current frozen full after source/static acceptance;poll exact live handle,never restart on timeout |
| test_responsibilities | NEW unit exact literals/depth/frozen tuples/mapping proxies/all siblings/NFC-UTF8/subclasses/mutable children and error precedence. NEW integration fresh registered codec/range/type/Unicode rejection after valid records,unchanged input/encode-decode/hash/actual persisted replay and rollback semantics via existing affected/full callers. No tests asserting implementation call counts;diagnostic work counts stay owned evidence |
| acceptance | All semantic bytes/errors/ownership/caller behavior preserved;one narrow production diff. Current new/affected/static/import/CI/docs/full/9mode/persisted/runtime/source checks pass;all110other production/135prior non-scope/index/scene preserved,scope145. Exact primitive no-op probe calls removed,all timings retained. G07inventory/8engine witnesses/35public/8golden/4nested unchanged;use existing F74reviewed source scope/private index for fresh full,no gate changes. LOCAL_ACCEPTED Python/runtime only,fresh native NOT_RUN AWAY-001 |
| claude_checkpoints | CP01-05not newly triggered:private immutable validation cost only,same architecture/contracts,not new engine/pipeline. Shared boundary merits full regression,not fabricated independent feedback. CP06held;D2/independent rereview/global2s/MIN-SPEC/standalone/release OPEN |
| stop_conditions/delivery | Stop on changed user files/semantic divergence/new authority;record actual missing decisions while doing independent safe work. Keep Computer Use STOPPED/no agents/publication. English evidence and Korean primary2performance-support status,baseline/current/full handles/hashes preserved. Do not complete the original unbounded objective after this task |

## Current environment and independent verification sequencing

ENV-001blocks existing import-linter/grimp3.17native startup;both import gates remain
failed/unverified,no security/checker/dependency bypass. All other current static checks,
232affected/47new and31boundary cases pass. Old9whole stable outputs/pins/core/protocol/
actual persisted checkpoint/replay body bytes match before/current;18mode samples and8
actual short/long direct/framed query samples retain source bytes. The failed baseline
fixture-encoder diagnostic was corrected to existing durable read_segment/raw body BLOB
comparison without changing product codecs or repeating a successful comparison.

Whole-query current long samples are slower than their baseline samples and remain
recorded;do not claim latency gain. Five alternating same-interpreter guard-only pairs
on13actual checkpoint records show lower local wall cost;CPUtimer is coarse. This does
not establish end-to-end/global2s/min-spec improvement. Shared-core full and import gates
remain acceptance prerequisites. Targeted existing replay/G07checks may proceed as
independent verification on frozen inputs while trust resolution is deferred;they are
not a substitute for the required full or failed import commands. Do not mark accepted.

## V2 correctness repair and complete regression

An additional semantic review exposed three introduced metaclass-equality admissions.
The original branch rejected all three through canonical sealing;new regressions passed
on baseline3/3 and failed first optimization3/3. Preserve the original outer equality
branch and only omit sealing after identity-proven exact literals. Repaired50new/
235affected/31boundary and both Ruffconfigs/format55/strict251 PASS. V2source audit,
probe,all9modes and four fresh current query samples pass with unchanged baseline reused.
Earlier47/232/168replay/runtime/guard evidence is retained as pre-repair,not current PASS.
Run one complete frozen regression now to discover other current regressions,including
the known ENV-001dependency failure without skips or checker changes. A failing expected
environment gate does not qualify acceptance;all outcomes and frozen input hashes remain.

## Terminal current full;acceptance blocked

One complete current run exec82669/PID28480TERMINAL1:3123cases,3037PASS/86FAIL/0error/
0skip in1452.18s,wrapper1453.609685s. Every86failure is the same ENV-001native checker
startup in test_dependency_contracts;no graph-contract result inferred. All50new and
168current replay/G07cases PASS. All359frozen inputs and real index remained unchanged
during run;reviewed engine blobs/private index only. Final7documentation files follow
terminal;delivery.json closes scope145/hash/doc checks with status ENV_BLOCKED,not acceptance.
Required successful import/full gates remain unresolved. Reuse unchanged passing evidence;
do not rerun failed native startup or whole suite without a real external-state change.
All F76jobs terminal. Computer Use STOPPED/AWAY-001,CP06/independent/release holds retained.
