# QT-F22 — Read-only Saved Branch Inventory

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/review:self.
Authorization:director requests next work after R1 and stops the current partial Claude review.
Primary6 storage support;related7. Bounded save usability follow-up;no release acceptance.

| Field | Contract |
|---|---|
| goal/non-goals | Explicit CLI lists retained .loaded working saves with logical tick/revision and current-path marker. Detect invalid/incompatible candidates without hiding healthy ones. No deletion,orphan/ownership inference,load/attach/game creation,limit/schema/CORE/wire/UI change |
| baseline/prerequisites | HEAD0e06577 plus preserved F21/RS-DOC-005 and R1 work. Existing CORE-05 retention/8-clone contract remains;read actual stage_load,cleanup_owned_clone,safe_path,validate_save,state_io,watch/quest/memory bundle wiring,scenario selectors,README/setup and three progress docs |
| allowed | NEW src/app/save_inventory.py,tests/integration/test_save_inventory.py,this order,docs/reviews/QT-F22_EXECUTION_2026-10-16.md. MODIFY docs/CLI_WORKFLOWS.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md. Owned tmp/qt-f22,.pytest_cache/qt-f22-* |
| forbidden | Existing runtime/contracts/adapters/domain/engines/orchestration/Unity/content/pins/dependencies/config/CI,all prior archives/private saves. No cleanup or authoritative gameplay semantics |
| public API | inspect_clones(working:Path,*,io:StateIO)->JsonObject;main(argv:Sequence[str]\|None=None)->int. CLI --working required;--scenario legacy/harbor/grove defaults legacy;optional paired --quest-catalog/--quest-sha256;--npc-memory requires quest pair. Quest mode rejects nonlegacy scenario selector rather than silently ignoring it |
| format | reverie-save-clone-inventory/v1,status READ_ONLY_SNAPSHOT,current={filename,tick,revision,branch_id};clones sorted filename with filename,is_current,status,tick,revision,branch_id. Invalid candidate has exact SaveError.code and null metadata. Candidate names are not deletion permission;is_current means only supplied path identity,not global liveness |
| algorithm/ownership | Validate current existing working save via safe_path+validate_save. Scan only its parent,match exact .loaded-[0-9a-f]{32}.sqlite names;never recurse/open other files or lock sidecars. At most64candidate names;excess→SAVE_LIMIT,no partial JSON. Validate each with the caller-selected original bundles;SaveError becomes row,OS scan failure→SAVE_INVENTORY_UNAVAILABLE. CLI sanitizes ordinary input/IO errors;unexpected programming failures and process-control propagate |
| edges/examples | No clones→empty list;current loaded clone→is_current true;older retained clone→its own saved tick/revision,never current stats. Corrupt,missing-raced,symlink,reparse,directory/hardlink or wrong-pin candidate→diagnostic row,no creation/repair. Invalid current→SaveError,no listing. Slot files,sidecars,uppercase/malformed lookalikes ignored. Ordering lexicographic;no implied chronological/causal relation |
| consistency/performance | Each file is an independent read-only SQLite snapshot,not one atomic directory snapshot or promise of later resumability. No cache/index/provider/ownership lock;no persistent writes. At most65validations,64rows. Existing compatible saves only;never auto-detect or repin content/feature pins |
| tests | Real retained loads across sessions and 8-clone refusal unchanged;current marker and resumable progress;legacy/scenario/quest/memory modes;empty/malformed/corrupt/incompatible/alias/race/over-cap;source+sidecar/tree bytes unchanged;standalone CLI output/errors/mode validation,process-control propagation |
| checks/acceptance | Targeted inventory/save-slot/durable regressions;README Ruff both,format changed files+canonical scope,mypy,pip/import3+1;docs link/UTF8/diff/protected-file checks. Correct data/no source changes/no outputs on current-input failure;progress docs agree. No CORE edit:full/native NOT_REQUIRED unless affected failures warrant |
| checkpoints/stops/delivery | CP01–05 closed for original scopes;V3 stopped PARTIAL by director,CP06 held. No new checkpoint from a read-only developer command. No independent/native/release acceptance inferred;no commit/push/agent/provider calls. Stop for unsettled save/ownership semantics rather than invent cleanup |

Accepted:[execution](../reviews/QT-F22_EXECUTION_2026-10-16.md). Combined225affected tests,
static/scope/doc checks PASS;real retained branches remain resumable and eight-clone cap unchanged.
