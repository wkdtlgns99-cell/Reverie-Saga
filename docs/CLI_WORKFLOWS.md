# Optional CLI Workflows

Lookup only. Run from repository root in PowerShell;read the relevant section for the active task.
[Setup/play/verification](../README.md),[status/qualification](../BACKLOG.md),[Unity](../clients/unity/README.md).
Examples use fresh output paths. Existing outputs/pending files are preserved,not overwritten.

## Shared Inputs

For the approved memory game started by README:
```powershell
$env:PYTHONPATH="$PWD/src"
$taskWorking='tmp/client-harbor-memory/game.sqlite'
$taskCatalog='content/dialogue/harbor-memory-v1.json'
$taskPin=(Get-Content -LiteralPath content/dialogue/harbor-memory-v1.sha256 -Raw).Trim()
```

Use the actual displayed working path after load. Every read/preparation requires the save's original
scenario,feature and catalog pins;old saves are never upgraded/repinned. Read-only tools do not create
games,advance turns or change authoritative facts. Normal play/replay requires no live provider.

## Key Loading and Explicit Generation

Ignored local `C:/ReverieSaga/.env`:GEMINI_API_KEY primary,GEMINI_API_KEY_2/_3 manual spares.
The CLI neither auto-loads it nor rotates keys. The old tmp/gemini-api-key.txt was removed.
Load only for an explicitly authorized live job;never print keys or include them in artifacts:
```powershell
$taskGeminiEntries=@(Get-Content -LiteralPath C:\ReverieSaga\.env | Where-Object { $_ -match "^GEMINI_API_KEY=" })
if ($taskGeminiEntries.Count -ne 1) { throw "Expected one primary GEMINI_API_KEY entry" }
$env:GEMINI_API_KEY=($taskGeminiEntries[0] -split "=",2)[1].Trim()
.\.venv\Scripts\python.exe -m app.dialogue_prepare --live --free-tier-confirmed --free-data-use-confirmed --output tmp/dialogue/candidate.json
```

