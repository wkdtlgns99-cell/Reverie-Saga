"""Bounded communal provisions produced by one NPC on logical time."""

from dataclasses import dataclass

from domain.primitives import EntityId, TypeKey, require_integer, require_namespace
from domain.state_types import ComponentRecord

WORK_PERIOD = 4
STOCK_CAP = 3
STOCK_SCHEMA = TypeKey("quest.provisions", 1)


def stock_at(tick: int) -> int:
    require_integer(tick)
    return min(STOCK_CAP, tick // WORK_PERIOD)


@dataclass(frozen=True, slots=True)
class ProvisionsRecord(ComponentRecord):
    entity_id: EntityId
    stock: int

    def __post_init__(self) -> None:
        if type(self.entity_id) is not str:
            raise ValueError("NPC_WORK_OWNER")
        require_namespace(self.entity_id)
        try:
            require_integer(self.stock, 0, STOCK_CAP)
        except ValueError as error:
            raise ValueError("NPC_WORK_STOCK") from error

    @property
    def schema(self) -> TypeKey:
        return STOCK_SCHEMA
