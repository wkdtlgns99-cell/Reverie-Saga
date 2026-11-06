"""Nonmodal resident conversation and explicit supported-action confirmation."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
import tkinter as tk
from tkinter import ttk

from app.world_supply import SupplyOffer
from app.world_worker import WorldUpdate


def dialogue_notice(code: str) -> str:
    return {
        "GENERATION_TIMEOUT": "응답을 기다리다 시간이 초과됐습니다. 응답만 다시 요청하거나 답 없이 계속할 수 있습니다.",
        "GENERATION_CANCELLED": "응답 요청을 취소했습니다. 전달한 발언과 시간은 유지됩니다.",
        "GENERATION_KEYS_EXHAUSTED": "등록된 모든 키가 제공자의 요청 한도에 도달했습니다. 나중에 다시 요청하거나 답 없이 계속해 주세요.",
        "GENERATION_DEFERRED": "제공자의 요청 한도에 도달했습니다. 나중에 다시 요청해 주세요.",
        "GENERATION_AUTH": "API 키 인증에 실패했습니다. 키 설정을 확인해 주세요.",
        "GENERATION_KEY_MISSING": "대화용 API 키가 없습니다. 로컬 키 설정을 확인해 주세요.",
        "GENERATION_KEY_CONFIGURATION": "API 키 설정이 중복되거나 충돌합니다. 로컬 설정을 확인해 주세요.",
        "GENERATION_OUTPUT": "사용할 수 없는 응답을 받았습니다. 응답만 다시 요청하거나 답 없이 계속할 수 있습니다.",
        "DIALOGUE_NPC_UNAVAILABLE": "이 주민은 지금 잠들어 있어 대화할 수 없습니다.",
        "DIALOGUE_OUT_OF_REACH": "해당 주민이 있는 도시에서 대화해 주세요.",
        "DIALOGUE_WRONG_NPC": "현재 도시의 대화할 주민을 선택해 주세요.",
        "DIALOGUE_SPEAKING": "먼저 진행 중인 말을 마쳐 주세요.",
        "DIALOGUE_HISTORY_FULL": "이 저장 파일의 대화 기록이 가득 찼습니다. 새 발언은 전달하지 않았습니다.",
        "DIALOGUE_CONTEXT_STALE": "상황이 달라져 응답을 적용하지 않았습니다. 현재 상황에서 다시 요청해 주세요.",
    }.get(
        code,
        "응답이나 처리를 완료하지 못했습니다. 처리 재시도 또는 응답 다시 요청을 선택해 주세요.",
    )


class ConversationPanel:
    def __init__(
        self,
        root: tk.Tk,
        send: Callable[[str, str], None],
        action: Callable[[str], None],
        confirm: Callable[[SupplyOffer], None],
        pause: Callable[[tk.Event[tk.Misc]], str],
        *,
        live_npc: bool = True,
    ) -> None:
        self.live_npc = live_npc
        self.panel = tk.Toplevel(root)
        self.panel.title("주민과 대화")
        self.panel.geometry("620x640")
        self.panel.minsize(450, 600)
        self.panel.bind("<Escape>", pause)
        self.panel.protocol("WM_DELETE_WINDOW", self.panel.withdraw)
        self.send_callback, self.action_callback, self.confirm_callback = send, action, confirm
        self.update: WorldUpdate | None = None
        self._ready = False
        self.identifiers: dict[str, str] = {}
        self.selected = tk.StringVar(self.panel)
        self.residents = ttk.Combobox(self.panel, state="readonly", textvariable=self.selected)
        self.residents.pack(fill="x", padx=12, pady=8)
        self.residents.bind("<<ComboboxSelected>>", self.selection_changed)
        self.transcript = tk.Text(self.panel, wrap="word", height=12, state="disabled")
        self.transcript.pack(fill="both", expand=True, padx=12, pady=4)
        self.status = tk.StringVar(self.panel, "말을 보내면 실제 발언과 소요 시간이 기록됩니다.")
        self.status_label = ttk.Label(self.panel, textvariable=self.status, wraplength=570)
        self.status_label.pack(fill="x", padx=12)
        self.input = tk.Text(self.panel, height=4, wrap="word", undo=True)
        self.input.pack(fill="x", padx=12, pady=6)
        controls = ttk.Frame(self.panel)
        controls.pack(fill="x", padx=8, pady=4)
        self.buttons: dict[str, ttk.Button] = {}
        for index, (name, label) in enumerate(
            (
                ("send", "말하기"),
                ("retry", "응답 다시 요청"),
                ("speech", "말 계속하기"),
                ("skip", "답 없이 계속"),
                ("cancel", "응답 요청 취소"),
                ("recover", "처리 재시도"),
            )
        ):
            button = ttk.Button(
                controls,
                text=label,
                command=self.send if name == "send" else partial(self.action_callback, name),
            )
            button.grid(row=index // 3, column=index % 3, sticky="ew", padx=3, pady=3)
            self.buttons[name] = button
        self.terms = tk.StringVar(self.panel)
        self.terms_label = ttk.Label(
            self.panel, textvariable=self.terms, wraplength=570, justify="left"
        )
        self.terms_label.pack(
            fill="x",
            padx=12,
            pady=6,
        )
        self.offer: SupplyOffer | None = None
        self.confirm = ttk.Button(
            self.panel, text="조건을 확인하고 실행", command=self.confirm_offer
        )
        self.confirm.pack(pady=6)
        if not live_npc:
            self.panel.title("저장된 주민 대화")
            self.status.set("AI 대화가 꺼져 있습니다. 보급 의뢰는 각본 대화로 진행할 수 있습니다.")
            self.input.pack_forget()
            self.confirm.pack_forget()
            for name in ("send", "retry", "skip", "cancel"):
                self.buttons[name].grid_remove()
        self.panel.bind("<Configure>", self.resize, add=True)

    def resize(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget is self.panel:
            width = max(200, event.width - 24)
            self.status_label.configure(wraplength=width)
            self.terms_label.configure(wraplength=width)

    def show(self) -> None:
        self.panel.deiconify()
        self.panel.lift()

    def text(self) -> str:
        return self.input.get("1.0", "end-1c")

    def send(self) -> None:
        self.send_callback(self.identifiers.get(self.selected.get(), ""), self.text())

    def selection_changed(self, event: tk.Event[tk.Misc]) -> None:
        if self.update is not None:
            self.render(self.update)

    def confirm_offer(self) -> None:
        if self.offer is not None:
            self.confirm_callback(self.offer)

    def render(self, update: WorldUpdate) -> None:
        self.update = update
        self.identifiers = {r.name: r.resident_id for r in update.residents}
        values = tuple(self.identifiers)
        self.residents.configure(values=values)
        if self.selected.get() not in self.identifiers:
            self.selected.set(values[0] if values else "")
        selected = self.identifiers.get(self.selected.get())
        state = update.conversation
        lines: list[str] = []
        if state is not None:
            for entry in state.exchanges:
                if entry.npc_id != selected:
                    continue
                lines.append(f"나: {entry.player_text}")
                if entry.reply_text:
                    lines.append(f"{self.selected.get()}: {entry.reply_text}")
                else:
                    lines.append("(아직 응답이 없습니다.)")
        self.transcript.configure(state="normal")
        try:
            self.transcript.delete("1.0", "end")
            self.transcript.insert("1.0", "\n\n".join(lines))
            self.transcript.see("end")
        finally:
            self.transcript.configure(state="disabled")
        self.offer = None
        if self.live_npc and state is not None and state.exchanges and not state.remaining:
            entry = state.exchanges[-1]
            self.offer = next(
                (
                    o
                    for o in update.offers
                    if o.action.npc_id == selected == entry.npc_id
                    and o.action.operation == entry.proposal
                ),
                None,
            )
        self.terms.set(self.offer.summary if self.offer is not None else "")
        self.confirm.configure(
            state="normal" if self._ready and self.offer is not None else "disabled"
        )

    def controls(
        self, *, paused: bool, busy: bool, running: bool, recovery: bool, generating: bool
    ) -> None:
        state = self.update.conversation if self.update is not None else None
        ready = state is not None and not paused and not busy and not running and not recovery
        self._ready = ready
        unanswered = bool(state and state.exchanges and not state.exchanges[-1].reply_text)
        enabled = {
            "send": self.live_npc and ready and not state.remaining if state is not None else False,
            "retry": self.live_npc and ready and unanswered and not state.remaining
            if state is not None
            else False,
            "speech": ready and bool(state.remaining) if state is not None else False,
            "skip": self.live_npc and ready and unanswered,
            "cancel": self.live_npc and generating,
            "recover": recovery and not paused and not busy,
        }
        for name, button in self.buttons.items():
            button.configure(state="normal" if enabled[name] else "disabled")
        self.confirm.configure(state="normal" if ready and self.offer is not None else "disabled")
