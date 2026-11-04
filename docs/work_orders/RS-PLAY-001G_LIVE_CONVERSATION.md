# RS-PLAY-001G — Live NPC Conversation

CURRENT_OVERRIDE2026-11-04:director explicitly resumes verification/ordinary merge/main
and remaining settled work. PR35foundation merged265fc4b;[completion order](RS-PLAY-001G_UI_COMPLETION.md)
owns active worker/UI qualification and newly authorized quota-only ordered key fallback.
The earlier checkpoint pause and no-key-rotation statements below are historical.

CHECKPOINT/INCOMPLETE2026-11-04;self-review;primary4,related2/3/5/6/7. Baseline6b12f51clean/main.
LATEST_DELIVERY_OVERRIDE:director requests reaching PR upload ONLY,then continuing at home.
Publish an explicitly incomplete Draft PR with current code,tests and session inventory;
do not finish the remaining UI now,wait for full CI,merge or update main. The prior
one-feature-through-main instruction below is superseded at this checkpoint.
Director resumes ONE feature,then stop after ordinary CI/PR/main delivery. Latest follow-up
also requires auditing every session decision/completed/unfinished item into BACKLOG,
SESSION_HANDOFF and GAME_SYSTEM_SUMMARY_KO before publication. No transport/local2D work.

Confirmed failure UX:submitted speech/time remain;retry only the response or continue
without a reply. Runtime cadence:one call per explicit send/retry,without preparation's
artificial60s gap. Provider429 is an explicit error,not automatic retry/key rotation/paid
fallback. Preparation policy remains unchanged. Existing primary Gemini key/free-tier and
data-use authorization reused;credentials never enter saves,commands,logs or artifacts.

Reads:MASTER2.4–2.6,parentRS-PLAY-001,supply/time/worker/client/session registries,
gemini_dialogue/transport/generation_budget,CLI_WORKFLOWS,README,numbered structure.
Installed Python3.13.12/Tk/Git/.venv reused;no new dependency,agent or external message.
New C:/ReverieSaga/src paths:domain/world_conversation.py,contracts/world_conversation.py,
engines/world_conversation.py,orchestration/world_conversation.py,
orchestration/world_conversation_context.py,
app/world_conversation_registry.py,app/world_conversation.py,app/world_conversation_worker.py,
adapters/world_conversation.py. New tests:unit/test_world_conversation.py,
unit/test_world_conversation_provider.py,integration/test_world_conversation.py,
integration/test_world_conversation_client.py. Modify world_session/worker/client,
world_supply pure offer eligibility,shared budget configurable spacing (default60s unchanged),
related tests and progress/play/receipt docs. Forbidden:shared CORE/kernel/save envelope,
legacy modes/fixtures/pins,reference checkout,credentials/dependencies/security/release rules.
pyproject.toml:register the new concrete world engines in the existing independence guard
and add only the explicit live IO adapter to the established TID251 boundary allowlist.
Qualify that path with the existing positive/negative lint probes;no core ban is relaxed.

## Authoritative speech and memory

- New isolated conversation bundle extends supply;old profiles retain pins. One player-owned
  conversation component stores ordered immutable exchanges and current speaker/remaining
  duration. Up to4096exchanges,all retained across slots/restart/checkpoint;full capacity
  rejects BEFORE delivery,never silently forgets. Retrieval/context is bounded independently.
- Text:strict NFC Unicode,1..512codepoints,nonblank,UTF8 encodable;no control characters
  except newline/tab. UI normalizes NFC before submission;stored exact normalized text.
  Player rate6codepoints/s;NPC rates by stored disposition:신중함4,사교적6,과묵함5,
  호기심 많음7. Duration=ceil(codepoints/rate),minimum1second;whitespace/punctuation count.
  Example:13player characters→3s;65at4/s→17s. Prototype tuning,not final speech balance.
