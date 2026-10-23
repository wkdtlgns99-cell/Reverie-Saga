# QUALITY-07 — Explicit continuation and useful engineering

Status:READY,2026-10-23. Executor:self-review,current Codex;not independent review.
Director asks to record automatic next-turn execution and sound,efficient product code,
then publish all current work and ordinarily merge main after passing CI. Broader development
goal remains paused. Primary support across1–7;no gameplay capability is added here.

| Field | Contract |
|---|---|
| goal/non_goals | Clarify explicit cross-turn continuation and product-led quality;no runtime/tool/CI changes,new scheduler,goal resume,agent or checkpoint waiver |
| baseline/prerequisites | Clean codex/cycle-call-links-20261023 at5497d4e,PR16contains accepted F48;existing rulebook501words/five stages/document tests and protected checks |
| reads | ENGINEERING_RULES,AGENTS,handoff,backlog,Korean progress,v2.6quality/checkpoint/companion rules,numbered guide,SOL_CODING_WORK_ORDER,ENGINEERING_ENFORCEMENT,tests/unit/test_engineering_rules.py,actual goal and PR state |
| MODIFY | C:/ReverieSaga/ENGINEERING_RULES.md;C:/ReverieSaga/AGENTS.md;C:/ReverieSaga/docs/ENGINEERING_ENFORCEMENT.md;C:/ReverieSaga/BACKLOG.md;C:/ReverieSaga/SESSION_HANDOFF.md;C:/ReverieSaga/GAME_SYSTEM_SUMMARY_KO.md;this order |
| NEW | C:/ReverieSaga/docs/AUTONOMOUS_EXECUTION.md;this order;owned tmp/quality07/evidence |
| forbidden | Runtime,test oracle,CI/security/dependency changes,unrelated user files/frozen witnesses and automatic continuation activation |
| public contract/behavior | English canonical policy linked from existing every-turn rules and AGENTS. Explicit automatic work uses supported next-turn goals without reprompting;pause is immediate. Related tasks may share a PR. Passing tests alone never qualifies product usefulness,architecture or efficiency |
| edges/examples | Automatic request→verify supported goal state;pause→no new development;edit rules/publish current scope while paused→goal stays paused. Green tests with disconnected helpers/hardcoded sample outcomes→reject acceptance. Unmeasured performance→report limit,not efficiency proof |
| algorithm/wiring | Compare existing rules,add compact clauses plus linked detail,clarify entry route and enforcement limits,update progress trio,validate documents/goal pause,commit/push to existing PR16,wait all required exact-head CI,ordinary merge and local sync |
| performance | No runtime change;retain existing≤550word/five-stage rulebook bound and reuse applicable existing tests |
| verification/tests | Existing10rulebook/document/standard-guard cases,UTF-8/local links/scope/whitespace,actual paused goal. Remote CI still required for new published head;do not infer it from prior SHA |
| acceptance/checkpoints | Requested rules discoverable,nonduplicated and honest;runtime unchanged,checks preserved,goal paused,progress synchronized. No new risky runtime boundary/checkpoint;existing holds unchanged |
| stop/delivery | Resolve broken links/size/CI failures or overlapping edits. User explicitly authorizes current combined publication/main merge only;no broad goal resume. Record actual results below |

## Local execution evidence

LOCAL_ACCEPTED2026-10-23. Existing rulebook already prohibited weakened checks/fake
success and required real callers;it lacked an explicit cross-turn mechanism and an
explicit usefulness/structure/efficiency acceptance statement. Added compact clauses and
one linked policy,clarified AGENTS routing and enforcement limits. No runtime,test,CI or
dependency edit. Root progress trio synchronized,including actual paused goal and current
publication scope. Historical F48receipts retain their original local acceptance scope.

README environment and .venv Python3.13.12 reused. Existing
`python -m pytest -q tests/unit/test_engineering_rules.py --basetemp .pytest_cache/quality07-docs`:
exit0,10PASS0.94s. Rulebook535words retains the five stages and ≤550bound unchanged.
Actual get_goal returned PAUSED;no resume/create-goal or scheduled automation executed.
Final UTF-8/local-link/scope/whitespace and post-progress document checks are recorded under
owned tmp/quality07/. Publication/main acceptance requires actual new-head GitHub CI;
older successful F48runs do not qualify these policy changes.
