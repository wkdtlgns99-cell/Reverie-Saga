"""Static adapter routing must never retain record validity across calls."""

from dataclasses import replace
import pytest
from app.headless import state_io
from contracts.errors import SchemaError
from tests.unit.registered_io_fixtures import GaugeRecord, ACTOR, bundle, session


def test_later_invalid_record_is_rejected_after_valid_source() -> None:
    io = state_io((bundle(),))
    core = session().snapshot()
    first = io.encode_core(core)
    for value in (True, 10, -10):
        invalid = replace(core, components=(GaugeRecord(ACTOR, value, "계기"),))
        with pytest.raises(SchemaError) as caught:
            io.encode_core(invalid)
        assert (caught.value.code, caught.value.path) == (
            "INVALID_COMPONENT",
            "core.component.fields",
        )
    assert io.decode_core(first) == core
