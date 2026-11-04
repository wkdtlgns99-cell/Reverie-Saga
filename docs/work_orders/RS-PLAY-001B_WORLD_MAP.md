# RS-PLAY-001B — In-Client World Map

READY2026-11-04;primary5,related3/7. Parent RS-PLAY-001 remains incomplete.
Baseline9fdb95e+001A dirty inputs. Read app/client.py:main,domain/world.py,
app/world_catalog.py,tests/integration/test_client.py,workstation Tk instructions.
Edit C:/ReverieSaga/src/app/client.py (MODIFY),src/app/world_client.py (NEW),
tests/integration/test_world_client.py (NEW),this order and parent progress docs only.

Contract:WorldMapFrame(parent,catalog,on_select) renders all existing continents/cities and
their road/sea connections. Selection returns an existing place ID to the owning window;
selection inspects public geography,does not travel or change any authoritative state.
Map metadata includes country livelihood/export/need,not undiscovered residents' memories.
WorldMapWindow owns a readonly catalog and Tk root. app.client --world launches it using
the fixed development catalog;legacy main behavior unchanged. Closing destroys owned root.
Paths/IO belong to app boundary;load/validation errors log and return explicit failure.
This map is the first rendering component of the eventual ordinary world play window;
it is not completed travel/time/dialogue/save acceptance. Do not add fake movement buttons.

Actual Tk tests render6continents/12cities,invoke city selection and verify selected IDs,
country details,source bytes,all12route lines and close. Invalid catalog startup fails
explicitly. Existing client tests qualify parser/routing compatibility.
Verify both Ruff configs,format touched files,strict mypy,Tk integration and existing
client regression. No shared CORE modification in this stage. No new checkpoint triggered;
native Unity and release remain unqualified. No parent completion/PR/main claim.

Current pending product gate:long-distance journey presentation/time flow,asked one question.
Read-only geography rendering is independent and may proceed while awaiting the answer.

Evidence:combined90PASS17.43s;final single-callback ownership change actualTk4PASS0.70s,
scoped Ruffboth/strict293PASS. Imports3+1PASS before the final callback-only edit. Parent
remains incomplete. Main owns root destruction after mainloop exits;WM close requests quit.
