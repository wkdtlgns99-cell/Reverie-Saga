# RS-PLAY-001F — Supply Slice Execution

Local implementation2026-11-04;self-review;primary2/6,related3/5/7.
[Contract](../work_orders/RS-PLAY-001F_SUPPLY_INCIDENT.md). Publication facts follow Git/PR.
Director latest scope:finish this ONE feature,then stop;parent D01-D07 remains incomplete.

## Observable slice

- Opt-in `python -m app.client --world` opens the fixed development world with
  registered supply state for all12cities. Default working file is
  `tmp/world-supply-play/game.sqlite`,isolating older prototype pins/saves.
- Logical30starts disruption at the starting city;stock3→2→1→0 at30/60/90.
  Saved NPCs change activity from actual shortage. Ordinary routines/sleep remain.
- Nonmodal resident offer states exact role,goods,deadline,reward and consumption.
  Confirm accept→collect one crate twice→deliver two crates;one atomic owner moves
  city warehouse/player inventory,consumes repair materials and pays5from treasury.
  Preview/refusal transfer nothing. Current location,role,stage,goods and deadline are
  revalidated;stale terms do not override current rules. Expired cargo stays player-owned.
- Supply event/cue,city stage/treasury/inventory survive exact retry,slot load/restart
  and deterministic replay. An uncertain SQLite commit or failed GUI acknowledgement
  retains the same confirmed command;retry neither duplicates cargo nor pays twice.
- Seed variants choose existing places/timing/duration without fresh world/provider
  generation. Actual worker integration qualifies an unvisited city's shortage without
  materializing its residents. This is bounded goods supply,not a complete economy.
- Controls use two rows and remain reachable at780x560. Map/inventory/offer consideration
  keep slow time;ESC freezes. Actions consume recorded1second without overlapping idle charge.

## Evidence and limits

- Related world/old-client/rulebook regression:169PASS33.14s before the final
  presentation-acknowledgement/two-row repair. Final actual Tk18PASS13.04s qualifies
  those edits. Final combined world/old-client/rulebook171PASS33.05s includes both fixes,
  with PytestUnraisableExceptionWarning promoted to errors. Basetemp:tmp/pytest-world-supply-publish.
- Both all-source Ruff configurations,strict mypy324files,import contracts3+1,
  pip check PASS. Scoped formatting12PASS. No shared CORE files changed.
- Real GUI inspected through computer-use:world/stock0/changed residents/offer control visible.
  First screenshot was occluded;foreground capture established actual game state.
  An attempted close was not executed when automatic approval review hit account quota;
  later account query confirmed ordinary usage available again. No unsafe-action finding.
- Final manual UI flow confirmed accept→two separate collections→delivery/reward5gold;
  inventory showed5gold/no remaining cargo and the courier left shortage activity.
  A follow-up boundary regression reproduced an offer appearing at29before the30incident.
  Repaired projection requires both present activity and eligibility at the action's end;
  the629deadline case remains hidden. The new independent test failed before the repair.
  Final affected supply/domain/Tk36PASS16.54s and both Ruff/strict324PASS after that repair;
  earlier171case evidence is reused for unchanged inputs,not reported as a new combined run.
- First tests:10PASS/domain;two temporary-root setup errors and one missing record-only
  presenter failure. Used owned workspace basetemp and registered the required presenter;
  original tests then13PASS. No skip,oracle weakening,dependency/security alteration.
- Real GUI failure injections exercise actual SQLite COMMIT followed by an exception,
  unavailable recovery read and presentation acknowledgement failure;domain outcomes
  are real. Supply action timing assertion<2s on this host passed in the live-flow test.
- Local whole-repository regression NOT_RUN at this stage;required CI must qualify the
  final published tree before merge. Native Unity,other-device,standalone release and
  independent review remain outside this slice. CP06release hold remains.

## Remaining parent scope

Live free-form NPC conversation/personality-memory grounding,speech duration and social
memory/claims vs facts,local2D traversal,transport journeys/interruptions and full parent
demonstration remain. Prepared supply offers do not establish live AI completion.
Director requires stopping after this feature;do not begin those items automatically.
