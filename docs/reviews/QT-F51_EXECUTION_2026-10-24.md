# QT-F51 — Panel readability repair receipt

Order:[panel occlusion](../work_orders/QT-F51_PANEL_OCCLUSION.md).
Status:LOCAL_ACCEPTED;bounded visual repair acceptance complete.
Baseline72c2d58plus14accepted F49/F50dirty paths;current branch reused. Self-review only.
Primary5presentation support,related4/6/7. No gameplay,Python,save/wire/content change.

## Problem and repair

Actual F50cycle-return-change.png showed bright board geometry behind dialogue text.
PlayRoom.OnGUI drew only the translucent default GUI.Box. It now draws one opaque dark
backing over the exact existing panel rectangle,then preserves the existing skin/controls/
layout. Reuses Texture2D.whiteTexture;no new per-frame texture/material allocation.
GUI.color is restored in finally before other widgets. Normal/dialogue/save-manager modes
use the same shared panel;dimensions,scrolling,input,polling and commands unchanged.

## Independent real-pixel regression

New native PanelOcclusion probe temporarily changes the actual world camera clear color
red→green,reads screen pixels after end-of-frame,and captures both images/response/history.
Uncovered pixel outside the panel must follow the background;blank panel gap at(30,80)
must stay dark and invariant. Saved view/history/file bytes,focus and camera values must
be restored. Readback texture is destroyed in finally. This is actual rendering,not a
Python source-string test or a duplicated implementation oracle.

- Before production repair:14PASS/1FAIL. Inside pixel red(0.600,0,0)→green(0,0.600,0);
  uncovered red(1,0,0)→green(0,1,0). panel_backing_blocks_world_pixels failed;RESULT/
  RETAINED/IDLE code1. Original baseline.log and red/green captures preserved.
- After repair:142PASS0FAIL;ENGINE_VERIFY_PASSED and RESULT/RETAINED/IDLE code0. Inside
  pixel identical(0.024,0.031,0.043)under both backgrounds;outside still changes red→green.
  State/history/save/camera/focus preservation guard PASS. All prior cycle/player/supply/
  call/slot/recovery/reconnect assertions retained.
- Actual642x500cycle-return-change.png inspected:all text now has dark stable background;
  board remains visible outside the panel. Existing save-manager captures also produced.

## Native/build/save evidence

Same installed pinned Unity6000.3.25f1/e1dba0a9aba4,editor31168/window3539826 retained;
zero editor launches/restarts. Owned stage-driven F51VerificationTrigger used public
Environment/EditorApplication and existing PlaytestBuild.Verify/BuildInteractive APIs.
Explicit approved harbor/catalog/memory1/work0/cycle1,private baseline/native saves.
Baseline/final/build markers split from original append-only editor log to owned logs.

Fresh same-editor Windows build:ENGINE_BUILD_PASSED bytes89489696;
RELEASE_VERIFICATION_HOOK_ABSENT and F51_BUILD_COMPLETE. Output
tmp/unity-builds/5e4cd196291a40188e28abe42c998d72/ReverieSaga.exe. The existing build routine
inspects the actual release assembly for absence of LiveVerification. No standalone launch,
public distribution,CP06release or whole human-UX acceptance claimed.

Exact9owned managed saves:validate/replay/activity/direct-talk/new-talk delta/retry and
source-byte guards PASS(readback.json). Continued-talk mean893.273ms,max1200.482ms,
not a new performance claim for this constant-cost visual repair. Original156native input
hashes unchanged through final run/build after restoring the owned scene byte-exact.
Removed temporary trigger and generated .meta;refreshed/reloaded restored scene through
observed Unity UI and left same editor open. All F49/F50Python files and frozen receipts/
orders/tests remain unchanged against entry manifest. No user saves or assets changed.

## Evidence reuse and delivery

Python inputs unchanged:reuse F50qualified243affected cases,31boundary guards,Ruff/
format/strict208/import3+1/pip evidence at that snapshot. No fresh Python regression or
new independent review claimed. New native compiler/pixel/gameplay/build/save evidence
qualifies actual changed C#and registered renderer. Final18combined-path scope/link/UTF-8/whitespace/scene/hash/cleanup checks PASS;
10document guards PASS1.62s. Progress trio synchronized;final manifest delivery.json.
Goal ACTIVE;no agents,publication or new authority. CP06held;D2and broader UX remain OPEN.


Acceptance:PASS for reproduced baseline failure,independent final pixels,actual readable
capture,registered native flow/source preservation,fresh Windows build and release-hook
exclusion,and final documentation delivery. No new independent review or release acceptance.
Goal remains ACTIVE for subsequent bounded work;publication still requires user authority.
