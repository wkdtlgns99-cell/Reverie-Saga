# QT-F57 — Validate and copy canonical serialization in one traversal

Status:LOCAL_ACCEPTED2026-10-25. Executor:current Codex;self-review,not independent.
Authority:director's active automatic NPC/world development and measured-latency scope.
Primary2internal-calculation performance support;related4retrieval,6save,7integration,5client.

| Field | Contract |
|---|---|
| goal/non_goals | Reduce repeated canonical serialization traversal/allocation on real verified long-history NPC dialogue. Preserve every validation and byte/hash result. No new gameplay,state/cache,LLM,dependency,pin/schema/save/wire change,validation bypass or target-waiver |
| baseline | HEAD72c2d588d7f64c3e113cf462af35fb673bf82582,branch codex/cycle-call-recall-20261024;54accepted F49–56dirty paths. F56delivery copied to tmp/qtf57/entry.json;prior goal turn progress:implemented/qualified F56. No live jobs. Fresh read-only aid265profile5.810s with profiler,10,438,742calls;canonical_json20,201calls/1.350s cumulative,seal903,391calls/1.765s(shared with other operations),_plain185,982calls/0.363s. Source bytes preserved. Timings with profiler are diagnostic only |
| prerequisites/reads | ENGINEERING_RULES,handoff/backlog/Korean progress,AUTONOMOUS_EXECUTION,numbered guide,Sol template,WORKSTATION_SETUP/README verification;MASTER3/8/9/11;domain.canonical/primitives,serialization/replay/read-view consumers,existing literal vectors and new semantic coverage. Existing installed Python3.13.12/Tk8.6/editor6000.3.25f1 reused |
| MODIFY | C:/Reverie Saga/src/domain/canonical.py;clients/unity/Assets/Reverie/Scripts/PlayRoom.cs;clients/unity/Assets/Reverie/Scripts/LiveVerification.cs;BACKLOG.md;SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md;this order |
| NEW | C:/Reverie Saga/tests/unit/test_canonical_conversion.py;docs/reviews/QT-F57_EXECUTION_2026-10-25.md;owned ignored tmp/qtf57 and .pytest_cache/qtf57-*;temporary clients/unity/Assets/Reverie/Editor/F57VerificationTrigger.cs/.meta then remove and byte-exact restore original PlayRoom.unity |
| forbidden | Other source/tests/goldens/configuration/governance/CI/content/dependencies,user saves/credentials,prior frozen receipts/orders and source logic. No agents/publication/release/security or reference-checkout change |
| public_contract | Existing seal(value:object,depth:int=0)->JsonValue and canonical_json(value:JsonValue)->bytes unchanged. seal returns owned immutable MappingProxyType/tuple tree. canonical_json returns identical sorted UTF8 compact JSON;hash_document/tagged_hash/decode_json/pack unchanged. No Python callers change. Editor/development-only internal IsolatePhysicalInputForVerification defaults false per room;automated runner sets before readiness and clears on destruction. Poll/render/scripted commands unchanged;only physical key/mouse/scroll input is ignored while true. No nondevelopment flag/API |
| behavior/algorithm | Replace seal→_plain double traversal with one private recursive conversion,parameterized only by output ownership representation. Shared scalar/type/NFC/UTF8/depth/key validation remains one implementation. Immutable mode constructs MappingProxyType/tuple;serialization mode constructs owned dict/list consumed immediately by unchanged json.dumps options. seal delegates immutable mode;canonical_json delegates serialization mode. No trusted-input fast path or memoization. Existing JsonValue boundary cast only after immutable conversion,with no Any |
| edge_policy | Preserve exact bool/int acceptance(no int subclass),str subclass handling,NFC and strict UTF8 rejection,non-string key error,unsupported objects/floats/bytes/sets,depth>32rejection including object keys,cycle rejection via depth,empty containers,aliases copied per occurrence,key sort and integer rendering. Preserve error type/message/order and source object contents;decode_json duplicate/nonfinite guards unchanged |
| independent_examples | {'b':[True,None,-2],'a':'문'}→UTF8 bytes of '{"a":"문","b":[true,null,-2]}';tuple and list same bytes,distinct bool/int tokens. Leaf beneath32array edges accepted;33rejected with JSON nesting exceeds32. An empty mapping at depth32accepted;any string key at depth33rejected. Non-string key rejects JSON object keys must be strings before key-depth validation. A sealed view of externally backed MappingProxyType retains original values after backing-dict mutation |
| wiring | Shared canonical_json/hash_document used by StateIO/replay/durable publications and existing ClientSession cycle talk/activity through one verified replay;same framed worker/Tk/Unity. No new endpoint. Existing literal vectors/replay digest checks and negative schema/read-view/source guards must continue |
| performance | Sequential current-host measurements:isolated nested canonical documents and real long cycle/aid talks on fresh owned copies,5alternating baseline/current pairs per long mode. Freeze baseline domain.canonical.py and import it before consumers in separate worker processes. Compare exact messages/core/protocol/hash/save input/retry and activity. Require measured canonical median improvement with no demonstrated end-to-end regression;report noise/ranges honestly. Existing2sTARGET/10sclient deadline remains;do not close broad long-history/MIN-SPEC from a few samples |
| baseline_commands | New semantic tests and existing literal canonical vectors pass on original code;optimization has no intended functional red case. Preserve new baseline/current logs. Fresh source profiler already completed in tmp/qtf57/activity-profile.txt without mutation |
| verification_commands | README Ruff both,scoped format canonical+new test+canonical list,strict mypy/import3+1/pip,exact CI31. Full pytest required because shared CORE changes;use existing canonical capture=sys and permitted host for hardlink fixtures. Preserve reviewed8-source private index setup from F55 without real staging/refs. Freeze current source/test/tool inputs;observe terminal session,never restart on timeout. Retained-editor fresh aid2=54+cycle2=153after evidenced input-isolation repair,actual captures,13new-stage save readbacks/replay/query/new-talk/retry/bytes,scene159hash guard. Preserve initial failed cycle1/passed aid1sources/logs. Fresh nondevelopment Windows build and actual type/method/field hook exclusion required |
| test_responsibilities | NEW test_canonical_conversion.py:literal outputs,strict invalid scalar/key/subclass/Unicode cases,depth boundary/error precedence,cycles,empty/alias trees,owned immutable snapshot and no caller mutation. Existing canonical vectors/complete replay/runtime tests qualify hash and behavior compatibility;new tests assert contracts,not converter internals |
| acceptance | Shared validator exactly preserves outputs/errors/immutability,measured cost reduction,full/static/boundary/native/save checks and exact source/diff/scope proofs,synchronized English evidence/Korean roots. Failure/performance regression triggers repair or removal within this order,not acceptance by test count |
| checkpoints/stops | Internal implementation of frozen canonical contract;no new CP01–05contract/integration. CP06held,independent patch rereview deferred. Stop/escalate if accepted bytes/errors/schema need changing,new authority is needed,user edits overlap or required checks unavailable after safe alternatives |
| delivery | English receipt with actual commands/results/performance/raw failure evidence and limits;root trio together before advancement. Goal ACTIVE;no commit/push/PR/merge,agents,external messaging or release |

