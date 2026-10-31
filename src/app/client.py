"""Provisional 2D playable boundary harness;not the final HD-2D renderer."""

from __future__ import annotations

import argparse
from collections import deque
from collections.abc import Sequence
from concurrent.futures import CancelledError, Future
from dataclasses import replace
from functools import partial
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from app.client_worker import ClientWorker
from app.client_text import QUEST_STAGE_NAMES, status_text
from app.scenarios import select_scenario
from app.quest import client_quest
from contracts.dialogue import QuestContent
from contracts.client import ClientRequest, ClientUpdate, ClientView
from domain.encounter import ACTOR_HP_MAX, ENEMY_HP_MAX, STAMINA_MAX
from domain.watch import CHARGE_MAX, WAIT_MAX
from domain.scenario import resolve_selection, LEGACY, Scenario

CELL_PIXELS = 144
POLL_MS = 20
BACKGROUND = "#151c27"
LOG_LINE_LIMIT = 200
LOG_TEXT_LIMIT = 500
LABELS: tuple[tuple[ClientRequest, str], ...] = (
    ("up", "↑ 위"),
    ("left", "← 왼쪽"),
    ("down", "↓ 아래"),
    ("right", "→ 오른쪽"),
    ("open", "문 열기"),
    ("close", "문 닫기"),
    ("attack", "공격"),
    ("rest", "휴식"),
    ("wait", "기다리기"),
    ("bell", "NPC 호출"),
    ("save", "저장"),
    ("load", "불러오기"),
    ("retry", "직전 명령 재전송"),
    ("recover", "저장 상태 복구"),
)
KEYS: dict[str, ClientRequest] = {
    "Up": "up",
    "Down": "down",
    "Left": "left",
    "Right": "right",
    "w": "up",
    "s": "down",
    "a": "left",
    "d": "right",
}


