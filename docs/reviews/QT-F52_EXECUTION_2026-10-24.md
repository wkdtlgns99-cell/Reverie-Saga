# QT-F52 — History reading-position repair receipt

Order:[history reading](../work_orders/QT-F52_HISTORY_READING.md).
Status:LOCAL_ACCEPTED;bounded UI reading-position repair complete.
Baseline72c2d58plus18accepted F49–51dirty paths;existing branch reused,self-review only.
Primary5screen support,related4/6/7. No Python,gameplay,wire/save/content/policy change.

## Actual problem and implementation

PlayRoom.Update forced scroll.y=float.MaxValue for every nonempty response,overriding
reading position. New bounded AppendHistory detects empty/reset/tail before append. Away
from tail it preserves the offset;when trimming old messages it subtracts the removed
prefix's prior rendered height,or clamps to oldest retained content when that row/geometry
is unavailable. Existing200message cap/order unchanged. Previous-Repaint row starts are
local UI geometry for scroll restoration,not a shared authoritative-state cache. Stale
measurements clear after append and rebuild during the existing label repaint.

ShowLatestHistory and the ordinary Korean latest-history button share the local scroll
operation. The button occupies the existing history heading row;focus toggle retains its
established jump-to-tail behavior. Empty nonreset response leaves scroll alone;reset/load
clears geometry and follows the new branch. Caller/state/files/history text never mutate
from this action. Existing O(200)label rendering remains with bounded float measurements;
no extra Brain command/replay/IO for bookkeeping or button. Resize uses existing reflow;
this is not a promise of pixel stability across arbitrary window resizing.

## Real native reproduction and corrected behavior

Baseline added only layout observers/native probe before changing auto-tail behavior.
The probe fills the actual200row history through ordinary read-only activity requests,
scrolls to the middle,records top row/within-row offset,then appends another inspection.

- Baseline127PASS/1FAIL:top33second response(count2)became35second response(count4),
  offset39.25→25.2002;history_append_preserves_retained_reading_position failed.
  RESULT/RETAINED/IDLE code1;baseline.log and actual before/after captures preserved.
- Corrected153PASS0FAIL:top33second response preserved,offset39.25→40.25(within2px
  rounding tolerance). Bounded cap,evicted-top clamp,explicit latest read-only operation,
  tail-following on new output,and load/reset-to-new-branch guards all PASS. Existing
  opaque-panel/player/supply/call/save-manager/recovery/reconnect checks preserved.
- Actual native history-reading-before/after images show the retained text at the same
  position. PASSED/RESULT/RETAINED/IDLE code0. One canonical replay per activity request
  remains the existing behavior;no changes to its Python source.

## Actual button input

Same editor31168/window3539826,zero editor launches/restarts. Owned stage-driven temporary
F52VerificationTrigger uses public editor APIs with explicit approved harbor/catalog SHA,
memory1/work0/cycle1 and separate baseline/native/interactive working saves. Interactive
stage uses ordinary Play without verification runner;Computer Use selected the observed
Unity window,scrolled controls to NPC activity,and clicked its real activity button.

With scrollable actual returned history,the wheel moved to earlier supply rows. Clicking
the real 최신 기록 button moved back to the final empty-call rows,as shown in
manual-reading-before.png/manual-latest-after.png. Interactive save SHA remained identical
before/after,tick0(manual-input.json). Only read-only inspection/scroll/button input used.
Stopped that owned Play session via observed toolbar before arming same-editor build.

## Build,saved sources and delivery

Native log markers are appended to the original editor log under tmp/qtf49/unity.log;
completed baseline/final segments are preserved under tmp/qtf52/. Final source inputs
manifest156files and original scene snapshot retained. Fresh same-editor Windows build PASS89490720bytes,release verification-hook absence
PASS,F52_BUILD_COMPLETE. Output tmp/unity-builds/2edc26e86fb44d7bb8587728a0d08064/
ReverieSaga.exe(build.log). No standalone launch or release acceptance claimed.

Owned9native saves validate/replay/activity/direct-talk/new-talk delta/retry/source bytes
PASS(readback.json);continued-talk mean1308.815ms/max1834.004ms,not a performance change
claim for this UI repair. Interactive source additionally validates tick0and original bytes
after Play shutdown. Removed owned temporary trigger/.meta,restored scene byte-exact,
refreshed/reloaded through observed UI,and retained editor31168with no launch/restart.
All156native input hashes unchanged through run/build/cleanup. Earlier Python files and
receipts/orders/tests frozen against entry manifest.

Final20combined-path scope/hash/local-link/UTF-8/whitespace/scene/cleanup checks PASS;
document guards10PASS1.64s. Root progress trio synchronized;delivery.json records final
file hashes. No authoritative behavior,history persistence or unlimited buffer added.
Reuse F50/F51Python evidence only for unchanged inputs;no new full/independent/release
acceptance claimed. CP06held,D2and broader human UX/device qualification remain OPEN.


Acceptance:PASS for actual baseline reproduction,retained-row/eviction/tail/reset logic,
ordinary button input,existing native flow and state/source preservation,fresh Windows
build/release-hook exclusion,and synchronized delivery. Logical reading retention is for
stable panel geometry;unrendered/evicted rows clamp to retained history as specified.
Goal remains ACTIVE for subsequent bounded work. No publication authority inferred.
