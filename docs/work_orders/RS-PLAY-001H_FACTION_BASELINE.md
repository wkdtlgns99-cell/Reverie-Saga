# RS-PLAY-001H — Species, Membership and Earned Reputation

READY2026-11-05. QF01 answered:include species,countries,regional groups and action
consequences;executor chooses suitable design. Supersedes country-only proposal and pending
blocker. Primary3internal data;related2/4/5/6/7. Executor:self-review,no agents.
Authority:MASTER0.4D01/QF01,parentRS-PLAY-001. No whole-society completion claim.

## Baseline / prerequisites / reads

HEAD53914db,codex/world-faction-baseline-20261105;four owned dirty preparation docs only.
PR35/36/37 ordinarily merged,PR37final-head full3955/boundary32PASS twice. No pending CI.
Historical blocked audit resolved by director answer. Reuse local Python3.13.12/.venv,Tk8.6,
SQLite3.50.4/Git,no installs. Read rulebook,handoff,backlog,Korean progress,MASTER0.4,
numbered structure,workstation setup,READMEverification,Sol template,autonomous policy and
actual catalog/travel/supply/conversation/session/worker/UI/codec/checkpoint/registry consumers.

## Concrete contracts

SocialCatalog:immutable persisted UTF8 JSON,world seed-bound,exact6countries/12places/48NPCs.
Six ancestry definitions(id,name,culture),six national factions,twelve city organizations;
resident identities map NPC to ancestry and local organization. Local groups belong to their
country. Ancestry,citizenship,personality and earned reputation remain distinct. All15unordered
national diplomatic pairs explicitly score -20/0/20 with reasons;self20. Local groups inherit
parent diplomacy;local reputation remains separate. No inherent biological hostility.

SocialState on WORLD_ACTOR:ancestry_id,country_id initially both empty;explicit citizenship
may be none. Reputation sorted unique tuple of all18faction IDs and exact ints[-100,100];
credited_places sorted unique tuple. SocialAction(operation,ancestry_id='',country_id=''):
identify1second valid ancestry/country-or-none once;protest5seconds local-15/national-5;
reconcile10seconds local+5/national+1each capped0,reject when both>=0. Protest/reconcile
require current city,not road. Invalid fields/actions reject before any time/state change.

WorldSocial alone owns SOCIAL_FAMILY. RESOLVE applies confirmed actions. POST_TICK after
world.supply reads actual stage2supplies;uncredited delivery adds local20/national5 clamped
[-100,100] and credits exactly once in same COMMIT. Existing supply engine alone owns all
inventory/treasury;no new resource grant. Retry/replay never re-rewards. Reaction=clamp(parent
national diplomacy toward citizenship + national reputation + local reputation,-100,100).
Unchosen/none citizenship contributes0. NPC shared ancestry adds2tone familiarity only.
Hostile<=-30 denies starting city entry and NEW supply contracts;return already on road and
collection/delivery of existing cargo remain possible. Reconcile works even while hostile.
Map inspection never travels/mutates. This is initial playable social behavior,not dynamic
interstate war/general commerce/combat completion.

Same canonical context factory supplies approved public social facts,including the own
organization's derived public standing and current policy (no private incident omniscience), and suppresses unavailable
contracts at BOTH generation and reply admission. Optional social arguments defaultNone preserve
old context bytes/hashes/pins. Distinct world-social-v1 profile/working path isolates old saves;
no migration or format rewrite. Checkpoint wraps Gpolicy after removing exactly one validated
social record;credited set MUST equal real stage2supply places. Exact decode fields/types.

## Edges / independent examples

Exact tuples,nonempty bounded NFC names,valid namespace IDs,sorted unique keys and pairs.
Missing/extra/unknown/duplicate refs reject;bool-as-int rejects. Unknown identity ->SOCIAL_IDENTITY;
repeat ->SOCIAL_IDENTITY_LOCKED;road ->SOCIAL_OUT_OF_REACH;unknown command ->INVALID_COMMAND;
unneeded reconcile ->SOCIAL_NOTHING_TO_REPAIR;gates SOCIAL_ENTRY_DENIED/SOCIAL_CONTRACT_DENIED.
Unexpected CORE/codec failures propagate. Two protests from0 ->local-30,national-10,reaction-40.
Reconcile ->-25/-9,reaction-34;second ->-20/-8,reaction-28,access restored. Real delivery from0
->20/5;duplicate receipt and later ticks remain20/5. Speech claims/map clicks give no reward.

## Exact allowed paths / wiring

All paths below resolve under absolute C:/Reverie Saga/;these exact paths only.
NEW:content/worlds/development-social-v1.json;src/domain/world_social.py;
src/contracts/world_social.py;src/engines/world_social.py;src/orchestration/world_social.py;
src/app/world_social_registry.py;src/app/world_social.py;tests/unit/test_world_social.py;
tests/integration/test_world_social.py;tests/integration/test_world_social_client.py;
docs/reviews/RS-PLAY-001H_EXECUTION_2026-11-05.md.
MODIFY:src/app/world_catalog.py;src/app/world_session.py;src/app/world_worker.py;
src/app/world_conversation_worker.py;src/app/world_client.py;
src/orchestration/world_conversation.py;src/orchestration/world_conversation_context.py;
pyproject.toml;tests/governance/test_dependency_contracts.py;README.md;
docs/MASTER_GAME_ARCHITECTURE.md;BACKLOG.md;SESSION_HANDOFF.md;GAME_SYSTEM_SUMMARY_KO.md;this order.
Ignored scratch:tmp/rs-play-001h for owned audit scripts/source witnesses/results/private saves;
not published content. Forbidden:reference repo,credentials,old content/save identities,shared CORE implementation,
CI/protection/guard weakening,native/ComputerUse/device/release changes.

Register codecs/adapter/reducer/patch/admission/engine/consumer access/checkpoint in composed
Gbundle. Replace only new-profile context admissions,wrap prior routes in social access gate.
Extend engine independence guard AND literal synthetic fixtures. Optional social catalog in
session/worker selects new profile and initial record. --world loads that catalog and uses
 tmp/world-social-play. Worker retains exact confirmed command/key/attachment on rollback/
uncertain COMMIT/ack failure. Nonmodal social panel shows identity/standings/diplomacy,
explicit identify/protest/reconcile confirmation and retry. Selected map city shows access;
preserve slow clock/ESC/input/poll/shutdown ownership and existing dialogue lifecycle.

## Algorithm / verification / acceptance / delivery

Define/validate data and independent domain tests;register durable simulation;then canonical
context,worker and actual GUI. Prototype numeric tuning is delegated,not director-answered
balance. Unit tests derive coverage/malformed types/scoring/clamps/actions independently.
Real integration covers admission/COMMIT/gates/delivery/idempotency/checkpoint/slots/restart/
replay/stale reply/old profile;actual Tk/worker covers controls,pause/idle/errors/retry/map.
No per-test live AI generation. Measure catalog/context/inspect/short save-restart TARGET<2s
this PC;report misses. Run README env,both Ruff,scoped format,strict mypy,imports3+1,pip,
affected tests/document guards;full required CI twice at final head. No native/human/device claim.
CP01-05 NOT_APPLICABLE:no new kernel,first client,first quest,native or import boundary;
existing acceptances remain scoped. CP06holds release,no new review schedule/agents.
Stop for evidenced contract contradiction,user overlap,unavailable qualification after safe
alternatives or material choice outside QF01delegation. Scoped commit/push/PR/checks/ordinary
merge/fetch-ff-clean main already authorized. Accept only actual evidence;then continue parent.
