from __future__ import annotations

from contracts.errors import BootstrapError
from contracts.turn import CapabilityManifest, CompiledSchedule, NodeActivation, NodeKey
from domain.canonical import JsonValue, hash_document
from domain.primitives import Phase, require_namespace


def compile_schedule(manifests: tuple[CapabilityManifest, ...],
                     activations: tuple[NodeActivation, ...]) -> CompiledSchedule:
    by_id = {m.engine_id: m for m in manifests}
    if len(by_id) != len(manifests):
        raise BootstrapError("DUPLICATE_ENGINE", "engine IDs")
    if not manifests:
        raise BootstrapError("UNKNOWN_NODE", "empty schedule")
    nodes: set[NodeKey] = set()
    for manifest in manifests:
        require_namespace(manifest.engine_id)
        if not manifest.phases or len(set(manifest.phases)) != len(manifest.phases):
            raise BootstrapError("UNKNOWN_NODE", "missing/duplicate phases")
        for phase in manifest.phases:
            if phase not in (Phase.PRE_TICK, Phase.RESOLVE, Phase.REACT, Phase.CASCADE, Phase.POST_TICK):
                raise BootstrapError("UNKNOWN_NODE", "non-engine phase")
            nodes.add(NodeKey(phase, manifest.engine_id))
        for access in (*manifest.reads, *manifest.writes):
            if access.phase not in manifest.phases:
                raise BootstrapError("UNKNOWN_NODE", "access phase")
    active = {a.node: a for a in activations}
    if len(active) != len(activations) or set(active) != nodes:
        raise BootstrapError("INVALID_ACTIVATION", "one activation per node")
    for manifest in manifests:
        lanes = {active[NodeKey(p, manifest.engine_id)].lane for p in manifest.phases}
        if len(lanes) != 1 or not lanes <= {"A", "B"}:
            raise BootstrapError("INVALID_LANE", "engine lanes")
        if "B" in lanes and manifest.emits:
            raise BootstrapError("INVALID_LANE", "B cannot emit simulation facts")
    writers: dict[tuple[Phase, str, str], str] = {}
    edges: dict[NodeKey, set[NodeKey]] = {n: set() for n in nodes}
    for manifest in manifests:
        for write in manifest.writes:
            target = (write.phase, write.family.component, write.family.field)
            if target in writers:
                raise BootstrapError("WRITE_CONFLICT", str(target))
            writers[target] = manifest.engine_id
        for dependency in manifest.depends_on:
            node = NodeKey(dependency.at, manifest.engine_id)
            if node not in nodes or dependency.after not in nodes or dependency.after.phase > node.phase:
                raise BootstrapError("UNKNOWN_NODE", "invalid dependency")
            if active[node].lane == "A" and active[dependency.after].lane == "B":
                raise BootstrapError("INVALID_LANE", "A depends on B")
            edges[node].add(dependency.after)
    for node in nodes:
        edges[node].update(n for n in nodes if n.phase < node.phase)
    ordered: list[NodeKey] = []
    remaining = set(nodes)
    while remaining:
        ready = sorted((n for n in remaining if not (edges[n] & remaining)),
                       key=lambda n: (n.phase, n.engine_id))
        if not ready:
            raise BootstrapError("DEPENDENCY_CYCLE", "schedule cycle")
        chosen = ready[0]
        ordered.append(chosen)
        remaining.remove(chosen)
    documents: list[JsonValue] = []
    for node in ordered:
        m, a = by_id[node.engine_id], active[node]
        documents.append({
            "phase": node.phase.name, "engine_id": node.engine_id, "lane": a.lane,
            "reads": tuple(sorted(f"{x.family.component}.{x.family.field}" for x in m.reads if x.phase == node.phase)),
            "writes": tuple(sorted(f"{x.family.component}.{x.family.field}" for x in m.writes if x.phase == node.phase)),
            "depends_on": tuple({"phase": d.after.phase.name, "engine_id": d.after.engine_id}
                                for d in sorted(m.depends_on, key=lambda d: (d.after.phase, d.after.engine_id)) if d.at == node.phase),
            "action_kinds": tuple({"kind": k.kind, "version": k.version} for k in sorted(a.action_kinds, key=lambda k: (k.kind, k.version))),
            "on_matching_events": a.on_matching_events, "every_tick": a.every_tick,
            "emits": tuple({"kind": k.kind, "version": k.version} for k in sorted(m.emits, key=lambda k: (k.kind, k.version))),
            "consumes": tuple({"kind": k.kind, "version": k.version} for k in sorted(m.consumes, key=lambda k: (k.kind, k.version))),
            "cost_class": m.cost_class,
        })
    return CompiledSchedule(tuple(ordered), hash_document("schedule/v1", {"version": 1, "nodes": tuple(documents)}))
