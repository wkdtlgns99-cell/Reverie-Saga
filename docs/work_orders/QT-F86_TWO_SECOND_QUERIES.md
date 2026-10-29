# QT-F86 — Bring the four measured long queries below two seconds

Status:LOCAL_ACCEPTED2026-10-29,self-review;[receipt](../reviews/QT-F86_EXECUTION_2026-10-29.md).
Explicit human acceptance:all four remaining long direct/framed
talk/activity cases <2seconds,verify then execute exactly one further bounded task.
Executor:local Codex,self-review;primary2performance support,related4/5/6/7.

| Field | Contract |
|---|---|
| goal/non_goals | Make all current representative12query samples <2swithout changing output/state/hash/errors/ownership. No history truncation,domain-state cache,validation bypass,format/pin/schema/default/dependency/native/publication change |
| baseline | main5fa348b plus28accepted dirty paths,F84/F85. Preserved current src under tmp/qtf86/baseline/src and entry.json. Profile current132step source12.282s(with profiler):validate_checkpoint5.174s,encode_core4.050s,component fields3.562s,canonical conversion5.201s. F84paired worst3.726747s |
| prerequisites/reads | ENGINEERING_RULES,HANDOFF,BACKLOG,Korean progress,MASTER performance/authority,numbered guide,Sol template,WORKSTATION_SETUP;F84/F85orders/receipts;canonical conversion,RegisteredStateIO,Runner,ObservedReadViewFactory/AdapterBinding/contracts and exact codec/read-view/replay tests |
| allowed_edit_paths | MODIFY C:/ReverieSaga/src/domain/canonical.py;src/domain/primitives.py;src/orchestration/serialization.py;src/orchestration/replay.py;src/orchestration/turn.py;src/contracts/state_io.py;src/app/headless.py;src/app/npc_activity.py;src/orchestration/read_views.py only if actual profile justifies static registration metadata reuse. BACKLOG.md;SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md;README.md;docs/DEFERRED_USER_DECISIONS.md. NEW tests/unit/test_owned_canonical.py;tests/unit/test_submit_documents.py;tests/unit/test_replay_conversion.py;tests/unit/test_static_read_registration.py;docs/work_orders/QT-F86_TWO_SECOND_QUERIES.md;docs/reviews/QT-F86_EXECUTION_2026-10-29.md. Owned tmp/qtf86/.pytest_cache/f86-* |
| forbidden_paths | Engine/contracts/old tests/goldens/checkers/content/settings/policy/CI/scene/native/user/reference paths. Preserve existing28paths/index. No agents/dependency/security/native/commit/push/goal change |
| public_contract | Existing public signatures/bytes/hashes/error codes+paths/read lifetime/validation remain. Reuse newly computed documents only inside one conversion/replay operation;never cross-call cached domain results. Only validated static registration metadata may persist in an IO instance |
| algorithm | Profile/factor responsibility:static schema-to-registration routing with fresh record validation;avoid duplicate encoding/parsing of freshly validated same-operation documents;use canonical-byte equality for the successful replay path and retain exact detailed mismatch fallback. Canonical builtin-kind dispatch may reduce ABC overhead while preserving subclass/Unicode/depth/ownership checks. No guessed fast path for arbitrary external MappingProxyType |
| ownership/order | Fresh read roots/views per operation and canonical immutable DTO ownership remain. Existing full registry validation happens before metadata reuse. Every stored source/command/witness/receipt still verified;COMMIT-only state and truthful recovery unchanged. No new writer/subscriber/event/action |
| edge_policy | Preserve exact bool/int/subclass/Unicode/depth/container checks,mutable/externally backed input isolation,codec second-encode coercion rejection,registration duplicates and absent adapters,unknown IDs/unsupported schemas,protocol order/cap/fingerprint/head checks. Replay mismatch first path/value/order remains identical,including noncanonical whitespace witnesses and bool/int distinctions |
| examples | Same tick132/132step source yields exact output/core/protocol/SQL dump and no source mutation. Original expected true vs actual1 is mismatch. Identical valid witness bytes pass;changed witness or hash still reports original detailed location. Same schema with invalid later record must reject after valid earlier record |
| steps/wiring | Freeze baseline/profile;independent new semantic tests before optimization;measure each bounded change on the same saved source. Then complete before/current direct/framed12sample parity,repeat each slow case three times <2s,static/CI/full frozen suite/source checks;only then next bounded task |
| performance | Hard acceptance for this current-host sample:all12short/long direct/framed talk/activity/slot<2s,and3repetitions of each slow case<2s. Same retained histories/commands,all samples retained. No global4096step/device/MIN-SPECclaim. If any miss persists,continue diagnosis rather than relabel acceptance |
| baseline_commands | Existing preserved matrix/bench from F84adapted to frozen/current F86sources;new semantics pass baseline (optimization changes no behavior). Keep unprofiled timings separate from cProfile overhead |
| verification_commands | New+canonical/codec/protocol/metadata/read-view/replay/durable/query affected tests,old13mode output/pin/core/protocol/SQL parity;Ruffboth/strict/import3+1/pip/scopedformat/currentCI31/docs10/UTF8/links/scope. Fresh full required after shared source freeze;proper PYTHONPATH=src and permitted local-server/hardlink execution |
| test_responsibilities | New unit files assert actual registered source/range/ownership/lifetime and independent replay mismatch vectors,not implementation call counts. Existing old tests/goldens unchanged. Owned actual direct/framed probe asserts output/state/raw-source/retry and timing;no mocked domain outcomes |
| acceptance | Every designated sample<2s,semantic parity and all required tests pass;root trio synchronized. Native/independent/CP06/release/device holds remain;self-review only |
| claude_checkpoints | Internal optimization under existing contracts,not new engine/format/owner/pipeline,so no new CP01–05trigger. Preserve independent patch review and CP06holds;full regression required |
| stop/delivery | Preserve all prior/user work;escalate only real overlap/new authority/semantic divergence/unavailable verification after safe alternatives. No2swaiver. English receipt/Korean result,then exactly one useful next task;no publication/agents/automatic general loop |


Measured scope refinement:explicit owned canonical document composition retains exact
depth and rejects unlisted proof objects. Internal optional checkpoint-encoding service
returns fresh documents from the existing actual commit operation. Existing StateIO and
TurnDriver interfaces/serialized contracts unchanged;normal submit uses the same checked
staging/COMMIT/presentation pipeline. Replay can consume returned documents only for the
same IO owner and committed head;rejections/retries/abort/foreign IO use ordinary encoding.
Activity replay shares static IO registration within one query;no domain result survives
across commands/queries. New DTOs are process-local conversion values,not persisted schema.
