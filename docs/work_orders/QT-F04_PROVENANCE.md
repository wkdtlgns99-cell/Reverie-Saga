# QT-F04 — Quilltale Provenance / Reuse Rights Investigation

Date:2026-10-07 | State:UNVERIFIED | Investigation:RECORDED | Reuse rights:NOT_ESTABLISHED | Review:self-review only
Authorization:director requested the next backlog task;read-only provenance investigation,not import/license assignment/runtime work.

## Scope / acceptance contract

- Baseline:Reverie main/HEAD b0f98e2aa19c5db11d0c746226d4bf321b34dee8,172 nonignored input files;preserve prior dirty work. Reference C:/Quilltale HEAD3c50c34f4c756e3a27405a1abd1a00ecc6098c51,276 present nonignored input files/15 dirty paths;read-only with GIT_OPTIONAL_LOCKS=0.
- Reads:AGENTS,BACKLOG,handoff,Korean companion,engineering document/quality/Claude/reuse rules,MASTER product/v1 restriction,Sol template,prior Claude feedback,reuse inventory,curated JSON,source Git history/README/four candidate files,public repository metadata/trees/README and GitHub licensing guidance.
- Allowed MODIFY:C:/ReverieSaga/BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md,docs/work_orders/IMPLEMENTATION_ROADMAP_ORDERS.md. Allowed NEW:docs/work_orders/QT-F04_PROVENANCE.md,docs/reviews/RS-REVIEW-CP02_REQUEST.md under C:/ReverieSaga.
- Forbidden:reference writes;runtime/tests/config/locks/policy/AGENTS/architecture/curated JSON/previous evidence;no checkout/fetch/clone/import/license file creation/deletion/agent/provider/commit/push. Public/source contracts and code tests:NOT_APPLICABLE,documentation/read-only inspection.
- Acceptance:identify evidenced origin chain,check actual license notices/artifact suitability and source witnesses,record unresolved rights honestly,validate UTF8/local links/fragments/diff/IDs/scope and reference preservation. Investigation recording is not rights qualification or task DONE.
- Stop:external ownership/permission cannot be inferred;ask director for artifact authorship/origin or actual permission. Hold reuse/bulk distribution while rights remain unresolved. CP02 feedback required before reuse;CP01 independently holds further game/core/client expansion.

## Primary sources / pinned observations

