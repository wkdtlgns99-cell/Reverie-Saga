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
from app.client_text import status_text
from contracts.client import ClientRequest, ClientUpdate, ClientView
from domain.encounter import ACTOR_HP_MAX, ENEMY_HP_MAX, STAMINA_MAX
from domain.watch import CHARGE_MAX, WAIT_MAX

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
    def __init__(self, root: tk.Tk | tk.Toplevel, path: Path) -> None:
        self.root = root
        self.worker = ClientWorker(path)
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
        panel = ttk.Frame(root, padding=18)
        panel.pack(fill="both", expand=True)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(8, weight=1)
        ttk.Label(panel, text="REVERIE SAGA", font=("Segoe UI", 21, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(panel, text="작은 코어 연결 테스트 · 임시 2D 화면").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 14)
        )
        self.canvas = tk.Canvas(
            panel,
            width=CELL_PIXELS * 3,
            height=CELL_PIXELS * 3,
            background=BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.grid(row=2, column=0, sticky="n")
        controls = ttk.Frame(panel, padding=(18, 0, 0, 0))
        controls.grid(row=2, column=1, sticky="n")
        ttk.Label(controls, textvariable=self.stats, font=("맑은 고딕", 11)).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        for index, (request, label) in enumerate(LABELS):
            button = ttk.Button(controls, text=label, command=partial(self._send, request))
            button.grid(row=1 + index // 2, column=index % 2, sticky="ew", padx=3, pady=3)
            self.buttons[request] = button
        ttk.Label(controls, text="대기 시간(게임 초)").grid(row=8, column=0, sticky="w")
        self.wait_input = ttk.Spinbox(
            controls, from_=1, to=WAIT_MAX, textvariable=self.wait_seconds, width=10
        )
        self.wait_input.grid(row=8, column=1, sticky="ew", pady=6)
        ttk.Label(controls, text="저장 슬롯").grid(row=9, column=0, sticky="w")
        self.slot_input = ttk.Combobox(
            controls,
            values=tuple(f"slot0{index}" for index in range(1, 9)),
            textvariable=self.slot,
            state="readonly",
            width=10,
        )
        self.slot_input.grid(row=9, column=1, sticky="ew")
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
        ttk.Label(panel, text=f"행동·대화 기록 · 최근 {LOG_LINE_LIMIT}줄").grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(8, 4)
        )
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

    def _append_messages(self, messages: tuple[str, ...]) -> None:
        prefix = "" if self.view is None else f"[{self.view.tick}초 · 턴 {self.view.revision}] "
        for message in messages:
            line = prefix + message.replace("\r", " ").replace("\n", " ")
            self.history.append(line[:LOG_TEXT_LIMIT])
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "\n".join(self.history))
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def _key(self, event: tk.Event[tk.Misc]) -> None:
        if isinstance(event.widget, (ttk.Entry, ttk.Spinbox, ttk.Combobox, tk.Text)):
            return
        request = KEYS.get(event.keysym)
        if request is not None:
            self._send(request)

    def _enable(self, enabled: bool) -> None:
        for button in self.buttons.values():
            button.configure(state="normal" if enabled else "disabled")
        self.wait_input.configure(state="normal" if enabled else "disabled")
        self.slot_input.configure(state="readonly" if enabled else "disabled")

    def _send(self, request: ClientRequest) -> None:
        if self.busy:
            return
        try:
            seconds = int(self.wait_seconds.get()) if request == "wait" else 1
        except ValueError:
            self.status.set("INVALID_INPUT · 대기 시간에 정수를 입력하세요.")
            self.status_text.set(status_text("INVALID_INPUT"))
            self._append_messages((status_text("INVALID_INPUT"),))
            return
        self._pending = self.worker.request(request, seconds=seconds, slot_id=self.slot.get())
        self.status.set("처리 중…")
        self.status_text.set("처리 중…")
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
    args = parser.parse_args(argv)
    root = tk.Tk()
    window = PlayWindow(root, args.working)
    try:
        root.mainloop()
    finally:
        window.worker.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
