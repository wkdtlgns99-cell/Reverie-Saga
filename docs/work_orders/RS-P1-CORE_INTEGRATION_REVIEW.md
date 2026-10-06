# RS-P1-CORE — Representative Slice Integration Review

Date:2026-10-06 (Asia/Seoul) | Executor/reviewer:Sol | Status:ACCEPTED/DONE

Director authorized the next review with "다음꺼 ㄱㄱ" after CORE-05 acceptance. Review the existing [parent goal](RS-P1-CORE_VERTICAL_SLICE.md#1-slice--dependency-decisions):one local space/controlled actor/legal and blocked movement/interactable obstacle/combat/autonomous delayed consequence/durable save-load/replay. Scope is this representative headless slice; graphical/client/full-game/cognition/performance qualification remains later. Self-review is not independent-person review.

## 1. Scope / Entry / Review Contract

- READ all existing production/tests/config/locks/independent vectors/architecture/specifications. HEAD/main efd2478ff8a6ed93ee833c3f8464a0efdd8a181a; preserve preexisting primary/MASTER edits and untracked prior work. Entry133source/test/design/order/config/spec hashes captured for final exact scope comparison.
- NEW this review record and tests/integration/test_core_slice.py; no runtime API/rule/save-format/engine/oracle change. MODIFY only BACKLOG.md,SESSION_HANDOFF.md and parent RS-P1-CORE_VERTICAL_SLICE.md for factual review/coverage corrections. CORE-05 acceptance remains READ as a dated predecessor snapshot. No new parent/CORE-06/dependency/checker/CI/commit/push/agent.
- Test responsibility:real bootstrap→DurableSession→same Driver→SQLite→presentation; one combined path with literal independently reasoned states,mid-combat export/load both before and after close/fresh resume,old-token rejection/exact receipt retry/no duplicate due wake,and full retained Runner replay. Filesystem outputs use pytest-owned workspace basetemp; domain engines/reducers/presenters are real,not mocks.
- Review source registration/ownership/strict pins/bounds/transaction/lifecycle and existing actual CLI/crash/negative replay tests. Refresh relevant checks and full suite/Ruff/strict types after the new integration coverage. Failures require in-scope diagnosis; old assertions/oracles remain READ. Parent DONE requires every representative goal row PASS with actual evidence; unrelated future capabilities stay explicit.

## 2. Finding / Independent Combined Scenario

IR-001 CLOSED — the thirteen-request watch main vector includes waits,Bell,one move and gate opening,but no attack or blocked movement. CORE-05 tested combat in a separate generic encounter-bundle path;the parent §19 claim that this same main trace traverses combat overstates coverage. Correct the claim and add an integrated guard using existing rules,without changing those rules or regenerating old fixtures.

Initial requirements:actor cell0/HP3/stamina2,closed gate cell4,enemy cell8/HP5,NPC cell6/bells0/replies0,charge0/future Wake2. One valid action costs one second. Wall cell1 blocks;closed gate4 blocks. Attack from7 has range1/damage2/cost1/counter1 only if enemy survives. Rest restores1. NPC increments once each even tick;Bell produces one reply;charge adds1 per second up to3. These settled prototype requirements independently give:

| Tick/revision | Action | Actor cell | Gate | Actor HP | Enemy HP | Stamina | NPC bells | Replies | Charge |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Right into wall | 0 | 0 | 3 | 5 | 2 | 0 | 0 | 1 |
| 2 | Down to3 | 3 | 0 | 3 | 5 | 2 | 1 | 0 | 2 |
| 3 | Right into closed gate | 3 | 0 | 3 | 5 | 2 | 1 | 0 | 3 |
| 4 | Open adjacent gate | 3 | 1 | 3 | 5 | 2 | 2 | 0 | 3 |
| 5 | Right to4 | 4 | 1 | 3 | 5 | 2 | 2 | 0 | 3 |
| 6 | Down to7 | 7 | 1 | 3 | 5 | 2 | 3 | 0 | 3 |
| 7 | Attack enemy;mid-combat save | 7 | 1 | 2 | 3 | 1 | 3 | 0 | 3 |
| 8 | Bell/NPC reply/due wake | 7 | 1 | 2 | 3 | 1 | 4 | 1 | 3 |
| 9 | Attack enemy | 7 | 1 | 1 | 1 | 0 | 4 | 1 | 3 |
| 9 unchanged | Exhausted attack rejected | 7 | 1 | 1 | 1 | 0 | 4 | 1 | 3 |
| 10 | Rest | 7 | 1 | 1 | 1 | 1 | 5 | 1 | 3 |
| 11 | Lethal attack;no counter | 7 | 1 | 1 | 0 | 0 | 5 | 1 | 3 |
| 12 | Move onto defeated enemy cell8 | 8 | 1 | 1 | 0 | 0 | 6 | 1 | 3 |

Full committed trace has12steps,not13;the rejected attack consumes no tick/revision/sequence/SQL step. Save at7 preserves the complete Wake8/cause/order/CORE/protocol/receipt7. Loading it after progress rewinds to7 and replaces the attachment token;retry7 adds no effects/step,and executing8..12 restores exactly the original final CORE/protocol/publications. Fresh Runner repeats and detects missing NPC facts even if state hashes are unchanged.

## 3. Verification / Decision

| Parent goal / review boundary | Actual evidence | Result |
|---|---|---|
| One local space / one controlled actor | watch bootstrap registers ten records/single actor-bound stream;real combined path stays in space:trial | PASS |
| Legal / blocked movement | Right at0 remains0/wall;Down0→3;Right at3 remains3/closed door;after open3→4→7;after defeat7→8;each valid blocked attempt commits a second | PASS |
| Interactable obstacle | At3,open adjacent gate4;explicit position/HP/stamina/clock literals through both branches | PASS |
| Small combat/status | Enemy HP5→3→1→0;actor HP3→2→1 and no lethal counter;stamina2→1→0/reject/rest1/kill0;exhausted rejection preserves pair/queue/sequence | PASS |
| Autonomous delayed consequence | Each even second emits exactly one NpcActed;Bell at8 adds one reply;future Wake8 survives save/load with its exact cause/body/order and later Wake14 persists | PASS |
| Durable save/load / retry | Save7 mid-combat;progress12;load→7,new token,old token blocked;retry7 returns retained receipt without effects;8..12 gives identical full publications/CORE/protocol;active clone closes/fresh resumes12 | PASS |
| Replay / fresh ownership | Twelve NEW commits;fresh Runner twice agrees;removing the tick8 NPC fact expectation with unchanged CORE/protocol reports one mismatch step7,$facts_hash;loaded segment Runner agrees | PASS |
| Failure / compatibility / real CLI | Refreshed full suite includes existing eight owned-process crash points,lock/release,uncertain/stale/presenter failures,strict save rejection,slots/CLI,retention/rotation and all old six goldens | PASS |
| Registration / mutation ownership | Explicit watch bundle composes qualified encounter/trial components;seven compiled nodes/disjoint declared writers/observed reads/typed deltas;one Driver head after SQL COMMIT;no production edits | PASS |

IR-001 CLOSED by a meaningful regression guard and parent §19 factual correction. Separate CORE-05 encounter compatibility remains valid;no old watch fixture/vector was regenerated to pretend it contained attack. New independently reasoned scalar states are §2's literals,not captured production output. Exact publication comparison after load is a differential durability/continuation check,not a replacement golden oracle. The negative fact case deliberately perturbs only the expected facts hash to prove the replay checks effects separately from CORE/protocol.

Actual commands/results (existing .venv,PYTEST_DISABLE_PLUGIN_AUTOLOAD=1):
- Full pytest tests --basetemp='.pytest_cache/core-review-full-20261006':1113passed in 263.97s.
- Final new test module --basetemp='.pytest_cache/core-review-typed-final':2passed in6.66s.
- Six explicitly qualified original golden nodes:6passed in3.15s.
- Ruff check src tests:exit0.
- Strict mypy src tests --no-incremental using unchanged installed mypy2.4.0 Python sources:exit0,87files.

Environment diagnosis:normal python -m mypy failed before analysis because Windows Application Control blocked compiled 6ec57f84c680d3a3778b__mypyc DLL import. The installed distribution also contains its Python .py sources. A one-off importlib MetaPathFinder for mypy/mypyc selected those existing .py files,then runpy invoked the unchanged mypy CLI with --strict --no-incremental src tests. No package/file/config/stub/rule/dependency or OS policy was changed and no blocked DLL was loaded. Initial full source-mode analysis caught a new-test comparison between Tick and WorldRevision NewTypes;the assertion was split into two comparisons to the same literal tick,retaining both conditions. Final new tests and strict source-mode analysis passed after this repair. The complete suite had already started with the logically equivalent chained assertion;the final two-case rerun confirms the final test source. Native compiled mypy invocation remains blocked in this environment;source-mode PASS is not native-DLL qualification. Existing launcher-location stderr remains non-failing.

## 4. Acceptance / Scope / Next

SELF-REVIEW ACCEPTED. All nine representative goal/boundary rows PASS. Parent RS-P1-CORE DONE for the first representative headless gameplay slice on2026-10-06;all five internal units DONE. This does not close the full MASTER gameplay/client/cognition/world requirement set. New review found no production defect requiring a gameplay/runtime change;the coverage gap and overstated trace claim are repaired.

NEW one integration test module/two parametrized cases and one review record;MODIFY only BACKLOG/SESSION_HANDOFF/parent. All production/prior tests/config/lock/fixtures/reference/spec bytes unchanged;130of133entry files identical,exact three authorized existing documentation differences. No dependency/install/CI/checker/agent/commit/push/external write. 1113tests in 263.97s (1111previous+2new),final combined2tests6.66s,six original qualified goldens3.15s,Ruff PASS,strict mypy2.4.0 installed Python-source mode87files PASS. HEAD/main remains efd2478ff8a6ed93ee833c3f8464a0efdd8a181a;preexisting primary/MASTER changes retained. Review entry Driver SHA256=f19d1ad8e97600cb547f0cc5344f0155d748721d9db914582e574b110fe7547c,SQLite-store SHA256=7dd55b81112c785c3056a494ed19e95b3fe29f9ce7a70a5440ac8e09b2defc45;both remain unchanged.

RS-P1-CORE DONE for the first representative headless slice;CORE-01/02/03/04/05 DONE. NEXT author a source-specific staged RS-P1-GOV order against actual dependency/coverage/access evidence;existing packet remains DRAFT,no wholesale eleven-gate installation. Graphical client/full world/NPC cognition/emotion/persona/BDI/memory/packages/migration transforms/performance/release remain later;ARCH-002 IN_PROGRESS/B09 #6/#34 PARTIAL. Self-review only,no independent-person/full-game qualification.

Next scope is order authoring,not GOV implementation:inspect actual sources/dependencies/coverage/access/required evidence,select the first applicable control and specify exact paths/tool compatibility/contracts/checks before READY. Client public delivery/IPC/supervision and performance qualification need their own later source-specific orders. Current save1/unsupported accepted packages/empty migration transforms/Windows directory_synced=False/physical power-loss/native hardlink/performance limits remain as CORE-05 documented.

Final delivery checks (actual exit0):four delivery/review docs validate UTF8,fence balance,53local links,Python declaration/probe syntax and trailing whitespace;new test AST/whitespace PASS. Exact133entry hash comparison gives130unchanged/three authorized delivery-doc edits;exact two additions are this record and tests/integration/test_core_slice.py. All original runtime/tests/config/lock/reference/fixture/spec bytes retained. git diff --check PASS (preexisting primary/MASTER LF→CRLF warnings only),HEAD unchanged;final Ruff PASS.

## 5. Reproduce Installed Source-mode Type Check

This one-off shell probe selects the unchanged installed Python source for mypy/mypyc;it is not a new repository helper/checker or a DLL-policy modification. All existing strict configuration still applies.

```powershell
$env:PYTHONIOENCODING='utf-8'
@'
import importlib.abc,importlib.util,importlib.metadata
from pathlib import Path
import sys,runpy
root=Path('.venv/Lib/site-packages').resolve()
class InstalledPythonSources(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] not in ('mypy','mypyc'):return None
        location=root.joinpath(*fullname.split('.'))
        if location.is_dir():
            source=location/'__init__.py'
            if source.is_file():return importlib.util.spec_from_file_location(fullname,source,submodule_search_locations=[str(location)])
        source=location.with_suffix('.py')
        if source.is_file():return importlib.util.spec_from_file_location(fullname,source)
        return None
sys.meta_path.insert(0,InstalledPythonSources())
print('Installed mypy',importlib.metadata.version('mypy'),'pure Python sources')
sys.argv=['mypy','--strict','--no-incremental','src','tests']
runpy.run_module('mypy',run_name='__main__',alter_sys=True)
'@ | .venv/Scripts/python.exe -
```