| Object | Observed evidence | Limit |
|---|---|---|
| Local origin / public source | [wkdtlgns99-cell/Quilltale_practice](https://github.com/wkdtlgns99-cell/Quilltale_practice);[API metadata](https://api.github.com/repos/wkdtlgns99-cell/Quilltale_practice):id1347375289,public,default main,fork=false,license=null,no parent/source fields | GitHub network status is not proof of independent authorship or reuse permission |
| Local/public source HEAD | [3c50c34f](https://github.com/wkdtlgns99-cell/Quilltale_practice/commit/3c50c34f4c756e3a27405a1abd1a00ecc6098c51);public branch matches local HEAD,parent9f2ec20a7a06fedf01dd141b740bf4da8c3fc3ec | Dirty local README/source changes are not remote branch content |
| Initial upload | [ae6837d4](https://github.com/wkdtlgns99-cell/Quilltale_practice/tree/ae6837d4e8184bad2cfdb5d9b972566439f38811/Quilltale);source files initially nested under Quilltale/ | Initial commit title/upload and Git author identity do not establish copyright ownership |
| Historical README / claimed origin | [first root README ba1d9c16](https://github.com/wkdtlgns99-cell/Quilltale_practice/blob/ba1d9c16b289f76a22e020ea8e32191b4bbb9a84/README.md) links aeesh/quilltale and aeesh1 demo | Prior review searched rewritten working README only;Claude's older-README origin concern now has evidence |
| Referenced upstream | [Aeesh/Quilltale](https://github.com/Aeesh/Quilltale),[pinned README](https://github.com/Aeesh/Quilltale/blob/217677d35779769a57119ae31e92e8e903e6f631/README.md),HEAD217677d35779769a57119ae31e92e8e903e6f631/tree0c565c05a3a02abac42c315a9f9ec38388316772;API license=null | README contains no license/copyright/attribution grant;not assumed owner authorization |
| Recursive trees | Source80288c9705f1affc396018d02b8242ba60918d8e:299 entries;upstream0c565c05:35 entries;both truncated=false,zero license/notice/copying/attribution-named files | Filename and GitHub detection checks are not an exhaustive legal audit or proof of no permission elsewhere |

## Origin-chain evidence — do not infer blanket rights

Four initial-upload blobs are identical to the pinned Aeesh tree:

| Path after removing initial Quilltale/ prefix | Equal Git blob SHA-1 |
|---|---|
| src/world/state.py | d800e945aa5c946ca6798e3c6afd7e01e4d4ed80 |
| src/llm/base.py | 0aebf09836e9647b46f25e92858220ba59c71e80 |
| assets/styles.css | b8ca98029f8ef639d49f778a29bd6d3b7ec7de2d |
| data/worlds/default.json | eba6b59ea9cb8642dee5d4a0989049cbf7c2a62b |

Combined with historical README links,this establishes shared file content and an evidenced origin relationship despite fork=false. It does not prove copying direction/ownership for every later file. Upstream pinned tree has no data/templates/ paths;the selected descriptions entered the practice repository later,so do not label all six as copied from Aeesh or automatically original.

## Candidate trace / artifact-specific rights

Existing [six candidate dossier](../reference/QUILLTALE_CONTENT_CANDIDATES.json) and [reuse policy](../../architecture/V1_REUSE_INVENTORY.md) are READ ONLY. Each source id is unique and its two named fields are present;all six remain CURATED_REFERENCE/runtime_imported=false. Source history first introductions:

| Candidate IDs | Source file | Introduction commit | Rights disposition |
|---|---|---|---|
| harbor_salt_mist,village_tree_canopy,oasis_caravan_rest | settlement_templates.json | 34706e0b2ce6b8fc74dc9105dd36a7537fe775b8 | UNVERIFIED;need authorship/generation inputs/third-party origin evidence |
| inn_moonlight_traveler | facility_templates.json | 657fdc11225815f42a1a78f0b641ab403c1ac07b | UNVERIFIED;same prerequisite |
| quest_moonflower_premise | quest_templates.json | 3d800d4c8ada4abf94037e84a309ea4f06eb2bd3 | UNVERIFIED;same prerequisite |
| creature_copper_catfish_visual | monster_templates.json | cae4c48261c91ef4452dc5270d3bf0307ab538ff | UNVERIFIED;same prerequisite |

Git commit identity/introduction is provenance,not proof of original expression or rights. Selected narrative fields remain potential new-schema inputs only;no old code/formulas/stats/conditions/rewards/entity bindings/test oracles ported. Unselected corpus includes recognizable third-party fictional references;that observation does not establish infringement in these six,but rules out a blanket whole-corpus clearance. Do not import or distribute new candidates while rights are unresolved.

### Byte witness / line-ending reconciliation

Initial raw comparison found3of4 current-file SHA256 values different from the historical dossier. Native byte reads of the recorded commit and LF/CRLF reconstruction reconcile ALL recorded hashes without changing any source/candidate file. Local normalized text equals the recorded commit for all four;their Git blob ids also equal current local/public HEAD. This is newline presentation drift,not established content drift.

| Source file | Dossier EOL / current EOL | Normalized LF SHA-256 |
|---|---|---|
| settlement_templates.json | CRLF / CRLF | 594ae8b95e2726ee910f2584b5658be4aa8f823f9ce01104819af6d9f52e2fc9 |
| facility_templates.json | LF / CRLF | 8a23083db8fd6b07a527dbd6812c66077340f2d2d6240e559bd631230f7bfb83 |
| quest_templates.json | CRLF / LF | bc8d18103bc74f8c3b39146fa3423d21f916ad7d27171af25925f71689d8d19a |
| monster_templates.json | CRLF / LF | 0eed145400dc00d307e547d9cfd1b33a7ae6326453ca0120ff4578af4ccdcdfd |

Future import orders must pin immutable source blobs plus explicit encoding/EOL/normalization;never silently overwrite historical SHA values or accept unexplained content changes as newline fixes.

## Decision / manual checkpoint

QT-F04 remains UNVERIFIED:origin investigation recorded,artifact ownership/license/permission not established. Public visibility is not a reuse grant;see [GitHub's licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository). This is evidence triage,not legal clearance. No license text is invented or added.
Asked director whether the six descriptions are self-authored/AI-generated anew or from external sources,and for source/permission if external. If original,gather provenance/input/service terms when relevant;Git identity alone is insufficient. If external,obtain artifact-applicable grant and attribution requirements;otherwise reject/defer or separately authorize newly authored replacements. Do not delete existing historical references or add a blanket license to third-party work.
[CP02 request](../reviews/RS-REVIEW-CP02_REQUEST.md) is prepared for director-mediated Claude review:Sol flags timing/lists files → director shows files/project → director returns Claude reply → Sol verifies findings and performs only approved scoped fixes/retests. Claude cannot replace the missing rights evidence. Review NOT_RECEIVED;CP02 not DONE. CP01 code review is separately pending,not waived by this investigation.

## Actual execution / verification

- Read-only Git:rev-parse/status/remote URL,root/history/path introduction logs,ls-files/ls-tree/rev-parse blob ids. No git fetch/checkout or reference write. rg found no license-named source files;exit1 means no matches,not tool failure. No runtime candidate symbol/reference found in inspected src/tests;not a full importer audit.
- Public GETs:both repository metadata/main branches/recursive trees and pinned upstream README;no secret/email/token copied into this report. Metadata snapshots and exact refs above are factual observations,not current remote claims for every future turn.
- Native Process.StandardOutput.BaseStream preserves Git blob bytes for SHA256 comparisons;both newline reconstructions checked. Initial root README probe failed because README was nested;ls-tree and first-root-README history resolved the correct paths. A broad property-value lookup matched unrelated facility references;explicit id equality validated six unique source entries. No witness/check weakening or historical hash rewrite.
- Document verification:PowerShell exit0,6strict-UTF8 documents/92local links/8fragments/fences/whitespace/git diff --check PASS;root backlog125lines/handoff55lines,six candidate entries/runtime_imported=false and accurate pending statuses checked. Existing Korean-file LF→CRLF Git notice is a warning,not a failed check.
- Scope verification:172Reverie entry files,168byte-identical/exact4authorized existing docs modified plus2NEW docs;all276present nonignored reference files,15dirty paths and both HEADs unchanged. Historical curated JSON/policy/runtime/tests/config/lock/archives/evidence preserved. No imports/dependencies/assets/rules/commit/push/deletion.
- Investigation/document recording accepted by self-review only;QT-F04 RIGHTS_UNVERIFIED,CP02 feedback NOT_RECEIVED,CP01 separately TODO. Runtime/lint/types/replays NOT_RUN;previous1242PASS belongs to RS-CLIENT-002,not this task. No independent Claude/legal/product acceptance fabricated.
