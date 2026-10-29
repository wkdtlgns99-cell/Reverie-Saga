# QT-F55 — Reuse static schemas and read saved headers as binary

Status:LOCAL_ACCEPTED,2026-10-25. Executor:current Codex;self-review,not independent.
Authority:director's active automatic development request;F54locally accepted first.
Primary2internal-calculation performance support;related4retrieval,6save,7integration,5wait.

| Field | Contract |
|---|---|
| goal/non_goals | Remove repeated allocation/validation of the same8static component TypeKeys from long NPC conversation replay. Preserve every schema value,component/command/state/pin/save/replay/error and read-view contract. No dynamic state/result cache,validation bypass,new gameplay,scheduler,save format,dependency,governance policy,publication or release |
| baseline | HEAD72c2d588d7f64c3e113cf462af35fb673bf82582,branch codex/cycle-call-recall-20261024;40accepted F49–54dirty paths. Snapshot tmp/qtf54/delivery.json into owned tmp/qtf55/entry.json before implementation. F53profile records343,705calls to8component schema properties,about1.37s cumulative of7.949s profiled talk;profiling overhead means no inferred unprofiled speed ratio |
| prerequisites/reads | ENGINEERING_RULES,handoff/backlog/Korean progress,AUTONOMOUS_EXECUTION,MASTER3/11,numbered guide,Sol template,WORKSTATION_SETUP,README verification;F53order/profile/owned saves,F54receipt/source hashes;domain encounter/trial/watch records and primitives TypeKey,contracts encounter/trial/watch ComponentKeys,StoredRoot,ObservedReadViewFactory,RegisteredStateIO,Runner,ClientSession/NPC activity callers and current checkout tests |
| MODIFY | C:/Reverie Saga/src/domain/encounter.py;src/domain/trial.py;src/domain/watch.py;src/contracts/encounter.py;src/contracts/trial.py;src/contracts/watch.py;BACKLOG.md;SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md;this order |
| NEW | C:/Reverie Saga/tests/unit/test_static_component_schemas.py;docs/reviews/QT-F55_EXECUTION_2026-10-25.md;owned ignored tmp/qtf55 and .pytest_cache/qtf55-*;temporary clients/unity/Assets/Reverie/Editor/F55VerificationTrigger.cs and its .meta,then remove/restore exact original scene |
| forbidden | All other production/test/contract/CI/governance/dependency/settings/content files,earlier frozen witnesses,user saves/credentials,reference checkout. Preserve all earlier dirty inputs except root progress;no model/engine/helper agents |
| public_contract | Existing constructors,fields,properties,ComponentKey objects and returned TypeKey values remain unchanged. Define validated immutable module constants for encounter.gate/hp/stamina,trial.map/position,watch.npc/lantern/reply,all version1. Records and existing ComponentKey registrations use the same corresponding constant. No new serialized field or identity/hash rule. ComponentKey identity guards remain unchanged |
| behavior/ownership | Construct each TypeKey once at module load through its unchanged strict constructor. Property reads return that immutable static metadata independent of entity/state/epoch. Domain values and all codec/reducer/adapter validation continue on every original path;no cross-root/phase/session authoritative or derived world-state cache |
| edge_policy | Empty/closed/open/dead/charged/negative/out-of-range state behavior is unchanged and remains owned by existing validators. Only fixed valid metadata literals are introduced;invalid kind/version still use original TypeKey errors. Shared metadata is frozen and cannot be mutated by ordinary callers. Different component kinds/versions must never alias;same kind across records/registered keys should share one immutable value |
| independent_examples | GateRecord(...,closed).schema and open gate schema both equal TypeKey('encounter.gate',1);same for all8listed kinds. State fields/canonical serialization differ when state differs;schema identity does not. Existing saves/fixture hashes and memory/work/cycle/aid pins remain byte-identical;retrieval and ordinary talk retain exact committed facts/messages |
| algorithm_steps | Snapshot inputs,qualify new invariants red against baseline;benchmark identical owned source copies before edits. Add8domain constants and route the8properties/ComponentKeys through them. Run affected/static/full checks and paired benchmarks;profile same starting bytes if useful. Inspect actual diff and ordinary registered/native consumers before acceptance |
| performance | Preserve F53representative talk TARGET2s and Unity deadline10s;do not relax either. Measure5unprofiled full act(talk) samples per baseline/optimized phase from identical source bytes,with current-host/version/process caveats. Use retained long old-cycle source and owned long aid source,verify supply/player/call/reward/retry and original bytes independently. Report medians/ranges/reduction and any remaining overrun;target attainment is not inferred from fewer allocations |
| baseline_commands | Installed .venv Python3.13.12/Tk8.6 and existing Unity6000.3.25f1/editor36260reused after actual readiness check;no installs. Current2347distinct Python qualifications and195native checks are historical evidence,not new results. Real Git index retains pre-F54encounter source;three original checkout tests require the already-qualified private-index approach |
| verification_commands | README both Ruff configs,applicable changed-file format plus baseline formatter evidence for legacy files,strict mypy source fallback,both import checks,pip;new static schema tests,affected domain/read-view/serialization/client/replay tests,exact CI31selection and full pytest because shared CORE records change. Keep sys capture/Tcl behavior and permitted hardlink qualification. Full invocation may use owned private GIT_INDEX_FILE/GIT_OBJECT_DIRECTORY containing the current8reviewed source bytes;real index unchanged,no staging/publication |
| test_responsibilities | New unit parameterization independently pins all8kind/version values,distinct record states,shared immutable metadata and registered ComponentKey identity. Existing negative state/codec/read-view lifetime/rollback/retry/replay tests stay unchanged and run in full. Real old-cycle/aid sessions and binary bridge preserve facts/messages/pins/source bytes. Reuse retained editor for fresh aid/old-cycle native verification;no new C#player build needed for unchanged client sources |
| acceptance | Static metadata allocated once and legally shared;all old values/pins/save bytes/projections preserved;required static/affected/full/native checks pass with original failures truthfully retained;paired measurements show actual effect and report2s status. Synchronize order/receipt/root progress;local acceptance only. No whole-game latency,MIN-SPEC,standalone/release or independent review claim |
| checkpoints/stops | No new public simulation/storage/IPC contract;CP01–05bounded closures retained,CP06held,deferred independent patch review remains deferred. Stop/escalate on changed values/pins,error semantics,overlapping edits,new validation/cache authority or unavailable required checks after safe alternatives |
| delivery | English order/receipt/evidence and Korean progress together;preserve earlier F49–54sources/results. Goal remains active for the next authorized bounded task. No commit/push/PR/merge/agent/release |

