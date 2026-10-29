"""Commit documents are fresh actual results,not cached candidate success."""

from pathlib import Path
from typing import cast
import pytest
from app.headless import state_io
from app.durable import create_durable
from contracts.persistence import DurableCheckpoint
from contracts.turn import TurnCommitted, TurnRejected, TurnAborted
from domain.canonical import canonical_json
from orchestration.turn import Driver
from orchestration.serialization import RegisteredStateIO
from tests.unit.registered_io_fixtures import bundle, session, command
from tests.integration.test_durable_turn import UncertainPort


def test_same_actual_submit_yields_exact_owned_checkpoint() -> None:
    private, public = session(), session()
    driver = cast(Driver, private.driver)
    previous = None
    for sequence, amount, value in ((1, 3, 5), (2, -3, 2), (3, 1, 3)):
        request = command(sequence, amount, sequence - 1)
        outcome, proof = driver._submit_with_checkpoint(request)
        assert outcome == public.driver.submit(request) and isinstance(outcome, TurnCommitted)
        assert (
            proof is not None
            and proof.core is private.snapshot()
            and proof.protocol is private.protocol()
        )
        assert proof.core_document.to_bytes() == canonical_json(
            proof.owner.encode_core(public.snapshot())
        )
        assert proof.protocol_document.to_bytes() == canonical_json(
            proof.owner.encode_protocol(public.protocol())
        )
        assert (
            proof.core_hash
            == proof.owner.hash_core(private.snapshot())
            == outcome.receipt.core_hash
        )
        assert getattr(private.snapshot().components[0], "value") == value
        if previous is not None:
            assert previous.core_document.to_bytes() != proof.core_document.to_bytes()
        previous = proof
    duplicate, proof = driver._submit_with_checkpoint(request)
    assert duplicate == outcome and proof is None and not private.last_publication().facts
    rejected, proof = driver._submit_with_checkpoint(command(4, 1, 0))
    assert (
        isinstance(rejected, TurnRejected)
        and rejected.failure.code == "STALE_REVISION"
        and proof is None
    )


def test_foreign_io_is_not_a_commit_proof_consumer() -> None:
    owner = session()
    driver = cast(Driver, owner.driver)
    other = cast(RegisteredStateIO, state_io((bundle(),)))
    assert not driver._encoding_owner(other)
    _, proof = driver._submit_with_checkpoint(command())
    assert proof is not None
    with pytest.raises(ValueError, match="foreign checkpoint encoding"):
        other._validate_effects_encoding(
            proof, command(), owner.last_publication().outcome, (), None
        )


@pytest.mark.parametrize("commit", (False, True))
def test_uncertain_durability_only_publishes_confirmed_documents(
    tmp_path: Path, commit: bool
) -> None:
    initial = session()
    checkpoint = DurableCheckpoint(initial.snapshot(), initial.protocol())
    owner = create_durable(tmp_path / "game.sqlite", checkpoint, bundles=(bundle(),))
    try:
        driver = owner._attachment.owner._driver
        store = owner._attachment.store
        driver._commit_port = UncertainPort(store, commit=commit)
        outcome, proof = driver._submit_with_checkpoint(command())
        assert isinstance(outcome, TurnCommitted if commit else TurnAborted)
        assert (proof is not None) is commit
        assert store.load() == DurableCheckpoint(owner.snapshot(), owner.protocol())
        if not commit:
            assert store.load() == checkpoint
    finally:
        owner.close()
