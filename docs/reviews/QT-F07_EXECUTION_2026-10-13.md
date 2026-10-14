# QT-F07 — Local Implementation / Native Acceptance

Date:2026-10-13 | Sol execution/self-review;not independent review.
Local implementation/qualification DONE. CP05-CONTRACT accepted with verified corrections;
CP05-INTEGRATION READY_FOR_REVIEW,feedback NOT_RECEIVED. Director explicitly deferred live
Gemini qualification and requested local/Unity completion. No automatic next feature.
[Order](../work_orders/QT-F07_QUEST_DIALOGUE.md)/[contracts](../work_orders/QT-F07_QUEST_DIALOGUE_CONTRACTS.md)/
[integration request](RS-REVIEW-CP05_INTEGRATION_REQUEST.md).

## Result and Evidence

One opt-in harbor quest is wired through registered Brain rules,admission,codecs,stage reducer,
checkpoint,presentation,worker,Tk,private-pipe bridge and Unity. The Brain accepts the quest,
observes enemy defeat,requires a report and records exactly one favor. Committed facts select
four prepared Korean dialogue intents. Ordinary gameplay/replay never invokes Gemini.
Default legacy/harbor/grove and prior saves retain their earlier pins;quest content uses distinct
behavioral pins and an explicit catalog/hash. A favor is a recorded quest reward,not a wallet.

Full final regression:1437 PASS,333.03s (JUnit suite332.869s),77 more cases than entry1360.
Command: `.venv/Scripts/python.exe -m pytest -q --basetemp .pytest_cache/qt-f07-full-final --junitxml tmp/qt-f07/full-final.xml`.
Actual real-process/real-IO tests cover budget contention/restarts,owned deadline cleanup,
network-forbidden play/replay,uncertain persistence/exact retry,binding omissions,forged saves,
precommit preservation and postcommit presentation failure. The manually authored numeric
quest vector supplies state/fact expectations;the resulting durable trace is a recorder witness,
not an independently authored full-hash oracle. Existing goldens and assertions retained.

README shared Ruff and selective Ruff (`--config ruff-quality.toml`) PASS;README12-file formatter
and20 new Python files PASS;strict mypy (`--no-native-parser`)127source files PASS.
Import Linter's declared Python entry point:shared config3contracts kept/runtime config1kept,
both `--no-cache`. No new dependency,CI gate weakening or blanket lint suppression.
The exact three external IO modules have clock exceptions;CORE time prohibition is retained.

Final graphical native runs reused Unity6000.3.25f1/e1dba0a9aba4 and the existing Python
environment on this observed Windows host. Current-account permitted execution,fresh owned
working directory per case,owned helper `tmp/qt-f07/native.ps1`,five sequential runs:

| Case / final run directory under tmp/qt-f07/native | Checks | Result |
|---|---:|---|
| quest-0f403d2af7de4ab8b4926c9718821670 |14|exit0,PASS|
| legacy-df50ee31ee1c45bc963c712d2b750a97 |24|exit0,PASS;Windows build/release-hook absence|
| harbor-ed5c8688ad254331b0f7617464fb131f |11|exit0,PASS|
| grove-f4eb018f35fe44dcb7502d3bdbbf2af5 |11|exit0,PASS|
| corrupt-3ab2b7a14e614861975c5c6f9c03cc1a |1|exit0,PASS|

Total61native checks. Editor methods:ReverieSaga.PlaytestBuild.Verify for quest/harbor/grove,
BuildAndVerify for legacy,and VerifyCorrupt for corrupt. Quest checks actual acceptance/range,
goal/report/one-time reward,exact retry,gratitude,load/reconnect and loaded-branch continuity.
The final quest120-frame sample:median1.870699ms,p952.767404ms;placeholder render measurement
on this host only,not MIN-SPEC/generation latency or full-game performance qualification.
Final quest public state:tick11,stage3,reward1,actorHP1,enemyHP0. Screenshot visually inspected;
latest NPC completion dialogue is visible after the action log scrolls to the newest message.
Windows build reports89,478,576bytes;release verification hook absent. Generated verification
scene churn restored from exact entry bytes;runtime code/build evidence remains current.

Native test catalog/receipt comes from `tests/unit/quest_fixtures.py`,marked automated-test-only.
It is offline example data,not Gemini output or director approval for shipped content.
The packet includes public screenshots,performance,sanitized final state and check labels;
raw account/license logs,private databases,attachment tokens and local key file are excluded.

## Initial Failures and Repairs

The first full run had69failures/1366passes:the governance synthetic package omitted the newly
registered quest engine. Add that fixture module/import and forward/reverse independence probes;
all existing guards remain. Final full1437PASS above replaces the failed qualification result.
An initial Windows exclusive hard-link publication failed;the adapter now uses exclusive atomic
rename on Windows and exclusive hard-link publication on POSIX. Windows tests pass;POSIX runtime
qualification NOT_RUN. Initial forged-checkpoint assertions expected quest diagnostics before
canonical decoding;assert the actual earlier canonical rejection without weakening the checks.

The first new native performance instrumentation accidentally duplicated a scenario-local
variable (CS0128). Move quest timing to QuestFlow,stop only the owned failed editor,and rerun.
A first exporter call lacked PYTHONPATH;rerun with PYTHONPATH=src. Final generated wire,Python
checks and all five native cases pass. After visual inspection,the action log was changed to
scroll to new messages;all61native checks/build rerun on the final C# source. A helper exit-code
propagation issue stopped the shell after a passing quest run;explicit zero propagation and
separate remaining fresh runs completed qualification. No skip/golden update or policy relaxation.

## Deferred API and Review Boundaries

Live Gemini calls:0. Current process key was absent at the last presence-only probe. Director
will fill ignored local `C:/ReverieSaga/tmp/gemini-api-key.txt` later;empty file prepared,contents
never read or included in this packet. [Setup memo](../WORKSTATION_SETUP.md)/
[future command](../../README.md#first-quest--prepared-gemini-dialogue).
Actual free-project tier/quota,model availability,STOP response/text quality and production
approval remain UNVERIFIED. Real AI is unnecessary for the completed deterministic/local
checks;one explicit preparation/qualification job is needed later to validate the actual service
before approving its candidate for play. No per-turn API is required by this implementation.

Standalone launch,new remote CI,extracted-packet execution,other-device/native qualification,
production content approval,final HD-2D/release/human UX NOT_RUN/UNVERIFIED. Historical standalone
Windows application-control block remains. No install,account/billing change,commit/push,upload,
external review invocation,agent launch or larger quest/world/memory expansion occurred.
HEAD1ad22446d48c50b8b72a6d3af8de3c9d775134ea and prior QT-F02/CP03 work retained.
Original CP03/CP05 witnesses/ZIPs remain frozen;integration manifest separately anchors current
bytes and exact task delta against307-file entry. Actual independent integrated review remains
pending;local acceptance is not a self-issued CP05 closure.
