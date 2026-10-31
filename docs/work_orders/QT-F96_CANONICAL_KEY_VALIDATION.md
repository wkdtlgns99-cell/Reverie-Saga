# QT-F96 — Reduce recursive canonical object-key dispatch

LOCAL_ACCEPTED2026-11-01after READY execution;local assistant executor,self-review,
not independent review. Full3713PASS894.34s after process-local Git context repair.
Publication pending;[receipt](../reviews/QT-F96_EXECUTION_2026-11-01.md).
Primary2internal calculation performance support;related5inspection,6save,7village flow.

| Field | Contract |
|---|---|
| goal/non_goals | Reduce fresh canonical object-key validation overhead measured in retained NPC replay. Preserve all values,bytes,hashes,errors,ownership and depth limits. No new gameplay,public/save contract,cache,skipped replay,trace truncation,dependency or native change |
| baseline | Clean main5005ee6bcdb8337135dcd1570c1b9bef334f68b6 equals freshly fetched origin/main,0ahead/behind. F95PR28merged;both required full3703/boundary31PASS. Goal ACTIVE/ordinary usage allowed. F95new memory contract remains pending actual director reply;this private optimization is independent |
| prerequisites/read_files | ENGINEERING_RULES,HANDOFF,BACKLOG,Korean companion,MASTER,AUTONOMOUS_EXECUTION,numbered guide,Sol template,WORKSTATION_SETUP,READMEverification;F84protocol conversion order/receipt;domain/canonical.py _convert/seal/canonical_json/CanonicalDocument;serialization protocol/command/core conversion;replay Runner/turn commit;canonical/owned/protocol/replay/query tests |
| allowed_edit_paths | MODIFY C:/Reverie Saga/src/domain/canonical.py;C:/Reverie Saga/BACKLOG.md;C:/Reverie Saga/SESSION_HANDOFF.md;C:/Reverie Saga/GAME_SYSTEM_SUMMARY_KO.md;C:/Reverie Saga/docs/WORKSTATION_SETUP.md(current-host Git verification context only). NEW C:/Reverie Saga/tests/unit/test_canonical_keys.py;C:/Reverie Saga/docs/work_orders/QT-F96_CANONICAL_KEY_VALIDATION.md;C:/Reverie Saga/docs/reviews/QT-F96_EXECUTION_2026-11-01.md. Owned tmp/qtf96 and .pytest_cache/f96-* |
| forbidden_paths | Other production,old tests,goldens,content,CI/configuration/dependencies,reference/private saves/native/scene,review/approval ledgers. No F95runtime component/flag/pin/migration implementation |
| public_contract | Existing seal(value:object,depth:int=0)->JsonValue,canonical_json(value:JsonValue)->bytes,CanonicalDocument construction/selection/value/depth/bytes and every caller unchanged. Private text-validation helper may be factored;no exported new contract |
| behavior | Validate strings through a shared private helper. Exact built-in ASCII str is already NFC and strictly UTF8-encodable;use the built-in isascii proof only after type(value)isstr. All other strings,including subclasses,use existing NFC then strict UTF8 in original order. For mapping keys retain isinstance(str) rejection first,then depth+1>32,then the same text proof/validation before child traversal. Avoid full generic recursive dispatch for known string keys. The child at the same depth records key/value height,including empty-container leaves;owned-child depth accounting remains exact |
| edge_policy | None/bool/exact-int/str-subclass/list/tuple/Mapping/proxy behavior unchanged. Preserve key-type before key-depth before NFC/UTF8 before child error order. Empty map at32valid,nonempty at32invalid,string-key leaf at31valid. Invalid/surrogate/decomposed keys never bypass checks or mutate caller data. No trusted external proxy,static/dynamic value cache or cross-call validation reuse |
| examples | Nested32empty map accepted;Nested32{1:0}->JSON object keys must be strings;Nested32map with decomposed e+U+0301key->JSON nesting exceeds32;Nested31map with that decomposed key->non-NFC string;Nested31{"x":0}accepted. A valid canonical key can compose through an owned child without changing exact32boundary. Original literal/reference vector bytes remain exact |
| algorithm_steps | Preserve original src/test/content/config hashes and source copy;add contract-derived boundary/ownership/key-callback ordering tests and pass on original implementation;factor private string validation and replace only mapping-key generic recursion;run semantic/static/full qualification and isolated paired actual callers;self-review/root updates/publication/main sync |
| wiring | Existing canonical conversion ->RegisteredStateIO->Driver COMMIT/Runner->ClientSession talk/activity/slot->direct worker/Tk/framed. No new registration/caller/IO;qualify registered paths and all old modes using existing integration probes/tests |
| performance | Actual dense132receipts activity3samples1.710367/1.763678/1.775400s;dense264receipts5.289223/4.912780/4.741390s,source/state preserved. Dense264diagnostic profile12.984s includes overhead:generic conversion2.498million calls/3.584s cumulative. Private-copy feasibility paired10x20 real protocol documents:canonical median4.104->3.439ms,sealing3.398->2.673ms;NOT product speedup. Require lower median fresh paired actual long queries with exact outputs;retain2sTARGET misses/10sdeadline and current-host-only limits |
| baseline_commands | tmp/qtf96/preflight.py,dense_more.py,key_probe.py terminal0. Source132retained unchanged while building264copy. Before edits new canonical-key tests plus existing canonical/owned/protocol suites must pass;performance optimization has no intended functional red case |
| verification_commands | README Ruffdefault+quality,format existing scope plus changed files,strict mypy,imports3+1,pip;new and existing canonical/serialization/protocol/replay/actual query tests;CI31/docs10;full pytest for shared domain change using canonical capture=sys/default flags. Use owned basetemp paths,run heavy jobs sequentially,retain source/hash/byte parity and real retry/read-only/error results |
| test_responsibilities | NEW tests/unit/test_canonical_keys.py covers independent key/type/depth/Unicode/owned composition/callback ordering/alias preservation across public entry points,all128ASCIIcodepoints and hostile str-subclass isascii override. Existing tests unchanged qualify literal hashes,replay/durability/error boundaries/worker/Tk/framed. Owned probes compare baseline/current all modes and short/dense actual direct/framed complete updates,CORE/protocol/SQL/source/retry and timings |
| acceptance | Original/new semantic expectations pass,all required static/full checks pass,exact prior outputs/pins/state/protocol/SQL/source unchanged,measured actual long median improves without semantic bypass,root trio records F95publication/pending authority and F96truthful evidence;ordinary PR/main synchronization complete. Remaining target misses must remain explicit |
| claude_checkpoints | NOT_APPLICABLE:new private dispatch under existing canonical contract,no new subsystem/schema/format/owner/CP01-05trigger. Full shared-domain regression required;independent/native/device/CP06/release holds remain. No new/reopened/waived gate |
| stop_conditions/delivery | Stop on semantic/error/ownership divergence,user overlap,unproven performance or unavailable required evidence after safe alternatives. Do not adopt a slower speculative optimization. User automatic goal plus standing2026-10-30delivery authority permits scoped branch/commit/push/PR/requiredCI/ordinary merge/localmain sync. F95approval remains separate;continuation requested,never mark the whole goal complete for this one task |

