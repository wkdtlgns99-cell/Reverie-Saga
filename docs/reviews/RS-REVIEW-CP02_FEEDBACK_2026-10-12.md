## CP02 Review: Evaluation of RS-REVIEW-CP02_REQUEST and Next-Step Plan

### 0. Scope and evidence status

yaml
```yaml
review_type: document_review_only   # no tests, replay, or native checks were run
not_legal_clearance: true
not_import_approval: true
inputs_actually_seen:
  - RS-REVIEW-CP02_REQUEST.md (full text, pasted)
  - github.com/wkdtlgns99-cell/Reverie-Saga (repo landing page only)
inputs_NOT_seen:
  - docs/work_orders/QT-F04_PROVENANCE.md
  - docs/reference/QUILLTALE_CONTENT_CANDIDATES.json
  - architecture/V1_REUSE_INVENTORY.md
  - BACKLOG.md (contents)
  - docs/reviews/CLAUDE_QUILLTALE_FEEDBACK_2026-10-07.md
  - local uncommitted files
  - the immutable GitHub v1 "Reverie" source links (not in the pasted text)
verified_from_repo_page:
  visibility: public
  fork: false          # does not prove original authorship
  commits_on_main: 5
  license_file_visible_on_landing: false
  description_or_topics: none
  top_level: [architecture, docs, src, tests, .gitignore, .importlinter-runtime.toml, BACKLOG.md, GAME_SYSTEM_SUMMARY_KO.md, REFERENCE_REPOSITORY.txt, SESSION_HANDOFF.md, pyproject.toml, requirements-dev.lock]
unverifiable_now:
  - HEAD b0f98e2aa19c5db11d0c746226d4bf321b34dee8   # not shown on the page
  - all five SHA-256 values in the packet table
  - whether pushed main equals local working tree
```

Every conclusion about QT-F04 content, the six candidates, blob matching and the v1 inventory is **UNVERIFIED**. This is the same rule the packet sets for itself.

### 1. Verdict on the packet

| Aspect                                                                       | Rating       | Note                                                                                     |
| ---------------------------------------------------------------------------- | ------------ | ---------------------------------------------------------------------------------------- |
| Structure and handoff safety (no `.env`, keys, or logs; manual paste-back)   | Good         | Intentional policy.                                                                      |
| Honesty of status fields (`NOT_RECEIVED`, `UNVERIFIED`, “no review claimed”) | Good         | No fabricated results.                                                                   |
| Reviewability of the six questions                                           | Good         | Q1–Q6 are bounded and separate evidence from rights.                                     |
| Freshness                                                                    | **Stale**    | Dated 2026-10-07; today is 2026-10-12. The packet itself says the hashes are historical. |
| Internal consistency                                                         | Minor issues | See section 2.                                                                           |

**Overall:** the packet is sound but not forwardable yet. Hash and HEAD refresh is a hard gate.

### 2. Findings

#### 2.1 Confirmed defects (visible in the pasted text)

| ID | Location                      | Issue                                                                                                                                                            | Bounded repair                                                                 |
| -- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| D1 | “Reviewed input snapshot”     | HEAD and all five hashes are explicitly stale after the scheduling edit.                                                                                         | Recompute them (section 4) and rewrite the table.                              |
| D2 | Hash table vs “Minimum files” | The feedback file is hashed as a reviewed input, but the text calls it “historical context, not current evidence”. A hashed input implies evidentiary status.    | Mark that row `context-only` in a role column.                                 |
| D3 | Hash table vs header          | The delivery also modified SESSION_HANDOFF, the Korean companion and the roadmap, but they are not hashed. They are non-evidence, but the packet doesn’t say so. | Add one line: “modified but not reviewed inputs: …”.                           |
| D4 | Snapshot paragraph            | The request file is excluded from its own hash table. This is correct (avoids circularity), but there is no external witness for it.                             | Record the final request hash in the BACKLOG CP02 entry after it is finalized. |

#### 2.2 Documentation issues (clarity, not correctness)

| ID | Issue                                                                                                                                                                                                                                                    |
| -- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M1 | Q2 says “four matching initial upstream blobs”, but the scope is “six candidates”. The packet never says which four of the six match or what the other two are. A cold reviewer can’t map 4→6 without opening the QT-F04 report. Add a one-line mapping. |
| M2 | “Immutable primary GitHub sources” are referenced, but no URLs or commit SHAs appear in the packet. Put at least the pinned refs in the packet or point to the exact QT-F04 section.                                                                     |
| M3 | Q1 refers to “the stated source relationship” without stating it. Add one neutral sentence of what QT-F04 claims.                                                                                                                                        |
| M4 | “Expected reviewed inputs are the current uncommitted project files, not older GitHub Reverie code.” The public repo (5 commits) is not the reviewed target. Say explicitly that the pushed main may differ and that the hashes are the authority.       |

