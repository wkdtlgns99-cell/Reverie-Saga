from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sqlite3

import pytest

from adapters.sqlite_store import SqliteCommitStore
from app.durable import create_durable, resume_durable
from app.watch_registry import watch_bundle
from contracts.persistence import (
    DurableCheckpoint, DurableTurn, RecoveryResult, WorldUnavailable,
)
from contracts.turn import CapabilityManifest, CommitReceipt, Engine, EngineInvocation, EngineResult, TurnAborted, TurnCommitted
from contracts.watch import WaitCommand
from domain.canonical import array_value, canonical_json, object_value
from orchestration.persistence import project_rows
from tests.unit.durability_fixtures import checkpoint, io, projection_document, requirements, vectors
from tests.unit.watch_fixtures import command, reference


class CountEngine:
    def __init__(self, engine: Engine) -> None:
        self.engine, self.calls = engine, 0

    @property
    def manifest(self) -> CapabilityManifest:
        return self.engine.manifest

    def evaluate(self, invocation: EngineInvocation) -> EngineResult:
        self.calls += 1
        return self.engine.evaluate(invocation)


class UncertainPort:
    def __init__(self, store: SqliteCommitStore, *, commit: bool, unreadable: bool = False) -> None:
        self.store, self.commit, self.unreadable = store, commit, unreadable
        self.persist_calls = self.recover_calls = 0

    def persist(self, turn: DurableTurn) -> CommitReceipt:
        self.persist_calls += 1
        if self.commit:
            self.store.persist(turn)
        raise RuntimeError("injected uncertainty at real persistence boundary")

    def recover(self, turn: DurableTurn) -> RecoveryResult:
        self.recover_calls += 1
        if self.unreadable:
            raise OSError("recovery temporarily unreadable")
        return self.store.recover(turn)


def test_real_main_durable_path(tmp_path: Path) -> None:
    selected = io()
    owner = create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),))
    expected = array_value(vectors()["steps"])
    publications = array_value(reference("expected_publications"))
    fixture = requirements()
    try:
        for index, value in enumerate(array_value(object_value(fixture["trace"])["steps"])):
            request = selected.decode_command(object_value(object_value(value)["command"]))
            publication = owner.submit(request, attachment_id=owner.attachment_id)
            assert canonical_json(selected.encode_publication(publication)) == canonical_json(publications[index])
            current = DurableCheckpoint(owner.snapshot(), owner.protocol())
            assert owner._attachment.store.load() == current
            assert canonical_json(projection_document(project_rows(current, io=selected))) == canonical_json(object_value(expected[index])["rows"])
        assert len(owner.retained_segment().trace.steps) == 9
        saved = DurableCheckpoint(owner.snapshot(), owner.protocol())
    finally:
        owner.close()
    with resume_durable(tmp_path / "work.sqlite", bundles=(watch_bundle(),)) as resumed:
        assert DurableCheckpoint(resumed.snapshot(), resumed.protocol()) == saved
        resumed.submit(command(revision=9, sequence=10), attachment_id=resumed.attachment_id)
        assert resumed.snapshot().tick == 28
        q = selected.decode_pending(resumed.snapshot().pending[0])
        assert q.event.due_tick == 30
        from domain.watch import WatchNpcRecord
        assert next(c.bells for c in resumed.snapshot().components if isinstance(c, WatchNpcRecord)) == 14


def test_passive_wait_durable(tmp_path: Path) -> None:
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        publication = owner.submit(command(WaitCommand(16)), attachment_id=owner.attachment_id)
        assert canonical_json(io().encode_publication(publication)) == canonical_json(array_value(reference("passive_publications"))[0])
        assert canonical_json(projection_document(project_rows(DurableCheckpoint(owner.snapshot(), owner.protocol()), io=io()))) == canonical_json(object_value(array_value(vectors(True)["steps"])[0])["rows"])
        assert len(owner.retained_segment().trace.steps) == 1


