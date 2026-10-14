# CP05-INTEGRATION — First Quest / Prepared Dialogue Implementation

Date:2026-10-13 | State:READY_FOR_REVIEW;feedback NOT_RECEIVED.
This is the separate AFTER-IMPLEMENTATION pass. The [contract feedback/dispositions](RS-REVIEW-CP05_CONTRACT_DISPOSITIONS.md)
are accepted for the first implementation;they do not close this integration checkpoint.
[Order](../work_orders/QT-F07_QUEST_DIALOGUE.md)/[contracts](../work_orders/QT-F07_QUEST_DIALOGUE_CONTRACTS.md).
Read [execution evidence](QT-F07_EXECUTION_2026-10-13.md) and actual packet sources/tests before reviewing.

## Request

Review the actual integrated one-quest code,not just the earlier design. Check registered
consumers,observed reads,phase staging,delta composition,COMMIT/save/retry/recovery truth,
exact binding checks,old/new save pins,dialogue validation/approval/provenance,provider isolation/
budget/error/resource behavior and live client paths. Return PASS/PASS WITH CORRECTIONS/BLOCKED
with actual file/line,priority,proof and smallest repair. State what was inspected/omitted and
which commands you actually ran;do not inherit Sol's test/native results as your own execution.

Focused questions:
1. Does required-role boot validation reject both absent properties and skipped constructors
   before scenario validation,including all quest codecs/adapters/checkpoint/presenters?
2. Are codec/single-step/net/checkpoint checks correctly split? Can forged0→3/1→3,stage1 with
   dead target or stage2/3 with living target,duplicates/noncanonical records bypass them?
3. Do uncertain2→3 recovery and exact retry yield only one grant/receipt;does composed0→2
   precommit failure preserve stage0? Can postcommit presentation fail without false rollback?
4. Do texts/approval anchors change behavioral pins while timestamps/reviewer/usage do not?
   Can ordinary play/load/replay mutate dialogue or call the provider?
5. Does the killable owned HTTPS worker close resources on timeout/cancel,disable proxy/redirect
   defaults,and sanitize provider errors/credentials? Do real process locks/atomic reservation/
   idempotent reconciliation prevent local call-budget bypass across processes/restarts?
6. Are the stdlib generation request/JSON parsing/nullable thought usage and explicit free/key/
   data-use flags coherent? List actual API uncertainties without claiming a live response.
7. Are Tk/private-pipe/Unity talk/status/text/save/load/reconnect/retry paths fully wired and
   release verification hooks absent? Identify missing behavioral tests,not cosmetic conjecture.

## Input / Evidence Boundaries

HEAD remains1ad22446d48c50b8b72a6d3af8de3c9d775134ea;existing QT-F02/CP03 changes retained.
The new RS-REVIEW-CP05_INTEGRATION_INPUTS.json in the packet anchors current file bytes and task
delta against the307-file feedback-entry snapshot. changes.patch is cumulative HEAD context;
it is not exclusively QT-F07. Original CP03/CP05 contract witnesses and ZIPs remain frozen.

Inspect new domain.quest,contracts.quest/dialogue,engines.quest,orchestration.quest;
orchestration.serialization boot validation;app.quest/quest_definition/quest_registry/watch bootstrap;
client_session/worker/text/Tk/bridge/exporter and all Unity Scripts/Editor callers;
adapters.quest_dialogue/gemini_dialogue/gemini_transport/generation_budget and preparation CLI.
Include actual durable/store/slots/driver/scheduler/read-view/canonical helpers rather than
assuming prior review covered them. New unit/integration/replay/adapter tests and existing
legacy goldens/guard tests are included. The independent quest vector is manually authored
state/fact expectations;retained engine trace is a recorder witness checked against that vector,
not a falsely claimed independent full hash oracle.

Native evidence uses a temporary offline test-only catalog/receipt derived from the preserved
example,not Gemini output or director approval for shipped content. Screenshots/performance/
sanitized public final views and summarized check labels are packet evidence. Private saves,
attachment tokens,raw account/license logs,build/cache folders and the local API key file are excluded.
No key was read,submitted or printed. Director explicitly deferred real Gemini calls and will
fill the ignored local key file later. Account/free tier/quota,actual model/endpoint STOP result,
production content approval and other-device/standalone/release/human UX remain separate.

Sol's current local tests/static/native/build results and initial failures/repairs are stated in
the execution receipt. There was no remote CI,new dependency,billing change,publication,external
upload or agent launch. Larger quest/world/memory expansion is held until actual feedback,
verified dispositions and required repairs/retests close CP05-INTEGRATION.
