# Sol Coding Work Order

Owner/executor: GPT-6.1 Sol for architecture, all implementation/tests/repair/integration/review. Astra: unresolved-blocker advice only.
Format: [v2.6 prompt](../ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md), **AI Documentation Format**.
This template is not an executable task. Supply concrete values and required contracts before READY.
Execution,language,repair and delivery:[ENGINEERING_RULES.md](../../ENGINEERING_RULES.md).
This template owns task-contract fields;it does not restate the per-turn checklist.

## 1. Authoring Rules

1. Fill every §3 field from actual files/contracts;label future paths NEW. Split large work by dependency order.
2. Specify applicable empty/zero/negative/boundary/duplicate/invalid-ID/missing-field/tie/ordering policies;otherwise NOT_APPLICABLE + reason.
3. Define algorithms/steps/formulas/fixed-point scales and independently derived examples;private naming remains discretion.
4. Name registration/callers/consumers and test responsibilities;standalone completion is not feature integration.
5. Missing input/contract/prerequisite,placeholder or unresolved design means DRAFT,not READY.
6. v1 reuse:individually reviewed narrative content only;no code/formulas/stats/balance/behavior/schema bindings/test oracles.
7. If BACKLOG is in scope,include GAME_SYSTEM_SUMMARY_KO in reads/allowed edits/delivery checks under the prompt's **Korean Game Progress Companion** rule.
8. Specify checkpoint IDs/trigger/held step/packet/acceptance from the [canonical Claude procedure](../ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md#claude-checkpoints-and-defect-repair--director-rule-2026-10-07),or NOT_APPLICABLE + reason.

Small tasks include pure functions under settled contracts, DTO conversion, approved-schema data preparation, adapters, tests, indexes.
Sol resolves boundaries, public contracts, ownership, scheduler/RNG/hash/catch-up/save/IPC/lifecycle/dependencies/concurrency/governance before implementation.

## 2. Executor Prompt

Supply this instruction with one complete §3 WORK_ORDER. Related contract excerpts may repeat only the minimum necessary.

```text
Execute one READY WORK_ORDER as GPT-6.1 Sol.
Workspace: C:\ReverieSaga. Reference: C:\Quilltale, read-only.
Documented model names do not change the actual model.
Read ENGINEERING_RULES.md from disk at the start of every assistant turn.
Execute its five stages against this order's scope/contracts/acceptance.
Use actual source/prerequisite evidence;edit allowed paths only.
This template grants no additional authority;latest user instructions/environment limits apply.
Apply the order's Claude checkpoint holds and linked canonical procedure.
For an unresolved blocker,report actual file/command/error and required decision.
Astra advice context,when authorized:problem/contracts/attempts/failures/question.

REPORT (brief Korean)
TASK_ID:
STATUS: READY_FOR_REVIEW | BLOCKED | UNVERIFIED
CHANGED_FILES:
VERIFICATION: command / exit / actual result / new failures
ACCEPTANCE: PASS | FAIL | UNVERIFIED per criterion
WIRING: actual path or NOT_APPLICABLE + reason
REMAINING:
Acceptance follows ENGINEERING_RULES.md and the concrete order.
```

## 3. Required WORK_ORDER Fields

Each field needs concrete values or NOT_APPLICABLE + reason. This table is a schema, not a task.

| Field | Required contract |
|---|---|
| task_id/title | Backlog ID; one action |
| status/executor/review | READY; gpt-6.1-sol; requirements + evidence; review independence explicit |
| goal/non_goals | Changed behavior; excluded capabilities |
| baseline | Actual HEAD, dirty inventory, input hash/version/marker, refresh procedure |
| prerequisites | Completed IDs, approved contracts, tools/versions |
| read_files | Actual paths/symbols/sections; current contracts/source |
| allowed_edit_paths | Exact absolute paths; NEW/MODIFY, including tests/docs |
| forbidden_paths | Reference repository, other modules/policies/user files |
| public_contract | Exact signature, field/type/default, result, callers |
| behavior | Algorithm/formulas/scales/units, read/write ownership |
| edge_policy | Empty/zero/negative/boundary/duplicate/invalid/missing/error/order/tie |
| examples | Input → exact value/type/error; independent derivation |
| algorithm_steps | Ordered small steps; permitted private choices |
| wiring | Registration/call site/symbol/consumer; standalone status |
| performance | Relevant numeric TARGET + method; missing measurement UNVERIFIED |
| baseline_commands | Real commands/exit expectations/existing failures |
| verification_commands | Necessary tests/lint/type/integration/replay |
| test_responsibilities | Actual/PLANNED paths/names; independent normal/edge/failure/integration checks |
| acceptance | Measurable files/behavior/wiring/evidence criteria |
| claude_checkpoints | Backlog IDs/trigger/held downstream step;actual-source/test/evidence packet;feedback/disposition/scoped repair/retest completion,or NOT_APPLICABLE with reason |
| stop_conditions | Cause/evidence/required decision |
| delivery | Report, edit list, commit/push authorization |

## 4. Acceptance

- Apply [rulebook verification/repair/delivery](../../ENGINEERING_RULES.md#verification) to every concrete acceptance criterion;this section adds no parallel repair loop.
- Verify task-contract examples,edge policies,live registration/consumers and exact edit scope;accept standalone work only as standalone.
- Include the Korean companion in the delivery check when BACKLOG changed.
- Revalidate Astra advice; a proposal is not completion.
- Applicable Claude checkpoints require actual feedback,verified dispositions and scoped repair/retest evidence per the canonical rule;checkpoints not triggered by this order remain pending/deferred,not silently DONE.

## 5. References

[OpenAI prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering): clear instructions/context/examples/evaluation; outputs are nondeterministic.
Project-specific requirements above bound scope/contracts/oracles/verification.
Prepared document task: `docs/work_orders/RS-DOC-002_README.md`.
Production orders require approved runtime contracts first.
