## CP02 Full-Input Review (English, AI-readable)

### 0. Inputs and limits

yaml
```yaml
review_type: document_consistency_review   # not legal clearance, not import approval
archive: RS-REVIEW-CP02_2026-10-12.zip      # 10 files, all opened
files_opened:
  - BACKLOG.md
  - architecture/V1_REUSE_INVENTORY.md
  - docs/reference/QUILLTALE_CONTENT_CANDIDATES.json
  - docs/reviews/CLAUDE_QUILLTALE_FEEDBACK_2026-10-07.md
  - docs/reviews/RS-REVIEW-CP02_FEEDBACK_2026-10-12.md
  - docs/reviews/RS-REVIEW-CP02_DISPOSITIONS_2026-10-12.md
  - docs/reviews/RS-REVIEW-CP02_INPUTS.json
  - docs/reviews/RS-REVIEW-CP02_REQUEST.md
  - docs/work_orders/QT-F04_PROVENANCE.md
  - docs/work_orders/RS-REVIEW-CP02_REFRESH.md
checks_actually_run_by_me:
  - SHA-256 + byte length of all 9 hashed files vs INPUTS.json: ALL MATCH
  - request file hash vs witness: MATCH (a29287f3...)
  - JSON parse: 6 unique candidate_id, 6 unique source_entry_id, runtime_imported=false, status=CURATED_REFERENCE
  - request dirty-file list vs witness: identical (11 lines)
not_run:
  - any fetch of the pinned GitHub commits/trees/READMEs (Quilltale_practice, Aeesh/Quilltale)
  - the original template files, so no raw/CRLF/LF source-byte rehash
  - tests, replay, lint, legal analysis
```

The zip contains no GAME_SYSTEM_SUMMARY_KO.md or SESSION_HANDOFF.md, which matches the request’s “modified-but-not-reviewed” statement.

### 1. Answers to Q1–Q6

| Q                                                              | Verdict                                          | Basis                                                                                                                                                                                                                                                                                                                |
| -------------------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Origin relationship bounded?                                | **Mostly yes** (one wording issue, W1)           | QT-F04 says README links plus four identical blobs give shared content and a relationship “despite fork=false”. It explicitly denies proof of ownership or copying direction.                                                                                                                                        |
| 2. 4 blobs / 6 candidates / 4 newline witnesses distinguished? | **Yes**                                          | The four shared paths (`src/world/state.py`, `src/llm/base.py`, `assets/styles.css`, `data/worlds/default.json`) differ from all four `data/templates/*.json` files. QT-F04 notes upstream has no `data/templates/`. The six IDs map to four files, and the mapping table in the request matches the JSON (checked). |
| 3. license=null / no-notice bounded?                           | **Yes, with a gap** (G1)                         | Claims are limited to “historical inspected evidence” and filename and GitHub detection are called not exhaustive. The missing evidence list is in section 4.                                                                                                                                                        |
| 4. Raw/normalized SHA and EOL claims                           | **Partly checkable, otherwise UNVERIFIED** (D-1) | See section 2.                                                                                                                                                                                                                                                                                                       |
| 5. Narrative-only boundary held?                               | **Yes**                                          | The JSON policy, inventory table and QT-F04 all agree. `runtime_imported=false`, and no formulas, stats, IDs or schema are carried.                                                                                                                                                                                  |
| 6. D1–D4/M1–M4 and the hash cycle                              | **Dispositions are sound**                       | See section 3.                                                                                                                                                                                                                                                                                                       |

### 2. Q4 detail: what I could and could not check

| Item                                                                                  | Result                                                                                                                                                                                                      |
| ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Facility file: JSON recorded SHA `8a23083d…` vs QT-F04 normalized-LF SHA `8a23083d…`  | **Match.** The dossier EOL is LF, so recorded equals normalized.                                                                                                                                            |
| Settlement (`e84da02a…`), quest (`4bd1ba1e…`) and monster (`0f2e64f3…`) recorded SHAs | **Not checkable from supplied data.** These are raw CRLF hashes. QT-F04 prints only the normalized-LF hashes (`594ae8b9…`, `bc8d1810…`, `0eed1454…`), never the reconstructed CRLF hash to put beside them. |
| “Initial raw comparison found 3 of 4 different”                                       | **Internally consistent.** Dossier vs current EOL differs for facility (LF→CRLF), quest (CRLF→LF) and monster (CRLF→LF); settlement is CRLF/CRLF.                                                           |
| “Reconciles ALL recorded hashes”                                                      | **Unsupported by supplied evidence** for three of four files (D-1).                                                                                                                                         |
| Blob SHA-1s, tree SHA-1s, commit IDs, entry counts (299/35)                           | **UNVERIFIED.** They are immutable-looking pins but I did not fetch them.                                                                                                                                   |

### 3. Findings

#### 3.1 Confirmed defects / documentation issues

