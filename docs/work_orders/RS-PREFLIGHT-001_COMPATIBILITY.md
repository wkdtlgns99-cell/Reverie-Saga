# RS-PREFLIGHT-001 — Compatibility / Order Finalization

Date:2026-10-03 | Executor/reviewer:gpt-6.1-sol | Mode:PREFLIGHT_DOCUMENTS
Director request:step2. Production implementation NOT_STARTED. Self-review is not independent review.
Inputs:[review](../../architecture/ARCHITECTURE_REVIEW.md) AR-010/011; [Phase0 contracts](PHASE0_CONTRACTS.md); [orders](IMPLEMENTATION_ROADMAP_ORDERS.md); B09§3 and coding-order template.

## 1. Decision / Reproduction

Phase0 selects **CPython3.13.12 x64, Ruff0.16.6, mypy2.4.0, pytest9.1.1**, standard-library-only runtime. Syntax target3.12 remains the portable baseline; actual execution qualified here only on3.13.12/Windows11 AMD64 build26200. Other Python patches/OS/devices and shipping bundle UNVERIFIED. No global package updates. Exact dependency closure and artifact hashes: [selected lock evidence](PHASE0_TOOLCHAIN.json). No uv/Poetry/build backend needed for this headless phase.

Initial installed tools:Python3.13.12,Ruff0.16.6,pytest9.1.1; mypy absent. Every global Python -c/stdin invocation prints `Failed to find real location...` but executes; this environment diagnostic is retained, not a project failure suppressed by config. Default sandbox temporary directory caused WinError5 during venv/ensurepip. Direct Python urllib PyPI lookup failed DNS, including escalated attempt (cancelled,exit1). Network-enabled **pip** lookup/install succeeded through the execution service. Use task-owned writable workspace temp for venv/temp/cache when sandbox default TEMP is unusable. No auto-review rejection occurred.

Inspection environment:`C:\Reverie Saga\.preflight-20261003\venv`; disposable, removed after evidence capture. First `python -m venv` returned1 at ensurepip because TEMP permissions; environment interpreter itself existed. `python -m pip --python .preflight-20261003/venv/Scripts/python.exe install --only-binary=:all: --timeout 10 --retries 0 ruff==0.16.6 mypy==2.4.0 pytest==9.1.1 --report .preflight-20261003/install-report.json` returned0,13packages. Native wheels selected for Ruff,mypy,librt,ast-serialize; others universal. Resolve/package metadata alone is not gameplay/type/performance proof.

In P0-002 create a normal isolated `.venv` with writable task temp if required, then install **all pinned closure rows** using `python -m pip --python .venv/Scripts/python.exe install --require-hashes --only-binary=:all: -r requirements-dev.lock`; pip bootstrap25.3 observed, not runtime dependency. Pin Python interpreter explicitly; reject wrong minor/platform before lock install. Windows lock includes installed wheel hashes; include universal and verified Linux/macOS wheel hashes only if separately qualified; do not silently use sdist or invent portable wheel compatibility. Current Windows lock is sufficient for Phase0 on this workspace. Future platform qualification extends an explicit platform lock, not gameplay schemas.

## 2. Exact P0-002 Configuration

The following is the complete initial pyproject.toml content. No project packaging metadata, CI, import-linter, coverage, mutation config or Any whitelist in Phase0. Domain/API implementations and tests typed; no broad ignores. Scope-expanded roots added only when they actually exist.

```toml
[tool.ruff]
target-version = "py312"
line-length = 100
src = ["src"]
required-version = "==0.16.6"

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "E722", "S110", "S112", "BLE001", "TID251", "PLW0603", "RUF012", "B006", "ANN401"]

[tool.ruff.lint.per-file-ignores]
"src/orchestration/turn.py" = ["BLE001", "TID251"]
"src/app/*.py" = ["TID251"]
"src/orchestration/rng.py" = ["TID251"]
"src/orchestration/replay.py" = ["TID251"]
"tests/unit/*.py" = ["TID251"]
"tests/integration/*.py" = ["TID251"]
"tests/replay/*.py" = ["TID251"]

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"random".msg = "Use scoped deterministic RNG in core/engines."
"time".msg = "Use logical ticks in core/engines."
"uuid".msg = "Use canonical semantic identity in core/engines."
"os.environ".msg = "Environment belongs at app/adapter boundary."
"os.getenv".msg = "Environment belongs at app/adapter boundary."
"builtins.open".msg = "Filesystem belongs at app/adapter boundary."
"pathlib.Path.open".msg = "Filesystem belongs at app/adapter boundary."
"unittest.mock".msg = "Do not mock domain/engine outcomes."
"pytest_mock".msg = "Do not mock domain/engine outcomes."

[tool.mypy]
python_version = "3.12"
strict = true
disallow_any_explicit = true
mypy_path = "$MYPY_CONFIG_FILE_DIR/src"
explicit_package_bases = true
namespace_packages = true
files = ["src", "tests"]
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "--strict-config --strict-markers"
```

