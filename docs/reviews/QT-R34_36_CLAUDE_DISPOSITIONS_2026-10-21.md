# QT-R34–36 — Claude findings and repair dispositions

Date:2026-10-21 | Status:LOCAL_ACCEPTED | Independent patch rereview pending.
Order:[repair scope](../work_orders/QT-R34_36_CLAUDE_REPAIR.md).
Primary5screen/input support;related2/4/6. Producer repair review:self;patch rereview pending.

## Received feedback

Director pasted Claude's independent F34–36review in this chat. Reviewed frozen snapshot:
tmp/reviews/CLAUDE_QT-F34-F36_20261021T114827Z.zip,
SHA2565c84e5879d78bca0904e60bbdf21942248307e5a45c8ce7395a6f727a0befb8e.
Reviewer reported no P0/P1,one P2and three P3findings. Linux Xvfb Python3.12.3/Tk8.6.14:
exact affected selection65PASS/1FAIL due to missing bundled F07JSON;both smokes PASS.
After installing missing Ruff,rulebook failures disappeared. Initial41ERRORdid not recur;
cause remains unconfirmed. Windows3.13.12native,pinned lint/types/imports,full suite and
Unity were NOT_RUN. This is scoped external feedback,not overall release acceptance.

| Finding | Independent qualification / disposition |
|---|---|
| P2:untracked F35/F36smokes only | Confirmed coverage gap:CI full suite would not detect removal of these controls. Promoted meaningful native invariants to13tracked real-Tk tests in test_client.py:readonly/latest/follow/pending identity,compact geometry,Return1/4/16,keypad callback,invalid/empty/range preservation,outside-field no-op and205-repeat flood. Supersedes earlier low-impact-test choice;no test deletion/skips or domain mocks |
| P3:keypad Enter binding absent | Confirmed source omission and Linux reviewer reproduction. Add KP_Enterbinding to existing _send(wait). Initial Windows synthetic probe did nothing even after binding. Further probe explicitly returned TclError:no keycode for keysym KP_Enter;thus absence of a Windows synthetic event is an environment limit,not evidence that an actual physical key failed. Tracked test uses actual registered Tcl callback on Windows and actual KP_Enterevent elsewhere;physical Windows keypad NOT_RUN. Ordinary Return real events PASS |
| P3:invalid Return log flood | Confirmed Windows:205blank events replaced every200retained line with one unique error. Preserve same visible status/text but append only if preceding retained line does not already end with the exact INVALID_INPUTmessage. Real intervening output allows a new error record. No gameplay,canonical parser/range,retry or save behavior changed |
| P3:button consumes history height | Confirmed Windows:heading39px vs label19px. Compact History.TButton uses TkDefaultFont,padding0,border0;heading now19px,so original label determines row height. Mapped geometry regression asserts equality,not font-specific pixel constants. Ordinary buttons unchanged |
| Bundle missing QT-F07_DIALOGUE_EXAMPLE.json | Confirmed packaging defect;fixture exists in source(826bytes)but was absent from original ZIP. Include it in new packet and qualify the exact review command using the packet files |

## Other reviewer observations

- Restore explicit game-seconds label with Enter hint. No timing semantic change.
- Held Return after a completed request may submit another wait. No hardware key-repeat
  reproduction from the reviewer;current busy guard intentionally covers pending requests.
  No new debounce/held-key policy is introduced or promised.
- int parsing of1_6,+3,full-width16is existing behavior,outside this repair;unchanged.
- Wrapped-line alignment is F34's documented logical-record limit;not a pixel-preservation
  defect. Readonly button while busy is intentional and now tracked by a regression.
- Tiny-window history collapse predates F35according to baseline comparison;broader responsive
  layout/human UX remains outside this repair. No claim of final small-screen qualification.

## Producer verification on current Windows host

Reused installed CPython3.13.12/Tk8.6;no installs,policy changes,Unity or agents.
Actual mapped baseline probe:heading39/label19;compact trial19;blank flood200lines/1unique,
original gameplay lost. New tests before repair:3FAIL/10PASS6.01s. Two failures establish
layout/flood defects;the keypad failure was later classified as synthetic-event limitation.
First repaired run12PASS/1keypad synthetic failure5.72s;replaced invalid platform injection
with registered callback verification,without skipping its actual command/busy assertions.
Final focused repair suite13PASS5.82s. A long translated label initially exceeded selective
lint width;scoped formatter repaired it,no suppression.

Affected native selection:
`python -m pytest -q tests/integration/test_client.py tests/unit/test_client_text.py tests/integration/test_npc_self_activity.py tests/integration/test_npc_work_inspection.py tests/integration/test_recent_memory_clients.py tests/unit/test_engineering_rules.py --basetemp .pytest_cache/r34-36-affected`

120PASS51.60s/exit0. Covers F34reading/load and F37status context along with repair callers.
Shared/selective Ruff PASS;README scoped format12PASS;mypy190PASS;type-inclusive import
contracts3PASS/runtime1PASS. No new full suite because CORE/runtime authority unchanged.

## Delivery / remaining limits

Keep F34–37changes and original ZIP/evidence intact. Fresh packet includes HEAD and reviewed
baselines,repair/full dirty patches,source/file hashes,actual dispositions and missing fixture.
Packet-stage verification used the copied source/tests/config/fixture with the existing
pinned interpreter and the original exact3-file review selection. First attempt omitted
README's explicit pytest temporary-parent preparation:25PASS/54setup errors,all naming the
missing .pytest_cacheparent. Created that owned parent per README;unchanged packet inputs
then79PASS22.59s/exit0 with fresh .pytest_cache/packet-review-final. The missing F07fixture
failure is resolved;the exact test that previously failed in Claude's bundle now passes.
Final packet source hashes retain these qualified production/test/content bytes;only
delivery docs/request/evidence metadata refresh afterward. No passing claim for the first
setup-failed attempt. Final document guards10PASS1.41s,diff whitespace and UTF-8 PASS.
These are producer repairs,not independent patch acceptance. Physical Windows keypad,
Linux rerun,hardware key repeat,other devices,full suite,Unity and release NOT_RUN.
D2OPEN;CP06held. No commit,push,PR,merge,external send or provider call.
