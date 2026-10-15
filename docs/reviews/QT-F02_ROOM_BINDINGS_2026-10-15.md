# QT-F02 Room Bindings — Execution Receipt

Date:2026-10-15 | Baseline:1ad22446d48c50b8b72a6d3af8de3c9d775134ea.
Scope:[runtime order](../work_orders/QT-F02_ROOM_BINDINGS.md);self-review,not CP03 acceptance.
Current native scope:Python Brain/client and real Tk widgets. Unity unchanged/unqualified
for the courtyard. Existing Unity/CP04 results remain historical,not fresh evidence.

## Implemented

- Frozen bounded Scenario binds one player/space/door/enemy/NPC/lantern,all IDs and five
  placements;exact-type/range/uniqueness/occupancy validation precedes runtime registration.
  Legacy room and new courtyard use the same engines,admission,codecs,reducers,presenters,
  durable owner and Python client. No imported legacy mechanics or new dependency versions.
- Courtyard starts6,wall7,door2,enemy0,NPC8;all role IDs differ from the historical room.
  Tk `--scenario scenario:courtyard` selects it explicitly. Inputs/projection/Korean fact
  explanations use those roles. View/wire DTOs and Unity launch behavior remain unchanged.
- All custom bindings are included in rules fingerprints;gate/NPC schema/field bounds match
  the selected metadata. Legacy literals/pins/golden fixtures remain unchanged. Initial
  components are canonically sorted;checkpoint lookup resolves exact schema/entity identity.
- SQLite envelope/format unchanged. Caller selects matching shipped scenario on reopen;
  cross-scenario open/load rejects UNSUPPORTED_RULESET,without changing working/slot files,
  current attachment/protocol/view. No automatic scenario inference or repinning.

## Commands and evidence

Local Python3.13.12 AMD64/Tk8.6. [Environment qualification](../WORKSTATION_SETUP.md#qt-f02-current-workspace-qualification--2026-10-15):
7missing tools installed from unchanged hash-locked requirements;20exact versions/pip check
PASS. Initial sandbox pip DNS failure retained as environment history,permitted retry succeeded.
Mypy native fscache blocked with/without sandbox;strict source-mode checker from the same
installed2.4.0 package PASS106files. All964copied source/data files byte-identical;no installed
binaries/sources or OS policy changed. Python base-location warning persists with successful runs.

Independent contract outcomes:wall/living-enemy/door blockers,gate cue at(2000,0),NPC cue at
(2000,2000),combat(3,5,2)→(2,3,1)→(1,1,0),rest→(1,1,1),kill→(1,0,0),one reply per bell.
Exact retry/save/load/private branch/reopen,wrong-target and wrong-scenario state/file preservation,
reversed lexical role ordering,real worker/Tk buttons and actual SQLite uncertainty before/after
commit are exercised. Fresh processes with hashseeds0/2249326019 reopen and replay identical hashes.

| Command/check | Actual result |
|---|---|
| Initial courtyard integration | Environment temp-directory setup ERROR;documented basetemp retry gave1FAIL:unsupported scenario constructor,expected missing behavior |
| First implementation focused | 10PASS1.06s |
| Existing encounter/events/client/replay selection | 382PASS/9FAIL50.98s;old custom subclasses owning their constructors lacked newly introduced instance bindings |
| Repair of those9cases | 9PASS0.89s/249deselected;immutable legacy class defaults preserve old subclass construction;configured production registration stays explicit |
| Expanded focused suite | 35PASS6.44s;then37PASS/1teardownFAIL15.31s because PlayWindow had already destroyed its test root |
| Final focused,proper host Tk plus owned Toplevel | 38PASS12.85s,all expectations retained |
| Shared/selective Ruff | PASS |
| README format selection plus3new Python files | 15files PASS;unformatted legacy blocks preserved to avoid unrelated churn |
| Strict mypy source-mode | PASS106files |
| Import Linter shared/runtime | PASS3+1contracts |
| Frozen inputs | 69tracked Unity/archives/vectors/fixtures/candidate/lock inputs unchanged under Git newline normalization |
| Initial full regression | 1321PASS/6FAIL/3ERROR376.32s;1new legacy CellReducer subclass construction defect plus8baseline dossier representation failures |
| Affected trial/narrative/engine-pipe modules after repair | 84PASS3.93s;no assertion weakening |
| Final full regression | 1330PASS362.34s,exit0;all1330cases in one fresh full run |

Focused command:`.venv/Scripts/python.exe -m pytest -q tests/unit/test_scenario.py
tests/integration/test_scenario.py --basetemp .pytest_cache/qtf02-focused-final --tb=short`.
Full command:README parent preparation,then PYTHONPATH=tmp/qtf02/typecheck;src and
`.venv/Scripts/python.exe -m pytest -q --basetemp .pytest_cache/qtf02-full --tb=short`.
Owned local full log:tmp/qtf02/full.log;excluded from review packet/private runtime data.

Baseline dossier LF bytes/Git blob SHA7923b65eb67de2e0cc82e6249bf08a20ce6dcb4f846106ede961f9ab84e82092
failed the unchanged existing qualification. The exact LF→CRLF transform gives original approved
SHAb10e8dcab4f6d93a1f60b3e9388897ed8c40a0ea0d63a1c5a8c4a18f9e720b31. Restored only that
representation after proving the expected hash and preserving original LF bytes under ignored
tmp/qtf02/dossier-before-lf.json. Narrative fields/Git-normalized blob/qualification/witnesses
unchanged. Compiler rejection remains strict;no normalized-hash fallback added. This repair
is local clone qualification,not new provenance approval. Final full log:tmp/qtf02/full-final.log.

All119runtime/test/content/lock input hashes captured during the final run are unchanged
at delivery. Four historical review ZIPs match exact Git blob bytes;69protected tracked inputs
match under Git newline normalization. Final UTF8/local links/fragments/fences/scope/whitespace
checks PASS. [CP03 source packet](RS-REVIEW-CP03_REQUEST.md) prepared with current inputs;
feedback NOT_RECEIVED. This first runtime unit is self-accepted/DONE,parent QT-F02 IN_PROGRESS.

## Limits and next gate

This is the first bounded QT-F02 unit,not all scenario/content generalization:3x3/one wall/
one instance per role only,typed shipped definitions rather than external content packages.
No multiple targets,bigger maps,quests/NPC cognition,new rights qualification,bulk imports,
Unity courtyard native validation,human UX,release/standalone/security-policy changes.
CP03 independent review must precede further scenario/world/bulk expansion;packet/feedback
are separate from this native/self acceptance. CP05 not triggered by unchanged save format.
Pre-update stash and frozen CP02/CP04 archives/witnesses remain untouched. No commit/push.
