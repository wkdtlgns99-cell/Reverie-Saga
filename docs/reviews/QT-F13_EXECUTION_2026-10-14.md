# QT-F13 — Preview-to-Generation Acceptance

Date:2026-10-14 | LOCAL_IMPLEMENTATION_ACCEPTED;LIVE_PLAN_GENERATION PASS.
[Order](../work_orders/QT-F13_DIALOGUE_PREVIEW_GENERATION.md). Primary4;related3/6.
Execution/self-review;independent review NOT_RUN.

## Final Behavior

Actual npc_memory_prepare --preview publishes a fresh offline PREVIEW plan containing full scoped
memory context,exact brief,and model/request fingerprints;no key/provider/reservation required.
--plan consumes only a plan matching current validated source and the canonical brief/request
configuration. Caller-edited prompts are rejected even if their self-declared brief hash is updated.
Source change,configuration change,missing/malformed/oversize/occupied artifacts reject before
provider construction/send. Source or plan changes during generation reject publication without
rolling back actual committed game state or overwriting either input. Later use still needs a
freshness check;this is not a signed approval or a lock spanning live gameplay.

memory_brief is moved unchanged to a shared pure helper;the original import is explicitly retained.
The no-plan preparation/v1 path is retained. Plan-driven output uses preparation/v2 and records
canonical plan/request hashes along with existing raw candidate/usage/source evidence.
There is no production approval,dialogue installation,authoritative memory/save change,UI/C#/art
or per-turn provider call. Both scoped mandatory memories remain in every generation brief.

## Qualification

- Initial44affected tests PASS25.52s. Final98affected tests PASS48.48s
  (tmp/qt-f13/qualified.xml/qualified.log),including27new cases and prior memory/query/export/check/
  provider-boundary regressions. Real committed stage0/2/3 sources,read-only preview,canonical
  reencoding,edited brief/model/request/evidence,preview/read race,source/plan changes after send,
  service/bad-output failures,exclusive outputs and CLI flag conflicts are covered.
- Actual GeminiDialogue with an IO-only fake transport proves emitted request hash/text match the
  preview and the existing strict response decoder/usage ledger execute;no domain outcomes mocked.
- Standalone subprocess preview and offline plan consumption run with socket/urllib audit forbidden
  and no GEMINI_API_KEY;result CONTEXT_ONLY/v2. Invalid-plan live CLI fails before key/budget checks.
- Shared/selective Ruff,5file format,strict mypy151files and imports3+1 PASS. Initial unused test
  import and indexed mutation of a readonly Mapping annotation were fixed without suppressions.
- Historical QT-F09 diagnostic context/brief hashes still match the moved helper;original artifacts
  preserved. CORE/full/native/build NOT_RUN for unchanged authoritative/client inputs;previous
  full/native evidence retained,not relabeled. No new checkpoint/reviewer/publication/dependency.

## Actual Gemini Workflow

Fresh public automated-test-only harbor memory game at tick11,acceptance@2/report@11.
Actual CLI preview created without a key;actual CLI generation used the primary.env key only,
normal shared ledger/free flags/no reset/rotation/model switch/account administration.

| Observation | Actual |
|---|---|
| status/exit |GENERATED_NEEDS_REVIEW/0 |
| model |gemini-3.5-flash-lite |
| attempts/elapsed |1/2.149seconds |
| prompt/output/total tokens |686/179/865;thought usage absent/null |
| preview bytes |3998 |
| inputs |game save and preview file bytes unchanged |
| context SHA256 |3b0c13dc5c878d69f6f06fdbae7396b350ac7319b82aefff1bcc71543e27e1c5 |
| canonical plan SHA256 |2d24be9a6d01df8151c2f48efdf78555727e61de26bbb66b585adfad263f42b3 |
| request SHA256 |32b24cc12a1c60aa43063be2d6d2a67baf35083e288dc3b52a5c4a9e0f7f4f7a |
| raw candidate SHA256 |bd944eda92c53604e2fed3f593db5daa102ca6b1f2a761273d11b467577f4657 |
| receipt |tmp/qt-f13/live-result.json |
| preview/candidate directory |tmp/qt-f13/live-e8599c2107104ccda0e6ae2301b5d2ba |

Plan/source/request/candidate fingerprints and four-intent validation PASS. Candidate wording is
still editorial NEEDS_REVIEW,not accepted gameplay content or proof of all narrative semantics.
The completion line uses 확인했다 although the evidence is only a report;editorial review should
avoid implying independent verification. No semantic acceptance or auto-approval is claimed.
Account billing/remaining provider quota remain UNVERIFIED;no pricing or free-account guarantee.
Scope/frozen-input/document checks:tmp/qt-f13/checks.json. No further task started.
