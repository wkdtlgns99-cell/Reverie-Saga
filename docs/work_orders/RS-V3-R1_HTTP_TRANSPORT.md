# RS-V3-R1 — HTTP Framing Failures Remain Retryable

Date:2026-10-16 | State:LOCAL_ACCEPTED | Executor/review:self;external partial finding R1.
Authorization:director requests local reproduction and repair if confirmed,ends current Claude review.
Primary4 AI preparation support;related7 integration. No new gameplay capability.

| Field | Contract |
|---|---|
| goal/non-goals | Classify http.client.HTTPException from the fixed-origin transport as GENERATION_TRANSIENT;retain bounded retry. No new provider,endpoint,dependency,save/CORE/wire/approval/budget policy or automatic cleanup |
| baseline | HEAD0e0657702a0bbeed04ed8d07c8826ce05a9f34cc;preserve F21/RS-DOC-005 dirty work. Owned tmp/v3-r1 entry hashes before edits |
| reads/prerequisites | Rulebook,handoff/backlog,template/setup/guide,MASTER generation failure UX;gemini_transport,gemini_dialogue,GenerationError,budget and existing adapter tests;README gates. Existing Python3.13.12 AMD64/pytest9.1.1,pip check PASS |
| allowed | MODIFY src/adapters/gemini_transport.py,BACKLOG.md,SESSION_HANDOFF.md,GAME_SYSTEM_SUMMARY_KO.md. NEW tests/adapters/test_gemini_http_framing.py,this order,docs/reviews/RS-V3-R1_EXECUTION_2026-10-16.md,docs/reviews/OPEN_WORK_V3_FINAL_PARTIAL_2026-10-16.txt,docs/reviews/OPEN_WORK_V3_FINAL_DISPOSITIONS_2026-10-16.md. Owned tmp/v3-r1,.pytest_cache/v3-r1-* |
| API/wiring | Existing fetch(bytes)->bytes;main serializes GenerationError;parent transport accepts GENERATION_TRANSIENT;GeminiDialogue retries at most once with existing budget/reservation/delay. Fixed production HTTPS origin and no proxies/redirects unchanged |
| behavior/edges | HTTPException(including BadStatusLine/IncompleteRead)→GenerationError GENERATION_TRANSIENT from None. HTTPError keeps existing status-specific branch;URLError/TimeoutError/OSError remain GENERATION_TIMEOUT. JSON/output/size/deadline/redirect errors unchanged. Owned response closes on read failure;process-control propagates |
| examples/algorithm | Local socket server sends malformed status or incomplete chunked body;before fix actual library exception escapes,after fix exact transient code. Child then returns canonical status rather than nonzero exit;real parent retries once,conservative failed-request reservation retained. Normal response remains valid;no provider/API call |
| test responsibilities | Real loopback HTTP bytes for open/read failures and recovery;subprocess main/parent route;no key/raw network text in returned error;bounded retry count/accounting and resource closure;status/timeout/process-control regressions. Only test endpoint is redirected;no production configurability |
| verification | New regression baseline must fail before repair;then affected adapters/dialogue preparation integration plus README Ruff both,format scoped,mypy,pip/import3+1,UTF8/link/diff checks. No shared CORE change:full/native not required |
| performance | Existing 60s transport deadline,one retry/60s delay,256KiB cap unchanged;loopback test waits bounded,network requests to provider0 |
| acceptance | Real malformed HTTP failure reproduced;fixed code visible through actual child/parent/retry path;affected/static checks pass;earlier dirty files preserved;three progress docs agree |
| checkpoints/stops | Current extra V3 inspection stopped at director request with PARTIAL coverage,not PASS. CP01–05 retain bounded closure;CP06 release held. Stop only for unsettled semantics/overlapping edits/unavailable required evidence after safe alternatives |
| delivery | Local fix/tests,evidence and partial-review dispositions;no commit/push/agents/live API/cleanup or independent patch-rereview claim |

Accepted:[execution](../reviews/RS-V3-R1_EXECUTION_2026-10-16.md). Real baseline framing failures
reproduced;combined225affected tests and static/scope/doc checks PASS. No independent rereview.
