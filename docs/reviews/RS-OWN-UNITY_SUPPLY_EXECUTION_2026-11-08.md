# RS-OWN-UNITY — Authored Supply Play Verification

2026-11-08. Primary 5 presentation with 2 rules, 6 persistence and 7 integration. Current Windows workstation, local self-review. [Work order](../work_orders/RS-OWN-UNITY_SUPPLY.md).

## Player flow

The separate Unity editor panel **Reverie → 보급 의뢰 플레이** follows the current `--world-knowledge` working branch. It previews the current authored line and terms. Confirming a choice calls the existing Python worker and SQLite owner. A new world starts at tick 0. Confirm a one-second wait, accept the quest, collect two crates in separate exchanges, then deliver them to the merchant. The panel displays committed status, cargo and gold. An active Python owner is reported as a lock conflict. No provider is called.

Confirmations bind the resolved working file, branch, committed revision, last core hash, offered action and terms. A superseded confirmation returns the current offer and a stale diagnostic. Replaying a confirmation after delivery or either crate collection cannot repeat the command. If a SQLite read transaction makes the write abort, the committed progress remains unchanged and the same confirmation can be retried. A confirmation cannot create missing progress. Unfinished committed speech must be completed in Python before the panel offers a command.

## Current-host Unity

Unity 6000.3.25f1 (`e1dba0a9aba4)) compiled and ran the editor window in batch mode. A temporary editor entry point opened the production window on an isolated save and drove its actual Python subprocess launcher and response polling. At each step it checked the offered Korean label and terms, then submitted the offered confirmation token. The first run committed the delivery but exposed an editor deserialization issue when the JSON had no next offer. An explicit offer-presence field fixed completion display.

The final batch exited 0 after wait, acceptance, two distinct collections and delivery at revisions 1–5. The production window projected completion, zero crates and 5 gold. Replaying the delivery token returned `WORLD_SUPPLY_STALE` and kept revision 5. The temporary entry point is outside the tracked change. Batch verification invoked the confirmed request path programmatically. Interactive clicks, modal confirmation rendering, a Windows player build and other devices were outside the measured scope.

## Python and publication

The bridge integration uses separate subprocesses and real saved knowledge worlds. It covers the whole provider-free flow, repeated confirmation, branch replacement, competing owner, read-lock failure and same-token recovery, invalid input, missing progress and unfinished speech. The existing read-only observer independently checks the persisted quest result.

The related Python regression passed 124 tests in 108.77 s. After binding the displayed terms into the token, the Unity batch ran again successfully and the focused bridge, observer and rulebook rerun passed 22 tests in 25.92 s. Both Ruff profiles, scoped formatting, strict mypy across 362 files, four import contracts, `pip check`, eight documentation links and whitespace passed. The PR records the exact final CI and main synchronization.
