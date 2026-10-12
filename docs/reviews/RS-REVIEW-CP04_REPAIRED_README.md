# CP04 Repaired Review / Reproduction

Current repair source is separate from original CP04 witness/archive. RS-REVIEW-CP04_REPAIRED_INPUTS.json
hashes current byte snapshots;historical CP01/02/04 witnesses in this archive are context,not current-file hashes.
All source/tests,8replay fixtures,6reference-vector JSONs,engineering enforcement and20pin lock included.
Baseline proof records114pre-Unity source/test/fixture/vector/lock files byte-identical in Git blobs.
Independent reviewer source claims/partial execution limits retained;Sol repair/native evidence is separate.

Prerequisites:Windows x64 CPython3.13.12 with stdlib tkinter/Tk;install exact locked tool closure:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
$env:PYTHONPATH="$PWD/src"
New-Item -ItemType Directory .pytest_cache -Force | Out-Null
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/packet-run
```

import-linter is in the lock;Linux/headless/noTk and arbitrary tool versions are not the claimed
native reproduction environment. Unity editor/license is needed only for the separate graphical
commands in clients/unity/README;Python suite needs no Unity install/provider/network fetch.
Current development environment reused for extracted-packet run,not falsely claimed fresh interpreter install.

Source repair diff is available from Git baseline36ebc5e to repaired publication;baseline proof
and current witness are in docs/reviews. Corpus320entries remain unqualified,CP03/bulk/standalone
OS launch limits unchanged. Current CP04 disposition closes only this reviewed prototype scope.