BLE001 exception is solely the driver boundary converting unexpected engine/presenter exceptions into explicit chained diagnostic/abort or committed presentation failure; it never permits swallowed exceptions. Banned APIs remain enabled for domain/contracts/engines and tests/engines. App/replay process launch and fixture I/O use declared boundary scope. TID251 cannot prove reflection/re-export safety; ownership and contamination tests remain necessary. P0-004 generic registry uses a checked cast, not Any. No disallow-any-expr promise: stdlib json has erased return types; strict recursive validation immediately narrows private I/O values without domain leakage.

Lock format:UTF8 pip requirements, one exact `name==version --hash=sha256:<wheel digest>` row per PHASE0_TOOLCHAIN packages entry,sorted normalized package name; optional comment identifies CPython3.13 WindowsAMD64. All13packages explicit, no ranges/extras/unpinned transitive. Hashes come from actual pip download report and match installed artifact selection. Root pyproject and requirements-dev.lock remain NEW until step3.

## 3. Actual Probe Evidence

Results and exact command outputs are captured in PHASE0_TOOLCHAIN.json:8 selected-tool commands + pip check passed, negative lint/type commands returned the expected1 with the required diagnostics. Every row below PASS within this inspection scope. Initial socket probe hit sandbox WinError10013; identical loopback probe passed under authorized escalation. This proves local framing feasibility, not project IPC/security/lifecycle implementation.

| Probe | Required evidence |
|---|---|
| Native versions / dependency consistency | ruff --version,mypy --version,pytest --version,pip check exit0 |
| Exact TOML and required rules | selected Ruff parses TOML; all9 mandated rule IDs enabled, baseline syntax/undefined/unused |
| Negative lint | independent fixtures trigger E722/S110/S112/BLE001/TID251/PLW0603/RUF012/B006/ANN401; no ignored unknown rule |
| Positive lint / strict types | typed frozen record/function and registered generic cast bridge pass; intentionally explicit Any,wrong int and undeclared attribute fail mypy |
| Package identity | temporary domain/contracts regular packages imported as domain/contracts under src; mypy checks same package identities |
| pytest / subprocess | selected pytest actually collects/passes fixture; subprocess UTF8/hashseed0/1 execution checked |
| stdlib | sqlite3 version3.50.4 transaction rollback; JSON duplicate/nonfinite rejection,canonical UTF8,SHA256 knownvector,loopback bind/framing; no durability/bundle qualification |

No project source/tests exist yet. Probes are throwaway compatibility examples; no test-count/gameplay/performance/release claim. Source-dependent baseline replay/type checks remain mandatory at each implementation entry.

## 4. Deferred Compatibility Matrix

These families are not Phase0 dependencies. Select exact pins/closure when their feature order enters; current planning readiness does not certify shipping compatibility. Whole-family qualification remains UNVERIFIED; vendor documentation is capability evidence only.

| Family | Decision now / actual limitation / entry gate |
|---|---|
| import-linter+grimp | Phase1 standard tool; five regular production roots from §1; pin native Windows graph/closure/licenses and exercise real layer contracts before G03 |
| coverage.py | Phase1 public engine body tracing/context native JSON evidence; pin Windows3.13 extension and meaningful registered engine inventory before G07 |
| mutmut | Async engines-only WSL/Linux; native Windows **UNSUPPORTED** by documented fork requirement. Pin actual selected release +libcst wheels +WSL/Linux Python/pytest together before weekly/phase jobs; cosmic-ray only evidence-backed alternative. No WSL installation now |
| Pydantic2/pydantic-core | No Phase0 dependency. Strict frozen adapter +restricted export subset +native3.13 wheels +license closure must pass real schema conformance in Phase1 |
| SQLite/T0 | Local sqlite3 3.50.4 exercised only basic transaction; crash/flush/locking/export/FTS Korean quality/release library bundling deferred P1SAVE |
| Godot4/GDScript | Provisional; select matching exact editor/export templates and Compatibility renderer for min-spec prototype; integer-string JSON/framing conformance and Windows native export before CLIENT |
| Launcher/IPC | Loopback TCP retained. Windows ctypes stdlib is candidate JobObject/file-lock binding (no extra runtime default); actual structures/handle rights/crash cleanup/spawn conformance selected/tested in lifecycle order; no helper skeleton now |
| PyInstaller onedir | Provisional; current official docs support Python3.8+ and platform-native builds, not project bundle proof. Pin native hooks/hiddenimports/redistribution at packaging; build Windows on Windows; smoke on clean player machine without Python |
| SD1.5+LoRA+ADetailer | Fixed pipeline; exact runner/PyTorch/CUDA/driver/model/hash/licenses and actual6GB GPU4.5GB budget sample deferred FACTORY. No assumed checkpoint/LoRA rights or toolchain install |
| GLB/glTF2/PNG/WAV/OGG | Candidate typed artifact formats retained; exact rig/unit/material/audio codecs/profiles/provider rights/import/export samples before modality production; no provider/model rights invented |

