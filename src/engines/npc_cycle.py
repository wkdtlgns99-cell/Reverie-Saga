"""Off-screen prepare/use loop driven only by actual NPC wake events."""

from contracts.dialogue import QuestBound
from contracts.errors import CandidateError
from contracts.messages import EmittedFact
from contracts.npc_cycle import CYCLE, CYCLE_FAMILY, CycleChanged, CycleDelta
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from contracts.watch import NpcActed
from domain.npc_cycle import CycleRecord, advance, state_at
from domain.primitives import Phase
from domain.watch import WAKE_PERIOD


class NpcSupplyCycle(QuestBound):
    @property
    def manifest(self) -> CapabilityManifest:
        access = PhaseAccess(Phase.POST_TICK, CYCLE_FAMILY)
        return CapabilityManifest(
            "quest.cycle",
            (Phase.POST_TICK,),
            (access,),
            (access,),
            (),
            (CycleChanged.SCHEMA,),
            (NpcActed(self.quest_content.definition.layout.npc_id, 0, 1).schema,),
            "constant",
        )

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        if (
            invocation.phase != Phase.POST_TICK
            or invocation.wave != 0
            or (invocation.action is not None or len(invocation.incoming) != 1)
        ):
            raise CandidateError("INVALID_FACT", "cycle invocation")
        event = invocation.incoming[0]
        payload, header, tick = event.payload, event.header, invocation.logical_tick
        owner = self.quest_content.definition.layout.npc_id
        if (
            type(payload) is not NpcActed
            or not isinstance(payload, NpcActed)
            or (
                payload.npc_id != owner
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
            )
        ):
            raise CandidateError("INVALID_FACT", "cycle source binding")
        view = invocation.state.component(CYCLE, owner)
        before = CycleRecord(owner, view.state, view.entries)
        if before.state != state_at(tick - 1):
            raise CandidateError("INVALID_FACT", "cycle clock")
        after = advance(before, tick, header.event_id)
        count = (
            after.state.produced
            + after.state.consumed
            - before.state.produced
            - before.state.consumed
        )
        return EngineResult(
            () if before == after else (CycleDelta(before, after),),
            tuple(
                EmittedFact(CycleChanged(owner, entry), tick, (header.event_id,))
                for entry in after.entries[-count:]
            )
            if count
            else (),
            (),
        )