def test_disk_precedes_head_and_no_retry_write(tmp_path: Path) -> None:
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        store = owner._attachment.store
        driver = owner._attachment.owner._driver
        initial = DurableCheckpoint(owner.snapshot(), owner.protocol())

        class ObservePort:
            calls = 0

            def persist(self, turn: DurableTurn) -> CommitReceipt:
                self.calls += 1
                receipt = store.persist(turn)
                assert store.load() == turn.next
                assert DurableCheckpoint(driver.snapshot(), driver.protocol()) == initial
                return receipt

            def recover(self, turn: DurableTurn) -> RecoveryResult:
                return store.recover(turn)

        port = ObservePort()
        driver._commit_port = port
        first = owner.submit(command(WaitCommand(2)), attachment_id=owner.attachment_id)
        assert isinstance(first.outcome, TurnCommitted)
        duplicate = owner.submit(command(WaitCommand(2)), attachment_id=owner.attachment_id)
        assert duplicate.outcome == first.outcome and not duplicate.facts and duplicate.diff is None
        rejected = owner.submit(command(sequence=2, revision=0), attachment_id=owner.attachment_id)
        assert not isinstance(rejected.outcome, TurnCommitted)
        assert port.calls == len(store.retained_segment().trace.steps) == 1


def test_confirmed_rollback_atomic_after_real_wake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        store = owner._attachment.store
        previous = DurableCheckpoint(owner.snapshot(), owner.protocol())
        original = store._execute

        def failing(query: str, values: tuple[None | int | float | str | bytes, ...] = ()) -> sqlite3.Cursor:
            result = original(query, values)
            if query.startswith("INSERT INTO pending"):
                raise sqlite3.IntegrityError("after replacing the real consumed wake")
            return result

        monkeypatch.setattr(store, "_execute", failing)
        publication = owner.submit(command(WaitCommand(2)), attachment_id=owner.attachment_id)
        assert isinstance(publication.outcome, TurnAborted)
        assert publication.outcome.failure.code == "SAVE_UNAVAILABLE"
        assert not publication.facts and publication.diff is None
        assert DurableCheckpoint(owner.snapshot(), owner.protocol()) == store.load() == previous
        assert not store.retained_segment().trace.steps


@pytest.mark.parametrize("commit", [False, True])
def test_uncertain_commit_proves_old_or_new_without_reevaluation(tmp_path: Path, commit: bool) -> None:
    bundle = watch_bundle()
    npc = next(b for b in bundle.bindings if b.engine.manifest.engine_id == "watch.npc")
    counter = CountEngine(npc.engine)
    bundle = replace(bundle, bindings=tuple(replace(b, engine=counter) if b is npc else b for b in bundle.bindings))
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(bundle,)) as owner:
        port = UncertainPort(owner._attachment.store, commit=commit)
        owner._attachment.owner._driver._commit_port = port
        publication = owner.submit(command(WaitCommand(16)), attachment_id=owner.attachment_id)
        assert counter.calls == 8 and port.persist_calls == port.recover_calls == 1
        assert isinstance(publication.outcome, TurnCommitted if commit else TurnAborted)
        assert owner.snapshot().tick == (16 if commit else 0)
        assert owner._attachment.store.load() == DurableCheckpoint(owner.snapshot(), owner.protocol())
        if commit:
            assert canonical_json(io().encode_publication(publication)) == canonical_json(array_value(reference("passive_publications"))[0])


