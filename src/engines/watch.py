from __future__ import annotations

from dataclasses import replace

from domain.scenario import LEGACY, Scenario, ScenarioBound
from domain.npc_patrol import NpcScope
from contracts.npc_patrol import NpcCellDelta, NpcPatrolled
from contracts.quest import QuestSpoken
from contracts.npc_memory import MEMORY, MEMORY_FAMILY, read_record

from contracts.watch import (WATCH_NPC, LANTERN, REPLY, BellCommand, WatchWake, WatchRequested, WatchEcho, NpcActed, BellRung, WatchReplied, ChargeDelta, BellsDelta, ReplyDelta)
from contracts.encounter import HIT_POINTS
from contracts.trial import CELL_POSITION
from contracts.errors import CandidateError
from contracts.messages import EmittedFact, StateDelta, WorldEvent
from contracts.turn import CapabilityManifest, EngineInvocation, EngineResult, PhaseAccess
from domain.primitives import FieldFamily, MAX_INT, Phase, TypeKey, require_integer, require_namespace
from domain.watch import ECHO_DEPTH, increment_count, next_wake, recover_charge


def _manifest(engine: str, phase: Phase, reads: tuple[str, ...], writes: tuple[str, ...], emits: tuple[str, ...], consumes: tuple[str, ...]) -> CapabilityManifest:
    return CapabilityManifest(engine, (phase,), tuple(PhaseAccess(phase, FieldFamily(*f.rsplit(".", 1))) for f in reads), tuple(PhaseAccess(phase, FieldFamily(*f.rsplit(".", 1))) for f in writes), (), tuple(TypeKey("watch." + k, 1) for k in emits), tuple(TypeKey("watch." + k, 1) for k in consumes), "local")


def _context(invocation: EngineInvocation, phase: Phase) -> None:
    if invocation.phase != phase or phase != Phase.CASCADE and invocation.wave != 0:
        raise CandidateError("INVALID_FACT", "watch invocation phase")
    for event in invocation.incoming:
        if event.due_tick != invocation.logical_tick or event.header.type_key != event.payload.schema:
            raise CandidateError("INVALID_FACT", "watch input timing/schema")


