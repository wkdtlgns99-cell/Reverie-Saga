# RS-CI-001 — Clean-Run CI Repair

Date:2026-10-07 (Asia/Seoul) | Order:READY | Execution:DONE | Review:Sol self-review + actual hosted CI
Authorization:director requested the next backlog item,then explicitly approved commit/upload of the pending GPT evaluation and this CI repair/evidence after local verification. No repository administration or new gameplay authority.
Baseline:main99786af93eb4efbc9940110ef568b7156e8b16bb,175 nonignored files;prior GPT review/root-document changes preserved. [Investigation](../reviews/GPT_STRUCTURAL_PLAN_REVIEW_2026-10-07.md) records remote1065PASS/177setup errors and missing .pytest_cache parent;historical local full1242PASS is not this task's verification.

## Scope / contracts

- READ:AGENTS,BACKLOG,SESSION_HANDOFF,GAME_SYSTEM_SUMMARY_KO,README,canonical quality/review policy,work-order template,GPT review,.github/workflows/checks.yml,.gitignore,pyproject.toml,ruff-quality.toml,lock,pinned pytest getbasetemp implementation,actual tmp_path/governance/client/replay tests.
- MODIFY:.github/workflows/checks.yml,README.md,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md. NEW:this order/evidence. All paths under C:/ReverieSaga.
- MUST_NOT_TOUCH:src,tests,fixtures/goldens,dependencies/lock/shared tool configs,AGENTS/canonical policy,reference repo and existing historical/review artifacts. Preserve all previous dirty work. No new checker/library,skip/xfail/assertion weakening,format rewrite or feature expansion.
- CI input:new Windows checkout,exact existing Python3.13.12/qualified locked tools;ignored .pytest_cache can be absent. Output:all existing check steps exit0,full suite including native GUI/governance/goldens,plus complete actual remote green run before DONE.
- Keep on push/pull_request/workflow_dispatch,Windows runner,20min watchdog,read-only workflow permissions,hash/RNG/UTF8/PYTHONPATH environment and every existing check command. No public/save/schema/RNG/gameplay change.
- Add an explicit pwsh step before pytest:New-Item -ItemType Directory -Path .pytest_cache -Force -ErrorAction Stop | Out-Null,then require Test-Path -LiteralPath .pytest_cache -PathType Container or throw. This only establishes the ignored parent;no recursive cleanup or test suppression. A filesystem failure or file collision must fail the step;New-Item -Force alone can silently return an existing file.
- Keep existing pytest --basetemp .pytest_cache/ci-run;it is disposable CI-owned data,not a user save/workspace root. Local evidence uses new owned directories only;never overwrite another run's files.
- Align scoped formatter with README's11 paths by adding src/app/client_text.py and tests/unit/test_client_text.py. Do not expand repository-wide formatting or reduce any gate.
- Update README local verification instructions to create the missing parent too;retain prior remote failure evidence and distinguish local qualification from remote acceptance.
- Claude checkpoints:NOT_APPLICABLE to this infrastructure-only repair;CP01 core/client expansion and CP02 reuse holds remain unchanged. RS-CI-002 main protection is out of scope.

## Execution / independently checkable acceptance

1. Fingerprint current nonignored files and inspect dirty scope. Create a new ignored native verification snapshot containing current nonignored project files only;exclude .git,venv,cache,secrets and saves. Verify copies match inputs and initial .pytest_cache is absent. Existing pinned interpreter may be used outside the snapshot;this is not GitHub-hosted verification.
2. Before repair,run the existing allowed-dag dependency node with basetemp .pytest_cache/ci-run in that clean snapshot. Expected1setup error/WinError3,not a gameplay assertion failure;record actual result.
3. Apply the small workflow/README patch. Parse embedded PowerShell,compare YAML steps/formatter paths and preservation of original gates. Validate actual fixed workflow commands from the same snapshot,not a newly invented weaker substitute.
4. Run the new preparation step and the same focused node;expected1PASS. Verify repeat preparation is idempotent and preserves a preexisting child's bytes. No owned-path recursive deletion by the harness.
5. Run both Ruff commands,11-file format,mypy --no-native-parser,both import contracts and full pytest in the clean snapshot after preparation. Existing1242 cases must all pass without skips;no new tests are required for unchanged game code. Resolve task-scoped failures without policy weakening;record environment limits separately.
6. Validate UTF8/links/diff/task and checkpoint state/protected hashes. Local pass alone leaves READY_FOR_REVIEW/remote UNVERIFIED. After explicit publication approval,commit/push only authorized files and inspect the exact-SHA actual Actions run/jobs/logs. Never rerun old workflow content and call it validation of this patch.
7. DONE requires native evidence and actual complete remote green run. Main protection requires separate authority/order;do not advance or claim it is enabled.