@pytest.mark.parametrize("commit", [False, True])
def test_unreadable_recovery_blocks_until_proved(tmp_path: Path, commit: bool) -> None:
    bundle = watch_bundle()
    npc = next(b for b in bundle.bindings if b.engine.manifest.engine_id == "watch.npc")
    counter = CountEngine(npc.engine)
    bundle = replace(bundle, bindings=tuple(replace(b, engine=counter) if b is npc else b for b in bundle.bindings))
    owner = create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(bundle,))
    token = owner.attachment_id
    port = UncertainPort(owner._attachment.store, commit=commit, unreadable=True)
    owner._attachment.owner._driver._commit_port = port
    try:
        with pytest.raises(WorldUnavailable, match="SAVE_UNCERTAIN"):
            owner.submit(command(WaitCommand(16)), attachment_id=token)
        for read in (owner.snapshot, owner.protocol, owner.last_publication, owner.retained_segment):
            with pytest.raises(WorldUnavailable):
                read()
        with pytest.raises(WorldUnavailable):
            owner.submit_json(b'{}', attachment_id=token)
        with pytest.raises(WorldUnavailable):
            owner.export("slot01")
        with pytest.raises(WorldUnavailable):
            owner.load("slot01")
        with pytest.raises(WorldUnavailable):
            owner.recover()
        port.unreadable = False
        resolved = owner.recover()
        assert isinstance(resolved.outcome, TurnCommitted if commit else TurnAborted)
        assert counter.calls == 8 and port.persist_calls == 1
        assert owner.snapshot().tick == (16 if commit else 0)
        if commit:
            retry = owner.submit(command(WaitCommand(16)), attachment_id=owner.attachment_id)
            assert retry.outcome == resolved.outcome and not retry.facts and counter.calls == 8
    finally:
        owner.close()


def test_no_recovery_pending_and_closed_session(tmp_path: Path) -> None:
    from contracts.persistence import SaveError
    owner = create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),))
    with pytest.raises(SaveError, match="NO_RECOVERY_PENDING"):
        owner.recover()
    owner.close()
    owner.close()
    with pytest.raises(WorldUnavailable, match="SESSION_CLOSED"):
        owner.snapshot()


def test_postcommit_real_presentation_failure(tmp_path: Path) -> None:
    from contracts.messages import PresentationEvent, WorldEvent
    from contracts.read_views import ReadPort
    from orchestration.watch import WatchPresenter

    class FailingPresenter(WatchPresenter):
        def map(self, facts: tuple[WorldEvent, ...], receipt: CommitReceipt, committed: ReadPort) -> tuple[PresentationEvent, ...]:
            super().map(facts, receipt, committed)
            raise RuntimeError("after real presenter mapping")

    bundle = watch_bundle()
    bundle = replace(bundle, presenters=tuple(replace(p, presenter=FailingPresenter()) for p in bundle.presenters))
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(bundle,)) as owner:
        publication = owner.submit(command(WaitCommand(2)), attachment_id=owner.attachment_id)
        assert isinstance(publication.outcome, TurnCommitted)
        assert tuple(d.code for d in publication.diagnostics) == ("PRESENTATION_FAILED",)
        assert len(publication.facts) == 2 and publication.diff is not None and not publication.cues
        saved = DurableCheckpoint(owner.snapshot(), owner.protocol())
        assert owner._attachment.store.load() == saved
        duplicate = owner.submit(command(WaitCommand(2)), attachment_id=owner.attachment_id)
        assert duplicate.outcome == publication.outcome and not duplicate.facts
        assert len(owner.retained_segment().trace.steps) == 1
    with resume_durable(tmp_path / "work.sqlite", bundles=(watch_bundle(),)) as restored:
        assert DurableCheckpoint(restored.snapshot(), restored.protocol()) == saved


