# Product Direction — Complete Base Game and Optional AI

APPROVED_DIRECTION2026-11-05 by the director after reviewing the two supplied technical/
business proposals and the assistant's corrections. Primary7 (integration/design support),
related1/2/3/4/5/6. Requirements are not implementation or release evidence.

## Accepted product compromise

- Option C:ship a complete authored main RPG with state-aware scripted conversations and
  an optional memory/personality-grounded free-form NPC conversation mode. The main quest,
  ending and essential progression must remain available without purchasing AI API access.
  Preserve meaningful optional free-form interaction rather than restricting all AI to postgame.
- Support base gameplay without provider availability;offline delivery is a qualification
  target,not a claim that the current prototype already contains a complete offline campaign.
- Optional generated adventures/regions/history use supported mechanics and approved assets.
  Begin with a small bounded adventure,not unrestricted runtime media/world generation.
  Past-era/alternate stories must not overwrite committed present-world history;exact branch/
  timeline contracts require a later bounded order. Accepted generated packages are saved;
  replay/load must not regenerate accepted content or call providers.
- Keep deterministic Python authority,validated typed actions,COMMIT-only writes and SQLite
  canonical persistence. Optional AI speech cannot grant money,rewards,damage or quest success.
  Scripted and free-form dialogue share the same authoritative state/action boundary.
- Local LLM is optional pending measured quality and total Unity+inference resource use.
  No mandatory local-model hardware requirement,no promised model parity from100playthroughs.
  Qdrant remains a rebuildable derived index and is introduced only if retrieval evidence
  justifies it. NPC-specific knowledge filtering precedes any index expansion.

## Payment/provider HOLD

API payment,service access,quotas and commercial backend are explicitly DEFERRED. Neither
BYOK/direct provider billing nor developer-funded relay/Steam billing is approved for release.
Existing development provider/key rotation remains a testing mechanism,not a shipping promise.
Do not introduce billing,automatic paid fallback,credential migration or recurring costs.
The main game must not require an additional AI payment. If API usage is enabled later,the
player must explicitly understand/accept its costs and limits;keys must stay out of logs/saves.

Checked2026-11-05:[Steam Content Survey](https://partner.steamgames.com/doc/gettingstarted/contentsurvey?l=english)
requires live-AI disclosure/guardrail explanation. Its external live-AI service FAQ instructs
developers to manage service access and collect payment using a Steam-supported method.
No BYOK exception was established. Validate the concrete distribution/payment design with
Valve and applicable provider terms before commercial implementation;no platform approval
or legal conclusion is claimed. This supersedes MASTER7.2's prior BYOK-only business rule.

## Execution order and boundaries

1. Finish already-authorized RS-PLAY-001I transport acceptance,ordinary PR merge and clean
   local-main synchronization. Do not abandon or relabel its unfinished delivery.
2. Review actual data ownership/mutation/visibility across NPC personality/private memory,
   objective history,economy/inventory,social relations,time/quests and accepted dialogue.
   Produce the A–J ownership map,ranked gaps and proposed bounded repair order from the supplied
   technical proposal. Review/design first;no Qdrant/runtime/save-format implementation here.
3. After resolving ownership/bridge contracts,qualify a tiny graphical experiment and modular
   assets,then one complete playable slice with save/restart/replay and measured performance.
   A visually isolated experiment may use immutable agreed DTOs without waiting for all
   future simulation features. Existing native/device/independent/release holds remain.
4. Compare provider/local inference on identical Korean NPC situations with latency/memory/
   FPS measurements;expand content/simulation/asset production only after the slice is proven.
   Model names/licenses/current hardware claims require actual qualification,not adoption
   from an attachment. Optimize measured bottlenecks throughout,not only at the end.

This changes product requirements and task ordering by explicit director instruction. It
does not authorize agents,native/ComputerUse operations,release,new dependencies or billing.
Current Python prototype integration and past CI evidence do not establish commercial quality.

Read-only ownership review:[actual A–J map,ranked gaps and bounded next contracts](reviews/RS-OWN-001_DATA_OWNERSHIP_2026-11-05.md). This is review evidence/proposals,not new runtime/save/knowledge semantics or approval to release.

The next implementation proposal is a small O1 proof using an authored supply offer and the existing confirmed action path. Its acceptance includes provider-disabled progression and equivalent gameplay effects at the same action boundary. [Claude feedback and next contract](reviews/RS-OWN-002_CLAUDE_FEEDBACK_2026-11-06.md)
