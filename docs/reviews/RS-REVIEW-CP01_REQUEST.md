# RS-REVIEW-CP01 — Claude Review Request

Date:2026-10-08 (Asia/Seoul) | Packet:HISTORICAL_REVIEWED | Feedback:RECEIVED | Checkpoint:DONE
Timing:after QUALITY-05 + CLIENT-002,before next gameplay/core/client expansion. Preparation is not checkpoint completion. Canonical procedure:[engineering prompt](../ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md#claude-checkpoints-and-defect-repair--director-rule-2026-10-07);status:[backlog register](../../BACKLOG.md#claude-checkpoints-and-defect-repair--2026-10-07).

## Director handoff

1. Show Claude this request plus the local review ZIP,or the exact files from the [input manifest](RS-REVIEW-CP01_INPUTS.json). The ZIP preserves repository-relative paths;extract before reviewing. Do not upload the working directory wholesale:private saves,secrets,caches and the native environment are outside the package.
2. Ask Claude to follow the pasteable request below and return its full answer. No automatic provider call/upload or Claude execution is claimed.
3. Paste the answer back unchanged. Sol rechecks findings against the current files/contracts and reproduction,then records dispositions and prepares required bounded repairs/retests. Core/client expansion stays held until actual feedback and required repairs pass. CP02/rights/graphics/GOV-03 holds remain unchanged.

## Snapshot / refresh

Preparation HEAD:`564c11eb1eb9f7fd7d3e72745c67afb30d9e2848`;entry tree clean. Delivery dirty inventory is exactly this request,input manifest,preparation order and root BACKLOG/SESSION_HANDOFF/GAME_SYSTEM_SUMMARY_KO. Production sources/tests/configs/fixtures are unchanged.

The manifest records raw on-disk SHA-256 and byte size of every reviewed input,including the final root records and preparation order. The request and manifest are excluded from their own input hashes to avoid circularity;ZIP validation verifies their packaged bytes separately. HEAD alone cannot identify these uncommitted documents. Before forwarding a later-edited project,recheck HEAD/status and every manifest entry;refresh the packet if any input differs. Package excludes `.git`,`.venv`,`venv`,`.env*`,keys,private SQLite files,ignored runtime output and external Quilltale content.

Local delivery:`tmp/reviews/RS-REVIEW-CP01_2026-10-08.zip`;142hashed inputs + this request/manifest =144entries. This is a bounded project packet,not the entire documentation archive;references outside its inventory may require separate context and must not be treated as inspected. Sol verified local paths and packaged raw bytes;no external transmission occurred.

## Reading order / concrete focus

| Read | Responsibility / questions |
|---|---|
| [AGENTS](../../AGENTS.md),[prompt](../ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md),[MASTER](../MASTER_GAME_ARCHITECTURE.md),[README](../../README.md) | Current engineering/product authority,runtime/check commands;historical source-order NEXT instructions are non-operative |
| [QUALITY](../work_orders/RS-P1-QUALITY.md),[CLIENT-002](../work_orders/RS-CLIENT-002_ACTION_LOG.md),[Phase0 contracts](../work_orders/PHASE0_CONTRACTS.md),[CORE-03](../work_orders/RS-P1-CORE_03_INTERACTION_COMBAT.md),[CORE-05](../work_orders/RS-P1-CORE_05_DURABILITY_SAVE.md),[integration evidence](../work_orders/RS-P1-CORE_INTEGRATION_REVIEW.md) | Accepted scope and superseding contract/acceptance sections;do not equate earlier prospective NOT_RUN paragraphs with final acceptance |
| [Driver](../../src/orchestration/turn.py),[turn contracts](../../src/contracts/turn.py),[read views](../../src/orchestration/read_views.py),[read contracts](../../src/contracts/read_views.py),[events](../../src/orchestration/events.py) | `_check_command/_admit/_invoke/_run_barrier/_compose/_prepare_commit/_commit/_present`;static metadata vs fresh epoch ports,barrier visibility,exception cleanup,atomic CORE+protocol and retry ordering |
| [Encounter engine](../../src/engines/encounter.py),[payloads](../../src/contracts/encounter.py),[domain rules](../../src/domain/encounter.py),[ports](../../src/orchestration/encounter.py),[registry](../../src/app/encounter_registry.py) | Exact-type dispatch,SCHEMA identities,canonical constants,consuming no-ops vs rejection,atomic HP/stamina deltas and trusted codec/reducer/admission responsibilities |
| [Client](../../src/app/client.py),[worker](../../src/app/client_worker.py),[session](../../src/app/client_session.py),[text](../../src/app/client_text.py),[client DTO](../../src/contracts/client.py) | `PlayWindow._send/_poll/_render/close`,`ClientWorker.request/_run/close/join`,`ClientSession.act/retry/load/recover`,`turn_messages`;thread ownership,immutable updates,error projection freshness,history/reset/dedup/focus/close-drain |
| [Durable owner](../../src/app/durable.py),[headless owner](../../src/app/headless.py),[SQLite](../../src/adapters/sqlite_store.py),[slots](../../src/adapters/save_slots.py),[persistence contracts](../../src/contracts/persistence.py) | Single storage owner,disk-before-memory,uncertain proof/recovery,attachment swap and failure before/after publication;random attachment tokens are boundary identity,not authoritative simulation RNG |
| [Client integration](../../tests/integration/test_client.py),[text units](../../tests/unit/test_client_text.py),[skeleton integration](../../tests/integration/test_skeleton.py),[durable integration](../../tests/integration/test_durable_turn.py),[view units](../../tests/unit/test_read_views.py),[encounter replay](../../tests/replay/test_encounter.py) | Actual normal/error/lifetime tests;inspect their surrounding helpers/callers and independent fixtures rather than assuming test count proves correctness |

All tracked `src/` and `tests/` files except `.gitkeep` are supplied as surrounding context,including replay fixtures. Relevant Phase0/CORE-02/03/04/05 source orders and independent reference vectors plus B02–05,BLOCK_01,quality/client/CI evidence and existing configs are supplied;exact inventory is the manifest. Inclusion is not a claim that every file received an exhaustive Sol audit. Unseen context or unexecuted review checks must be labeled UNVERIFIED.

## Independently checkable expectations

Expectations come from the accepted source contracts,not observed output or regenerated goldens.

- CORE-03 §4.1/§5:in-range attack `(actorHP,targetHP,stamina)=(3,5,2)` gives `(2,3,1)`;target damage2/counter1/cost1. `(1,1,1)` gives `(1,0,0)`,defeat and no counter. Rest changes only stamina `min(2,old+1)` and consumes one second even at cap. Repeat-open also consumes one second;occupied-close rejects with unchanged CORE/protocol.
- Existing Driver/protocol contracts:exact retained request returns original receipt without engine/durable reevaluation,new tick/diff/facts/cues. Same ID with different request rejects COMMAND_ID_CONFLICT;retry resolution precedes actor-death admission. Verify intended failure code and unchanged authoritative state,not merely that an exception exists.
- Phase0 §2 + current read-view implementation:all nested aliases/slices/iterators expire on close;mutation raises ReadOnlyViolation without backing change. Every same-phase engine/reducer reads pre-barrier state. Static cache must never retain epoch ports.
- CORE-05 §6–7:confirmed precommit rollback preserves old disk/memory pair;uncertain outcome must prove exact old or next without executing gameplay again,otherwise block commands/publication. Failed staged load preserves old owner/token;successful load swaps owner/token and rejects the old attachment.
- CLIENT-002 contracts:only committed facts narrate attack/counter/defeat;abort/rejection suppress supplied success facts;retry adds confirmation only;load clears displayed later history and prior retry. Worker errors replace earlier success messages/reset flag. Display retains at most200lines,each≤500characters;selection in Text does not move the player;accepted work drains before owner close. These projections/history are not persisted CORE.

## Verification / known limitations

Fresh execution2026-10-08:Windows project `.venv`Python3.13.12;PYTHONPATH=src;owned ignored pytest basetemp. Existing nine modules:exit0,116PASS57.70s,no failed/skipped cases. This is bounded regression,not the full1242-test suite or independent review. No source/test modifications.

```powershell
$env:PYTHONPATH = "$PWD/src"
New-Item -ItemType Directory -Path .pytest_cache -Force -ErrorAction Stop | Out-Null
if (-not (Test-Path -LiteralPath .pytest_cache -PathType Container)) { throw 'Pytest temporary parent is not a directory' }
.\.venv\Scripts\python.exe -m pytest -q tests/integration/test_client.py tests/unit/test_client_text.py tests/integration/test_skeleton.py tests/integration/test_durable_turn.py tests/unit/test_read_views.py tests/replay/test_golden.py tests/replay/test_trial.py tests/replay/test_encounter.py tests/replay/test_watch.py --basetemp .pytest_cache/cp01-review-20261008
```

Observed startup stderr:`Failed to find real location of C:\ReverieSaga\venv\python-3.13.12\python.exe`;tests still completed successfully. CORE-03 historical evidence also records a launcher-location diagnostic;exact environment cause not diagnosed by this documentation task. `.venv/Scripts/python.exe --version` exit0:Python3.13.12. No installation/policy change or warning suppression.

Historical evidence only:[CLIENT-002](../work_orders/RS-CLIENT-002_ACTION_LOG.md) full1242PASS283.95s/client36twice/replays45;[CI-001](../work_orders/RS-CI-001_CLEAN_RUN.md) fresh clean native1242PASS280.99s and patched-SHA remote1242PASS393.67s/all steps PASS. These are dated prior runs,not current execution or independent review. Preserve prior1241PASS/1Tcl setup error and failed clean CI evidence. Exact intermittent Tcl cause remains unproven.

Full regression,lint,format,mypy,dependency gates and manual UX are NOT_RUN in this documentation preparation unless explicitly recorded below. Final HD-2D/camera/gamepad/device/performance/packaging/release and advanced world/NPC cognition remain UNVERIFIED/deferred. The representative fixed scenario and Tk boundary harness are accepted limited scope,not a complete game. Scope/performance improvements alone are not correctness defects;route speculative future work to existing backlog items.

## Pasteable request

Please independently review RS-REVIEW-CP01 using the supplied current files and accepted source contracts. This is a correctness/lifetime/boundary/test-evidence review of the implemented representative CORE slice and provisional Tk client. Do not implement changes or introduce new architecture/product rules.

1. Trace actual command → admission → phase staging → durable COMMIT → publication → client narration. Find partial publication,stale read-port reuse,barrier leaks,incorrect retry/admission ordering or failure paths that falsely claim committed/aborted results.
2. Check encounter exact-type restrictions,stable schemas/canonical rule constants,admission priorities,consuming no-ops and atomic multi-entity deltas. Distinguish settled limited-scenario contracts from future content generalization.
3. Check SQLite/session single-worker ownership,load attachment lifetime,uncertain recovery,queued shutdown,Future exception paths and error-view/message freshness. For a suspected issue,show the concrete trigger and actual resulting state/publication/UI behavior.
4. Check fact-based Korean narration,retry dedup,load reset,unknown/abort diagnostics and bounded UI history. Consider after-COMMIT projection/presentation errors;do not infer rollback from a display error.
5. Evaluate tests against independently derived expectations and fault boundaries. Identify missing meaningful failure/lifetime integration coverage;do not request assert-count metrics,rewritten goldens or generic test duplication.
6. Return findings by severity with file/symbol/line,violated current contract,evidence or minimal reproduction,expected vs actual behavior,and bounded repair plus regression acceptance. Classify confirmed bug,maintainability issue,intentional behavior,false positive or unresolved. State whether each blocks CP01's next core/client expansion. If execution/context is unavailable,label the finding's verification limits. List what you actually inspected and ran;never claim unseen files or tests passed. If no confirmed defect is found,say so and retain residual risks.

No rights clearance,branch-protection administration,bulk imports,graphics commitment,rule/dependency/save-format changes or new provider calls are part of CP01. Return the complete answer so Sol can verify each disposition;review opinion alone cannot close the checkpoint.

## Feedback / repair

Director returned actual feedback2026-10-08:[verbatim receipt](RS-REVIEW-CP01_FEEDBACK.txt),[verification/dispositions](RS-REVIEW-CP01_DISPOSITIONS.md),[accepted bounded repair](../work_orders/RS-REVIEW-CP01_REPAIR.md). F1/F2/F3 repaired,native full1252PASS313.32s;F4 nonblocking risk linked to RS-STRUCT-001. CP01 DONE. The request body/input manifest/original ZIP identify preparation and reviewed history,not current repaired source bytes;historical forwarding/hold instructions above are superseded by this receipt. CP02/rights/graphics/GOV-03 hold unchanged;new semantics/governance/dependency/rights changes still require explicit director authority.
