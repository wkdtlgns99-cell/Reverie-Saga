# CP05-CONTRACT — Verified Feedback and Corrections

Date:2026-10-13 | Feedback:PASS_WITH_CORRECTIONS,received from director attachment.
Original [feedback](RS-REVIEW-CP05_CONTRACT_FEEDBACK.txt) preserved byte-for-byte;
SHA256 e8e76cd7239e2eac3810044cfa77f09448a7d6333f042d9772c0180803a34c37.
Original contract ZIP/input witness remain frozen. Reviewer ran no tests and omitted durable
store/recovery internals,Unity/bridge/exporter,order and example. No full independent audit claim.

| Finding | Actual verification / disposition |
|---|---|
| H1 | Confirmed:pyproject layers forbid app imports from domain and IO in core. QuestDefinition validates structure in domain;harbor equality factory in app;QuestContent/QuestConsumer in contracts;compile/load in adapters. Explicit pyproject engine-independence addition is authorized task scope,not disabling a guard. Timestamp is str |
| H2 | Confirmed:current scenario protocol-only loop can skip a nonconsumer. New quest extension declares exact required role set and boot requires property on every such role before comparing pins;missing-property regression is required |
| M1 | Confirmed:turn._stage and serialization net checks restrict reads to target. Quest reducer reads stage only;QuestRules/checkpoint own HP relation. Stage1 requires living target,2/3 dead |
| M2 | Confirmed:composed delta is encoded and persisted through codec. Codec range/increasing validation;stage single-step;compose/net permitted set0→1/0→2/1→2/2→3. Forged net tests required |
| M3 | Confirmed:WatchAdmission uses actor/codec/dead/target order. Quest follows that order then range/overflow;read families and combinations declared |
| M4 | Confirmed:watch._bootstrap hardcodes bundle and RegisteredStateIO requires exactly one. Reuse helper with optional merged bundle/extra initial quest record,default unchanged;quest rules keep scenario |
| M5 | Accepted maintainability correction:pin four texts/approval hash anchors only;timestamps,usage/reviewer provenance sidecar;same content with different provenance remains compatible |
| M6 | Confirmed risk:thinking consumes output budget. Selected MINIMAL config and nullable thought-token accounting;actual endpoint/model STOP qualification remains UNVERIFIED until an explicit live job |
| M7 | Confirmed:urllib default proxy/redirects and DNS deadline gaps. Explicit handlers,owned killable/reaped transport process60s parent deadline;two attempts+60s gap TARGET180s+process overhead. OS file locks tested with real processes |
| L1 | Accepted:stage int with-1no-quest sentinel;wire uses existing decimal-string encoding |
| L2 | Confirmed:current narration falls back for unhandled facts. Explicit content parameter/quest handlers and presentation-failure checks |
| L3 | Official Gemini free-service data-use terms checked separately;no legal clearance inferred. Preparation CLI discloses limited brief/data and requires explicit free-data-use acknowledgement before live calls. No player secrets/saves/context sent |
| L4 | Reviewer model facts came from secondary guides. Sol checked official pricing/schema/model/thinking docs;account/free tier/quota and actual API remain UNVERIFIED,not a confirmed account capability |

Contracts rewritten before production implementation;H1/H2 required preconditions resolved.
The named independent numeric vector agrees with existing combat rules. Add review-specified
fault/save/replay/binding/provider cases during implementation without changing old goldens.
CP05-CONTRACT accepted for bounded implementation after contract/document checks;patch external
rereview NOT_RECEIVED. CP05-INTEGRATION stays pending before larger expansion.

Official sources:[pricing](https://ai.google.dev/gemini-api/docs/pricing),
[schema](https://ai.google.dev/gemini-api/docs/generate-content/structured-output),
[thinking](https://ai.google.dev/gemini-api/docs/thinking),
[terms](https://ai.google.dev/gemini-api/terms). Checked2026-10-13;provider change requires requalification.