@pytest.mark.parametrize("feature", ["trial", "encounter", "gauge"])
def test_generic_selected_bundle_durability(tmp_path: Path, feature: str) -> None:
    from app.headless import state_io
    from app.trial_registry import trial_bundle
    from app.encounter_registry import encounter_bundle
    from tests.unit import trial_fixtures, encounter_fixtures, registered_io_fixtures
    if feature == "trial":
        bundle, memory, request = trial_bundle(), trial_fixtures.session(), trial_fixtures.command()
    elif feature == "encounter":
        bundle, memory, request = encounter_bundle(), encounter_fixtures.session(), encounter_fixtures.command()
    else:
        bundle = registered_io_fixtures.bundle()
        memory, request = registered_io_fixtures.session(bundle), registered_io_fixtures.command()
    selected = state_io((bundle,))
    initial = DurableCheckpoint(memory.snapshot(), memory.protocol())
    with create_durable(tmp_path / "work.sqlite", initial, bundles=(bundle,)) as owner:
        publication = owner.submit(request, attachment_id=owner.attachment_id)
        memory.driver.submit(request)
        assert isinstance(publication.outcome, TurnCommitted)
        assert canonical_json(selected.encode_publication(publication)) == canonical_json(selected.encode_publication(memory.last_publication()))
        saved = DurableCheckpoint(owner.snapshot(), owner.protocol())
        assert owner._attachment.store.load() == saved
        owner.export("slot08")
        owner.load("slot08")
        assert DurableCheckpoint(owner.snapshot(), owner.protocol()) == saved
        path = owner.working_path
    with resume_durable(path, bundles=(bundle,)) as restored:
        assert DurableCheckpoint(restored.snapshot(), restored.protocol()) == saved


def test_real_commit_then_exception_resolves_new(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        store = owner._attachment.store
        execute = store._execute

        def fail_after_commit(query: str, values: tuple[None | int | float | str | bytes, ...] = ()) -> sqlite3.Cursor:
            result = execute(query, values)
            if query == "COMMIT":
                raise sqlite3.OperationalError("return lost after real SQL COMMIT")
            return result

        monkeypatch.setattr(store, "_execute", fail_after_commit)
        publication = owner.submit(command(WaitCommand(2)), attachment_id=owner.attachment_id)
        assert isinstance(publication.outcome, TurnCommitted)
        assert store.load() == DurableCheckpoint(owner.snapshot(), owner.protocol())
        assert len(publication.facts) == 2 and owner.protocol().revision == 1


def test_stale_durable_base_blocks_publication(tmp_path: Path) -> None:
    from tests.unit.durability_fixtures import turn
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        store = owner._attachment.store
        store.persist(turn())
        with pytest.raises(WorldUnavailable, match="SAVE_STALE"):
            owner.submit(command(WaitCommand(2)), attachment_id=owner.attachment_id)
        with pytest.raises(WorldUnavailable, match="SAVE_STALE"):
            owner.last_publication()
        assert store.load().protocol.revision == 1
    with resume_durable(tmp_path / "work.sqlite", bundles=(watch_bundle(),)) as restored:
        assert restored.protocol().revision == 1


@pytest.mark.parametrize("mixed", [False, True])
def test_mismatched_recovery_proof_blocks(tmp_path: Path, mixed: bool) -> None:
    from contracts.persistence import RecoveryCommitted
    from domain.primitives import WorldRevision
    with create_durable(tmp_path / "work.sqlite", checkpoint(), bundles=(watch_bundle(),)) as owner:
        store = owner._attachment.store

        class WrongProof:
            def persist(self, turn: DurableTurn) -> CommitReceipt:
                receipt = store.persist(turn)
                return replace(receipt, core_hash="0" * 64)

            def recover(self, turn: DurableTurn) -> RecoveryResult:
                assert isinstance(turn.publication.outcome, TurnCommitted)
                receipt = turn.publication.outcome.receipt
                if mixed:
                    return RecoveryCommitted(DurableCheckpoint(turn.next.core, turn.previous.protocol), receipt)
                return RecoveryCommitted(turn.next, replace(receipt, revision=WorldRevision(receipt.revision + 1)))

        owner._attachment.owner._driver._commit_port = WrongProof()
        with pytest.raises(WorldUnavailable, match="SAVE_UNCERTAIN"):
            owner.submit(command(), attachment_id=owner.attachment_id)
        with pytest.raises(WorldUnavailable):
            owner.snapshot()
        with pytest.raises(WorldUnavailable):
            owner.recover()
        owner._attachment.owner._driver._commit_port = store
        resolved = owner.recover()
        assert isinstance(resolved.outcome, TurnCommitted) and owner.protocol().revision == 1
