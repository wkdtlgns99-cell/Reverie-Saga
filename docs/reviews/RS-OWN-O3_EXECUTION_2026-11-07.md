# RS-OWN-O3 — Merchant and Courier Quest Verification

2026-11-07. Primary 7 integration verification with 2 rules, 3 data, 4 optional AI, 5 UI and 6 persistence. Local acceptance is self-reviewed. Baseline `ccf30bbaa0a58a3720e5a4f73a5fdcedb84f1390`. See the [work order](../work_orders/RS-OWN-O3_TWO_NPC_SUPPLY_PROOF.md) and the [integration regression](../../tests/integration/test_world_two_npc_supply.py).

The regression plays the existing `--world-knowledge` quest with actual Tk, WorldWorker, the registered knowledge profile and SQLite. A simulated idle clock makes the timeline reproducible. The provider test controls the external transport and inspects the actual serialized request. It uses the existing Gemini adapter, parser and admission without making a network call. The deliberately false AI reply checks whether accepted speech can change the game. It is not a language-quality test.

| Mode | Observable path |
| --- | --- |
| AI enabled, controlled responses | The courier hears “보급로가 이미 열렸어요” and a private sentence. The merchant's tick-12 prompt contains neither. At tick 19 the merchant receives the selected quote with the courier, original player and speech ID attached. The private sentence stays in the courier's own conversation. The merchant still sees a blocked route and no observed delivery. The accepted reply falsely says the route opened and proposes delivery. The status stays blocked, with both crates and zero gold, until confirmation. The first crate and delivery use the AI confirmation controls, and the second crate uses the authored route. |
| AI disabled | The free-speech control is disabled and provider creation is forbidden. The written dialogue and existing confirmations complete the quest. No exchanges are recorded. |
| Provider timeout | The courier's heard speech survives with no reply or judgment. The authored controls complete the quest. The delivery commit succeeds, its acknowledgement and first recovery fail, and a retry using the original request key reports that same committed delivery. |

The actual trace in all three modes commits acceptance at tick 2, collection at ticks 10 and 14, and delivery at tick 23. The objective CORE at tick 27 equals an independently driven authored-only trace at the same ticks. Delivery consumes two crates, opens the route, pays 5 gold once, and credits city +20 and nation +5 once. After delivery, both NPCs see the public open route and only the merchant's prompt contains the direct observation at tick 23.

Closing and reopening SQLite retains completion and the expected transcript. Each trace replays without a provider. Restoring the pre-claim slot and reaching tick 19 produces no rumor or delivery observation. Reloading the later slot restores the completed state. The same test covers both the durable action and its separation from heard speech. Production runtime and save formats use the already qualified O1 and O2 paths.

The initial new-file run passed all three cases in 13.39 s. The final focused selection passed 200 tests in 103.99 s, including the final O3 test and its persisted action-tick assertions. This selected the world supply, transport, social, dialogue, knowledge and client suites plus the durable turn and engineering rulebook suites. Both Ruff configurations, the new-file format, strict mypy across 358 files, four import contracts, `pip check`, ten local documentation links and `git diff --check` passed.

The delivery PR records final CI, the ordinary merge and local main synchronization. The current scope is the one existing development quest.
