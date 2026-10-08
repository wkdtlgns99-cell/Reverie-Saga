# Reverie Saga — Agent Entry Point

## Authority and entry

- MUST read [ENGINEERING_RULES.md](ENGINEERING_RULES.md) from disk at the start of EVERY assistant turn, including chat/status turns and after compaction; apply relevant actions before work or response. Session discovery or remembered text does not replace this read.
- Work in this repository. Task entry/resume: read [handoff](SESSION_HANDOFF.md), [backlog](BACKLOG.md), and the applicable READY order.
- Engineering/governance authority: [v2.6 prompt](docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md).
- Product authority: [MASTER](docs/MASTER_GAME_ARCHITECTURE.md). Historical v1 rules are reference only.
- Execution/repair authority: [turn rulebook](ENGINEERING_RULES.md); architecture/product contracts retain authority. This file is the entry router, not another checklist.
- Use [work-order template](docs/prompts/SOL_CODING_WORK_ORDER.md) for concrete scope/contracts/acceptance; [README](README.md#verification) owns actual commands, [enforcement map](docs/ENGINEERING_ENFORCEMENT.md) owns active/deferred control routing.

No automatic next task,agent launch,publication or remote administration is authorized by these routes.