Normal example:missing ignored parent → preparation creates it → existing tmp_path test and full suite run. Repeated parent preparation → no file deletion/content change. Failure example:uncreatable parent → PowerShell error fails step,not a false green test result. Existing malformed/rejected-command/save tests remain unchanged.
Performance:record elapsed time;no benchmark/3s/G07/device qualification. Full-suite duration is evidence,not a new gameplay threshold. Stop for unresolved workflow semantics,unexpected input drift,new dependency/admin requirements,unrelated source changes or absent remote publication authority. Preserve safe local progress and report remaining acceptance instead of falsely marking DONE.

## Evidence / delivery

Owned native root:C:/ReverieSaga/.pytest_cache/ci001-f59afaae097f4135a5b85d187c40e7ec;baseline snapshot/snapshot and fixed snapshot/fixed-snapshot each copied176 nonignored files with matching SHA256 and initially absent .pytest_cache. Qualified existing external interpreter:C:/ReverieSaga/.venv/Scripts/python.exe,CPython3.13.12;not a fresh dependency install or hosted runner. PYTHONPATH=src/PYTHONHASHSEED=0/PYTHONUTF8=1.

| Actual check | Exit / result |
|---|---|
| Baseline allowed-dag node,--basetemp .pytest_cache/ci-run | 1;78deselected/1setup error0.09s,WinError3/absent parent |
| Initial preparation/same node in second fresh snapshot,--basetemp .pytest_cache/ci-probe | 0;1PASS/78deselected0.46s;repeat preparation preserves child bytes |
| ruff check src tests;ruff check --config ruff-quality.toml src tests;11-file ruff format --check | All0/PASS,11 already formatted |
| mypy --no-native-parser;both import CLI commands --no-cache | All0;96files,3type-inclusive+1runtime contracts kept |
| pytest -q --basetemp .pytest_cache/ci-run | 0;1242PASS280.99s,no skips;GUI/governance/goldens included |
| Final actual preparation body + same focused node,--basetemp .pytest_cache/ci-probe-final | 0;parse/absent/idempotence/child preservation/file collision PASS;1PASS/78deselected0.40s |

Boundary discovery:an added file-collision witness initially failed the harness expectation because New-Item -Force silently accepted an existing file. Repaired only the preparation step with an explicit Container postcondition,then reran all preparation cases and the focused node. Full1242 run used the initial successful parent preparation;final extra postcondition was verified separately,no test/source change. The remote final-workflow run below must validate the combined patch.
Input check:111source/test/workflow/config paths matched fixed snapshot before the postcondition-only follow-up. Scope baseline175files/HEAD99786af unchanged;only five permitted existing paths plus NEW order,prior GPT review byte-identical. StrictUTF8/fences91local links/3fragments/7docs/diff PASS before publication evidence refresh;root BACKLOG129/HANDOFF58lines. Recheck updated docs/staged paths at publication. No settings/reference/source/test/fixture/lock/policy writes or test suppression.
Publication:director explicitly approved evaluation+repair/evidence after local verification. Review29669e5 and repair8d905920408900af57c71383ca61455f0a7ab31d pushed to origin/main;remote SHA matched/tree clean,exact7paths/no saves/environment/cache/private logs. Scoped credential-pattern scan found no matches,not an exhaustive security audit. Before upload:7UTF8docs/93local links/3fragments/fences/diff/staged scope PASS.
Remote acceptance:[run37581088580](https://github.com/wkdtlgns99-cell/Reverie-Saga/actions/runs/37581088580),attempt1,push main/exactSHA8d905920408900af57c71383ca61455f0a7ab31d,completed success;[checks job112660673988](https://github.com/wkdtlgns99-cell/Reverie-Saga/actions/runs/37581088580/job/112660673988) every step success. Downloaded completed log:1242PASS393.67s,shared/selective Ruff PASS/format11/mypy96/imports3+1;actual final preparation step passed. Locked fresh install and native GUI/governance/goldens ran on windows-latest;no skips/failures. In-progress log retrieval earlier returned BlobNotFound404;completed retrieval succeeded,not a test failure.
DONE:independent parent reproduction/final boundary probes/native full/actual hosted final-workflow acceptance all passed. Old run37578176533 remains failed baseline. Main protected=false/enforcement off/empty contexts,unchanged;RS-CI-002 separately needs administration approval. CP01 TODO/CP02 DEFERRED/rights UNVERIFIED unchanged;hosted CI is not human/Claude review or release/device qualification.
Closure receipt:director subsequently authorized Antigravity fact-check/nonduplicate storage and immediate upload. This follow-up edits documents only;workflow/src/tests/fixtures/pins remain byte-identical to accepted8d90592. The automatically triggered receipt run is separate from the patch acceptance above;do not label it passed without inspection. No additional rule,feature,dependency,settings or rights change.
Closure checks:8strictUTF8docs/116local links/8fragments/fences/diff PASS;exact6document paths changed/170of176files unchanged from published8d90592,including workflow/code/tests/locks and original GPT review. BACKLOG129/HANDOFF58lines,CP states/task IDs preserved except accepted CI-001→DONE. Receipt upload is authorized;verify actual Git remote tip on resume rather than inventing a self-referential receipt SHA.
