# QT-F32 — Compact Unity dialogue focus

Date:2026-10-20 | LOCAL_ACCEPTED,self-review/current Windows host only.
Primary5screen/presentation;related4context display,6state preservation,7integration.
[Contract](../work_orders/QT-F32_DIALOGUE_FOCUS.md). D2 remains OPEN;this is presentation
support for its existing NPC slice,no new NPC cognition or authoritative rule.

## Result

An always reachable 대화 크게 보기 button collapses the scrollable controls and expands
history in the existing window. 조작 화면으로 or Escape restores controls. At547x376,
normal history100px becomes250px in focus;actual full NPC report37and non-eyewitness wording
plus stock are readable without enlarging the editor. Earlier history remains scrollable.
Changing mode opens the latest history;it never creates a query/command or changes messages.

The local default is controls visible. Idempotent setters retain slot/wait/control-scroll
selection;focus survives load/reconnect and accepted in-flight responses still poll/display.
WASD/arrows are suppressed while reading,including the Escape frame. Escape is processed
before connection/failure early returns. A transport/failure status strip remains visible;
return controls expose existing recovery/reconnect. No domain/wire/save/Python changes.

## Actual verification

- Existing editor8336/Python3.13.12/Tk8.6 reused;zero editor launches/restarts,no install.
- Initial native112PASS/0FAIL. Then extended actual malformed-wire coverage for the focused
  error strip:final116PASS/0FAIL,result/retained/idle0. These repeated runs are not228distinct
  cases. Existing98assertions retained;18final focus/layout/read-only/in-flight/load/reconnect/
  transport assertions/capture guards added. Logs tmp/qt-f32/native-first.log,native-final.log.
- Actual547x376focus-player-reported and focus-error captures inspected. Full remembered
  report time/content and INVALID_REQUEST strip readable in the compact Game view.
- Real Computer Use selected the returned Unity window,used the actual mode buttons,W and
  Escape in ordinary Play on this task's own first verification save. Before focus:talk17,
  revision7,actor cell3. W while focused and Escape keep17/revision7/cell3and exact save hash;
  normal W after exiting advances18/revision8/cell0. Both button directions also observed.
  A new ordinary room started with controls visible. No GUI error/exception observed.
- Both Ruff configs,strict mypy189files,imports3+1,pip/diff and final10document guards PASS.
  Python sources/tests/config unchanged:reuse F31fresh206affected and F28full2029-case
  evidence with its restricted-environment failures/permitted reruns. New full/CI NOT_RUN.

## Windows build

The editor's new Build Windows Player(Keep Editor Open) menu calls the existing build and
assembly inspection through a destination helper. Fresh GUID output preserves previous
builds;existing CLI Build destination remains unchanged. Play-mode build attempts reject.
Actual current-source Windows build succeeded,89,487,648bytes;RELEASE_VERIFICATION_HOOK_ABSENT
confirmed by existing assembly inspection. Editor stays open in Edit mode. Output:
tmp/unity-builds/e7f404430d5c4a6fa9054a1bc0363d26/ReverieSaga.exe;tmp/qt-f32/build.log.
This is a local compilation/hook check,not portable standalone/runtime/release acceptance.

## Exact durable witnesses

Final native root:tmp/unity-verification/97f3ed4030b3425d8e55b3c1428e7061.
Six exact managed saves plus the actual-input save independently validate/replay;each has
byte-identical before/after readback,stock3and the expected persistent statement:

| Source | Tick / quest stage | Latest player statement |
|---|---|---|
| Final original |16/1|accepted2|
| Final first loaded |35/1|accepted2|
| Final second loaded |38/3|reported37|
| Final third loaded,focused in-flight wait |39/3|reported38|
| Final fourth loaded,reconnected/malformed input |35/2|accepted2|
| Final slot01 |35/2|accepted2|
| Actual UI source,first native root f58ffcffcc034df69f824950ccc410df/game.sqlite |18/1|accepted2|

Sidecars/unowned files excluded from seven-file count. Logs/probes/readback under tmp/qt-f32;
source hashes/scene restoration preserved. Scene normalized equality proved before restoring
exact entry bytes after native/build work. All35entry dirty files copied/hashed before edits.

## Scope and remaining limits

Production edits:PlayRoom rendering/input and editor build-menu reuse;other changes native
verification/docs only. Earlier work/stash/evidence preserved. No commit/push/PR/merge,
agents/provider/public distribution. CP06held,V3stoppedPARTIAL. This host's compact rendering
and input are qualified;other devices,smaller windows,MIN-SPEC,long-save,independent review,
human UX and broader NPC/relationship/economy remain open.
