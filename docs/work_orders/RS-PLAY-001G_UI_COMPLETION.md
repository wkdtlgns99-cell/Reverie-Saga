# RS-PLAY-001G — Complete the Ordinary Conversation Flow

READY2026-11-04;self-review. Primary4live conversation;related2/3/5/6/7.
Baseline clean main265fc4b equals freshly fetched origin/main after PR35ordinary merge.
Both published-head CI runs41846021869/41846030829passed3935full/32boundary each.
Local130dependency/conversation,11document and57world/real-Tk integration PASS.

Authority:latest director resumes remaining confirmed backlog work after PR/main delivery.
The following key instruction explicitly replaces G's earlier no-key-rotation choice:
three configured Gemini keys must be used in order when the preceding one is exhausted.
The original Gorder's speech/state/context/provider/GUI contracts remain otherwise binding:
[Gcontract](RS-PLAY-001G_LIVE_CONVERSATION.md). Parent remains incomplete after this feature.

## Execution contract

- No new CORE/schema/save pin/engine/LLM model/dependency. WorldWorker retains supply default;
  ordinary --world opts into conversation with isolated tmp/world-conversation-play/game.sqlite.
  Older save paths/pins are untouched. New app/world_conversation_worker.py coordinates
  commands on the existing single-owner worker thread;app/world_conversation.py owns the panel.
- GUI drives one stage per settled Future:Say,remaining16ssegments,one explicit generation
  job,accept validated reply,remaining NPC segments. No segment or reply starts while ESC
  is paused. A completed provider result waits in app memory until unpaused acceptance.
  Speech processing/provider wait exclude wall-clock idle;before-send slow idle flushes once.
- Coordinator retains exact GameCommand,attachment,request key,payload and committed outcome
  across uncertain persistence/presentation acknowledgements. Same-key retry returns the
  accepted result without a second utterance/time charge. Different pending identity rejects
  WORLD_DIALOGUE_PENDING;stale attachments/replies reject explicitly. Keep a generated reply
  across NpcReply save/ack failure;never regenerate merely to retry persistence.
- Saved incomplete speech requires explicit continuation after restart;no provider call on
  inspect/load/restart. Failed/cancelled generation keeps committed player speech/time;
  retry targets that exchange. Continue-without-reply returns ordinary gameplay. Close/cancel
  signals the exact active generator and cleans its child;process-control errors propagate.
- Nonmodal panel:current resident selector,free text,NFC normalization,saved own transcript,
  speaking/generating/error status,send,retry response,continue speech,continue without reply,
  cancel. Preserve typed input until Say acknowledgement;retry storage uses the same identity.
  Any supported proposal shows actual SupplyOffer terms inline and requires confirmation
  through unchanged SupplyAction/revalidation. No proposal/prose directly transfers resources.
- Keys:load only GEMINI_API_KEY_1,_2,_3;legacy unnumbered primary remains an alias when _1
  is absent. Environment overrides the corresponding local .env entry. Strict bounded parse,
  reject duplicate/conflicting primary aliases or duplicate secret values;never print keys.
  Attempt each configured key at most once per explicit generation job,in numeric order.
  Only provider GENERATION_DEFERRED(HTTP429) advances;auth,timeout,bad output,transport and
  cancellation stop immediately. All keys429 ->GENERATION_KEYS_EXHAUSTED. No paid fallback,
  unbounded retry or provider-limit claim. Each actual attempt reserves/reconciles usage;
  preparation default60s and primary-only behavior remain unchanged. Runtime starts at key1
  for each explicit job,so provider resets need no invented cooldown/persistent key identity.

## Paths and acceptance

NEW:src/app/world_conversation_worker.py,src/app/world_conversation.py,
tests/integration/test_world_conversation_client.py and execution receipt.
MODIFY:src/app/world_worker.py,src/app/world_client.py,src/adapters/world_conversation.py,
tests/unit/test_world_conversation_provider.py,README,Gorder,docs/MASTER_GAME_ARCHITECTURE.md,BACKLOG,SESSION_HANDOFF,
GAME_SYSTEM_SUMMARY_KO and PR35receipt. Owned ignored tmp/rs-play-001g-ui and pytest folders.
No changes to legacy production/tests/goldens,central CORE,private credentials or CI gates.

Independent tests:exact speech/time/ack identity,SQL uncertain commit and presentation retry,
provider error/cancel/429key order/all exhausted/nonquota no fallback,typed-input retention,
ESC between segments/provider result,slow-clock exclusion,save/load/restart/stale attachment,
inline proposal with zero unconfirmed reward. Mock only external transport,never domain results.
Actual provider:two saved personas and own-memory recall after restart,typed proposal with
no automatic transaction;sanitized model/timing/usage evidence. Record2scommand/15sprovider
targets and any misses. Actual Tk screenshots when permitted by current computer-use scope;
automated Tk evidence remains distinct from manual/native Unity/device/release acceptance.
Both Ruff/scopedformat/strictmypy/import3+1/pip,affected tests,final required both-head full CI,
ordinary PR merge/main equality/clean. Reuse PR35unchanged CORE evidence truthfully.
No new scheduled checkpoint trigger;existing CP06/independent/native/device/release holds.
No agents or external messages. After this publication continue settled parent prerequisites;
latest2026-11-05director instruction requests autonomous continuation without questions.
Proceed with settled contracts and record choices/limits;do not infer unrelated new authority.

## Latest scope and local acceptance — 2026-11-05

The director says no questions and ONLY previously asked/answered work. Finish this Gbatch
and ordinary publication;do not select new unanswered product features. Existing broad parent
limits remain explicit. Final207affectedPASS34.25s,341inputs unchanged;Ruffboth/format19/
strict337/import3+1/pip PASS. Real4responses/own recall/proposal and timing misses recorded
in [receipt](../reviews/RS-PLAY-001G_UI_EXECUTION_2026-11-05.md). Final-head required CI/merge/
main equality pending. No native/manual capture/independent/device/release acceptance.
