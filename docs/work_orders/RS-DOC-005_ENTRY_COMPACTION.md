# RS-DOC-005 — Compact Session Entry Documents

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/review:self;no agents.
Authorization:director requests low-token,AI-readable English organization of backlog,handoff,README.
Primary7documentation support across1–7;no gameplay implementation.

| Field | Contract |
|---|---|
| goal | BACKLOG=current status/dependencies;HANDOFF=resume context;README=setup/play/verification. Move detailed history and optional CLI workflows behind explicit links |
| baseline | HEAD0e06577,existing QT-F21dirty work preserved. Capture exact entry bytes/hashes and nonignored file hashes before mutation |
| reads | ENGINEERING_RULES,AGENTS,three entry docs,Korean companion,AI Documentation Format/companion rules,numbered guide,prior QT-F03compaction,actual CI commands and inbound anchors |
| allowed | MODIFY C:/ReverieSaga/BACKLOG.md,SESSION_HANDOFF.md,README.md,GAME_SYSTEM_SUMMARY_KO.md. NEW docs/history/BACKLOG_2026-10-16.md,SESSION_HANDOFF_2026-10-16.md,README_2026-10-16.md;docs/CLI_WORKFLOWS.md;this order;docs/reviews/RS-DOC-005_EXECUTION_2026-10-16.md. All relative NEW paths resolve under C:/ReverieSaga. Owned tmp/doc005only |
| forbidden | Runtime/tests/config/locks/AGENTS/ENGINEERING_RULES/authority files/existing evidence and user edits. No commit/push/deletion |
| prerequisites/tools | Existing Python3.13.12/PowerShell/Git for document checks;no installs/native engine needed |
| contracts/wiring | Preserve root filenames,verification commands,referenced fragments,all task IDs/history,actual current states,dependencies/holds/rights and source evidence. Archive rebases prose links only;reverse transform must recover original raw bytes. CLI guide retains supported command examples,credential/privacy,approval/source-freshness and save-pin semantics |
| edge/error policy | No silent supersession:resolve stale records against latest accepted receipts and retain historical originals. Completed IDs may move to archive;open task IDs/gates stay in active backlog. Missing link/fragment,unexplained file mutation or unrecoverable snapshot blocks acceptance |
| examples | Old pause/publication/completion log→historical snapshot;current QT-F21→one row/receipt. CP01–05closed,CP06held,V3incomplete,GOV-03stale inventory preserved. README#verification remains runnable;old first-quest fragment routes to the CLI guide |
| steps | Snapshot/rebase and verify exact recovery;write compact roots/CLI guide;update companion;check links/fragments/fences/commands/status/scope and measure size |
| performance | TARGET backlog<=130lines,handoff<=65lines,README<=120lines;combined UTF8bytes reduction>=65%. Byte/line measurements only;no tokenizer or billing-savings claim |
| checks | Strict UTF8,Markdown link/fragment/fence checks,inbound anchors,archive byte recovery,old/new CLI module inventory and exact CI command retention,entry-vs-final hashes,git diff --check. Existing relevant document guards only;runtime/full/native NOT_RUN |
| acceptance | Targets pass;every old record recoverable;active statuses/gates and three progress docs agree;only allowed docs differ from entry;prior QT-F21work byte-identical |
| checkpoints | NOT_TRIGGERED:documentation routing only;V3review remains deferred/incomplete,CP06release held. No governance/contract/checkpoint change |
| delivery | Local accepted docs,measured before/after,actual verification/limits;no automatic next task/publication |

Accepted:[execution receipt](../reviews/RS-DOC-005_EXECUTION_2026-10-16.md). Three roots1600→223lines,
UTF8bytes−87.84%;exact history recovery,links/commands/prior-work preservation and5entry guards PASS.
