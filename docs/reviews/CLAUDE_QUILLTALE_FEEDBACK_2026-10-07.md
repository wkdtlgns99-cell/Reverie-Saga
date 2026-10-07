# Claude Quilltale Comparison — Feedback Record

Date:2026-10-07. Source:user-supplied Claude review in this conversation. Director requested storage and placement reporting,not implementation of its proposals. This document preserves the substantive feedback in structured English with current-state corrections;it is not a new architecture/rule authority.
Follow-up status SSOT:[BACKLOG](../../BACKLOG.md#external-feedback--quilltale-comparison-2026-10-07). Existing uncommitted quality/client work is preserved. No runtime/config/dependency/provider/migration/commit/push changes in this task.

## Claims and disposition

| Review claim | Current assessment / evidence |
|---|---|
| Independent engines and forced layers structurally prevent another oversized state.py | Supported coupling protection,overstated size guarantee. The active import-linter contracts prevent forbidden imports,not oversized DTOs or orchestration functions. Responsibility review and integration evidence remain necessary. See [shared config](../../pyproject.toml),[quality policy](../ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md#implementation-quality-and-repair-loop--director-rule-2026-10-07). |
| Whole-turn success prevents partial HP/state updates | Accepted design and tested behavior:private candidates,phase barriers,persist-before-head publication,blocked uncertain persistence. Not a proof that every future implementation/error is impossible. See [Driver](../../src/orchestration/turn.py),[durable tests](../../tests/integration/test_durable_turn.py). |
| Post-commit narration avoids describing rejected actions as successful | Correct for current presentation facts/cues;there is no implemented AI GM narration. Rejected commands must not receive a successful committed presentation. Claude's particular historical Quilltale README admission was not found in the inspected local README;retain it as an unverified source claim. |
| Replay reconstructs why an outcome occurred;Quilltale could not do this | Current deterministic state/fact/diff replay is implemented. It is not a complete causal explanation or proof that Quilltale has no replay/debugging capability;that broad comparison is unverified. See [replay tests](../../tests/replay/test_encounter.py). |
| AI GM,NPC memory/RAG,and butterfly-effect quests have not been reimplemented | NPC cognition/memory and full quest consequences remain future capabilities;delayed events supply a tested foundation,not complete quest logic. Mandatory AI GM/per-turn narration is NOT a v2 requirement. MASTER preserves gameplay capabilities while making live LLM optional;a specific RAG framework is not fixed. |
| Nothing is visible/playable in Reverie Saga;Quilltale can already be played | Reverie claim is outdated against current files:[Tk client](../../src/app/client.py),[typed projection/input](../../src/contracts/client.py),[native widget tests](../../tests/integration/test_client.py),[run instructions](../../README.md#play-the-prototype). It is a placeholder 2D boundary harness,not final HD-2D art/camera/device qualification. Human playtest is pending;Quilltale's current playability was not rerun here. |
| GATE_ID/ENEMY_ID etc hardcode one scenario | Valid scoped limitation. The representative encounter and input/projection mapping select fixed entities. Before claiming reusable content,define content-owned targets/rules and exercise multiple independent scenarios. Do not expand speculatively or port old engines. Follow-up QT-F02. |
| Governance/handoff/backlog bloat repeats v1's habit | Valid maintenance risk. Pre-edit local snapshot:Reverie BACKLOG57857bytes/229lines,SESSION_HANDOFF28621bytes/94lines;Quilltale SESSION_HANDOFF58041bytes/384lines. Claude's524lines/67KB is not this local snapshot;byte size is not a token measurement. Keep current context compact and link detailed history/evidence;archive recoverably only in an approved maintenance task. Follow-up QT-F03. |
| Import descriptive templates and NPC field definitions,not engine code | Retain descriptive concepts/curated individual fields and cognition semantics,not whole JSON/old schemas/DTOs/formulas/balance/tests. Current [reuse policy](../../architecture/V1_REUSE_INVENTORY.md) is stricter than wholesale schema conversion:strip old IDs/mechanics,assign new schemas/IDs and validate references. 10-factor attitude/12-axis traits/20-factor persona are retained product references,not mandatory old classes or formulas. |
| Quilltale clone/demo point to aeesh/quilltale;check upstream licensing | Preserve as a provenance concern,not a verified fork/ownership claim. The inspected local README contains no aeesh/clone/demo match;the local file inventory query found no LICENSE/COPYING file. Neither observation establishes permissions or absence of an external license. Identify the actual origin/upstream and artifact-specific rights/attribution before any new import;review already curated references too. Follow-up QT-F04 remains UNVERIFIED. |
| Add TUI/Gradio and one LLM NPC line to validate the adapter boundary | Thin UI already exists;do not introduce another framework just to replace it. An optional NPC-line adapter experiment is retained as a proposal,not accepted implementation or a mandatory per-turn dependency. It needs a separate contract/order,non-authoritative input/output,offline fallback,timeout/error behavior,and unchanged deterministic save/replay results. Follow-up QT-F05. |

## Existing rule coverage — do not duplicate Quilltale AGENTS

Inspected C:\Quilltale\AGENTS.md read-only and the [historical copy](../reference/AGENTS_v1.md). Its implementation-specific TwoPassEngine/GameMasterAgent paths and blanket rules are not imported.

| Useful lesson from the review | Existing canonical location / limit |
|---|---|
| Verify real live-turn reachability and integration | Engineering prompt B1 Wiring,B4 Scope gate;[work-order template](../prompts/SOL_CODING_WORK_ORDER.md) §1/§4 requires named callers/consumers/live paths. Symbol search alone does not prove execution. |
| No write-only/unconsumed fields | Engineering prompt C-04 and B1 Wiring. Declared/observed reads exist;the complete planned automated C-04 audit is not claimed active. |
| Bound growing memories/logs/traces | Engineering prompt B1 Wiring requires capped lists;feature orders must settle cap/decay and retention semantics. Existing receipt/event bounds do not prove future NPC memories are bounded. |
| Verify handoff markers against actual files/evidence | Engineering prompt B1 Handoff Truth;root [AGENTS](../../AGENTS.md) requires source inspection,actual verification and accepted DONE marking. A historical test count is not a fresh run. |
| Add an engine only for demonstrated need | Engineering prompt B4:live trigger,existing-module extension assessment,playtest evidence or non-negotiable MASTER requirement. Do not silently drop required gameplay or add one engine file per idea. |

The review's assertion that these four safeguards are absent is incorrect. No new rulebook or AGENTS copy is needed;keep [engineering authority](../ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md),[MASTER](../MASTER_GAME_ARCHITECTURE.md),and root router as the existing authorities.

## Carry forward

QT-F01 uses the existing playable harness to test a very small gameplay loop. QT-F02 is demand-driven content generalization;QT-F03 is bounded document maintenance;QT-F04 is provenance/rights qualification before migration. QT-F05 remains optional and separately scoped. None is implemented or READY solely because this review is saved.
Do not copy thermal/hangover/pupil/other old engines or old test oracles. Reuse reviewed descriptions and gameplay requirements through new maintainable contracts. Preserve authoritative Python outcomes;LLM text must never invent damage,quest completion,state mutations or successful rejected actions.

## Verification for this storage task

Document-only acceptance PASS:4strict-UTF8 documents,88local prose links,fences/whitespace,five unique backlog follow-up IDs and git diff --check. The link probe excludes historical code literals and checks target existence,not external license rights or runtime execution. Git status inventory preserves prior dirty work and adds only this review artifact;this task edits three existing progress documents. No production/test/config/lock/rule/Quilltale input changes. Runtime tests NOT_RUN;the prior1221-test result belongs to QUALITY acceptance,not this storage task.