class WatchNpc(NpcScope):
    def __init__(
        self, layout: Scenario = LEGACY, *, npc_patrol: bool = False,
        talk_pause_quest: str | None = None, quest_patrol: bool = False, call_pause: bool = False,
    ) -> None:
        if talk_pause_quest is not None:
            if npc_patrol is not True or type(talk_pause_quest) is not str or not talk_pause_quest.startswith("quest:"):
                raise ValueError("NPC_TALK_PAUSE_CONTENT")
            try:
                require_namespace(talk_pause_quest)
            except ValueError as error:
                raise ValueError("NPC_TALK_PAUSE_CONTENT") from error
        if type(quest_patrol) is not bool or quest_patrol and talk_pause_quest is None:
            raise ValueError("NPC_QUEST_PATROL_CONTENT")
        if type(call_pause) is not bool or call_pause and not quest_patrol:
            raise ValueError("NPC_CALL_PAUSE_CONTENT")
        super().__init__(layout, npc_patrol=npc_patrol)
        self._talk_pause_quest = talk_pause_quest
        self._quest_patrol = quest_patrol
        self._call_pause = call_pause

    @property
    def manifest(self) -> CapabilityManifest:
        base = _manifest("watch.npc", Phase.PRE_TICK, ("watch.npc.bells", "watch.npc.cell", "watch.npc.space_id"), ("watch.npc.bells",), ("npc-acted", "wake"), ("wake",))
        if not self._npc_patrol:
            return base
        post = _manifest(
            "watch.npc", Phase.POST_TICK,
            ("watch.npc.bells", "watch.npc.cell", "watch.npc.space_id", "trial.position.cell", "trial.position.space_id"),
            ("watch.npc.cell",), ("npc-patrolled",), ("npc-acted",),
        )
        if self._talk_pause_quest is not None:
            post = replace(post, consumes=(*post.consumes, QuestSpoken.SCHEMA))
        if self._quest_patrol:
            post = replace(post, reads=(*post.reads, PhaseAccess(Phase.POST_TICK, MEMORY_FAMILY)))
        if self._call_pause:
            post = replace(
                post,
                reads=(*post.reads, PhaseAccess(Phase.POST_TICK, FieldFamily("watch.reply", "count"))),
                consumes=(*post.consumes, WatchReplied(self._layout.npc_id, 0, 1).schema),
            )
        return replace(
            base,
            phases=(*base.phases, *post.phases),
            reads=(*base.reads, *post.reads),
            writes=(*base.writes, *post.writes),
            emits=(*base.emits, *post.emits),
            consumes=(*base.consumes, *post.consumes),
        )


    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        if self._npc_patrol and invocation.phase is Phase.POST_TICK:
            if self._call_pause:
                return self._answered_patrol(invocation)
            return self._spoken_patrol(invocation) if self._talk_pause_quest is not None else self._patrol(invocation)
        _context(invocation, Phase.PRE_TICK)
        if invocation.action is not None or len(invocation.incoming) != 1 or invocation.logical_tick % 2:
            raise CandidateError("INVALID_FACT", "watch wake scope")
        wake = invocation.incoming[0]
        if type(wake.payload) is not WatchWake or wake.payload.npc_id != self._layout.npc_id:
            raise CandidateError("INVALID_FACT", "watch wake subject")
        npc = invocation.state.component(WATCH_NPC, self._layout.npc_id)
        old, cell, space = npc.bells, npc.cell, npc.space_id
        if cell not in self._npc_cells or space != self._layout.space_id or old != invocation.logical_tick // 2 - 1:
            raise CandidateError("INVALID_FACT", "watch station/count")
        try:
            new, due = increment_count(old), next_wake(invocation.logical_tick)
        except ValueError as error:
            raise CandidateError("INTEGER_OVERFLOW", "watch recurrence") from error
        cause = (wake.header.event_id,)
        return EngineResult((BellsDelta(self._layout.npc_id, old, new),), (EmittedFact(NpcActed(self._layout.npc_id, old, new), invocation.logical_tick, cause), EmittedFact(WatchWake(self._layout.npc_id), due, cause)), ())


    def _answered_patrol(self, invocation: EngineInvocation) -> EngineResult:
        _context(invocation, Phase.POST_TICK)
        tick = invocation.logical_tick
        if (invocation.action is not None or type(invocation.wave) is not int or invocation.wave != 0
                or type(tick) is not int or not 1 <= tick <= MAX_INT
                or not 1 <= len(invocation.incoming) <= 2):
            raise CandidateError("INVALID_FACT", "answered patrol invocation")
        replies = tuple(event for event in invocation.incoming if type(event.payload) is WatchReplied)
        if not replies:
            return self._spoken_patrol(invocation)
        if len(replies) != 1:
            raise CandidateError("INVALID_FACT", "duplicate patrol answer")
        event = replies[0]
        payload, header = event.payload, event.header
        if not isinstance(payload, WatchReplied):
            raise CandidateError("INVALID_FACT", "patrol answer type")
        count = invocation.state.component(REPLY, self._layout.npc_id).count
        if (type(payload.npc_id) is not str or payload.npc_id != self._layout.npc_id
                or header.producer_id != "watch.echo" or header.phase is not Phase.CASCADE
                or type(header.wave) is not int or header.wave != ECHO_DEPTH
                or type(header.sequence) is not int or header.sequence != 0
                or type(header.producer_rank) is not int or not 0 <= header.producer_rank <= MAX_INT
                or type(header.occurred_at) is not int or header.occurred_at != tick
                or type(event.due_tick) is not int or event.due_tick != tick
                or type(header.caused_by) is not tuple or len(header.caused_by) != 1
                or type(payload.before_count) is not int or not 0 <= payload.before_count < MAX_INT
                or type(payload.after_count) is not int or payload.after_count != payload.before_count + 1
                or type(count) is not int or count != payload.after_count):
            raise CandidateError("INVALID_FACT", "patrol answer source")
        remaining = tuple(source for source in invocation.incoming if source is not event)
        if any(type(source.payload) is QuestSpoken for source in remaining):
            raise CandidateError("INVALID_FACT", "mixed patrol speech and answer")
        if tick % 2:
            if remaining:
                raise CandidateError("INVALID_FACT", "answered patrol odd wake")
            return EngineResult((), (), ())
        return self._spoken_patrol(replace(invocation, incoming=remaining), pause=True)


    def _spoken_patrol(self, invocation: EngineInvocation, *, pause: bool = False) -> EngineResult:
        _context(invocation, Phase.POST_TICK)
        tick = invocation.logical_tick
        if (invocation.action is not None or type(invocation.wave) is not int or invocation.wave != 0
                or type(tick) is not int or not 1 <= tick <= MAX_INT
                or not 1 <= len(invocation.incoming) <= 2):
            raise CandidateError("INVALID_FACT", "conversation patrol invocation")
        wake: WorldEvent | None = None
        spoken = False
        for event in invocation.incoming:
            payload, header = event.payload, event.header
            if type(payload) is NpcActed:
                if wake is not None:
                    raise CandidateError("INVALID_FACT", "duplicate patrol wake")
                wake = event
            elif type(payload) is QuestSpoken:
                if (spoken or payload.quest_id != self._talk_pause_quest
                        or type(payload.quest_id) is not str or type(payload.npc_id) is not str
                        or payload.npc_id != self._layout.npc_id or type(payload.intent) is not str
                        or payload.intent not in ("offer", "reminder", "completion", "gratitude")
                        or header.producer_id != "quest.rules" or header.phase is not Phase.RESOLVE
                        or type(header.wave) is not int or header.wave != 0
                        or type(header.sequence) is not int
                        or header.sequence != int(payload.intent in ("offer", "completion"))
                        or type(header.occurred_at) is not int or header.occurred_at != tick
                        or type(event.due_tick) is not int or event.due_tick != tick
                        or header.caused_by != ()):
                    raise CandidateError("INVALID_FACT", "conversation patrol source")
                spoken = True
            else:
                raise CandidateError("INVALID_FACT", "conversation patrol source kind")
        if tick % 2:
            if wake is not None or not spoken:
                raise CandidateError("INVALID_FACT", "conversation patrol odd wake")
            return EngineResult((), (), ())
        if wake is None:
            raise CandidateError("INVALID_FACT", "conversation patrol missing wake")
        return self._patrol(replace(invocation, incoming=(wake,)), pause=spoken or pause)


    def _patrol(self, invocation: EngineInvocation, *, pause: bool = False) -> EngineResult:
        _context(invocation, Phase.POST_TICK)
        tick = invocation.logical_tick
        if (invocation.action is not None or len(invocation.incoming) != 1
                or type(tick) is not int or tick < 2 or tick > MAX_INT or tick % 2
                or type(invocation.wave) is not int or invocation.wave != 0):
            raise CandidateError("INVALID_FACT", "patrol invocation")
        source = invocation.incoming[0]
        fact, header = source.payload, source.header
        if (type(fact) is not NpcActed or fact.npc_id != self._layout.npc_id
                or header.producer_id != "watch.npc" or header.phase is not Phase.PRE_TICK
                or type(header.wave) is not int or header.wave != 0
                or type(header.sequence) is not int or header.sequence != 0
                or type(header.occurred_at) is not int or header.occurred_at != tick
                or type(source.due_tick) is not int or source.due_tick != tick
                or len(header.caused_by) != 1
                or type(fact.before_bells) is not int or type(fact.after_bells) is not int
                or fact.before_bells != tick // 2 - 1 or fact.after_bells != tick // 2):
            raise CandidateError("INVALID_FACT", "patrol wake source")
        npc = invocation.state.component(WATCH_NPC, self._layout.npc_id)
        current, space, bells = npc.cell, npc.space_id, npc.bells
        actor = invocation.state.component(CELL_POSITION, self._layout.actor_id)
        actor_cell, actor_space = actor.cell, actor.space_id
        if (type(current) is not int or current not in self._npc_cells
                or space != self._layout.space_id or type(bells) is not int
                or bells != fact.after_bells or actor_space != space
                or type(actor_cell) is not int or not 0 <= actor_cell <= 8):
            raise CandidateError("INVALID_FACT", "patrol current references")
        target = self._npc_cells[1] if current == self._npc_cells[0] else self._npc_cells[0]
        if self._quest_patrol:
            try:
                memory = read_record(self._layout.npc_id, invocation.state.component(MEMORY, self._layout.npc_id))
            except ValueError as error:
                raise CandidateError("INVALID_FACT", "quest patrol memory") from error
            if any(entry.observed_at > tick for entry in memory.entries):
                raise CandidateError("INVALID_FACT", "quest patrol future memory")
            if memory.known_phase == "available":
                if current != self._layout.npc_cell:
                    raise CandidateError("INVALID_FACT", "quest patrol unheard position")
                target = self._layout.npc_cell
            elif memory.known_phase == "reported":
                target = self._layout.npc_cell
            if target == current:
                return EngineResult((), (), ())
        if pause or target == actor_cell:
            return EngineResult((), (), ())
        return EngineResult(
            (NpcCellDelta(self._layout.npc_id, current, target),),
            (EmittedFact(NpcPatrolled(self._layout.npc_id, space, current, target), tick,
                         (header.event_id,)),),
            (),
        )


class WatchBell(NpcScope):
    @property
    def manifest(self) -> CapabilityManifest:
        return _manifest("watch.bell", Phase.RESOLVE, ("encounter.hp.hp", "trial.position.space_id", "watch.npc.cell", "watch.npc.space_id"), (), ("bell-rung", "requested"), ())

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        _context(invocation, Phase.RESOLVE)
        action = invocation.action
        if action is None or action.actor_id != self._layout.actor_id or type(action.payload) is not BellCommand or action.payload.npc_id != self._layout.npc_id or invocation.incoming:
            raise CandidateError("INVALID_ACTION", "watch bell action")
        npc = invocation.state.component(WATCH_NPC, self._layout.npc_id)
        if invocation.state.component(HIT_POINTS, self._layout.actor_id).hp == 0 or npc.cell not in self._npc_cells or npc.space_id != self._layout.space_id or invocation.state.component(CELL_POSITION, self._layout.actor_id).space_id != self._layout.space_id:
            raise CandidateError("INVALID_ACTION", "watch bell references")
        return EngineResult((), (EmittedFact(WatchRequested(self._layout.actor_id, self._layout.npc_id), invocation.logical_tick, ()), EmittedFact(BellRung(self._layout.actor_id, self._layout.npc_id), invocation.logical_tick, ())), ())


class WatchRespond(ScenarioBound):
    @property
    def manifest(self) -> CapabilityManifest:
        return _manifest("watch.respond", Phase.REACT, (), (), ("echo",), ("requested",))

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        _context(invocation, Phase.REACT)
        facts: list[EmittedFact] = []
        if invocation.action is not None:
            raise CandidateError("INVALID_ACTION", "watch response action")
        for event in invocation.incoming:
            if type(event.payload) is not WatchRequested or event.payload.npc_id != self._layout.npc_id or event.payload.actor_id != self._layout.actor_id:
                raise CandidateError("INVALID_FACT", "watch request subject")
            facts.append(EmittedFact(WatchEcho(self._layout.npc_id, ECHO_DEPTH), invocation.logical_tick, (event.header.event_id,)))
        return EngineResult((), tuple(facts), ())


class WatchEchoEngine(ScenarioBound):
    @property
    def manifest(self) -> CapabilityManifest:
        return _manifest("watch.echo", Phase.CASCADE, ("watch.reply.count",), ("watch.reply.count",), ("echo", "replied"), ("echo",))

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        _context(invocation, Phase.CASCADE)
        if invocation.action is not None:
            raise CandidateError("INVALID_ACTION", "watch echo action")
        old = invocation.state.component(REPLY, self._layout.npc_id).count
        count = old
        facts: list[EmittedFact] = []
        for event in invocation.incoming:
            payload = event.payload
            if type(payload) is not WatchEcho or payload.npc_id != self._layout.npc_id:
                raise CandidateError("INVALID_FACT", "watch echo subject")
            require_integer(payload.remaining, 0, 7)
            if payload.remaining:
                facts.append(EmittedFact(WatchEcho(self._layout.npc_id, payload.remaining - 1), invocation.logical_tick, (event.header.event_id,)))
            else:
                try:
                    new = increment_count(count)
                except ValueError as error:
                    raise CandidateError("INTEGER_OVERFLOW", "watch replies") from error
                facts.append(EmittedFact(WatchReplied(self._layout.npc_id, count, new), invocation.logical_tick, (event.header.event_id,)))
                count = new
        deltas: tuple[StateDelta, ...] = (ReplyDelta(self._layout.npc_id, old, count),) if old != count else ()
        return EngineResult(deltas, tuple(facts), ())


class WatchPassive(ScenarioBound):
    @property
    def manifest(self) -> CapabilityManifest:
        return _manifest("watch.passive", Phase.POST_TICK, ("watch.lantern.charge",), ("watch.lantern.charge",), (), ())

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        _context(invocation, Phase.POST_TICK)
        old = invocation.state.component(LANTERN, self._layout.lantern_id).charge
        new = recover_charge(old)
        deltas: tuple[StateDelta, ...] = (ChargeDelta(self._layout.lantern_id, old, new),) if old != new else ()
        return EngineResult(deltas, (), ())
