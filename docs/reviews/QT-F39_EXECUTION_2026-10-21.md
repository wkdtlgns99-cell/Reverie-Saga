# QT-F39 — Integrated save manager and explicit previous-slot recovery

Date:2026-10-21 | Status:LOCAL_ACCEPTED | Self-review,not independent.
Order:[QT-F39](../work_orders/QT-F39_SAVE_MANAGER_RECOVERY.md).
Primary7전체 연결;participants5화면·연출 and6저장. CP06release held.

## Implementation and ownership

Director requests work across5/6/7. Entry main d7f3217plus12modified/14new paths from
F34–38/repair;all preserved. Entry hashes and source/Unity copies are under tmp/qt-f39.
Earlier Claude patch rereview remains DEFERRED,not accepted. No agents,provider calls,
dependencies,publication,CORE/domain/content/save-format changes or old-save repinning.

Canonical slot APIs gain keyword-only previous:bool=False with exact-type validation.
Both versions use existing safe paths/validation;missing backup has its own explicit
PREVIOUS_SAVE_NOT_FOUND code. Corrupt latest never triggers automatic fallback. Previous
load reuses exclusive staged backup,prepared attachment swap,token renewal,owned cleanup
and the eight-clone limit. Sources are never overwritten by loading. Existing export
retains exactly one previous version before overwriting a valid current slot.

ClientSession preserves current output by default;previous metadata/load text identifies
its source and includes existing quest,memory comparison and saved work stock. Successful
load resets displayed history and clears old retry identity. Registered worker/private
framed-pipe requests add slot_previous_inspect and load_previous. Version1fields stay the
same;the canonical generated schema hash changes to
abac7ee67947f62f97b90e722614c5aa3566238710defc413b507ce651c00b77.
Wire.Generated.cs was produced directly by existing generate_wire;approved catalogs,
descriptors and save identities are unchanged.

Unity has a fixed save-manager toggle,slot01–08,current/previous previews,save and both
loads,with explicit private-branch/one-backup explanation. Its scrollable controls retain
busy/error guards and continue polling. Movement is suppressed while open;Escape closes
it. Dialogue focus and manager are mutually exclusive. Mode/slot survive load/reconnect.

Failure injection found that raw sqlite3.Error during prepared-attachment creation escaped
the existing cleanup catch. Added that library exception to this IO boundary;the new test
asserts unchanged live owner/head/token/source bytes and absence of leaked owned clones.
No post-swap rollback or success is fabricated.

## Python and environment evidence

New33cases in tests/integration/test_previous_slot_recovery.py cover actual current3/
previous1selection,corrupt latest refusal,explicit private restore,retry reset,source bytes,
resume,exact bool and slot ranges,missing/corrupt/hardlinked backup,busy/uncertain COMMIT,
backup/connect/preparation failure cleanup,clone cap,unattached worker guard,registered
actions,actual binary pipe stale request/attachment rejection,memory comparison and a
fresh process with original pins. Generated C#matches canonical schema output.

- First focused run:30PASS/3FAIL15.97s. Two failures were restricted os.link access denied;
  one exposed the raw SQLite preparation exception above. Originals retained;no skipped
  assertions,goldens or security changes. Fixed source qualified by full permitted run.
- Full canonical sys-capture regression,permitted host:2090PASS/6FAIL/76ERROR801.93s.
  All82nonpasses were Git provenance/checkout failures:the .git directory is owned by
  CodexSandboxOffline while permitted execution uses the director's Windows account.
  Plain git rev-parse reproduced dubious ownership;process-only exact safe.directory
  made it succeed. No global Git configuration was changed.
- Same failed modules with GIT_CONFIG_COUNT=1,GIT_CONFIG_KEY_0=safe.directory and
  GIT_CONFIG_VALUE_0=C:/Reverie Saga:117PASS161.48s/exit0. This includes all82previously
  blocked cases plus35overlapping passes. Combined full2172distinct cases qualify;the
  initial full invocation is not relabeled green. Real G07fixture verifies35registered
  bodies across8replays. No runtime/test assertions were weakened.
