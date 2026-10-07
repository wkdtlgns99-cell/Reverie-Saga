# Reverie Saga — Agent Entry Point

## Authority and entry

- Work in this repository; preserve unrelated user changes. Verify Git status before editing.
- Read [handoff](SESSION_HANDOFF.md), [backlog](BACKLOG.md), and the applicable READY order.
- Engineering/governance authority: [v2.6 prompt](docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md).
- Product authority: [MASTER](docs/MASTER_GAME_ARCHITECTURE.md). Historical v1 rules are reference only.
- Use [work-order template](docs/prompts/SOL_CODING_WORK_ORDER.md); inspect task-relevant originals when scope changes or after handoff.

## Implementation and repair

- Follow the prompt's **Implementation Quality and Repair Loop**; this file routes to that policy, not a second specification.
- Inspect actual sources/callers and search existing rules/helpers before coding; reuse through legal layer boundaries.
- Resolve required contracts before implementation; missing contracts are not solved by TODOs or guessed behavior.
- Preserve deterministic CORE, phase barriers, atomic durability/publication, retries, and read-view lifetime/ownership.
- Use existing domain rule constants and stable schema identifiers; explain intentional exceptions and responsibility boundaries.
- Runtime input validation must remain effective without asserts. Keep exact-type restrictions when changing dispatch.
- Reproduce defects with independently derived expectations; assert intended errors and unchanged state on failure.
- Diagnose and repair task-scoped/new failures, then rerun relevant checks. Never weaken tests, goldens, or lint to pass.
- Escalate only when repair needs new authority, unresolved semantics, unrelated edits, or unavailable verification.

## Verification and delivery

- [README](README.md) records actual runtime/check commands; follow task-specific acceptance too.
- Run relevant lint/types/dependency/tests/replays; shared core changes require full regression.
- Report actual commands/results; distinguish baseline/new failures and NOT_RUN/UNVERIFIED. Self-review is not independent review.
- Mark an item DONE only after its acceptance passes, then update backlog and handoff before the next item.
- Every backlog edit also updates [Korean progress](GAME_SYSTEM_SUMMARY_KO.md) in the same delivery.
- AI-facing documents: English; chat/player text and the progress companion: Korean.
- No unrequested commits/pushes, agent launches, dependency changes, destructive operations, or policy weakening.
- Further governance/public-contract/save-format changes require explicit task authorization; this file grants none.