Actual quota recovery2026-11-01:reported reset follow-up delivered,ordinary usage allowed;
native goal still usageLimited,not ACTIVE. No supported goal-resume tool was found.
Continue the explicitly authorized F96repair/delivery in this same reset-triggered chat.
Original full6FAIL/76ERRORare Git ownership/provenance failures,not domain outcomes.
Nested Git commands require the same exact repository trust used by direct commands:
append safe.directory=C:/Reverie Saga through this verification subprocess tree's
GIT_CONFIG_COUNT/KEY_n/VALUE_n only,preserving existing entries. No global/repo config,
wildcard trust,checker/test change or protection weakening. Both representative unchanged
cases PASS34.61s;rerun the failed full command with identical301inputs and fresh owned
basetemp/logs. This is environment repair of required verification,not a new contract.
Before editing it,the scope now includes the canonical workstation setup's current-host
note so later verification retains this demonstrated prerequisite. This is documentation
of the same repaired Git context,not an installation,global setting or other-device claim.

Pre-acceptance refinement2026-11-01:the first helper/key dispatch candidate preserved
all14mode pairs and6valid direct pairs,with direct medians2.7–3.7percent lower.
The original framed harness forced its inner engine to current src regardless of the
outer baseline selection;its before/current timing claims in matrix2/3are INVALID,
neither regressions nor improvements. Retain those artifacts as harness failure evidence.
The corrected matrix4launcher asserts the actual bridge/canonical module paths and hashes
inside each engine before real framed requests. Reuse only unchanged valid direct evidence.
Before the second edit,the exact built-in ASCII proof above was frozen and received
independent baseline vectors. No public/save behavior or authority changes.
