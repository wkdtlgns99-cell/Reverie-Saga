# QT-F88 — Retained conversation-end support plans

LOCAL_ACCEPTED2026-10-29;self-review. Primary5presentation support;related2committed
facts,6retained replay,7live delivery. [Order](../work_orders/QT-F88_CONVERSATION_SUPPORT_PLAN.md).

Clean entry main4cc0004 already contains PR19merge and F82–87delivery2c15df4;the locally
stored origin/main ref agrees. Root prepublication notes were stale and are corrected.
No fresh remote read/CI/publication is claimed. Actual checkout C:/Reverie Saga;reused
installed CPython3.13.12AMD64/Tk8.6 and pinned developer tools. Git requires the command-local
safe.directory exception for this known shared checkout;no global Git settings changed.

Only npc_activity.py production changes. Its existing verified isolated replay captures
canonical supply_support_plan text alongside each conversation's existing committed
supply/patrol snapshot. Operation-local storage retains at most two tick/text pairs.
The existing formatter shares strict window validation and labels support history distinctly.
Reach-mode talk selects the prior conversation;activity shows the latest two. No new
replay,IO,persistent cache,domain outcome,flag,signature,format,pin,native or save mutation.

Independent actual vectors:talk2stock0needs2units;talk9stock2/NPC6needs adjacent arrival;
talk12stock2/NPC7can request nearby help;live14gate open does not rewrite either retained
projection. Direct/framed baseline2FAIL1.54s at absent new rows;initial implementation plus
old conversation suite21PASS17.22s. Final new18within166affected PASS126.32s,including
both real channels,read-only bytes/state,retry/rejected talk,previous-save branch/restart,
compact checkpoints,misaligned/missing/duplicate windows,corrupt trace,one real replay,
old-ready-mode exclusion,actual worker/withdrawn Tk delivery and postcommit error/recovery.
No domain result is mocked;fault injection alters only derived history or presentation.

Initial new-test attempts exposed harness/oracle issues:extra npc_cycle keyword for
already-cycle-specific APIs,a compact heading mistaken for a historical row,and tick10
expectation omitting the existing one-unit consumption. Corrected the new tests from
API contracts and existing production/use timing;no product workaround. The first18case
run was6PASS/12FAIL;next17PASS/1FAIL;the final affected run passes all18. Strict mypy initially
reported2new-test dictionary typing findings;typed bool flags resolve them without ignores.

Commands/results (repository README environment PYTHONPATH=src,PYTHONHASHSEED=0,PYTHONUTF8=1):

- `python -m pytest -q` with the eight files test_conversation_support_plan,
  test_conversation_patrol_plan,test_reach_gate_aid,test_npc_support_status,
  test_call_support_feedback,test_call_patrol_feedback,test_client,
  test_pending_query_feedback;`--basetemp .pytest_cache/f88-affected`:166PASS126.32s.
- `python -m ruff check src tests`;same with `--config ruff-quality.toml`:both PASS.
- `python -m ruff format --check` with the12README paths plus changed production/new test:
  14PASS. `python -m mypy --no-native-parser`:271files PASS using installed package directly.
- Both README import-linter commands:`pyproject.toml`3contracts and runtime1contract PASS.
  `python -m pip check`:PASS. No install/source-mode workaround needed on this host.
- Final exact CI boundary selection:`python -m pytest -q --basetemp .pytest_cache/f88-boundaries`
  with the unchanged workflow's twelve named paths/node IDs:31PASS7.02s. Includes the
  10document guards. UTF8/local-link/input/scope/index/diff checks:PASS,final-audit.json.

Paired baseline/current qualification (`tmp/qtf88/qualify.py`):default plus11older opt-in
modes,234whole updates EXACT;reach short20/long37whole updates differ only the two declared
new history prefixes(11rows each). All other output fields,core,protocol,pins and complete
SQLite dumps EXACT. Long direct talk0.961->1.006s,activity1.099->1.024s;no speedup claim.
The qualification helper's first three attempts stopped at helper-only mappingproxy,
legacy QUEST_UNAVAILABLE and float/canonical JSON issues;preserved logs distinguish them
from product failures. Final pair run exits0;baseline source bytes checked before use.

Fresh current direct/framed talk/activity from identical saved sources at9/266ticks:
all8samples below2s(max0.922823s);real output ticks10/267. Complete direct/framed updates
EXACT;source bytes and post-talk read-only/retry state preserved. This is current-host
single-sample qualification,not global latency/MIN-SPEC/device or overall performance proof.

All281entry tracked source/test inputs preserved except declared npc_activity.py;old
tests/CORE/contracts/engine/native sources unchanged. F86historical full3599PASS is reused
for unchanged shared CORE;no new full run or historical latency refresh is implied.
Native compile/editor/render/build NOT_RUN;independent,CP06,other-device/release holds remain.
No agents,dependencies,security change,commit/push/goal action or automatic next task.

Artifacts:tmp/qtf88/entry-inputs.json,npc_activity-before.py,baseline.log,initial.log,new.log,
new2.log,affected.log,mypy*.log,qualification*.log,json,pairs4,performance.json/log,
boundaries.log,final-audit.json. Only the eight declared tracked paths are delivered.

## Git upload input snapshot

Later2026-10-29human requests Git upload. All8final-delivery hashes match exactly before
publication-document edits;fetched main remains4cc0004 with0ahead/behind and empty index.
The owned codex/qt-f88-conversation-support-20261029 branch retains these changes.
This authorizes one commit/push of the8paths,not a main merge. Product inputs are unchanged;
reuse the local acceptance above and run fresh document/scope checks. Actual commit/remote
SHA and ignored tmp/qtf88/publication own the final execution evidence;no future success
is asserted in this precommit snapshot. Native/independent/device/CP06/release holds remain.
