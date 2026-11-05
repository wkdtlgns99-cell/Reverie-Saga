"""Nonmodal travel terms,progress and explicit interruption choices."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
import tkinter as tk
from tkinter import ttk

from app.world_worker import WorldUpdate
from domain.world import WorldCatalog
from domain.world_transport import TransportRules, plan_journey, route_between


def transport_notice(code: str) -> str:
    return {
        "JOURNEY_ACTIVE": "여정 중에는 현지 주민과 행동할 수 없습니다. 도착하거나 귀환해 주세요.",
        "JOURNEY_NOT_ACTIVE": "진행 중인 여정이 없습니다.",
        "JOURNEY_BLOCKED": "통행이 제한되어 있습니다. 기다리거나 출발지로 돌아갈 수 있습니다.",
        "JOURNEY_CLEAR": "통행 제한이 끝났습니다. 이어서 이동을 선택해 주세요.",
        "JOURNEY_NOT_BLOCKED": "현재 통행 제한으로 멈춘 상태가 아닙니다.",
        "JOURNEY_DURATION": "이동 조건이 달라졌습니다. 현재 상황에서 다시 선택해 주세요.",
        "WORLD_ROUTE_ACTIVE": "도보 이동을 마치고 도시에서 승차해 주세요.",
        "WORLD_NOT_ADJACENT": "현재 도시와 연결된 목적지를 선택해 주세요.",
        "SOCIAL_ENTRY_DENIED": "목적지와의 관계 때문에 입장이 제한됩니다. 귀환할 수 있습니다.",
        "DIALOGUE_SPEAKING": "진행 중인 말을 마친 뒤 이동해 주세요.",
    }.get(code, code)


class TransportPanel:
    def __init__(
        self,
        root: tk.Tk,
        world: WorldCatalog,
        rules: TransportRules,
        confirm: Callable[[str, str], None],
        retry: Callable[[], None],
        pause: Callable[[tk.Event[tk.Misc]], str],
    ) -> None:
        self.world, self.rules, self.callback = world, rules, confirm
        self.update: WorldUpdate | None = None
        self.proposal: tuple[str, str] | None = None
        self.board_destination = ""
        self.panel = tk.Toplevel(root)
        self.panel.title("마차·선박 여정")
        self.panel.geometry("620x440")
        self.panel.minsize(440, 380)
        self.panel.protocol("WM_DELETE_WINDOW", self.panel.withdraw)
        self.panel.bind("<Escape>", pause)
        self.panel.withdraw()
        self.status = tk.StringVar(self.panel, "목적지를 선택하고 이동 조건을 확인해 주세요.")
        self.status_label = ttk.Label(
            self.panel, textvariable=self.status, wraplength=570, justify="left"
        )
        self.status_label.pack(fill="x", padx=12, pady=12)
        self.terms = tk.StringVar(self.panel)
        self.terms_label = ttk.Label(
            self.panel, textvariable=self.terms, wraplength=570, justify="left"
        )
        self.terms_label.pack(fill="both", expand=True, padx=12, pady=8)
        row = ttk.Frame(self.panel)
        row.pack(fill="x", padx=12, pady=4)
        self.buttons: dict[str, ttk.Button] = {}
        for index, (operation, label) in enumerate(
            (
                ("board", "승차 조건 확인"),
                ("advance", "여정 계속"),
                ("wait", "통제 해제까지 대기"),
                ("resume", "이어서 이동"),
                ("return", "출발지로 귀환"),
            )
        ):
            button = ttk.Button(row, text=label, command=partial(self.propose, operation))
            button.grid(row=index // 2, column=index % 2, sticky="ew", padx=3, pady=3)
            self.buttons[operation] = button
        row.columnconfigure((0, 1), weight=1)
        self.confirm = ttk.Button(
            self.panel, text="조건을 확인하고 실행", command=self.execute, state="disabled"
        )
        self.confirm.pack(pady=5)
        self.retry = ttk.Button(
            self.panel, text="같은 여정 처리 재시도", command=retry, state="disabled"
        )
        self.retry.pack(pady=5)
        self.panel.bind("<Configure>", self.resize, add=True)

    def resize(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget is self.panel:
            for label in (self.status_label, self.terms_label):
                label.configure(wraplength=max(200, event.width - 24))

    def show(self, destination: str = "") -> None:
        self.board_destination = destination
        self.panel.deiconify()
        self.panel.lift()

    def render(self, update: WorldUpdate) -> None:
        self.update = update
        journey = update.journey
        if journey is None or journey.phase == "idle":
            self.status.set(
                "현재 도시: "
                + self.world.place(update.state.place_id).name
                + " · 진행 중인 여정이 없습니다."
            )
        else:
            route = route_between(self.world, journey.origin_id, journey.destination_id)
            mode = "공용 마차" if journey.mode == "carriage" else "공용 선박"
            phase = (
                "통행 제한으로 정지"
                if journey.phase == "blocked"
                else "귀환 중"
                if journey.phase == "returning"
                else "여정 진행"
            )
            message = (
                f"{mode} · {self.world.place(journey.origin_id).name} → {self.world.place(journey.destination_id).name}\n"
                f"{journey.progress_m}/{route.distance_km * 1000}m · {phase} · 게임 시간 {update.tick}초"
            )
            if journey.block_id:
                closure = next(c for c in self.rules.closures if c.id == journey.block_id)
                message += f"\n정지 사유: {closure.reason}\n통제 종료: 게임 {closure.end_tick}초 · 자동으로 재개하지 않습니다."
                if update.tick >= closure.end_tick:
                    message += "\n통제 해제 · 이어서 이동하거나 귀환을 선택해 주세요."
            self.status.set(message)
        if update.transport_committed is False:
            self.terms.set(transport_notice(update.notice))

    def propose(self, operation: str) -> None:
        update = self.update
        if update is None or update.journey is None:
            return
        destination = self.board_destination if operation == "board" else ""
        try:
            plan = plan_journey(
                self.world,
                self.rules,
                update.journey,
                update.state,
                update.tick,
                operation,
                destination,
            )
        except ValueError as error:
            from orchestration.world_transport import JOURNEY_ERRORS

            if str(error) not in JOURNEY_ERRORS:
                raise
            self.proposal = None
            self.terms.set(transport_notice(str(error)))
            self.confirm.configure(state="disabled")
            return
        self.proposal = (operation, destination)
        if operation == "board":
            route = route_between(self.world, update.state.place_id, destination)
            mode = "공용 마차" if route.kind == "road" else "공용 선박"
            speed = self.rules.carriage_mps if route.kind == "road" else self.rules.ship_mps
            seconds = (route.distance_km * 1000 + speed - 1) // speed
            text = f"{self.world.place(destination).name}행 {mode} · 요금 0금\n기본 이동 시간 {seconds}초, 승차 1초. 사건에서 멈추면 직접 기다리거나 귀환을 선택합니다."
        else:
            text = {
                "advance": "확인한 목적지로 여정을 계속합니다.",
                "wait": "제자리에서 통제 해제를 기다립니다. 이후 이동은 다시 선택합니다.",
                "resume": "통제를 확인하고 여정을 재개합니다.",
                "return": "실제로 이동한 길을 따라 출발지로 돌아갑니다.",
            }[operation]
            text += f"\n현재 조건의 이번 처리 시간: {plan.seconds}초."
        self.terms.set(text + "\n실행 시 현재 조건을 다시 검증합니다.")
        self.confirm.configure(state="normal")

    def execute(self) -> None:
        if self.proposal is not None:
            self.callback(*self.proposal)

    def controls(self, *, busy: bool, recovery: bool) -> None:
        phase = (
            self.update.journey.phase
            if self.update is not None and self.update.journey is not None
            else "none"
        )
        for operation, button in self.buttons.items():
            enabled = (
                not busy
                and not recovery
                and (
                    operation == "board"
                    and phase == "idle"
                    and bool(self.board_destination)
                    or operation == "advance"
                    and phase in ("outbound", "returning")
                    or operation in ("wait", "resume")
                    and phase == "blocked"
                    or operation == "return"
                    and phase not in ("none", "idle")
                )
            )
            if (
                enabled
                and phase == "blocked"
                and operation in ("wait", "resume")
                and self.update is not None
                and self.update.journey is not None
            ):
                closure = next(
                    c for c in self.rules.closures if c.id == self.update.journey.block_id
                )
                enabled = (
                    (closure.start_tick <= self.update.tick < closure.end_tick)
                    if operation == "wait"
                    else not (closure.start_tick <= self.update.tick + 1 < closure.end_tick)
                )
            button.configure(state="normal" if enabled else "disabled")
        self.confirm.configure(
            state="normal"
            if self.proposal is not None and not busy and not recovery
            else "disabled"
        )
        self.retry.configure(state="normal" if recovery and not busy else "disabled")
