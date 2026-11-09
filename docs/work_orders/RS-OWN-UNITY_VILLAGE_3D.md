# RS-OWN-UNITY-VILLAGE-3D — Play the Southern Lane in 3D

Primary 5 presentation, with 1 asset intake and 7 integration. Baseline `39dde489983825a214125ba85453baa2facff7eb`. The director chose Y Bot for the prototype and authorized a 3D pixel-rendered village, movement and attack effects. [Village encounter](RS-OWN-COMBAT_WORLD_FIRST.md)

Use the ordinary Unity village window and its existing Python pipe. Project only committed tiles, combat health and actor state. Keep the tile view available. Render the isolated editor scene at 320 × 180 with point filtering and leave text at editor resolution. Use the current map rows, Kenney building pieces, the local Mixamo rig, a sword model and a Kenney impact sprite. Keep raw Mixamo files in the ignored local folder with a documented setup path.

Show the player's sword motion and trail once when a new committed result decreases the bandit's health. Show the impact near the target. An initial snapshot, unchanged revision, rejected input or reopening cannot create a fresh swing. Keep the final hit visible before hiding the defeated actor. Presentation cannot advance a world turn. Release the preview camera, objects, materials and render target when closing.

Verify actual Unity import, rendering, authoritative movement and combat through the framed village process, weapon/trail/impact during a committed hit, reconnect behavior, cleanup, and the normal protected PR path. Generated world art beyond this district and additional combat rules are separate scope.