Required boundary repair discovered after the first full2355PASS1449.97s:the real long
aid bridge talk/query/retry completed,but validating its committed106,496byte SQLite file
raised SAVE_CORRUPT. Original file bytes have a valid header and page-count26at offset31.
On this Windows host,os.open(O_RDONLY)uses text translation:os.read(fd,100)returned31bytes
at0x1A;O_RDONLY|O_BINARY returned exact100bytes,with source bytes unchanged. This is an
existing IO-boundary bug,not corruption or a schema/format change caused by static reuse.

Extend allowed MODIFY to C:/Reverie Saga/src/adapters/sqlite_store.py and NEW to
C:/Reverie Saga/tests/integration/test_sqlite_binary_header.py. Primary6save repair supports
the same2/4/7flow. Preserve classify_file signature,all header/limit/version/page checks,
error codes,os.open/read/close cleanup and the persistence envelope. Add O_BINARY only on
Windows;POSIX flags unchanged. Never retry a bad header as valid or suppress corruption.
Real SQLite databases with ordinary schema-cookie values26/0x0D0A/0x1A000001must validate,
open/reopen the same authoritative checkpoint and preserve bytes. Truncated/wrong headers
still reject SAVE_CORRUPT unchanged. New red/green cases and existing save/recovery/slot/
durable/replay/client guards are required,then a fresh full run because the adapter is shared.
Preserve first full and bridge failure evidence;do not claim that old full qualifies this
subsequent adapter change. Resume the already-committed bridge sources without replaying
talk/actions;qualify their stored results and make new requests only on fresh copies.
