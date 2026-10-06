from __future__ import annotations

from contracts.watch import (WATCH_NPC, LANTERN, REPLY, BellCommand, WatchWake, WatchRequested, WatchEcho, NpcActed, BellRung, WatchReplied, ChargeDelta, BellsDelta, ReplyDelta)
from contracts.encounter import HIT_POINTS
from contracts.trial import CELL_POSITION
from contracts.errors import CandidateError
from contracts.messages import EmittedFact, StateDelta
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from domain.primitives import FieldFamily, Phase, TypeKey, require_integer
from domain.trial import ACTOR_ID, SPACE_ID
from domain.watch import NPC_ID, NPC_CELL, LANTERN_ID, ECHO_DEPTH, increment_count, next_wake, recover_charge


def _manifest(engine: str, phase: Phase, reads: tuple[str, ...], writes: tuple[str, ...], emits: tuple[str, ...], consumes: tuple[str, ...]) -> CapabilityManifest:
    return CapabilityManifest(engine, (phase,), tuple(PhaseAccess(phase, FieldFamily(*f.rsplit(".", 1))) for f in reads), tuple(PhaseAccess(phase, FieldFamily(*f.rsplit(".", 1))) for f in writes), (), tuple(TypeKey("watch." + k, 1) for k in emits), tuple(TypeKey("watch." + k, 1) for k in consumes), "local")


def _context(invocation: EngineInvocation, phase: Phase) -> None:
    if invocation.phase != phase or phase != Phase.CASCADE and invocation.wave != 0:
        raise CandidateError("INVALID_FACT", "watch invocation phase")
    for event in invocation.incoming:
        if event.due_tick != invocation.logical_tick or event.header.type_key != event.payload.schema:
            raise CandidateError("INVALID_FACT", "watch input timing/schema")


class WatchNpc:
    @property
    def manifest(self) -> CapabilityManifest:
        return _manifest("watch.npc", Phase.PRE_TICK, ("watch.npc.bells", "watch.npc.cell", "watch.npc.space_id"), ("watch.npc.bells",), ("npc-acted", "wake"), ("wake",))

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        _context(invocation, Phase.PRE_TICK)
        if invocation.action is not None or len(invocation.incoming) != 1 or invocation.logical_tick % 2:
            raise CandidateError("INVALID_FACT", "watch wake scope")
        wake = invocation.incoming[0]
        if type(wake.payload) is not WatchWake or wake.payload.npc_id != NPC_ID:
            raise CandidateError("INVALID_FACT", "watch wake subject")
        npc = invocation.state.component(WATCH_NPC, NPC_ID)
        old, cell, space = npc.bells, npc.cell, npc.space_id
        if cell != NPC_CELL or space != SPACE_ID or old != invocation.logical_tick // 2 - 1:
            raise CandidateError("INVALID_FACT", "watch station/count")
        try:
            new, due = increment_count(old), next_wake(invocation.logical_tick)
        except ValueError as error:
            raise CandidateError("INTEGER_OVERFLOW", "watch recurrence") from error
        cause = (wake.header.event_id,)
        return EngineResult((BellsDelta(NPC_ID, old, new),), (EmittedFact(NpcActed(NPC_ID, old, new), invocation.logical_tick, cause), EmittedFact(WatchWake(NPC_ID), due, cause)), ())


class WatchBell:
    @property
    def manifest(self) -> CapabilityManifest:
        return _manifest("watch.bell", Phase.RESOLVE, ("encounter.hp.hp", "trial.position.space_id", "watch.npc.cell", "watch.npc.space_id"), (), ("bell-rung", "requested"), ())

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        _context(invocation, Phase.RESOLVE)
        action = invocation.action
        if action is None or action.actor_id != ACTOR_ID or type(action.payload) is not BellCommand or action.payload.npc_id != NPC_ID or invocation.incoming:
            raise CandidateError("INVALID_ACTION", "watch bell action")
        npc = invocation.state.component(WATCH_NPC, NPC_ID)
        if invocation.state.component(HIT_POINTS, ACTOR_ID).hp == 0 or npc.cell != NPC_CELL or npc.space_id != SPACE_ID or invocation.state.component(CELL_POSITION, ACTOR_ID).space_id != SPACE_ID:
            raise CandidateError("INVALID_ACTION", "watch bell references")
        return EngineResult((), (EmittedFact(WatchRequested(ACTOR_ID, NPC_ID), invocation.logical_tick, ()), EmittedFact(BellRung(ACTOR_ID, NPC_ID), invocation.logical_tick, ())), ())


class WatchRespond:
    @property
    def manifest(self) -> CapabilityManifest:
        return _manifest("watch.respond", Phase.REACT, (), (), ("echo",), ("requested",))

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        _context(invocation, Phase.REACT)
        facts: list[EmittedFact] = []
        if invocation.action is not None:
            raise CandidateError("INVALID_ACTION", "watch response action")
        for event in invocation.incoming:
            if type(event.payload) is not WatchRequested or event.payload.npc_id != NPC_ID or event.payload.actor_id != ACTOR_ID:
                raise CandidateError("INVALID_FACT", "watch request subject")
            facts.append(EmittedFact(WatchEcho(NPC_ID, ECHO_DEPTH), invocation.logical_tick, (event.header.event_id,)))
        return EngineResult((), tuple(facts), ())


class WatchEchoEngine:
    @property
    def manifest(self) -> CapabilityManifest:
        return _manifest("watch.echo", Phase.CASCADE, ("watch.reply.count",), ("watch.reply.count",), ("echo", "replied"), ("echo",))

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        _context(invocation, Phase.CASCADE)
        if invocation.action is not None:
            raise CandidateError("INVALID_ACTION", "watch echo action")
        old = invocation.state.component(REPLY, NPC_ID).count
        count = old
        facts: list[EmittedFact] = []
        for event in invocation.incoming:
            payload = event.payload
            if type(payload) is not WatchEcho or payload.npc_id != NPC_ID:
                raise CandidateError("INVALID_FACT", "watch echo subject")
            require_integer(payload.remaining, 0, 7)
            if payload.remaining:
                facts.append(EmittedFact(WatchEcho(NPC_ID, payload.remaining - 1), invocation.logical_tick, (event.header.event_id,)))
            else:
                try:
                    new = increment_count(count)
                except ValueError as error:
                    raise CandidateError("INTEGER_OVERFLOW", "watch replies") from error
                facts.append(EmittedFact(WatchReplied(NPC_ID, count, new), invocation.logical_tick, (event.header.event_id,)))
                count = new
        deltas: tuple[StateDelta, ...] = (ReplyDelta(NPC_ID, old, count),) if old != count else ()
        return EngineResult(deltas, tuple(facts), ())


class WatchPassive:
    @property
    def manifest(self) -> CapabilityManifest:
        return _manifest("watch.passive", Phase.POST_TICK, ("watch.lantern.charge",), ("watch.lantern.charge",), (), ())

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        _context(invocation, Phase.POST_TICK)
        old = invocation.state.component(LANTERN, LANTERN_ID).charge
        new = recover_charge(old)
        deltas: tuple[StateDelta, ...] = (ChargeDelta(LANTERN_ID, old, new),) if old != new else ()
        return EngineResult(deltas, (), ())
