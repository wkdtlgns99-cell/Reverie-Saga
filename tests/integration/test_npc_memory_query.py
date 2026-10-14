from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from app.npc_memory import read_memory
from app.npc_memory_prepare import memory_brief
from app.npc_memory_query import EvidenceQuery, select_evidence
from domain.npc_memory import EvidenceKind
from tests.integration.test_npc_memory import session_at
from tests.unit.quest_fixtures import content


def test_real_saved_evidence_filters_order_and_brief_without_mutation(tmp_path: Path) -> None:
    selected = content()
    path = tmp_path / "game.sqlite"
    session = session_at(path, 11)
    session.close()
    before = path.read_bytes()
    context = read_memory(path, selected, selected.definition.layout.npc_id)
    assert [entry.kind for entry in select_evidence(context, EvidenceQuery())] == [
        "completion_reported",
        "accepted",
    ]
    assert [entry.observed_at for entry in select_evidence(context, EvidenceQuery(since=11))] == [
        11
    ]
    assert select_evidence(context, EvidenceQuery(since=12)) == ()
    assert select_evidence(context, EvidenceQuery(limit=0)) == ()
    assert [entry.kind for entry in select_evidence(context, EvidenceQuery(limit=1))] == [
        "completion_reported"
    ]
    assert [
        entry.kind for entry in select_evidence(context, EvidenceQuery(kind="accepted", since=2))
    ] == ["accepted"]
    assert select_evidence(context, EvidenceQuery(kind="accepted", since=3)) == ()
    assert select_evidence(context, EvidenceQuery(subject_id="actor:foreign")) == ()
    for subject in (context.source.actor_id, context.source.quest_id):
        assert len(select_evidence(context, EvidenceQuery(subject_id=subject))) == 2
    brief = memory_brief(context).text
    assert brief.index('"kind":"completion_reported"') < brief.index('"kind":"accepted"')
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "field,value",
    (
        ("since", True),
        ("since", -1),
        ("since", 1.5),
        ("limit", True),
        ("limit", -1),
        ("limit", 3),
        ("subject", "item:foreign"),
        ("subject", "actor:bad space"),
        ("kind", "defeat"),
        ("kind", False),
    ),
)
def test_invalid_query_rejects_exact_types_and_bounds(field: str, value: object) -> None:
    with pytest.raises(ValueError, match="NPC_MEMORY_QUERY"):
        if field == "since":
            EvidenceQuery(since=cast(int, value))
        elif field == "limit":
            EvidenceQuery(limit=cast(int, value))
        elif field == "subject":
            EvidenceQuery(subject_id=cast(str, value))
        else:
            EvidenceQuery(kind=cast(EvidenceKind, value))
