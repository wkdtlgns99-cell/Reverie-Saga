# RS-DOC-005 — Entry Document Compaction

Date:2026-10-16 | State:LOCAL_ACCEPTED | Review:self,not independent.
[Order](../work_orders/RS-DOC-005_ENTRY_COMPACTION.md). Primary7 documentation support across1–7.
Director requests efficient,low-token English organization;no gameplay change.

## Structure

| Document | Responsibility | Reading scope |
|---|---|---|
| BACKLOG | Current statuses,open work,dependencies,checkpoint holds | Task entry/resume |
| SESSION_HANDOFF | Checkout/local work,resume context,lookup routes | Task entry/resume |
| README | Setup,play,verification,index | Relevant section when needed |
| CLI_WORKFLOWS | Optional generation/context/memory developer procedures | Relevant workflow only |
| Dated history snapshots | Complete pre-compaction text,including dirty QT-F21notes | Historical lookup,not automatic session input |

The existing AGENTS/ENGINEERING_RULES/authority files are unchanged. Root filenames and referenced
fragments remain compatible. Maintenance guidance replaces current rows/facts and routes detailed
execution to receipts;completed chronology is not appended to session entry again.

## Size

Measured logical lines(before counts exclude the trailing empty line reported by split-based tools):

| Root document | Before | After |
|---|---:|---:|
| BACKLOG | 668 | 84 |
| SESSION_HANDOFF | 580 | 41 |
| README | 352 | 98 |
| Total | 1600 | 223 |

Combined root UTF8 size falls from152438 to18534 bytes,an87.84%reduction.
This measures document bytes/lines,not model tokens,cache behavior or account usage savings.
The optional CLI guide and historical snapshots remain on disk and outside the routine entry read.

## Preservation and Acceptance

- Each original root was captured with raw SHA256. Only prose Markdown links were rebased in the
  dated snapshots;commands retain repository-root context. Reverse transformation reproduces all
  three original raw byte sequences exactly,including line endings. Old task IDs/states/failures/
  approvals/permissions/negative UX/CI records therefore remain recoverable.
- Current states retain V3deferred/incomplete,CP01–05bounded closures,CP06release hold,GOV-03stale
  inventory/G07inactive,ARCH-002/B09readiness gaps,open D2/D3/D4/D6/D7,artifact-specific rights,
  current-host-only evidence and original save/content pins. Stale pauses/publication claims now
  route to historical snapshots;they grant no new authority.
- All ten original README CLI modules remain documented;actual parser --help checks validate
  documented long flags without running gameplay/generation. Verification invocations are retained
  verbatim;PYTHONPATH is now visible in the verification section for both import checks.
- UTF8,492 local links/fragments(including80 inbound root links),fences,archive recovery,source scope and all
  preexisting QT-F21dirty-file hashes pass. Five existing entry/rulebook tests PASS0.06s.
- No runtime/full/native regression rerun for this documentation-only change. No authority/config/
  test/source/old evidence edits,dependency install,archive deletion,commit/push or agent work.

Raw witness/check scripts/results:tmp/doc005/{entry,verification}.json and helper scripts.
Existing QT-F21receipt/source/Unity README/setup changes remain byte-identical to task entry.
Local Git HEAD remains0e06577. Korean progress companion is updated in the same delivery.