| ID  | Location                                                      | Issue                                                                                                                                                               | Bounded repair                                                                                                                                                    | Acceptance check                                                                                                |
| --- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| D-1 | QT-F04 “Byte witness” table                                   | The reconciliation claim can’t be re-derived. The table has no column for the recorded dossier SHA or the raw-at-commit SHA.                                        | Add columns: recorded SHA (from the JSON), raw SHA at the introducing commit, EOL, normalized-LF SHA, and the transform used. Do not change any historical value. | For each file, `recorded == sha256(raw_at_commit)` or `recorded == sha256(crlf(normalized))`, shown explicitly. |
| W1  | QT-F04 “Origin-chain evidence”; request “Source Relationship” | “Origin relationship” and “shared-content/origin evidence” can read as a direction claim, while the same text denies direction.                                     | Use “shared-content and linkage evidence; direction unestablished” in both places.                                                                                | grep shows no unqualified “origin” in claims about the four blobs.                                              |
| G1  | V1_REUSE_INVENTORY.md “Visual files” row                      | It says Map JPG/icon/CSS “not copied; rights checked before import” but never notes that `assets/styles.css` is byte-identical to the Aeesh upstream blob.          | Add a cross-reference to QT-F04’s shared-blob table.                                                                                                              | The inventory row names styles.css and links to the table.                                                      |
| G2  | BACKLOG line 82                                               | `RS-CONTENT-001` is `DONE` while its target is rights-unverified. It is consistent with line 66 and `CURATED_REFERENCE`, but a skimmer could read DONE as “usable”. | Append “curation only; rights UNVERIFIED (QT-F04)”.                                                                                                               | The row text carries the qualifier.                                                                             |
| G3  | INPUTS.json                                                   | The witness is hashed by no file and no external anchor. Tampering or drift in the witness can’t be detected.                                                       | Record the witness SHA-256 in the director’s delivery message or a log outside the hashed set.                                                                    | The out-of-band hash equals `sha256(INPUTS.json)`.                                                              |

#### 3.2 Intentional policy (do not change)

- The hash-cycle design is valid: BACKLOG links the witness, the request hashes BACKLOG, and the witness hashes the request. A request hash inside BACKLOG would create a cycle.
- Hashes prove byte identity only, and the context-only roles are labeled correctly.
- Manual director handoff, no automatic provider calls, and no import while rights are unresolved.
- CP01 DONE and separate from CP02.
- Dated historical statements in QT-F04 (CP01 pending, HEAD b0f98e2) are retained and flagged historical.

#### 3.3 False positives to avoid

- `fork=false`, public visibility and `license=null` are not evidence of ownership or permission.
- Git author identity and the introduction commits are not copyright proof.
- The JSON `source_commit` `9f2ec20a` differs from practice HEAD `3c50c34f`. This is **not** a defect: `9f2ec20a` is the parent of `3c50c34f`, and QT-F04 states the four template blobs are unchanged.
- `source_repository: "C:/Quilltale"` is the local directory name, not a different repository from Quilltale_practice.

#### 3.4 Unresolved rights (no review can close these)

yaml
```yaml
per_candidate_missing_evidence:   # applies to all six, intended use = Reverie Saga
  - author or generator of the source text (self-written / AI-generated with inputs / external)
  - for AI-generated: tool, prompts, service terms
  - for external: owner, license or written grant covering Reverie Saga, attribution terms
  - for the adapted text in description_ko: confirmation that adaptation is allowed, because derivative rights depend on source rights
four_shared_blobs:
  - Aeesh upstream license/grant, or owner confirmation; relevant to styles.css if it is ever adopted
not_substitutes: [AI review, public visibility, absence of notice, Git identity]
```

QT-F04 itself says the director was asked whether the six descriptions are self-authored, AI-generated or external. No answer appears in any supplied file, so that question is still open.

### 4. Scope correction on my earlier message

My earlier section 2.5 wrote “reuse in Quilltale”. The target is **Reverie Saga**, and the dispositions file correctly fixed this. Permission evidence must cover use in Reverie Saga.

### 5. Recommended next steps

1. Apply D-1, W1, G1 and G2 as document-only repairs. Do not touch the historical hashes or the candidate JSON.
2. Re-hash edited files, then refresh the witness and request. Any edit to BACKLOG changes the request hash, so keep the existing order: BACKLOG first, then request, then witness.
3. Record the final witness SHA outside the hashed set (G3).
4. Get candidate-specific authorship and permission evidence from the director (section 3.4). Nothing is imported until then.
5. Optionally, fetch the four pinned GitHub refs to confirm the blob and tree claims independently. Until then, those claims stay UNVERIFIED. I can run that check if you want.

### 6. Status line for BACKLOG

`CP02: full-input document review RECEIVED (document-only; pinned GitHub sources and original bytes not rechecked). Packet/hash integrity PASS. Findings: D-1, W1, G1–G3 (docs only). Rights UNVERIFIED; no imports; CP02 not DONE until repairs and dispositions are accepted.`
