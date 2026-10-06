# RS-DOC-002 — README Index

Status: READY; revalidate baseline before execution.
Executor/reviewer: GPT-6.1 Sol; self-review against requirements/diff/evidence.
Format: prompt **AI Documentation Format**.
Prepared order, NOT_EXECUTED. This conversion does not execute README creation or runtime work.

## Task

Execute RS-DOC-002 only in `C:\Reverie Saga`; `C:\Quilltale` read-only.
Read `docs/prompts/SOL_CODING_WORK_ORDER.md` §2.

## Baseline / Prerequisites

- RS-DOC-003 and RS-REUSE-001 artifacts exist; roles: all development Sol, Astra only when blocked.
- HEAD: `efd2478ff8a6ed93ee833c3f8464a0efdd8a181a`.
- Expected dirty paths (existing documentation; preserve):
  - `docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md`
  - `docs/MASTER_GAME_ARCHITECTURE.md`
  - `SESSION_HANDOFF.md`, `BACKLOG.md`
  - `docs/prompts/SOL_CODING_WORK_ORDER.md`
  - `architecture/V1_REUSE_INVENTORY.md`, `architecture/BLOCK_01.md`
  - `docs/reference/QUILLTALE_CONTENT_CANDIDATES.json`
  - `docs/work_orders/RS-DOC-002_README.md`
- Changed HEAD, unrelated user changes, or existing README: stop before overwrite; report evidence and refresh order only with appropriate scope.
- No new dependencies/network/Python/pytest needed.

## Reads

Root SESSION_HANDOFF/BACKLOG (RS-DOC-001/002/003/004); MASTER Current Project Overrides/§4.2; architecture prompt Current Project Overrides/AI Documentation Format/§0.B; coding order §2.
All paths relative to the workspace.

## Allowed Edit

`C:\Reverie Saga\README.md` — NEW, UTF-8; this file only.
Do not edit inputs/src/tests/architecture/.gitignore/v1/governance/backlog/handoff.

## Exact Content Contract

Title: `# Reverie Saga`. Human-facing README text stays Korean; the following literals are output data, not instruction language.
Preserve order:

1. Introduction: `AI 제작 파이프라인으로 만드는 HD-2D / 2.5D 그래픽 턴제 RPG입니다.`
2. State: `현재는 문서·설계 준비 단계입니다. 실행 가능한 게임, 런타임 테스트, 빌드 도구는 아직 없습니다.`
3. Roles: `GPT-6.1 Sol이 설계·모든 코딩·테스트·오류 수정·통합·검토를 담당합니다. Astra는 막힌 문제에 대한 조언이 필요할 때만 사용합니다.`
4. Hardware: `Ryzen 7 7735HS / RTX 4050 Laptop 6GB / RAM 16GB / NVMe 512GB.`
5. Include each exact relative link once:
   - `[세션 핸드오프](SESSION_HANDOFF.md)`
   - `[백로그](BACKLOG.md)`
   - `[아키텍처 프롬프트](docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md)`
   - `[제품 명세](docs/MASTER_GAME_ARCHITECTURE.md)`
   - `[Sol 작업 지시서 규격](docs/prompts/SOL_CODING_WORK_ORDER.md)`
   - `[v1 참고 위치](REFERENCE_REPOSITORY.txt)`
6. Read order: `현재 상태는 핸드오프·백로그에서 확인하고, 아키텍처 첫 진입 시 아키텍처 프롬프트 → 제품 명세 → docs/reference/AGENTS_v1.md 순서로 읽습니다. AGENTS_v1.md는 역사적 참고 자료입니다.`
7. Scope: `새 구현은 C:\Reverie Saga에서 진행하며 C:\Quilltale은 읽기 전용 참고 저장소입니다.`

Max45lines; small headings/lists allowed. No extra technology choices/roadmap/install commands/measured values/completion claims.
Signature/wiring/performance/data-edge policies: NOT_APPLICABLE (document index).
Missing/duplicate links are errors.

## Steps / Acceptance

1. Confirm HEAD/status/README absent.
2. Read sources; compare actual state to content contract.
3. Confirm all six targets exist.
4. Create README via apply_patch only.
5. Run checks; compare seven requirements/six unique links/line count/edit scope.
6. Report READY_FOR_REVIEW; do not commit/push or mark backlog DONE.

Normal: inputs exist, README absent → one UTF-8 file, six valid links.
Boundary:45lines allowed;46 fails; shorten without dropping requirements.
Invalid: missing target/existing README/stale HEAD/role mismatch → BLOCKED before creation.
Do not guess missing inputs or install/run code.

## Commands

PowerShell, workspace `C:\Reverie Saga`.

Baseline:
```powershell
git -c safe.directory='C:/Reverie Saga' rev-parse HEAD
git -c safe.directory='C:/Reverie Saga' status --short --branch --untracked-files=all
Test-Path -LiteralPath 'C:\Reverie Saga\README.md'
```
Expected: stated HEAD/dirty inventory; README=False.

Verification:
```powershell
git -c safe.directory='C:/Reverie Saga' diff --check
git -c safe.directory='C:/Reverie Saga' status --short --untracked-files=all
Get-Content -Raw -Encoding UTF8 -LiteralPath 'C:\Reverie Saga\README.md'
$readmeLines = Get-Content -Encoding UTF8 -LiteralPath 'C:\Reverie Saga\README.md'
if ($readmeLines.Count -gt 45) { throw 'README line limit exceeded' }
foreach ($target in @('SESSION_HANDOFF.md','BACKLOG.md','docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md','docs/MASTER_GAME_ARCHITECTURE.md','docs/prompts/SOL_CODING_WORK_ORDER.md','REFERENCE_REPOSITORY.txt')) {
    if (-not (Test-Path -LiteralPath $target)) { throw "Missing link target: $target" }
}
git -c safe.directory='C:/Reverie Saga' diff --no-index -- /dev/null README.md
```

Expected: diff --check exit0; final diff --no-index exit1 (new-file difference); other commands error-free.
Status adds README only; existing dirty diffs unchanged. Directly verify exact literals/links/line count.
pytest/coverage: NOT_RUN (documentation only).
Delivery: task/status/files/actual commands+exits+results/criteria/scope/remaining. Sol self-review, not independent acceptance.