Official sources accessed2026-10-03: [CPython3.13.12](https://www.python.org/downloads/release/python-31312/), [Ruff0.16.6 metadata](https://pypi.org/project/ruff/0.16.6/), [Ruff settings](https://docs.astral.sh/ruff/settings/), [TID251](https://docs.astral.sh/ruff/rules/banned-api/), [mypy2.4.0 metadata](https://pypi.org/project/mypy/2.4.0/), [mypy config](https://mypy.readthedocs.io/en/stable/config_file.html), [pytest9.1.1](https://pypi.org/project/pytest/9.1.1/), [pytest config](https://docs.pytest.org/en/stable/reference/reference.html), [import-linter](https://pypi.org/project/import-linter/), [coverage](https://pypi.org/project/coverage/), [mutmut fork requirement](https://mutmut.readthedocs.io/en/latest/), [PyInstaller requirements](https://pyinstaller.org/en/stable/requirements.html), [Godot system requirements](https://docs.godotengine.org/en/stable/about/system_requirements.html).

Metadata/license expression for each selected package preserved in PHASE0_TOOLCHAIN. Python PSF and bundled SQLite notices checked against interpreter distributions/documentation at packaging; observed SQLite version is not redistribution clearance. MIT/BSD/Apache tool licenses from selected wheel metadata are development-tool evidence, not model/content approval. Linux/macOS/DEV-B/MIN-SPEC/bundle/performance and independent-person review UNVERIFIED.

## 5. Instruction Readiness

AR-010 closed only for qualified Phase0 subset; later family gates explicitly deferred. AR-011 Phase0 public schemas,errors,typed adapters,registry/bootstrap,canonical bytes,independent RNG/goldens,recorder/fixture and explicit edit lists settled in linked contracts/orders. All four instructions are fully authored; **execution READY** still requires step3 authorization and completed predecessors + actual source inspection at entry. No nonexistent source caller claimed verified.

B09 #6/#34 are now complete for the requested **Phase0** instructions, but remain PARTIAL for later source-specific orders. The prompt literally requires roadmap implementation orders to be Sol-ready; later DRAFT packets are not reclassified as READY. Preserve32/34 full-packet completeness and parent ARCH-002 IN_PROGRESS rather than weakening that requirement. This does not block the fully specified Phase0 sequence. Step2 acceptance:qualified subset+literal vectors+cross-doc status/link/schema checks+Sol self-review; step3 remains NOT_STARTED.

## 6. Final Evidence / Delivery

Actual `python .preflight-20261003/verify.py` returned0:19Python interface fences parse; all localdocumentlinks/fences/whitespace pass; exact13packageclosure/probeconfig hash pass; pack/UTF8/tree/protocol/fact/diff/RNG/five-step golden and self-consistent negative witness verified using a separately authored struct-based calculation;10protected primary/reference/architecture inputs retain step1 rawbytehashes; allfourordersections present; src/tests only.gitkeep and rootconfig/lock absent. Native probes8commands +pipcheck all expectedexits; rejectdiagnostics expectedexit1 are PASS evidence. Reference/source calculations are retained inside JSON artifacts for reproducibility, not installed project checkers.

Step2 edits:NEW5artifacts (thisrecord,PHASE0_WORK_ORDERS.md,PHASE0_CONTRACTS.md,PHASE0_TOOLCHAIN.json,PHASE0_REFERENCE_VECTORS.json); MODIFY5existingdocuments (roadmappacket,ARCHITECTURE_REVIEW addendum,B09,BACKLOG,SESSION_HANDOFF). Primary specs/template/activepolicy untouched. Temporary preflight environment/probes removed after evidence; pip cache may retain downloaded standard-tool wheels,globalinstalledpackages unchanged. Git diff --check0 checks trackedchanges; untrackednewdocs also checked explicitly above. Existing tracked primary/MASTER changes predate this task and were preserved.

Decision:PHASE0_PREFLIGHT_ACCEPTED; four instructions FINALIZED, execution NOT_STARTED. Later-tool/nativebundle/resource/license/modelqualification DEFERRED/UNVERIFIED at relevantentry. Current #6/#34full-roadmap readiness PARTIAL retained; no independent-person/product approval claim.
