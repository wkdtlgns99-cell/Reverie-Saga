# RS-PLAY-001D — World Clock and Pause

READY2026-11-04;self-review;primary2,related5/6/7. Parent RS-PLAY-001 remains active.
Baseline9fdb95e+001A-Cdirty inputs. Read shared turn driver (strict positive integral seconds,
simulation max16seconds),world registry/worker/client,MASTER D04/D05,workstation Tk setup.

Allowed NEW under C:/ReverieSaga:src/app/world_time.py,src/contracts/world_time.py,
src/engines/world_time.py,src/orchestration/world_time.py,src/app/world_time_registry.py,
tests/unit/test_world_time.py,tests/integration/test_world_time.py;MODIFY world_worker.py,
world_client.py,world_session.py and scoped world tests/progress docs. No shared kernel change.

Clock precision:existing CORE integer-second logical time. UI counts monotonic elapsed
nanoseconds outside CORE and carries fractional slow-idle accrual within the live session;
10_000_000_000real ns produce1game second. Visible/committed game time is whole seconds.
Subsecond derived carry resets on application restart/load;it is not an authoritative saved
fractional clock. This is an explicit precision choice,not a claim of fractional persistence.
Normal action duration comes from typed admission;its processing interval contributes no
additional idle charge. Reading/typing/idle/map/inventory share slow mode. ESC and AI-wait
contribute zero. Modes are mutually exclusive;sample old mode before transition.

Accumulator exact nonnegative integer timestamp inputs,monotonic check,unknown mode rejected.
Sample/reserve pending seconds at most16per request;restore reservation on rejected/failed
precommit wait rather than dropping elapsed time. No live clock read in deterministic CORE.
Typed WorldWait(seconds)1..16 -> existing admitted target=start+seconds;TimePassed fact/cue;
no location change. World time feature merges with registered foot bundle,distinct pins.
Old shipped modes untouched;no implicit migration. Use new default world-time working path.

UI owns clock and100ms timer. Worker owns durable command submission. Polling/close/pause
remain functional on failure. Ordinary save/load IO is not provider waiting;account slow idle
while requests are pending where no physical action is already counted. Load resets derived
timer epoch/carry to loaded timeline. No hidden catch-up for app shutdown. Background-window
and combat-specific time behavior remain unsettled and are not silently declared complete.

Examples:20real seconds idle=>2game seconds;5idle+20paused+5idle=>1game second;
10seconds AI wait=>0;action1second then20real seconds think=>3game seconds total.
Tests exact boundary/remainder/monotonic/mode/failed reservation,actual wait COMMIT/replay/
restart,real Tk ESC/map/inventory,failed wait/recovery. Full regression at parent delivery.
Performance TARGETUI timer nonblocking100ms cadence,measure actual scoped runtime not LLM.
Checks Ruffboth/format/strict types/imports/scoped integration. Existing native/release holds
remain;no new checkpoint triggered by this bounded integration. No completion/publication claim.

Backend evidence:combined73PASS4.25s,all-sourceRuffboth/strict310PASS,format8/import3+1PASS.
Initial simulation registration lacked system ownership/pinned policy definitions;fixed
feature metadata,no shared checks changed. UI/worker timing integration remains next work.


Current GUI evidence:recorded134PASS20.17s before final pending-resume guard;after guard,
actualTk12PASS3.17s,strict310/Ruffboth/format3/import3+1PASS. Tests drive real timer/ESC/map,
controlled boundary clock samples,actual SQLite postcommit/recovery IO failure,stable-key
retry and deferred-input preservation. No domain outcomes mocked. Request acknowledgement
is retained at the app owner until resolved;unknown commit is never treated as an absent wait.
AI waiting tested through lifecycle hook,not a live provider. Inventory remains unimplemented
until authoritative inventory state exists;do not claim all D04/D05/parent acceptance.
