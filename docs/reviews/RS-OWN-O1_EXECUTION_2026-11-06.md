# RS-OWN-O1 — Authored Supply Quest Verification

2026-11-06. Primary 7 integration, related 2 rules, 3 world data, 4 optional live dialogue, 5 UI and 6 persistence. Local verification is self-reviewed on this Windows workstation. Scope and contracts are in the [work order](../work_orders/RS-OWN-O1_AUTHORED_SUPPLY.md).

## Playable flow

Open `python -m app.client --world-authored` and wait one game second. **보급 의뢰 대화** opens a written line and the current action terms. Accept the merchant's request, confirm each of two collections from the courier, then confirm delivery to the merchant. Successful delivery uses both crates, pays 5 gold once, adds 20 city and 5 nation reputation, and shows the merchant's closing line. The text reads the actual offer and the result reads committed supply state. Authored confirmation and a validated AI suggestion both submit the existing typed `SupplyAction` through the same worker and durable session.

This profile saves at `tmp/world-authored-supply-play/game.sqlite`. AI is off by default. `--npc-ai` enables dialogue on the same save. After a generation failure the player can continue from the map's authored dialogue button. An unfinished recorded utterance can be completed from the saved transcript after reopening offline. Bare `--world` still selects its original transport profile. The retained witness reopened six prior profile saves and confirmed their original bytes, pins, core hashes and applicable conversation context hashes.

## Actual results

| Scenario | Observed result |
|---|---|
| AI disabled | Offline worker rejected new speech, generation and reply actions before opening a save. The actual Tk quest finished with provider creation forbidden and no recorded exchange. |
| Generation timeout | A controlled external-boundary `GENERATION_TIMEOUT` followed the player's saved utterance. The UI pointed to the authored route. The quest finished with the heard utterance and no saved reply. |
| Valid and invalid AI suggestion | The controlled courier collection suggestion used the same confirmation path. A courier delivery proposal was rejected as `DIALOGUE_PROPOSAL`, then the authored quest finished. |
| Save and replay | The real SQLite save, restart and slot load retained stage 2, 2 crates used, treasury 10, gold 5 and single merit credit. Each aligned trace contained only `accept`, `collect`, `collect`, `deliver` as supply actions. Each trace replayed, and all objective components matched the independently run typed actions at the same tick. Conversation was checked separately. |
| Storage failure and retry | A real SQLite transaction rolled back after an injected replay insert failure. The initial test reproduced the lost retry UI. The fix surfaced `SAVE_UNAVAILABLE`, preserved the original confirmation, and left the file bytes, clock and reward unchanged before retry. Retry completed one delivery. Existing real uncertain-commit, presentation-failure and stale-confirmation tests also passed. |
| Recorded speech and entry point | A saved segmented utterance resumed offline without calling a provider. Both authored CLI forms opened the isolated save, and incompatible or repeated flags were rejected. |

Focused world, client, durability and rulebook regression passed 187 tests in 65.41 s. The final O1 file passed 6 tests in 12.74 s after the test assertions were cleaned up for strict typing and duplicate-flag coverage was added. Both Ruff lint configurations, scoped formatting, strict mypy (356 files), three type-inclusive and one runtime import contract, and `pip check` passed. Pytest used the repository's default `--capture=sys` with separate `.pytest_cache` temporary roots.

One visible Tk and SQLite pass from offer opening through each committed update took 0.0927 s for acceptance, 0.0938 s and 0.1048 s for collection, and 0.1246 s for delivery. All four met the local 2 s target. The measurement excludes idle waiting and provider calls.

Provider success and failure were controlled at the provider boundary. This receipt covers the one development quest and local recovery behavior. The delivery PR records the final CI, ordinary merge and local main synchronization. O2 knowledge and retention, O3 integration and commercial API payment follow the current product direction in the [backlog](../../BACKLOG.md).