#### 2.3 Intentional policy (do not “fix”)

- The delay is a one-time director-approved deferral, and it is not a waiver or DONE.
- Claude’s answer is pasted back unchanged, with no API automation.
- No engine, formula, schema, oracle, or whole-template port.
- Unresolved rights hold all new v1 reuse regardless of the review outcome.
- CP01 (core/client) is out of scope for CP02.

#### 2.4 False-positive risks for the reviewer

- `fork=false` and `public` on this repo are consistent with `license=null`. Neither is evidence of permission or authorship.
- A visible 5-commit history does not show that the six candidates are original or upstream-owned.

#### 2.5 Unresolved rights (cannot be closed by any review)

yaml
```yaml
needed_to_clear_reuse:
  - verifiable owner/author identity for each of the six source narratives
  - explicit written permission or license from that owner (scope: reuse in Quilltale)
  - for the 4 upstream-matching blobs: the upstream license/notice, or confirmation none exists
  - for the later templates: authorship evidence, since "unknown" must not default to "ours"
not_acceptable_as_substitute:
  - AI review output
  - public repo visibility
  - absence of a notice (license=null)
```

### 3. The six questions: current answer status

| Q | Topic                                                       | Status               | Reason                                                                                    |
| - | ----------------------------------------------------------- | -------------------- | ----------------------------------------------------------------------------------------- |
| 1 | Source relationship vs `fork=false`                         | UNVERIFIED           | QT-F04 not seen. The framing is correct.                                                  |
| 2 | 4 initial upstream blobs vs later templates                 | UNVERIFIED           | Mapping (M1) is missing.                                                                  |
| 3 | license=null and missing-permission bounds                  | Partially assessable | The required evidence list is in 2.5. The accuracy of the report’s wording is unverified. |
| 4 | Raw vs normalized SHA/EOL, immutable refs                   | UNVERIFIED           | Needs the JSON and the report.                                                            |
| 5 | No-engine/formula/schema boundary; `runtime_imported=false` | UNVERIFIED           | The packet states it, but the JSON field was not inspected.                               |
| 6 | Defect list                                                 | Packet-level only    | See section 2.                                                                            |

### 4. Recommended work sequence (revised)

**Step 1: Refresh the packet (do this first)**

powershell
```powershell
cd C:\ReverieSaga
git rev-parse HEAD
git status --porcelain
Get-FileHash -Algorithm SHA256 BACKLOG.md, `
  docs\work_orders\QT-F04_PROVENANCE.md, `
  docs\reference\QUILLTALE_CONTENT_CANDIDATES.json, `
  architecture\V1_REUSE_INVENTORY.md, `
  docs\reviews\CLAUDE_QUILLTALE_FEEDBACK_2026-10-07.md
```

Acceptance criteria (independently checkable):

- Packet HEAD equals `git rev-parse HEAD`.
- The dirty-file list in the packet equals the `git status --porcelain` output.
- Each table hash equals `Get-FileHash` output.
- D2–D4 and M1–M4 are resolved or explicitly waived.
- The BACKLOG CP02 entry records the new request hash and the date.

**Step 2: Submit to Claude and verify its answer**

- Paste the answer back unchanged.
- For each claim, record: source, affected-file snapshot, disposition (confirmed / documentation / policy / false positive / unresolved rights).
- Documentation repairs need document checks. A CORE change needs regression, replay, and native checks.

**Step 3: QT-F04 rights**

- The investigation is already recorded, so what remains is **obtaining owner/permission evidence**, not further analysis.
- Nothing is imported until section 2.5 is satisfied.
- Keep `runtime_imported=false` throughout.

### 5. Notes on your own next-step text

- Item 3 reads as if QT-F04 is still to be done. The packet says the investigation is recorded and only rights evidence is missing. Rephrase it as “obtain permission evidence”.
- The order 1 → 2 → 3 is fine. Step 3 is independent of the Claude review and does not unblock on it.

I can also open `docs/work_orders/QT-F04_PROVENANCE.md` and the candidates JSON on GitHub to check what the pushed state shows. They would reflect pushed main only, not your uncommitted files, so any result would be provisional against your hashes.
