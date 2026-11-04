# PR35 — Verify and Merge Conversation Foundation

READY2026-11-04;executor self-review. Primary7integration support;related2/4/6.
Latest director instruction explicitly resumes verification,ordinary merge/main synchronization,
then the remaining confirmed backlog work. It supersedes the earlier PR-upload-only pause.

Baseline:clean a4851050 on codex/live-npc-conversation-20261104;main6b12f51.
PR35is an incomplete foundation,not acceptance of the remaining Gdialogue feature.
CI41801640562/job126478583607 fails because its synthetic dependency fixture has only
the eight older engine modules while the inclusive configuration now requires thirteen.
Local allowed-dag reproduction:1FAIL2.57s,missing engines.world_travel.

Scope:tests/governance/test_dependency_contracts.py;this order and a linked execution receipt;
BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO. No production/schema/provider/CI-policy edits.
Add the five actual registered world modules to the literal fixture inventory,qualify
forward/reverse engine independence and missing-input rejection,and assert configuration
inventory equality. Preserve all original probes,expectations and import restrictions.

Acceptance:original dependency qualification plus new world cases;both Ruff configurations,
strict types,actual inclusive/runtime import contracts,pip and affected conversation cases.
Inspect actual PR production diff and registered callers;required final-head push/PR CI must
pass full regression and boundary guards. Merge ordinarily,fetch/fast-forward main,verify
equal local/remote SHA and clean tree before starting Gworker/UI completion.
Full local regression may reuse identical successful final-head remote evidence;no source
change or unsupported local/native/provider acceptance is claimed from that evidence.

No new architecture/checkpoint trigger:fixture repair only. Existing CP06/native/device/
independent/release holds remain. No agents,force/direct-main push,security change or release.