## Evidenced verification repair — 2026-10-25

After full2418PASS/bridge/aid54PASS,cycle1failed strict genesis(tick0expected). Read-only
save validation proves tick1/one actual `trial.move(0,1)` before any scripted movement.
The existing normal keyboard/UI path remained active during automated verification.
Preserve cycle1/log/source and initial aid1;do not weaken genesis or invent rollback.

Scope amendment under the authorized verification repair:MODIFY
`clients/unity/Assets/Reverie/Scripts/PlayRoom.cs` and `LiveVerification.cs` only for
editor/development verification physical-input isolation. Add one per-room internal
flag(defaultfalse,compiled out of nondevelopment builds);automated runner sets it before
waiting for readiness and clears on runner destruction. Poll/render/direct scripted
commands remain active. While flagtrue,skip only physical Escape/movement reads and
consume IMGUI key/mouse/scroll events;layout/repaint/visual/button-enabled contracts remain.
Normal play is unchanged. No domain/state/wire/new gameplay authority or test bypass.

First retain the two old C#sources/native159manifest. Rebind current159inputs after this
explicit repair;run fresh aid2and cycle2with every original54/153assertion unchanged.
Do not reuse polluted cycle1or erase it. All13new-stage save readbacks/captures/source
guards remain required. Run actual Python consumers of the modified C#sources,if any.
Python CORE source and all244full inputs stay frozen;reuse completed Python full for
those unchanged inputs,with current C#qualification separate. New Windows build is now
REQUIRED;actual PE metadata must exclude LiveVerification,GateOpenForVerification and
the new isolation flag. F56build reuse is superseded for this amended scope.
Final58path inventory stays;49prior non-scope paths preserved(3progress+2C#authorized).

Acceptance:[execution receipt](../reviews/QT-F57_EXECUTION_2026-10-25.md).
Current Python full2418PASS1343.55s/244inputs unchanged;current C#native aid2=54+
cycle2=153PASS,13readbacks/new Windows build89,491,232bytes and actual PE type/method/
field exclusion PASS. All original assertions retained;initial failure/5sources preserved.
Original scene on disk byte-exact/current159inputs preserved,temporary harness removed.
User stopped Computer Use with Escape after disk cleanup;no further UI automation.
Post-cleanup editor scene reload/screen is UNVERIFIED,not part of the file-restoration
claim. No manual desktop/standalone/MIN-SPEC/release or whole-goal completion claim.
