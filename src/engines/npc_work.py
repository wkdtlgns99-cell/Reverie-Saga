"""Prepare communal stock from the NPC's actual scheduled work, including off-screen."""

from contracts.dialogue import QuestBound
from contracts.errors import CandidateError
from contracts.messages import EmittedFact
from contracts.npc_work import PROVISIONS, STOCK_FAMILY, ProvisionPrepared, ProvisionsDelta
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from contracts.watch import NpcActed
from domain.npc_work import STOCK_CAP, WORK_PERIOD, stock_at
from domain.primitives import Phase
from domain.watch import WAKE_PERIOD


class NpcProvisioner(QuestBound):
    @property
    def manifest(self) -> CapabilityManifest:
        access = PhaseAccess(Phase.POST_TICK, STOCK_FAMILY)
        return CapabilityManifest(
            "quest.provisioner",
            (Phase.POST_TICK,),
            (access,),
            (access,),
            (),
            (ProvisionPrepared.SCHEMA,),
            (NpcActed(self.quest_content.definition.layout.npc_id, 0, 1).schema,),
            "constant",
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        if (
            invocation.phase != Phase.POST_TICK
            or invocation.wave != 0
            or invocation.action is not None
            or len(invocation.incoming) != 1
        ):
            raise CandidateError("INVALID_FACT", "provision invocation")
        event = invocation.incoming[0]
        payload, header, tick = event.payload, event.header, invocation.logical_tick
        owner = self.quest_content.definition.layout.npc_id
        if (
            type(payload) is not NpcActed
            or not isinstance(payload, NpcActed)
            or payload.npc_id != owner
            or header.producer_id != "watch.npc"
            or header.phase != Phase.PRE_TICK
            or header.wave != 0
            or header.sequence != 0
            or event.due_tick != tick
            or header.occurred_at != tick
            or header.type_key != payload.schema
            or tick <= 0
            or tick % WAKE_PERIOD
            or type(payload.before_bells) is not int
            or type(payload.after_bells) is not int
            or (payload.before_bells, payload.after_bells)
            != (tick // WAKE_PERIOD - 1, tick // WAKE_PERIOD)
        ):
            raise CandidateError("INVALID_FACT", "provision source binding")
        before = invocation.state.component(PROVISIONS, owner).stock
        if type(before) is not int or before != stock_at(tick - 1):
            raise CandidateError("INVALID_FACT", "provision stock clock")
        if tick % WORK_PERIOD or before == STOCK_CAP:
            return EngineResult((), (), ())
        after = before + 1
        return EngineResult(
            (ProvisionsDelta(owner, before, after),),
            (EmittedFact(ProvisionPrepared(owner, before, after), tick, (header.event_id,)),),
            (),
        )