Use a locally qualified free-tier project/model;flags acknowledge tier and [data-use terms](https://ai.google.dev/gemini-api/terms).
No local daily call/token ceiling;shared durable accounting,60s cross-process spacing,max2attempts/job.
No billing change,paid fallback or spare-key rotation. Quota/project identity remain unmeasured here.
Generation success emits NEEDS_REVIEW,not gameplay approval;provider failures preserve the game/accepted output.

## Candidate Validation and Approval

Offline validation;then compilation only with an exact director-approved hash-bound receipt:
```powershell
.\.venv\Scripts\python.exe -m app.dialogue_prepare --candidate tmp/dialogue/candidate.json
.\.venv\Scripts\python.exe -m app.dialogue_prepare --candidate tmp/dialogue/candidate.json --receipt tmp/dialogue/approval.json --output tmp/dialogue/generated-v1.json
```

The assistant may prepare the receipt after actual approval;the director need not hand-author JSON.
Use the printed catalog SHA256 with a fresh game path. Different text requires a fresh game;
approval does not replace an existing save's catalog. The checked-in QT-F07example is offline test data;
the separately approved harbor-memory catalog has its own [lineage/decision](reviews/OPEN_WORK_CLOSURE_2026-10-14.md).

## Quest-State Context

For a quest game without memory,created with the same approved catalog:
```powershell
$taskQuestWorking='tmp/quest-context/game.sqlite'
.\.venv\Scripts\python.exe -m app.client --scenario harbor --working $taskQuestWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin
.\.venv\Scripts\python.exe -m app.npc_prepare --working $taskQuestWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin --output tmp/npc/context.json
```

Default CONTEXT_ONLY is offline. Add `--live --free-tier-confirmed --free-data-use-confirmed`
only for explicit generation after key loading. Stages1/2export acceptance knowledge;unreported defeat
is not witnessed NPC knowledge. Stage3adds the received report and one favor. This is a current-state
projection,not full episodic memory. [F08/retest evidence](reviews/GEMINI_RETEST_2026-10-14.md).

## Persisted Memory and Query Snapshots

Memory-enabled saves retain acceptance/report conversations with logical times/source event IDs.
Repeat talk/retry adds no duplicates;unreported enemy defeat is absent. Two scoped level1records,
not personality/BDI/relationship/five-level/vector cognition. Memory preparation defaults offline:
```powershell
.\.venv\Scripts\python.exe -m app.npc_memory_prepare --working $taskWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin --output tmp/npc/memory-context.json
.\.venv\Scripts\python.exe -m app.npc_memory_export --working $taskWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin --kind accepted --output tmp/npc/acceptance-query.json
.\.venv\Scripts\python.exe -m app.npc_memory_check --working $taskWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin --snapshot tmp/npc/acceptance-query.json
```

EvidenceQuery/select_evidence filter subject(actor:/quest:),kind(accepted/completion_reported),
inclusive `--since` and `--limit`0..2;newest first,ties by stable memory ID. Default preparation retains
both mandatory records. Exports are source-bound SNAPSHOTs,not approved generated content.
MEMORY_QUERY_CURRENT means consistency at check time;changed source→NPC_CONTEXT_STALE.
Modified/malformed snapshots reject without rewriting either source or artifact.

## Compare Saves

```powershell
.\.venv\Scripts\python.exe -m app.npc_memory_compare --before tmp/client-harbor-memory/slots/slot01.sqlite --after $taskWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin --output tmp/npc/memory-comparison.json
```

SNAPSHOT_COMPARISON records both source/context hashes and added/removed/retained stable IDs.
World/NPC/player/quest/catalog must match;different branches and reversed times are allowed.
Missing report in an older save is a snapshot difference,not proof of forgetting. Both sources are
rechecked before fresh publication;neither is modified. Developer CLI only,not automatic generation input.

## Preview and Generate Memory Dialogue

```powershell
.\.venv\Scripts\python.exe -m app.npc_memory_prepare --working $taskWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin --preview --output tmp/npc/dialogue-plan.json
.\.venv\Scripts\python.exe -m app.npc_memory_prepare --working $taskWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin --plan tmp/npc/dialogue-plan.json --live --free-tier-confirmed --free-data-use-confirmed --output tmp/npc/plan-candidate.json
```

Preview needs no key/network and exposes brief/context/model/request hashes. The second command
needs explicit live authorization/key loading. Edited/stale plans reject before generation;source/plan
freshness is rechecked afterward. Plan output uses preparation/v2;no-plan v1remains supported.
Omit `--live` for offline CONTEXT_ONLY;`--preview` excludes `--live`/`--plan`. Output stays NEEDS_REVIEW.

## Review and Compile Memory Dialogue

```powershell
.\.venv\Scripts\python.exe -m app.npc_dialogue_review --working $taskWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin --plan tmp/npc/dialogue-plan.json --preparation tmp/npc/plan-candidate.json --output tmp/npc/candidate-review.md
.\.venv\Scripts\python.exe -m app.npc_dialogue_compile --working $taskWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin --plan tmp/npc/dialogue-plan.json --preparation tmp/npc/plan-candidate.json --draft-approval --output tmp/npc/approval.json
```

Review is offline Korean Markdown(omit `--output` for stdout),showing four conditional lines,
observed/reported memories,fingerprints and nullable usage. Requires current matching preparation/v2;
v1/CONTEXT_ONLY/modified metadata reject. Schema/hash consistency grants no narrative approval or
provider authentication. Draft approval is PENDING with blank approved_by/approved_utc and cannot compile.
After actual director approval,set APPROVED,actual approver and actual UTC ISO8601timestamp;
preserve artifact/output/brief hashes,then:
```powershell
.\.venv\Scripts\python.exe -m app.npc_dialogue_compile --working $taskWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin --plan tmp/npc/dialogue-plan.json --preparation tmp/npc/plan-candidate.json --receipt tmp/npc/approval.json --output tmp/dialogue/memory-approved-v1.json
```

Source/plan/preparation/receipt are rechecked before exclusive publication. Result uses existing
catalog/v1;start a fresh game with its printed hash. Local approval metadata does not authenticate
human identity. No API/key/profile needed for review/compilation;`--draft-approval` excludes `--receipt`.

## Durable Diagnostic Interface

### Retained Working Saves

After load,the displayed working path may be a retained `.loaded-*.sqlite` save with real progress.
The existing eight-clone cap remains intentional;never delete a file merely because of its name.
List saved ticks/revisions and validation diagnostics without attaching,creating or deleting files:

```powershell
.\.venv\Scripts\python.exe -m app.save_inventory --working $taskWorking --quest-catalog $taskCatalog --quest-sha256 $taskPin --npc-memory
```

For non-memory quest saves,omit `--npc-memory`. For legacy/harbor/grove saves,omit the quest pair
and select the original `--scenario legacy|harbor|grove`. Wrong original pins reject;no upgrades.
`is_current` identifies only the supplied path,not which files other processes use. Each row is
a separate read-only snapshot;the list grants no deletion/ownership or later-resume guarantee.
Only exact clone names are inspected;sidecars/slots/lookalikes remain untouched. Limit:64candidates.

### Framed Commands

```powershell
.\.venv\Scripts\python.exe -m app.durable --working tmp/game.db --create
```

Fresh path only;never use `--create` to replace an existing game. This is a framed JSON-line
command/export/load/recover diagnostic,not the player UI. Keep private saves under ignored tmp/.
