"""Independent speech arithmetic and persistent own-memory boundaries."""

from dataclasses import replace

import pytest

from app.world_catalog import load_world
from domain.world import elaborate_place
from domain.world_conversation import (
    ConversationState,
    begin_reply,
    begin_speech,
    continue_speech,
    retrieve_memories,
    speech_seconds,
)


@pytest.mark.parametrize(
    "text,rate,expected",
    [
        ("가", 6, 1),
        ("가" * 6, 6, 1),
        ("가" * 7, 6, 2),
        ("가" * 13, 6, 3),
        ("말" * 65, 4, 17),
        ("a " * 256, 6, 86),
    ],
)
def test_speech_duration_counts_exact_nfc_codepoints(text: str, rate: int, expected: int) -> None:
    assert speech_seconds(text, rate) == expected


@pytest.mark.parametrize("text", ["", " \n\t", "a" * 513, "a\x00b", "\ud800", "가"])
def test_invalid_speech_rejects_before_delivery(text: str) -> None:
    with pytest.raises(ValueError, match="DIALOGUE_TEXT"):
        speech_seconds(text, 6)


def test_long_utterance_segments_preserve_one_exchange_and_exact_elapsed_time() -> None:
    resident = elaborate_place(load_world(), "place:p0-a").residents[0]
    state, elapsed = begin_speech(
        ConversationState(), resident, "place:p0-a", "가" * 100, "speech:s1", 0
    )
    assert elapsed == 16 and state.remaining == 1 and state.speaker == "player"
    again, elapsed = continue_speech(state, "speech:s1")
    assert elapsed == 1 and again.remaining == 0 and again.speaker == ""
    assert again.exchanges == state.exchanges
    assert again.exchanges[0].player_end == 17
    resident = replace(resident, disposition="신중함")
    reply, elapsed = begin_reply(
        again, resident, "speech:s1", "답" * 65, "gemini-3.5-flash-lite", "0" * 64, "none", 17
    )
    assert elapsed == 16 and reply.remaining == 1 and reply.exchanges[0].reply_end == 34
    completed, elapsed = continue_speech(reply, "speech:s1")
    assert elapsed == 1 and len(completed.exchanges) == 1
    assert completed.exchanges[0].player_text == "가" * 100
    with pytest.raises(ValueError, match="DIALOGUE_ALREADY_REPLIED"):
        begin_reply(completed, resident, "speech:s1", "또 답", "test", "0" * 64, "none", 34)


def test_retrieval_preserves_older_relevant_memory_and_excludes_other_npc() -> None:
    residents = elaborate_place(load_world(), "place:p0-a").residents
    state = ConversationState()
    tick = 0
    for i in range(10):
        npc = residents[0] if i != 1 else residents[1]
        text = (
            "내 비밀 암호는 파란도토리야"
            if i == 0
            else "남의 비밀은 붉은조개야"
            if i == 1
            else "안녕 " + str(i)
        )
        state, elapsed = begin_speech(state, npc, "place:p0-a", text, "speech:s" + str(i), tick)
        tick += elapsed
    memories = retrieve_memories(state, residents[0].id, "내 비밀 암호 기억해?")
    assert any("파란도토리" in e.player_text for e in memories)
    assert memories[-1] == state.exchanges[-1]
    assert all(e.npc_id == residents[0].id for e in memories)
    assert not any("붉은조개" in e.player_text for e in memories)
    context_memories = retrieve_memories(
        state, residents[0].id, "내 비밀 암호 기억해?", exclude_speech_id="speech:s9"
    )
    assert context_memories[-1] == state.exchanges[-2]
    assert all(e.speech_id != "speech:s9" for e in context_memories)
    assert len(state.exchanges) == 10
    assert retrieve_memories(state, residents[0].id, "안녕", byte_budget=0) == ()
