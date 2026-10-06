from __future__ import annotations

from dataclasses import replace

import pytest

from app.feature_registry import feature_bundles
from contracts.errors import BootstrapError
from contracts.turn import Dependency
from domain.primitives import EntityId, Phase
from orchestration.scheduler import compile_schedule


def test_registry_permutation() -> None:
    bindings = feature_bundles(EntityId("actor:toy"))[0].bindings
    manifests = tuple(b.engine.manifest for b in bindings)
    activations = tuple(a for b in bindings for a in b.activations)
    assert compile_schedule(manifests, activations) == compile_schedule(manifests[::-1], activations[::-1])


def test_writer_conflict() -> None:
    bindings = feature_bundles(EntityId("actor:toy"))[0].bindings
    first = bindings[0]
    other = replace(first.engine.manifest, engine_id="skeleton.other")
    activation = replace(first.activations[0], node=replace(first.activations[0].node, engine_id="skeleton.other"))
    with pytest.raises(BootstrapError, match="WRITE_CONFLICT"):
        compile_schedule((first.engine.manifest, other), (*first.activations, activation))


def test_cycle() -> None:
    first = feature_bundles(EntityId("actor:toy"))[0].bindings[0]
    node = first.activations[0].node
    other = replace(node, engine_id="skeleton.other")
    a = replace(first.engine.manifest, depends_on=(Dependency(Phase.RESOLVE, other),))
    b = replace(first.engine.manifest, engine_id=other.engine_id, writes=(), depends_on=(Dependency(Phase.RESOLVE, node),))
    with pytest.raises(BootstrapError, match="DEPENDENCY_CYCLE"):
        compile_schedule((a, b), (*first.activations, replace(first.activations[0], node=other)))


def test_activation_rights() -> None:
    first = feature_bundles(EntityId("actor:toy"))[0].bindings[0]
    with pytest.raises(BootstrapError, match="INVALID_LANE"):
        compile_schedule((first.engine.manifest,), (replace(first.activations[0], lane="B"),))
    with pytest.raises(BootstrapError, match="INVALID_ACTIVATION"):
        compile_schedule((first.engine.manifest,), ())
