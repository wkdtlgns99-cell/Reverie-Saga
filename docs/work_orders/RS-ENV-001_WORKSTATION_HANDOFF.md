# RS-ENV-001 — Workstation Setup Routing

Date:2026-10-12 | State:DONE / document routing | Executor:Sol | Review:self-review/document acceptance.
Baseline:63670be2ad551ae364ac2f08c4f6c9bc00deabce,clean main. Director explicitly
requests per-computer installation notes,discovery/install on task entry,and publication.

Goal:make approved task prerequisites discoverable on both computers;distinguish source
delivery from local installation and per-device runtime qualification.
Non-goals:install on an inaccessible second computer,change runtime/locks/engine selection,
copy accounts/saves,relax OS policy,run the next feature or alter frozen review snapshots.
Prerequisites:accepted RS-CLIENT-003/CP04 prototype;actual local tool paths/version probes.
Reads:AGENTS,ENGINEERING_RULES,SESSION_HANDOFF,BACKLOG,GAME_SYSTEM_SUMMARY_KO,README,
clients/unity/README,ProjectSettings/ProjectVersion.txt,BrainConnection,requirements-dev.lock,
.gitignore,SOL_CODING_WORK_ORDER;official agent discovery/Unity/Python documentation.

Allowed MODIFY:C:/ReverieSaga/AGENTS.md;BACKLOG.md;SESSION_HANDOFF.md;
GAME_SYSTEM_SUMMARY_KO.md;README.md;clients/unity/README.md.
Allowed NEW:C:/ReverieSaga/docs/WORKSTATION_SETUP.md;this order.
Forbidden:other source/tests/locks/reference files,private configuration,old witnesses/ZIPs.

Contract/callers:AGENTS task entry routes to one workstation setup document;BACKLOG/handoff
and both READMEs link it. Read-only chat/document tasks require no editor installation.
Behavior:read current task requirements;discover existing local installations;reuse correct
versions;install missing approved task-required prerequisites;verify before dependent work.
Director authorization covers that prerequisite setup,not engine/version upgrades or paid purchases.
Edge policy:unknown machine identity/status stays UNVERIFIED;missing executable is not PASS;
authentication requires the director's own login;empty CLI inventory is not proof of no editor;
preserve dirty files/existing environments/private saves. Missing semantics outside this scope
require a separate order. Types/formulas/units/ties:NOT_APPLICABLE,document routing only.
Examples:second computer with source but no Unity => discover/install pinned editor for Unity work;
matching installed editor at another path => reuse path;documentation only => no Unity install;
editor PASS on first computer => second computer runtime remains UNVERIFIED.
Steps:create canonical setup notes;wire entry and consumers;qualify current observations;
sync task/handoff/Korean companion;document checks;publish through protected PR/checks.
Performance:NOT_APPLICABLE,no runtime change or new device benchmark.
Baseline commands:git status --short (clean);Python version/Tk and editor/CLI version probes.
Verification:UTF8/local links/fences/scope/git diff --check;existing entry/rulebook document
guards only. No new tests or local full regression for document-only changes.
Test responsibilities:existing tests/unit/test_engineering_rules.py document guard nodes;
second-device installation/native tests NOT_RUN because this session cannot access that device.
Acceptance:all six consumers route;versions/publisher sources and Git/local split explicit;
per-device status truthful;bounded installation authority recorded;document guards PASS;
backlog/handoff/Korean companion synced;protected-main publication completed.
Claude checkpoints:NOT_APPLICABLE,no new gameplay/content/engine integration or contract change.
Stop conditions:unrelated overlapping edits or unavailable protected publication;report evidence.
Delivery:brief Korean result,actual checks/limits;explicit current request authorizes commit/push/PR merge.

## Acceptance Receipt

Eight scoped documents:strict UTF8/local links/fragments/fences and six consumer links PASS;
AGENTS remains below40lines;git diff --check PASS. Existing document guard nodes:
5PASS0.06s. Python3.13.12 AMD64/Tk8.6,editor file version6000.3.25.14801824,
CLI1.0.0-beta.13 re-probed;permitted license status success/active/signedIn=true.
Initial sandbox account probes failed;read-only permitted retries succeeded without reinstall.
Source/tests/locks/frozen archives unchanged. Local full regression/native Unity rerun NOT_RUN:
document-only changes use document acceptance;prior CP04 evidence remains historical.
Named second-device setup/qualification NOT_RUN/UNVERIFIED. Git publication follows the
protected PR/required-checks path under current director authorization;remote result is in
the PR/checks and delivery,not invented as a pre-publication result in this file.
