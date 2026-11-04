# RS-PLAY-001 — World and Social Gameplay

Status:IN_PROGRESS / child orders own executable contracts;not runtime acceptance. Executor:self-review.
Authority:direct director instruction2026-11-04 supersedes planning-only and main-merge holds.
Primary7end-to-end gameplay;related2/3/4/5/6. Parent objective:implement all confirmed D01-D07,
not just one helper,documentation change or isolated demonstration.

## Playable exit and acceptance

| Contract | Required observable behavior |
|---|---|
| D01 | New game establishes an inspectable connected world framework before local play;not a starting-room-only world |
| D02 | Travel elaborates smaller places/local definitions without contradicting established geography/history;return/restart preserves identity |
| D03 | Ordinary residents follow stored-data routines;relevant events change activity. Distant aggregate developments and nearby individual behavior remain consistent |
| D04 | Movement,interaction and each utterance advance their in-world duration;idle/read/think/type accrue real-time1/10. AI waiting contributes zero;no overlapping charge |
| D05 | ESC explicit pause freezes advancement;inventory/map remain at1/10 |
| D06 | Free-text negotiation exposes supported concrete action terms;explicit confirmation revalidates and executes. Refusal/no confirmation makes no transaction |
| D07 | Delivered speech can cause contextual NPC response/memory without another confirmation;heard claims,beliefs and objective truth remain distinct |
| Integrated proof | Ordinary graphical entry,not a script-only demo;map/travel/routines/free conversation/confirmation/save/load/restart. Real provider qualification,controlled error/retry/cancel paths and deterministic accepted-content replay |
| Delivery | Director-visible run instructions/screens,measured responsiveness,truthful limitations,required checks,ordinary protected PR merge and local main equality |

## Baseline and inspected consumers

- HEAD9fdb95e on codex/product-alignment-clarification-20261103;four existing dirty
  D01-D07 planning documents preserved. Existing PR33 checkpoint precedes these changes.
- Existing src/app/client.py:PlayWindow and main,src/app/client_worker.py:ClientWorker,
  src/app/client_session.py:ClientSession map fixed ClientAction values to commands.
- src/contracts/client.py has no free-text utterance or world-map DTO;existing scenario
  layouts and app/scenarios.py do not supply a generated world.
- src/app/durable.py owns DurableSession;feature registration and existing command/reducer/
  codec/checkpoint patterns are the integration foundation. Do not create a second independent
  authoritative simulation or mutate old mode/save identities in place.
- src/adapters/gemini_dialogue.py is preparation-only with four fixed quest intents;
  its current contract does not establish live conversation. Reuse lawful transport and
  error/budget boundaries;qualify any new provider contract rather than pretending fixed
  catalog output is free conversation. Do not read or print credentials in tool output.
- Python3.13.12/Git2.56.0 present on current host;reuse .venv. Unity/native/device/release
  qualification remains separately scoped;do not infer it from Tk or Python tests.

## Current product gate

Director confirmed6continents/6countries/12major cities with distinct identities and one
persisted reusable development world. Earlier proposed scales are superseded. Scale is no
longer a product gate. Execute RS-PLAY-001A,then registered travel and graphical integration.
Only current-feature blocking product questions may follow;do not revive the full M0 survey.
NPC intentional deception is not yet confirmed and is not this initial scale gate.

## Implementation preparation still required before READY

After the answer,split dependency-ordered implementation orders with exact edit paths,
new schema/command/event/DTO and owner contracts,units/ranges/errors/order,independent
examples,actual registration/callers,safe persistence/recovery/replay and measured targets.
Specify any further blocking player-facing choices with recommendation and examples.
Name actual tests and README verification commands,scope-specific checkpoint applicability
and held downstream steps. Missing public contracts remain DRAFT;technical naming/framework
choices are delegated and do not require director permission.

Required verification:both Ruff configurations,scoped formatting,strict mypy,both import
contracts,pip check,actual GUI/API/save/restart/error/replay flow and full regression for
shared CORE changes. Preserve original failures and run scoped repairs before required CI.
No implementation,provider call,CI/main merge or playable acceptance is claimed yet.
