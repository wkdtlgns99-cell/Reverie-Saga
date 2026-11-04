# RS-PLAY-001G — Incomplete Conversation Checkpoint

2026-11-04;self-review;primary4,related2/3/5/6/7. Baseline6b12f51/main,branch
codex/live-npc-conversation-20261104. Latest director request:reach Draft PR upload only,
stop implementation/CI waiting;continue at home. No merge/main synchronization now.
[Contract](../work_orders/RS-PLAY-001G_LIVE_CONVERSATION.md),[session inventory](../../BACKLOG.md#session-decision-and-implementation-inventory--2026-11-04).

## Implemented and qualified locally

- New optional `conversation=True` world checkpoint/session and world-conversation-v1bundle.
  Supply/default --world behavior and older pins remain. Registered PlayerSay/NpcReply/
  ContinueSpeech,one memory owner,append/replace-last/progress deltas,strict codecs/observed
  views/checkpoints and speech facts/presenter reuse existing CORE/COMMIT/SQLite/replay.
- Full own exchange text/provenance persists,up to4096exchanges with explicit rejection at
  capacity rather than silent forgetting. Retrieval selects only the addressed NPC's recent
  and relevant earlier exchanges within4096bytes. Heard claims are not objective facts or
  automatic formal quests/rewards. Broader social/numeric belief mechanisms remain absent.
- Strict NFC,1..512codepoints;player6/s,NPC stored-disposition rates4/6/5/7,specified prototype
  tuning.16scontinuations preserve one utterance and exact total duration across slots/restart.
  Other game actions reject during unfinished speech. Context hash,current reach/awake NPC
  and role-supported proposals revalidate before accepting a generated reply.
- Shared supply offer eligibility was moved to a pure domain helper and reused without
  changing existing supply semantics. Strict stale/deadline/no-unconfirmed-reward tests pass.
- Fixed-origin Gemini child transport wrapped with owned-child cancellation/deadline,strict
  output schema,one attempt and persistent usage accounting. GenerationBudget accepts explicit
  spacing0for a separate runtime profile;preparation default60s and its existing tests remain.
  Primary environment/ignored local .env only;no spares/rotation/billing/security change.
- New actual IO adapter has the same narrow TID251 boundary allowance as existing Gemini
  adapters. Positive/negative lint probe qualified;all world concrete engines now enter the
  existing independence contract. No CORE ban,dependency,test expectation or safety gate weakened.

## Actual commands/results

- Final affected selection84PASS8.99s:unit world conversation/provider,registered integration,
  engineering-rule guards,existing generation budget/Gemini preparation and supply cases.
  `--basetemp=tmp/pytest-conversation-handoff-final`;canonical sys capture retained.
- Both all-source Ruff configurations PASS;format15PASS;strict mypy334files PASS;
  type-inclusive import3/runtime-cycle1contracts PASS with --no-cache;pip check PASS.
- Earlier integration19PASS/1FAIL:non-NFC input is rejected by the canonical command boundary
  as INVALID_COMMAND before speech admission. Pure domain validation reports DIALOGUE_TEXT.
  Corrected the boundary-specific test oracle,retaining exact diagnostic and state/time checks.
- First lint-probe insertion was placed in the wrong parametrization,causing collection error;
  moved it into the existing five-field lint probe. Selective E501then required splitting a
  long adjacent string;all original guard assertions retained and final checks passed.
- Real provider attempt1:GENERATION_TIMEOUT,no accepted NPC reply and no success/latency
  qualification. Script prints timing only on success,so actual latency is NOT_MEASURED.
  Player utterance had already committed;ignored local progress remains at
  tmp/rs-play-001g-live/qualification-01.sqlite. Do not upload credentials/budget/private saves.
- Provider output/cancellation unit fixtures are controlled transport tests,not actual AI
  response qualification. Cancellation kills/closes the exact real owned local child process.
  No full local regression,new native Unity run or new GUI conversation run is claimed.

## Resume,not completed wiring

1. Implement the planned conversation coordinator:one explicit Say→remaining speech segments
   →context→one provider attempt→accepted NpcReply→remaining NPC segments. Preserve the exact
   pending GameCommand and validated generated reply through uncertain persistence/ack errors.
2. Add WorldWorker opt-in conversation mode and extend updates with saved conversation/NPCs.
   Add the nonmodal resident/free-text/transcript panel,reply retry/continue-without-reply,
   cancellation,remaining-speech continuation and inline supported SupplyAction confirmation.
3. Ensure slow idle before submission flushes once;pending speech/provider processing adds no
   wall time. ESC holds subsequent segments,close cancels owned child work;restart continues
   accepted progress once. Current --world remains the accepted supply UI,not live dialogue.
4. Qualify actual provider path and two personas/own-memory recall after restart. Then run
   real GUI pause/provider-error/cancel/stale attachment/uncertain COMMIT/ack/save flows.
5. Reconcile progress again,finish final required CI and ordinary PR/main publication only
   after explicit resume. Parent local2D/transport/rumors/deception/full product remain pending.

Native/device/independent-review/release limits and CP06hold remain;this Draft is neither
feature acceptance nor publication/release qualification. No automatic next work after upload.
