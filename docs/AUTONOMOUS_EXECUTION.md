# Authorized Continuation and Useful Engineering

Director rule2026-10-23. Execution authority:[ENGINEERING_RULES](../ENGINEERING_RULES.md).
These rules guide already-authorized work;they do not grant publication,agent or release authority.

## Continue across turns

- When the user explicitly requests automatic execution after each turn,use the available
  supported cross-turn goal mechanism. After completing one bounded task,continue the next
  necessary authorized task without requiring another user command. Preserve the user's
  full objective,scope and stopping conditions rather than declaring success after one batch.
- Create or resume continuation only within the user's explicit authorization. Confirm its
  actual tool state before claiming it is active. Files and conversational promises alone
  cannot schedule turns. If the supported mechanism is unavailable,report that limitation;
  do not substitute a shell daemon,new task or timed automation. A timed schedule requires
  a request for that schedule;it is not the default interpretation of automatic next turns.
- At task entry and after compaction,read the turn rulebook and current handoff/backlog;
  inspect actual files,Git and outstanding jobs. Resume unfinished work before choosing a
  new bounded order. Record concrete contracts,acceptance and verification before editing.
- Reuse evidence for unchanged inputs and group related accepted changes into reviewable
  PRs when efficient. A separate PR/merge after every small task is not required. Actual
  publication still requires user authorization,all required CI on the published revision,
  applicable review/checkpoint gates and ordinary protected main merge/synchronization.
  Never bypass protection or silently weaken checks to reduce waiting time.
- Advance through actual implementation,repair and verification. A wait must observe a
  confirmed live process/job;repeated plans or unchanged status alone are not progress.
  Preserve exact sources/results and real blockers so later turns can resume safely.
- Pause/stop requests take effect immediately. Rule edits,status questions or a request to
  finish a specific publication while paused do not resume the broader development loop.
  Resume it only when the user requests continuation. Retain existing checkpoint holds,
  user work and permissions across turns;automatic execution does not authorize agents.

## Build for the product

- Passing tests is necessary evidence,not the engineering objective. Implement useful
  behavior on the registered player/runtime path,consistent with the product and settled
  contracts. Main eligibility requires a sound implementation as well as successful CI.
- Production behavior must derive from accepted definitions and committed facts. Reject
  test-name/fixture/environment-specific branches,hardcoded sample outcomes,fake successes,
  disconnected helpers and patches that merely hide a failing symptom. Legitimate domain
  constants and test fixtures remain valid when independently justified by their contracts.
- Prefer cohesive responsibilities,clear data ownership,canonical helpers/constants and
  the smallest sufficient abstraction. Fix the underlying cause at the responsible layer;
  avoid duplicated authority,copy-pasted rules,unnecessary frameworks and speculative caches.
  Preserve determinism,atomicity,error semantics,retry/recovery and resource cleanup.
- Derive expectations independently from requirements;exercise real callers and relevant
  failure/state-preservation paths. Do not mirror implementation logic as the sole oracle
  or mock domain outcomes to obtain a green result. Follow the existing rulebook for any
  intentional behavior/oracle change and for immutable historical failure evidence.
- Review the actual diff before acceptance:does it solve the requested problem,fit existing
  boundaries,remove duplication and remain understandable? Measure relevant latency,
  memory/IO or algorithmic cost against the task's budget. Report unmeasured limits;neither
  test count nor speculative optimization proves efficiency or whole-product completion.

## Enforcement boundary

The existing [document guards and standard checks](ENGINEERING_ENFORCEMENT.md#active-controls)
qualify entry links,compact rules,selected bad patterns,types,dependencies and tests.
They do not observe user intent,goal scheduling,architectural usefulness or all test overfitting.
Those require actual tool-state evidence and source/caller/performance review. This policy
adds no background scheduler,CI bypass,new review gate or claim of automatic quality proof.