- Commands:python -m pytest -q --basetemp .pytest_cache/f39-full-1;then python -m pytest
  -q tests/governance/test_replay_body_coverage.py tests/integration/test_pinned_evidence_checkout.py
  --basetemp .pytest_cache/f39-git-context. PYTHONPATH=src,PYTHONHASHSEED=0,PYTHONUTF8=1.
  Logs:tmp/qt-f39/full-1.log and git-context.log. New33all passed in the full run.
- Early E-clusters were mistakenly described in progress as possible Tk initialization
  errors before final diagnostics were available. Final logs show no Tk failures;plain
  and redirected standalone Tk probes both pass8.6.15. This was an agent diagnostic
  mistake,not an environment repair or a reason to retry Tk tests.
- Shared/selective Ruff,README+new-test format13files,strict mypy193files,import contracts
  3plus runtime-cycle1,and pip check PASS. One long message line was split without changing
  its value after initial selective-lint rejection. No dependency/configuration changes.

## Native and delivery qualification

Reused existing editor6000.3.25f1/e1dba0a9aba4,PID3652;no editor launch/restart,installation
or login change. Computer-use skill invoked the existing public Verify Current Selection
menu. Fresh root:tmp/unity-verification/4fec6e862adc4a84b046f8429466511d. Source log remains
tmp/qt-f38/native-editor.log;the F39offset and filtered new lines are preserved separately
in tmp/qt-f39/native-log-start.json and native-current.log.

170native PASS/0FAIL;result,retained and idle codes all0. This includes prior148checks and
22new manager/preservation/capture checks:missing backup,selection/busy/no duplicate,
previous35/current36/live37,corrupt latest refusal,explicit previous35private load,
unchanged corrupt/latest/previous/former working bytes,retry NO_RETRY,wait36/save08,
new Brain PID with original memory/work pins,normal08load,mode/selection persistence and
mutual exclusion. Only the run-owned deliberately damaged slot07fixture was restored to
its original36bytes after checking that gameplay recovery had not modified it.

Inspected actual642x500save-manager-preview,save-manager-actions and save-manager-restored
PNGs under that root/evidence. All action buttons fit;scroll reveals private-branch and
one-backup text. Current36/slot08and load/reset text are readable. Comparison lines remain
independently scrollable. These are scoped display checks,not final art or human UX signoff.

Then entered ordinary Play in the same editor,without a verification runner. Actual W
while manager open preserved tick16and working SHA;Escape closed it;W then moved cell3→0
and committed tick17. Actual mouse selected07and pressed previous info;history scrolling
showed previous35/revision17and current17/saved35comparison,with unchanged working SHA.
tmp/qt-f39/manual-input.json records these observations and byte guards. Stopped Play;
the editor remains open. This is actual Windows keyboard input,not a simulated callback.

Final12exact managed saves (game,six retained private branches,five current/previous slot
files) independently validate under the unchanged work bundle,replay,compare memory and
preserve every byte. Previous07=35,current07=36,slot08=36;manual fixture game=17. Lock
sidecars/unowned names excluded. tmp/qt-f39/native-readbacks.json;owned script readbacks.py.

Public Build Windows Player menu on the same editor completed:
RELEASE_VERIFICATION_HOOK_ABSENT and ENGINE_BUILD_PASSED bytes=89488672.
Output:tmp/unity-builds/996f895c87c44606a97800b9d34bf3fd/ReverieSaga.exe.
Executable and managed assembly presence/SHA retained in tmp/qt-f39/build-artifacts.json;
build-current.log contains fresh markers only. No extra editor/build-only copy required.

Generated PlayRoom.unity restored byte-exact from task entry after idle/build. Entry hash
comparison verifies unchanged CORE/content/descriptors and prior client.py,tests/client,
npc_memory_compare.py and old tests. Both frozen Claude ZIP hashes still match their
recorded F34–36and repair witnesses. Final delivery status/docs/whitespace and scope checks
are recorded under tmp/qt-f39/final-verification.json.

This completes the bounded connected save-management/recovery flow across5/6/7locally.
Final art/engine,human UX,other-device/MIN-SPEC and standalone backend packaging/crash/
release acceptance remain separate;CP06held. No new remote CI,independent review,commit,
push,PR,merge or automatic next task. Earlier repair rereview remains DEFERRED.
