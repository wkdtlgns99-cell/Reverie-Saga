# CP05-CONTRACT — Review First Quest / Gemini Preparation Boundary

Date:2026-10-13 | State:READY_FOR_REVIEW / feedback NOT_RECEIVED.
Read [QT-F07 order](../work_orders/QT-F07_QUEST_DIALOGUE.md) and
[exact proposed contracts](../work_orders/QT-F07_QUEST_DIALOGUE_CONTRACTS.md) first.
Review the actual surrounding code/tests supplied in this packet,not contracts alone.
This is the required BEFORE-IMPLEMENTATION pass;no quest/Gemini production code exists yet.

## Request to Claude

Review whether the proposed one-quest state/reward and prepared-dialogue integration can be
implemented safely in this exact repository. Identify blocking contract ambiguity,invalid existing
API assumptions,persistence/retry/replay/COMMIT risks,registration/phase/field-ownership errors,
approval/provenance gaps,provider quota/error/lifecycle gaps and missing independently derived tests.
Return PASS / PASS WITH CORRECTIONS / BLOCKED,each finding with priority,actual file/line,
why the contract fails and the smallest concrete repair. State files inspected/omitted and whether
you ran any commands. Do not claim an implemented feature or native result from this design packet.

Questions:
1. Can one quest.rules engine own stage in RESOLVE/POST_TICK with the existing manifests,
   activation/read/staging APIs? Does the composed0→2 transition preserve validation/atomicity?
2. Is POST_TICK targetHP observation sufficient for this explicitly bounded quest without
   changing encounter.defeated's record_only policy or coupling engine modules?
3. Does stage3 serve as a durable exactly-once favor grant through duplicate submit,uncertain
   persistence/recovery,load/reconnect,precommit failure and presentation exceptions?
4. Are exact schema/entity extraction,stage/target invariants and catalog-to-rule fingerprints
   sufficient for old/new save rejection and offline replay without a save-format migration?
5. Does the four-intent generated content contract prevent state mutation and distinguish
   local validation from director semantic approval? Is the whole pinned catalog/provenance
   needed and can boot registration validate all static quest bindings without a new SSOT?
6. Are the stdlib Gemini adapter,free-only confirmation,hard call/token reservations,429/defer,
   bounded retry,timeout/cancellation and immutable artifact publication implementable as stated?
7. Is the numeric acceptance vector correct independently of the implementation? Which other
   failure/integration tests are necessary before CP05-INTEGRATION?

## Actual Input Index

Baseline HEAD1ad22446d48c50b8b72a6d3af8de3c9d775134ea;existing dirty work retained.
[Manifest](RS-REVIEW-CP05_CONTRACT_INPUTS.json) anchors current bytes and prior dirty paths;
changes.patch is cumulative worktree-versus-HEAD context,not a QT-F07-only patch.
Task-scope delta is the manifest's new/modified task paths;no production byte changed this turn.
Packet includes full current tracked repository plus retained QT-F02/CP03 new sources/tests/docs,
these contracts,authority/progress documents and the new input witness. Review inputs are frozen
at delivery;future findings must be checked against actual bytes before repair.

Inspect at least:
- src/domain/scenario.py,primitives.py,state_types.py,encounter.py,watch.py,canonical.py.
- src/contracts/turn.py,skeleton.py,messages.py,read_views.py,state_io.py,persistence.py,
  client.py,encounter.py,watch.py,replay.py,narratives.py.
- src/engines/encounter.py,watch.py;src/orchestration/turn.py,scheduler.py,serialization.py,
  watch.py,encounter.py,read_views.py,replay.py and their actual helper imports.
- src/app/scenarios.py,watch.py,watch_registry.py,encounter_registry.py,headless.py,durable.py,
  client_session.py,client_worker.py,client_text.py,client.py,engine_bridge.py,engine_project.py.
- src/adapters/narrative_catalog.py,sqlite_store.py and durable store/slot helpers in the packet.
- tests/integration/test_scenarios.py,test_cp03_repairs.py,test_durable_turn.py,test_save_slots.py,
  test_client.py,test_engine_bridge.py;tests/unit/test_narrative_catalog.py;
  existing replay tests/golden fixtures as compatibility context,not new quest test oracles.
- clients/unity/Assets/Reverie/Scripts and Editor callers;README/Unity README for actual commands.

The offline [four-line example](QT-F07_DIALOGUE_EXAMPLE.json) is Codex-authored schema/intent
review data,NOT Gemini output,NOT an approved runtime asset,NOT imported into the game.
No new live account/quota/paid-tier/provider-result claim. Key is absent from the current process;
current-project quotas/free status UNVERIFIED. Current Google references/observation date are
linked in the contract;documentation availability is not actual API qualification.

## Evidence / Limits

[Preparation receipt](QT-F07_CONTRACT_PREPARATION_2026-10-13.md) owns current document/scope/packet
checks. Prior CP031360full/133focused/47native/build/static PASS remain historical unchanged-code
acceptance,not quest/Gemini execution. No fresh game/native/full regression is necessary for this
document-only gate preparation;all proposed QT-F07 tests are PLANNED.
No external upload,Claude call,live Gemini generation,game save write,commit/push or agent launch.
CP05-CONTRACT hold is active. CP05-INTEGRATION is a separate subsequent pass and remains pending.
Claude contract review cannot grant content rights,approve new gameplay semantics on the director's
behalf,establish account free tier or replace native verification/player UX acceptance.