class PlayWindow:
    def __init__(
        self,
        root: tk.Tk | tk.Toplevel,
        path: Path,
        layout: Scenario = LEGACY,
        *,
        scenario: Scenario = LEGACY,
        quest_content: QuestContent | None = None,
        npc_memory: bool = False,
        npc_work: bool = False,
        npc_cycle: bool = False,
        npc_aid: bool = False,
        npc_supply_aid: bool = False,
        npc_call_aid: bool = False,
        npc_patrol: bool = False,
        npc_talk_pause: bool = False,
        npc_quest_patrol: bool = False,
        npc_call_pause: bool = False,
        npc_ready_patrol: bool = False,
        npc_reach_aid: bool = False,
    ) -> None:
        layout = resolve_selection(layout, scenario)
        self.root = root
        self.worker = ClientWorker(
            path,
            layout,
            quest_content=quest_content,
            npc_memory=npc_memory,
            npc_work=npc_work,
            npc_cycle=npc_cycle,
            npc_aid=npc_aid,
            npc_supply_aid=npc_supply_aid,
            npc_call_aid=npc_call_aid,
            npc_patrol=npc_patrol,
            npc_talk_pause=npc_talk_pause,
            npc_quest_patrol=npc_quest_patrol,
            npc_call_pause=npc_call_pause,
            npc_ready_patrol=npc_ready_patrol,
            npc_reach_aid=npc_reach_aid,
        )
        self._quest_content = quest_content
        self._npc_memory = npc_memory
        self.mode_label = (
            (
                "NPC 인접 통행 지원·지원 준비 우선·호출 응답 대기·의뢰 순찰·대화 대기·"
                "호출 지원·물자·반복 작업·기억 모드"
            )
            if npc_reach_aid
            else (
                "NPC 지원 준비 우선·호출 응답 대기·의뢰 순찰·대화 대기·"
                "호출 지원·물자·반복 작업·기억 모드"
            )
            if npc_ready_patrol
            else "NPC 호출 응답 대기·의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드"
            if npc_call_pause
            else "NPC 의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드"
            if npc_quest_patrol
            else "NPC 대화 대기·순찰·호출 지원·물자·반복 작업·기억 모드"
            if npc_talk_pause
            else "NPC 순찰·호출 지원·물자·반복 작업·기억 모드"
            if npc_patrol
            else "NPC 호출 지원·물자·반복 작업·기억 모드"
            if npc_call_aid
            else "NPC 물자 2개 확보 후 지원·반복 작업·기억 모드"
            if npc_supply_aid
            else "NPC 의뢰 지원·반복 작업·기억 모드"
            if npc_aid
            else "NPC 반복 작업·기억 모드"
            if npc_cycle
            else (
                "NPC 비축·기억 모드"
                if npc_work
                else "NPC 대화 기억 모드"
                if npc_memory
                else "기본 모드"
            )
        )
        self.memory_button: ttk.Button | None = None
        self.recent_memory_button: ttk.Button | None = None
        self.activity_button: ttk.Button | None = None
        self.view: ClientView | None = None
        self.last_update: ClientUpdate | None = None
        self.history: deque[str] = deque(maxlen=LOG_LINE_LIMIT)
        self.closed = False
        self._closing = False
        self._close_future: Future[None] | None = None
        self._pending: Future[ClientUpdate] | None = None
        self._logger = logging.getLogger(__name__)
        self.buttons: dict[ClientRequest, ttk.Button] = {}
        self.status = tk.StringVar(root, "연결 중…")
        self.status_text = tk.StringVar(root, "연결 중…")
        self.stats = tk.StringVar(root, "게임 상태를 읽는 중…")
        self.notices = tk.StringVar(root, "")
        self.path_text = tk.StringVar(root, str(path))
        self.wait_seconds = tk.StringVar(root, "1")
        self.slot = tk.StringVar(root, "slot01")
        self._build()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<KeyPress>", self._key)
        self._send("attach")
        root.after(POLL_MS, self._poll)

    @property
    def busy(self) -> bool:
        return self._pending is not None or self._closing

    def _build(self) -> None:
        root = self.root
        root.title("Reverie Saga · 플레이 프로토타입")
        root.configure(background=BACKGROUND)
        root.resizable(True, True)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background=BACKGROUND)
        style.configure("TLabel", background=BACKGROUND, foreground="#e3eaf5")
        style.configure("TButton", font=("맑은 고딕", 10), padding=8)
        style.configure("History.TButton", font="TkDefaultFont", padding=0, borderwidth=0)
        panel = ttk.Frame(root, padding=18)
        panel.pack(fill="both", expand=True)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(2, weight=3, minsize=120)
        panel.rowconfigure(8, weight=1, minsize=60)
        ttk.Label(panel, text="REVERIE SAGA", font=("Segoe UI", 21, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(panel, text="작은 코어 연결 테스트 · " + self.mode_label, wraplength=740).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 14)
        )
        play_panel = ttk.Frame(panel)
        play_panel.grid(row=2, column=0, columnspan=2, sticky="nsew")
        play_panel.columnconfigure(0, weight=1)
        play_panel.rowconfigure(0, weight=1)
        self.play_viewport = tk.Canvas(
            play_panel,
            width=CELL_PIXELS * 6,
            height=CELL_PIXELS * 3,
            background=BACKGROUND,
            highlightthickness=0,
        )
        self.play_viewport.grid(row=0, column=0, sticky="nsew")
        self.play_vertical_scrollbar = ttk.Scrollbar(play_panel, command=self.play_viewport.yview)
        self.play_vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        self.play_horizontal_scrollbar = ttk.Scrollbar(
            play_panel, orient="horizontal", command=self.play_viewport.xview
        )
        self.play_horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        self.play_viewport.configure(
            yscrollcommand=self.play_vertical_scrollbar.set,
            xscrollcommand=self.play_horizontal_scrollbar.set,
        )
        self.play_content = ttk.Frame(self.play_viewport)
        self._play_window = self.play_viewport.create_window(
            0, 0, anchor="nw", window=self.play_content
        )
        self._play_width = 0
        self.play_content.bind("<Configure>", self._layout_play_area)
        self.play_viewport.bind("<Configure>", self._layout_play_area)
        root.bind("<MouseWheel>", self._scroll_play_area, add="+")
        root.bind("<FocusIn>", self._reveal_play_focus, add="+")
        self.canvas = tk.Canvas(
            self.play_content,
            width=CELL_PIXELS * 3,
            height=CELL_PIXELS * 3,
            background=BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, sticky="n")
        controls = ttk.Frame(self.play_content, padding=(18, 0, 0, 0))
        controls.grid(row=0, column=1, sticky="n")
        ttk.Label(controls, textvariable=self.stats, font=("맑은 고딕", 11)).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        labels = LABELS if self._quest_content is None else (*LABELS, ("talk", "NPC 대화·보고"))
        for index, (request, label) in enumerate(labels):
            button = ttk.Button(controls, text=label, command=partial(self._send, request))
            button.grid(row=1 + index // 2, column=index % 2, sticky="ew", padx=3, pady=3)
            self.buttons[request] = button
        if self._npc_memory:
            self.memory_button = ttk.Button(
                controls, text="NPC 대화 기억", command=self._inspect_memory
            )
            self.memory_button.grid(
                row=1 + len(labels) // 2, column=len(labels) % 2, sticky="ew", padx=3, pady=3
            )
            self.recent_memory_button = ttk.Button(
                controls, text="최근 대화 기억", command=self._inspect_recent_memory
            )
            self.recent_memory_button.grid(
                row=9, column=0, columnspan=2, sticky="ew", padx=3, pady=3
            )
            self.activity_button = ttk.Button(
                controls, text="NPC 활동 기록", command=self._inspect_activity
            )
            self.activity_button.grid(row=10, column=0, columnspan=2, sticky="ew", padx=3, pady=3)
        wait_row = 11 if self._npc_memory else 9
        ttk.Label(controls, text="대기 시간(게임 초 · Enter)").grid(
            row=wait_row, column=0, sticky="w"
        )
        self.wait_input = ttk.Spinbox(
            controls, from_=1, to=WAIT_MAX, textvariable=self.wait_seconds, width=10
        )
        self.wait_input.grid(row=wait_row, column=1, sticky="ew", pady=6)
        self.wait_input.bind("<Return>", lambda _event: self._send("wait"))
        self.wait_input.bind("<KP_Enter>", lambda _event: self._send("wait"))
        ttk.Label(controls, text="저장 슬롯").grid(row=wait_row + 1, column=0, sticky="w")
        self.slot_input = ttk.Combobox(
            controls,
            values=tuple(f"slot0{index}" for index in range(1, 9)),
            textvariable=self.slot,
            state="readonly",
            width=10,
        )
        self.slot_input.grid(row=wait_row + 1, column=1, sticky="ew")
        self.slot_preview_button = ttk.Button(
            controls, text="선택 슬롯 정보", command=self._inspect_slot
        )
        self.slot_preview_button.grid(
            row=wait_row + 2, column=0, columnspan=2, sticky="ew", padx=3, pady=3
        )
        self.previous_slot_preview_button = ttk.Button(
            controls, text="이전 저장 정보", command=self._inspect_previous_slot
        )
        self.previous_slot_preview_button.grid(
            row=wait_row + 3, column=0, sticky="ew", padx=3, pady=3
        )
        previous_load = ttk.Button(
            controls, text="이전 저장 불러오기", command=partial(self._send, "load_previous")
        )
        previous_load.grid(row=wait_row + 3, column=1, sticky="ew", padx=3, pady=3)
        self.buttons["load_previous"] = previous_load
        ttk.Label(panel, text="파랑: 플레이어   빨강: 적   금색: 문   초록: NPC   회색: 벽").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        ttk.Label(panel, text="WASD / 방향키 이동 · 문 옆에서 열기 · 적 옆에서 공격").grid(
            row=4, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(panel, textvariable=self.status_text, wraplength=740).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        self.debug_details = ttk.Label(panel, textvariable=self.notices, wraplength=740)
        ttk.Checkbutton(panel, text="기술 정보 표시", command=self._toggle_details).grid(
            row=6, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(panel, textvariable=self.path_text, wraplength=740).grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )
        log_heading = ttk.Frame(panel)
        log_heading.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        ttk.Label(log_heading, text=f"행동·대화 기록 · 최근 {LOG_LINE_LIMIT}줄").pack(side="left")
        self.log_latest_button = ttk.Button(
            log_heading,
            text="최신 기록으로",
            style="History.TButton",
            command=lambda: self.log_text.see("end"),
        )
        self.log_latest_button.pack(side="right")
        log_panel = ttk.Frame(panel)
        log_panel.grid(row=8, column=0, columnspan=2, sticky="nsew")
        self.log_text = tk.Text(
            log_panel,
            height=6,
            width=76,
            wrap="word",
            state="disabled",
            background="#101722",
            foreground="#e3eaf5",
            font=("맑은 고딕", 10),
        )
        self.log_scrollbar = ttk.Scrollbar(log_panel, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)
        self.log_scrollbar.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True)

    def _toggle_details(self) -> None:
        if self.debug_details.winfo_manager():
            self.debug_details.grid_remove()
        else:
            self.debug_details.grid(row=10, column=0, columnspan=2, sticky="w")

    def _layout_play_area(self, event: tk.Event[tk.Misc]) -> None:
        width = max(self.play_viewport.winfo_width(), self.play_content.winfo_reqwidth())
        # Own the embedded width so Configure callbacks settle after a resize.
        if self._play_width != width:
            self.play_viewport.itemconfigure(self._play_window, width=width)
            self._play_width = width
        self.play_viewport.configure(
            scrollregion=(
                0,
                0,
                width,
                max(self.play_viewport.winfo_height(), self.play_content.winfo_reqheight()),
            )
        )

    def _scroll_play_area(self, event: tk.Event[tk.Misc]) -> str | None:
        if not event.delta or isinstance(event.widget, (ttk.Spinbox, ttk.Combobox)):
            return None
        widget: tk.Misc | None = event.widget
        while widget is not None and widget is not self.play_content:
            if widget is self.play_viewport:
                break
            widget = widget.master
        if widget is None:
            return None
        units = max(1, abs(event.delta) // 120)
        # Tk's Shift mask is bit0;non-numeric event state has no known modifiers.
        horizontal = isinstance(event.state, int) and event.state & 0x1
        scroll = self.play_viewport.xview_scroll if horizontal else self.play_viewport.yview_scroll
        scroll(-units if event.delta > 0 else units, "units")
        return "break"

    def _reveal_play_focus(self, event: tk.Event[tk.Misc]) -> None:
        target = event.widget
        if self._closing or self.closed or not isinstance(target, tk.Misc):
            return
        widget: tk.Misc | None = target
        while widget is not None and widget is not self.play_content:
            widget = widget.master
        if widget is None or not target.winfo_ismapped():
            return
        viewport = self.play_viewport
        left = target.winfo_rootx() - self.play_content.winfo_rootx()
        top = target.winfo_rooty() - self.play_content.winfo_rooty()
        width, height = target.winfo_width(), target.winfo_height()
        visible_width, visible_height = viewport.winfo_width(), viewport.winfo_height()
        x, y = viewport.canvasx(0), viewport.canvasy(0)
        # Reveal only the clipped axis;oversized targets keep their leading edge visible.
        if left < x or left + width > x + visible_width:
            offset = left if left < x or width > visible_width else left + width - visible_width
            viewport.xview_moveto(offset / max(1, self.play_content.winfo_width()))
        if top < y or top + height > y + visible_height:
            offset = top if top < y or height > visible_height else top + height - visible_height
            viewport.yview_moveto(offset / max(1, self.play_content.winfo_height()))

    def _append_messages(self, messages: tuple[str, ...]) -> None:
        follow_tail = not self.history or self.log_text.yview()[1] >= 1.0
        top_line = int(self.log_text.index("@0,0").split(".")[0])
        discarded = max(0, len(self.history) + len(messages) - LOG_LINE_LIMIT)
        prefix = "" if self.view is None else f"[{self.view.tick}초 · 턴 {self.view.revision}] "
        for message in messages:
            line = prefix + message.replace("\r", " ").replace("\n", " ")
            self.history.append(line[:LOG_TEXT_LIMIT])
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "\n".join(self.history))
        self.log_text.configure(state="disabled")
        if follow_tail:
            self.log_text.see("end")
        else:
            # Eviction shifts the retained record's logical line toward the top.
            self.log_text.yview(f"{max(1, top_line - discarded)}.0")

    def _key(self, event: tk.Event[tk.Misc]) -> None:
        if isinstance(event.widget, (ttk.Entry, ttk.Spinbox, ttk.Combobox, tk.Text)):
            return
        # Control and Alt/Mod1 belong to shortcuts;Shift and CapsLock still allow movement.
        if isinstance(event.state, int) and event.state & (0x4 | 0x8 | 0x20000):
            return
        key = event.keysym.lower() if len(event.keysym) == 1 else event.keysym
        request = KEYS.get(key)
        if request is not None:
            self._send(request)

    def _enable(self, enabled: bool) -> None:
        for button in self.buttons.values():
            button.configure(state="normal" if enabled else "disabled")
        if self.memory_button is not None:
            self.memory_button.configure(state="normal" if enabled else "disabled")
        if self.recent_memory_button is not None:
            self.recent_memory_button.configure(state="normal" if enabled else "disabled")
        if self.activity_button is not None:
            self.activity_button.configure(state="normal" if enabled else "disabled")
        self.slot_preview_button.configure(state="normal" if enabled else "disabled")
        self.previous_slot_preview_button.configure(state="normal" if enabled else "disabled")
        self.wait_input.configure(state="normal" if enabled else "disabled")
        self.slot_input.configure(state="readonly" if enabled else "disabled")

    def _send(self, request: ClientRequest) -> None:
        if self.busy:
            return
        try:
            seconds = int(self.wait_seconds.get()) if request == "wait" else 1
        except ValueError:
            self.status.set("INVALID_INPUT · 대기 시간에 정수를 입력하세요.")
            message = status_text("INVALID_INPUT")
            self.status_text.set(message)
            if not self.history or not self.history[-1].endswith(message):
                self._append_messages((message,))
            return
        message = "처리 중…"
        if request == "talk":
            message = "대화 결과를 확인하는 중입니다."
        elif request == "load_previous":
            message = "이전 저장을 별도 진행 파일로 불러오는 중입니다."
        self._begin_request(
            self.worker.request(request, seconds=seconds, slot_id=self.slot.get()), message=message
        )

    def _inspect_memory(self) -> None:
        if not self.busy:
            self._begin_request(
                self.worker.inspect_memory(),
                message="NPC 대화 기억을 확인하는 중입니다. 게임 시간은 흐르지 않습니다.",
            )

    def _inspect_recent_memory(self) -> None:
        if not self.busy:
            self._begin_request(
                self.worker.inspect_recent_memory(),
                message="최근 NPC 대화 기억을 확인하는 중입니다. 게임 시간은 흐르지 않습니다.",
            )

    def _inspect_slot(self) -> None:
        if not self.busy:
            self._begin_request(
                self.worker.inspect_slot(self.slot.get()),
                message="저장 슬롯 정보를 확인하는 중입니다. 현재 진행은 유지됩니다.",
            )

    def _inspect_activity(self) -> None:
        if not self.busy:
            self._begin_request(
                self.worker.inspect_activity(),
                message="NPC 활동 기록을 확인하는 중입니다. 게임 시간은 흐르지 않습니다.",
            )

    def _inspect_previous_slot(self) -> None:
        if not self.busy:
            self._begin_request(
                self.worker.inspect_previous_slot(self.slot.get()),
                message="이전 저장 정보를 확인하는 중입니다. 현재 진행은 유지됩니다.",
            )

    def _begin_request(self, pending: Future[ClientUpdate], *, message: str = "처리 중…") -> None:
        self._pending = pending
        self.status.set(message)
        self.status_text.set(message)
        self._enable(False)

    def _poll(self) -> None:
        if self.closed:
            return
        try:
            if self._pending is not None and self._pending.done():
                pending, self._pending = self._pending, None
                error = (
                    CancelledError("client request cancelled")
                    if pending.cancelled()
                    else pending.exception()
                )
                if error is None:
                    update = pending.result()
                else:
                    if not isinstance(error, Exception):
                        raise error
                    self._logger.error(
                        "client request Future failed",
                        exc_info=(type(error), error, error.__traceback__),
                    )
                    previous = self.last_update or ClientUpdate(
                        None, "CONNECTING", (), "", self.path_text.get()
                    )
                    update = replace(
                        previous,
                        status="CLIENT_ERROR",
                        notices=(str(error),),
                        messages=(status_text("CLIENT_ERROR"),),
                        reset_log=False,
                    )
                try:
                    self._render(update)
                except Exception as error:
                    self._logger.exception("client rendering failed")
                    self._report_render_failure(update, error)
                finally:
                    self._enable(not self._closing)
            if self._close_future is not None and self._close_future.done():
                try:
                    self._close_future.result()
                finally:
                    self.closed = True
                    self.root.destroy()
        finally:
            # An exceptional callback must not silently terminate the input/close polling loop.
            if not self.closed:
                self.root.after(POLL_MS, self._poll)

    def _report_render_failure(self, update: ClientUpdate, error: Exception) -> None:
        # The Brain result may already be committed. Keep its view/attachment;report the
        # display failure through independent status fields without calling the renderer again.
        failed = replace(
            update,
            status="CLIENT_ERROR",
            notices=(str(error),),
            messages=(status_text("CLIENT_ERROR"),),
            reset_log=False,
        )
        self.last_update = failed
        if failed.view is not None:
            self.view = failed.view
        self.status.set(failed.status)
        self.status_text.set(status_text(failed.status))
        self.notices.set(str(error))
        self.path_text.set("현재 진행 파일: " + failed.working_path)

    def _render(self, update: ClientUpdate) -> None:
        new_update = update is not self.last_update
        self.last_update = update
        self.status.set(update.status)
        self.status_text.set(status_text(update.status))
        self.notices.set(" · ".join(update.notices))
        self.path_text.set("현재 진행 파일: " + update.working_path)
        if update.view is not None:
            self.view = update.view
        if new_update:
            if update.reset_log:
                self.history.clear()
            self._append_messages(update.messages)
        if update.view is None:
            return
        self.view = view = update.view
        self.stats.set(
            f"체력 {view.actor_hp}/{ACTOR_HP_MAX}  적 {view.enemy_hp}/{ENEMY_HP_MAX}\n"
            f"스태미나 {view.stamina}/{STAMINA_MAX}  충전 {view.charge}/{CHARGE_MAX}\n"
            f"게임 시간 {view.tick}초  턴 {view.revision}\n"
            f"NPC 종 {view.npc_bells}  응답 {view.npc_replies}"
        )
        if update.quest_stage >= 0:
            stage = QUEST_STAGE_NAMES[update.quest_stage]
            self.stats.set(self.stats.get() + f"\n임무 {stage} · 포구의 호의 {update.quest_reward}")
        self._draw_map(view)

    def _draw_map(self, view: ClientView) -> None:
        canvas = self.canvas
        canvas.configure(width=view.width * CELL_PIXELS, height=view.height * CELL_PIXELS)
        canvas.delete("all")
        for cell in range(view.width * view.height):
            x = cell % view.width * CELL_PIXELS
            y = cell // view.width * CELL_PIXELS
            canvas.create_rectangle(
                x + 2,
                y + 2,
                x + CELL_PIXELS - 2,
                y + CELL_PIXELS - 2,
                fill="#465366" if cell in view.walls else "#243247",
                outline="#3a4d66",
            )
            canvas.create_text(x + 15, y + 16, text=str(cell), fill="#a5b7cc")
        self._marker(
            view, view.gate_cell, "문 열림" if view.gate_open else "문 닫힘", "#d9aa49", "gate"
        )
        self._marker(view, view.npc_cell, "NPC", "#65ba8d", "npc")
        if view.enemy_hp > 0:
            self._marker(view, view.enemy_cell, "적", "#e56c71", "enemy")
        self._marker(
            view, view.actor_cell, "나" if view.actor_hp > 0 else "쓰러짐", "#75b9ee", "actor"
        )

    def _marker(self, view: ClientView, cell: int, text: str, color: str, tag: str) -> None:
        x = cell % view.width * CELL_PIXELS + CELL_PIXELS // 2
        y = cell // view.width * CELL_PIXELS + CELL_PIXELS // 2
        self.canvas.create_oval(x - 33, y - 33, x + 33, y + 33, fill=color, outline="", tags=(tag,))
        self.canvas.create_text(x, y, text=text, fill="#151c27", font=("맑은 고딕", 11, "bold"))

    def close(self) -> None:
        if not self._closing:
            self._closing = True
            self._enable(False)
            self.status.set("진행 중인 작업을 마무리하고 종료 중…")
            self.status_text.set("진행 중인 작업을 마무리하고 종료 중…")
            self._close_future = self.worker.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Provisional Reverie Saga playable harness")
    parser.add_argument("--working", type=Path, default=Path("tmp/client/game.sqlite"))
    parser.add_argument("--scenario", default="legacy")
    parser.add_argument("--quest-catalog", type=Path)
    parser.add_argument("--quest-sha256")
    parser.add_argument("--npc-memory", action="store_true")
    parser.add_argument("--npc-work", action="store_true")
    parser.add_argument("--npc-cycle", action="store_true")
    parser.add_argument("--npc-aid", action="store_true")
    parser.add_argument("--npc-supply-aid", action="store_true")
    parser.add_argument("--npc-call-aid", action="store_true")
    parser.add_argument("--npc-patrol", action="store_true")
    parser.add_argument("--npc-talk-pause", action="store_true")
    parser.add_argument("--npc-quest-patrol", action="store_true")
    parser.add_argument("--npc-call-pause", action="store_true")
    parser.add_argument("--npc-ready-patrol", action="store_true")
    parser.add_argument("--npc-reach-aid", action="store_true")
    args = parser.parse_args(argv)
    layout = select_scenario(args.scenario).layout
    content = client_quest(layout, args.quest_catalog, args.quest_sha256)
    if args.npc_memory and content is None:
        raise ValueError("NPC_MEMORY_CONTENT")
    if args.npc_work and not args.npc_memory:
        raise ValueError("NPC_WORK_CONTENT")
    if args.npc_cycle and (not args.npc_memory or args.npc_work):
        raise ValueError("NPC_CYCLE_CONTENT")
    if args.npc_aid and not args.npc_cycle:
        raise ValueError("NPC_AID_CONTENT")
    if args.npc_supply_aid and not args.npc_aid:
        raise ValueError("NPC_SUPPLY_AID_CONTENT")
    if args.npc_call_aid and not args.npc_supply_aid:
        raise ValueError("NPC_CALL_AID_CONTENT")
    if args.npc_patrol and not args.npc_call_aid:
        raise ValueError("NPC_PATROL_CONTENT")
    if args.npc_talk_pause and not args.npc_patrol:
        raise ValueError("NPC_TALK_PAUSE_CONTENT")
    if args.npc_quest_patrol and not args.npc_talk_pause:
        raise ValueError("NPC_QUEST_PATROL_CONTENT")
    if args.npc_call_pause and not args.npc_quest_patrol:
        raise ValueError("NPC_CALL_PAUSE_CONTENT")
    if args.npc_ready_patrol and not args.npc_call_pause:
        raise ValueError("NPC_READY_PATROL_CONTENT")
    if args.npc_reach_aid and not args.npc_ready_patrol:
        raise ValueError("NPC_REACH_AID_CONTENT")
    root = tk.Tk()
    window = PlayWindow(
        root,
        args.working,
        layout,
        quest_content=content,
        npc_memory=args.npc_memory,
        npc_work=args.npc_work,
        npc_cycle=args.npc_cycle,
        npc_aid=args.npc_aid,
        npc_supply_aid=args.npc_supply_aid,
        npc_call_aid=args.npc_call_aid,
        npc_patrol=args.npc_patrol,
        npc_talk_pause=args.npc_talk_pause,
        npc_quest_patrol=args.npc_quest_patrol,
        npc_call_pause=args.npc_call_pause,
        npc_ready_patrol=args.npc_ready_patrol,
        npc_reach_aid=args.npc_reach_aid,
    )
    try:
        root.mainloop()
    finally:
        window.worker.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