- PlayerSay(npc_id,text) begins exactly one accepted utterance. Stored exchange binds a
  stable speech ID to the actual admitted command,NPC,current city and logical interval.
  Each command advances at most16s,matching the unchanged kernel limit. ContinueSpeech
  consumes min(16,remaining);no duplicate text. NpcReply binds generated text/model/context
  hash/proposal to the unanswered exchange and consumes its first speech segment. Full
  in-world duration is exact across segments,save/restart and idempotent retry.
- No other actions start while a speech segment remains. ESC pauses further segments;
  closing preserves accepted progress;explicit continue completes it after restart.
  An unanswered fully delivered player utterance does not lock ordinary gameplay. New
  speech may leave it unanswered;retry targets only its same exchange,not a duplicate Say.
- Same-city/current saved NPC reach;not mid-road. Sleeping NPCs reject new speech/reply.
  An already-started speech completes without reapplying start availability each segment.
  Submitted speech is heard personal memory,not a true world fact or formal quest acceptance.
  No numeric attitude/rumor/deception system is invented. Contextual social response is NPC
  generated speech grounded in personality and own records;objective resource rules remain code.
- Append/replace-last/progress deltas carry only the changed entry and expected previous
  digest/count,not the entire history. One owner and exact reducers/codecs/checkpoint rules.
  Earlier entries never change. Ordered intervals,IDs,NPC/place bindings,duration,reply
  provenance and current remaining time validate against the saved world and logical tick.

## Context,provider and UI

- Select only the addressed NPC's prior exchanges,recent plus text-relevant older records;
  fit complete records to a fixed prompt byte budget. Preserve full memory in saves.
  Include saved persona,current public local supply/time/activity and this NPC's currently
  supported supply action;no unrelated NPC/private memories or global omniscient inventory.
- Context canonical SHA256 binds accepted reply to the current exchange and context.
  JSON reply contains text_ko and proposal_operation:none/accept/collect/deliver. Only the
  currently eligible action of this actual NPC is allowed;generated prose cannot transfer
  goods/rewards. Show an inline summary and confirmation using the same SupplyAction.
- Reuse existing fixed-origin Gemini3.5Flash-Lite child HTTP boundary;strict JSON/finish
  validation,request/output limits,usage accounting,owned-child cleanup and cancellable
  deadline. No automatic retry. Real API tests qualified separately from offline fixtures.
  Official sources:ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite,
  ai.google.dev/gemini-api/docs/generate-content/structured-output and rate-limits.
- Ordinary --world flow shows selectable residents,free text,accepted player/NPC transcript,
  speaking/pending/error status,reply retry/continue-without-reply and supported confirmation.
  Idle/read/type/map/inventory/consideration remain1/10. Provider wait and action processing
  add no wall time;recorded speech advances once. Preserve typed input before rejection,
  pending command identity through uncertain commits,and valid generated reply through
  save/ack errors. Stale/cancelled replies never enter a different attachment/conversation.
  Cancel/close cleans owned work and leaves actual submitted speech/progress truthful.

## Acceptance and delivery

Independent duration/Unicode/history/own-memory/retrieval/invalid proposal/stale context,
long-segment/retry/rollback/uncertain commit/save/load/restart/replay tests. Real Tk error,
pause/idle/provider-wait/cancel/confirmation and input preservation tests;mock transport only,
never domain outcomes. Real provider run:two NPC personalities,follow-up own-memory recall
after restart,and typed proposal with no unconfirmed reward. Capture actual UI and sanitized
usage/timing. TARGETlocal command<2s,provider latency<15s/call on current host;misses explicit.
Ruffboth/scoped format/strict types/import3+1/pip/affected regressions;required full CI on
final head before normal protected merge/local-main equality and clean-tree verification.
Old CP01–05bounded closure retained;no new scheduled checkpoint trigger from this extension
of existing command/COMMIT/provider boundaries. CP06still holds release;no Unity/device/
independent-review/human-UX/release acceptance inferred. Scope stops after this feature and
session backlog reconciliation;pause parent goal,which remains incomplete.
