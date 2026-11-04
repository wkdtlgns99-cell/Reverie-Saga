"""World wait admission and recorded time presentation in the existing pipeline."""

import hashlib

from contracts.errors import SchemaError
from contracts.messages import EventHeader, PresentationEvent, WorldEvent
from contracts.read_views import ReadPort
from contracts.turn import (
    AdmittedAction,
    AdmittedCommand,
    AdmissionOutcome,
    CommitReceipt,
    GameCommand,
    TurnPlan,
    TurnRejected,
    failure,
)
from contracts.world_time import TimeCue, TimePassed, WorldWait
from domain.canonical import JsonObject, exact_fields, int_value, pack
from domain.primitives import (
    EventId,
    FieldFamily,
    FrozenPayload,
    Phase,
    Tick,
    TypeKey,
    require_integer,
)
from domain.world_travel import WORLD_ACTOR


class WorldWaitAdmission:
    schema = WorldWait.SCHEMA
    reads: tuple[FieldFamily, ...] = ()

    def admit(
        self, command: GameCommand, state: ReadPort, *, start_tick: Tick, world_id: str
    ) -> AdmissionOutcome:
        if command.actor_id != WORLD_ACTOR:
            return TurnRejected(failure("UNAUTHORIZED_ACTOR"), command.expected_revision)
        payload = command.payload
        if (
            type(payload) is not WorldWait
            or not isinstance(payload, WorldWait)
            or type(payload.seconds) is not int
            or not 1 <= payload.seconds <= 16
        ):
            return TurnRejected(failure("INVALID_COMMAND"), command.expected_revision)
        target = Tick(start_tick + payload.seconds)
        key = (
            "a1-"
            + hashlib.sha256(
                pack(
                    (
                        "world-wait/v1",
                        world_id,
                        str(start_tick),
                        str(target),
                    )
                )
            ).hexdigest()
        )
        return AdmittedCommand(
            TurnPlan(command, start_tick, target), AdmittedAction(command.actor_id, payload, key)
        )


class TimeCodec:
    def __init__(self, schema: TypeKey) -> None:
        self._schema = schema

    @property
    def schema(self) -> TypeKey:
        return self._schema

    def encode(self, payload: FrozenPayload) -> JsonObject:
        if payload.schema != self.schema:
            raise SchemaError("UNSUPPORTED_SCHEMA", "world time schema")
        if type(payload) is WorldWait and isinstance(payload, WorldWait):
            require_integer(payload.seconds, 1, 16)
            return {"seconds": payload.seconds}
        if type(payload) in (TimePassed, TimeCue) and isinstance(payload, (TimePassed, TimeCue)):
            require_integer(payload.start)
            require_integer(payload.end, payload.start + 1, payload.start + 16)
            return {"start": payload.start, "end": payload.end}
        raise SchemaError("UNSUPPORTED_SCHEMA", "world time payload")

    def decode(self, data: JsonObject) -> FrozenPayload:
        result: FrozenPayload
        if self.schema == WorldWait.SCHEMA:
            result = WorldWait(int_value(exact_fields(data, ("seconds",))["seconds"]))
        elif self.schema in (TimePassed.SCHEMA, TimeCue.SCHEMA):
            d = exact_fields(data, ("start", "end"))
            cls = TimePassed if self.schema == TimePassed.SCHEMA else TimeCue
            result = cls(int_value(d["start"]), int_value(d["end"]))
        else:
            raise SchemaError("UNSUPPORTED_SCHEMA", "world time schema")
        self.encode(result)
        return result


class TimePresenter:
    def map(
        self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort
    ) -> tuple[PresentationEvent, ...]:
        cues: list[PresentationEvent] = []
        for fact in facts:
            payload = fact.payload
            if type(payload) is not TimePassed or not isinstance(payload, TimePassed):
                raise SchemaError("UNSUPPORTED_SCHEMA", "world time presenter")
            if payload.end != receipt.tick:
                raise ValueError("WORLD_TIME_PUBLICATION")
            cue = TimeCue(payload.start, payload.end)
            identifier = (
                "p1-"
                + hashlib.sha256(
                    pack(
                        (
                            "cue-id/v1",
                            fact.header.event_id,
                            "world.time-presenter",
                            str(len(cues)),
                        )
                    )
                ).hexdigest()
            )
            header = EventHeader(
                EventId(identifier),
                cue.schema,
                "world.time-presenter",
                receipt.tick,
                Phase.PRESENT,
                0,
                0,
                len(cues),
                (fact.header.event_id,),
                (),
            )
            cues.append(PresentationEvent(header, cue, "important", "keep_all", ""))
        return tuple(cues)
