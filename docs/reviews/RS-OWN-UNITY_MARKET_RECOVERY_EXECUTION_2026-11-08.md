# RS-OWN-UNITY-MARKET — Visible Market Recovery

2026-11-08. Primary 5 presentation with 2 simulation, 3 data, 6 persistence and 7 integration. Current Windows workstation and local self-review. [Work order](../work_orders/RS-OWN-UNITY_MARKET_RECOVERY.md).

The Unity village draws a compact shelf at the market tile and a larger shelf below the village view. Both use the existing committed market stock and capacity. The shelf uses filled and empty slots and labels the road as blocked, restored or ordinarily open. The projection omits market detail outside the local district. Supply commands, economy timing and save pins use their existing paths.

The real framed integration trace reaches the two residents, accepts, collects twice and returns to the market. At tick 30 the blocked market has 2 of 3 slots filled. Delivery at tick 31 restores the road and leaves stock at 2. The player walks away, passes through tick 39 with stock unchanged, and returns at tick 40. The real supply transfer fills the third slot. Closing and reopening the working save retains stock 3, the restored road and the single five-gold reward. The trace replays under the registered village bundle.

Pinned Unity 6000.3.25f1 compiled the production shelf and window. An isolated batch probe drove the real pipe and confirmed the editor view received blocked 2/3 at tick 30, restored 2/3 at tick 31, and restored 3/3 at tick 40 and after reconnect. Physical input and pixel appearance were outside the batch measurement. Related Python regression passed 38 tests in 51.15 s. The PR records exact protected CI and main synchronization.
