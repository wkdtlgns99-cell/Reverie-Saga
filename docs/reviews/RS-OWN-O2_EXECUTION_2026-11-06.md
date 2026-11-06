# RS-OWN-O2 — NPC Knowledge and Retention Verification

2026-11-06. Primary 3 internal data, related 2 rules, 4 optional AI, 6 persistence and 7 integration. Local acceptance is self-reviewed. The [work order](../work_orders/RS-OWN-O2_NPC_KNOWLEDGE_RETENTION.md) records the director's choices, baseline code audit and pinned contracts.

## Behavior

Launch `python -m app.client --world-knowledge --npc-ai` and use the normal resident conversation box. The addressed NPC interprets the speech in context and can judge personal impact from 0 to 3. The accepted reply may select a verbatim part of the current utterance to repeat. No manual secrecy or rumor control is required. A model can misunderstand a secret. Admission checks source, size, types, attachment and context hash before the judgment can become durable. The rules send the selected quote and its original speaker, direct listener, location and timing. The rest of the direct conversation remains outside other residents' input.

Starting 10 game seconds after the accepted reply is complete, one other local resident learns the quote every 10 seconds in NPC ID order. This projection reads the active save and game clock. It never treats a rumor as a witnessed event or creates an action from the rumor. The merchant's own delivery observation comes from the authoritative committed supply resolution tick and role. Other residents keep their existing public and role-authorized facts. The slice uses fixed disposition and present situation. Persistent mood, deliberate NPC deception, trust changes, intercity transmission and multi-hop rumors have separate future contracts.

Retain the latest 32 exchanges per NPC and the best 8 older positive-score exchanges, with recent ties winning. Retirement occurs atomically on new speech. Retired entries cease to be recall or rumor candidates. The observation of a real delivery remains with its world record. Omit `--npc-ai` to use the separate profile's authored route. Failed generation leaves the delivered speech intact without inventing a judgment. Previously accepted rumors still advance by game time.

## Verification

- Actual Tk input used the unchanged conversation box, registered worker, strict Gemini response adapter with controlled transport, and SQLite. One accepted reply saved its importance and exact quote.
- Real slot, branch and replay checks verified local recipients immediately before and at +10, +20 and +30 game seconds. Private text and unselected portions never entered the other NPC's request. Stale contexts and fabricated quotes were rejected. The theft claim created no objective supply, inventory or reward change. Loading an earlier slot removed the later branch's rumor, and the saved later slot restored it.
- Actual registered speech and supply actions crossed the 32+8 boundary. A higher score survived; a newer equal score displaced the older one; an ordinary record and its outgoing rumor retired. Another resident's own record and the active speech segment stayed intact. A checkpoint-only SQLite save with an empty retained trace retained the true delivery observation. It was visible to the merchant and excluded from the courier's observations.
- Controlled timeout left the utterance in the save. Disabling AI rejected generation before any provider setup. An injected SQLite write failure rolled back the judgment without changing save bytes, and retry committed the same judgment once. Four malformed provider results were rejected.
- Reopened six retained pre-O2 world profile witnesses with their original pins, bytes and expected hashes. Reopened the separate O1 CLI save from its earlier test run under its original pins and confirmed unchanged bytes.

The final focused world, dialogue, client, durability and rulebook regression passed 197 tests in 150.09 s, including 10 O2 cases. The first broad run had two Tk-related timeouts with off-thread variable finalization warnings. The test now collects destroyed Tk variables on the UI thread before starting its worker and after each CLI launch. The same selection then passed. Both Ruff configurations, changed-file format (17 files), strict mypy (357 files), import contracts, `pip check` and 13 relative documentation links passed.

One current-workstation timing pass submitted 44 speech commands, 40 assessed reply commands and one continuation through real SQLite. With up to 42 retained exchanges in the fixture, maxima were 0.5509 s, 0.4087 s and 0.4455 s respectively. Timing excludes external generation and meets the local 2 s target at the exercised size.

Two live development Gemini runs used the same synthetic utterance about a food theft rumor and a private hideout. The first accepted both sentences as the quote in 1.968 s. After refining the instructions to interpret confidentiality by topic and quote only the intended topic, the second accepted the theft sentence alone with importance 2 in 2.001 s. The sampling does not establish a guarantee about how the model will handle future confidences. Both passed the typed boundary and committed no reward or cargo transfer.

The delivery PR records the final CI and ordinary merge evidence. Release, broader cognition and O3 integration are separate scope.
