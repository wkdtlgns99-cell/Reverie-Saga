"""World-map presentation shared by the emerging world play path."""

from __future__ import annotations

from concurrent.futures import Future
from functools import partial
from collections.abc import Callable
import logging
from pathlib import Path
import sys
import time
import unicodedata
import tkinter as tk
from tkinter import ttk

from app.world_catalog import (
    AUTHORED_SUPPLY_SCENARIO,
    DEVELOPMENT_WORLD,
    KNOWLEDGE_WORLD_PATH,
    load_social,
    load_transport,
    load_world,
)
from app.world_worker import WorldAction, WorldUpdate, WorldWorker
from app.world_time import ClockMode, SlowClock
from app.world_supply import SupplyOffer, authored_supply_line, item_label
from app.world_conversation import ConversationPanel, dialogue_notice
from app.world_social import SocialPanel, city_standing, resident_membership, social_notice
from app.world_transport import TransportPanel, transport_notice
from contracts.dialogue import GenerationError
from domain.world_conversation import validate_speech
from domain.world_supply import SupplyScenario
from contracts.world_supply import SupplyAction
from contracts.world_social import SocialAction
from domain.world import WorldCatalog


class WorldMapFrame(ttk.Frame):
    def __init__(
        self, parent: tk.Misc, catalog: WorldCatalog, on_select: Callable[[str], None]
    ) -> None:
        super().__init__(parent)
        self.catalog = catalog
        self.on_select = on_select
        self.selected = catalog.places[0].id
        self.canvas = tk.Canvas(self, background="#142539", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._resize)
        self.canvas.bind("<Button-1>", self._click)
        self.positions: dict[str, tuple[float, float]] = {}

    def _resize(self, event: tk.Event[tk.Misc]) -> None:
        self.draw(event.width, event.height)

    def draw(self, width: int, height: int) -> None:
        self.canvas.delete("all")
        self.positions.clear()
        for index, continent in enumerate(self.catalog.continents):
            x = (index % 3 + 0.5) * width / 3
            y = (index // 3 + 0.5) * height / 2
            country = next(c for c in self.catalog.countries if c.continent_id == continent.id)
            self.canvas.create_rectangle(
                x - width / 7,
                y - height / 5,
                x + width / 7,
                y + height / 5,
                fill="#263e45",
                outline="#55736b",
                tags=("continent",),
            )
            self.canvas.create_text(
                x, y - height / 6, text=continent.name, fill="#e0e8da", tags=("continent-name",)
            )
            places = tuple(p for p in self.catalog.places if p.country_id == country.id)
            for offset, place in enumerate(places):
                self.positions[place.id] = (x, y + offset * height / 10 - height / 24)
        for route in self.catalog.routes:
            origin = self.positions[route.origin]
            destination = self.positions[route.destination]
            self.canvas.create_line(
                *origin,
                *destination,
                fill="#729aa6" if route.kind == "sea" else "#c6ac70",
                dash=(5, 4) if route.kind == "sea" else (),
                tags=("route", route.kind),
            )
        for place in self.catalog.places:
            x, y = self.positions[place.id]
            tag = "city:" + place.id
            self.canvas.create_oval(
                x - 6,
                y - 6,
                x + 6,
                y + 6,
                fill="#ffe08a" if place.id == self.selected else "#dce5e7",
                tags=("city", tag),
            )
            self.canvas.create_text(
                x + 12, y, text=place.name, fill="white", anchor="w", tags=("city-label", tag)
            )

    def _click(self, event: tk.Event[tk.Misc]) -> None:
        for tag in self.canvas.gettags("current"):
            if tag.startswith("city:place:"):
                self.select_place(tag.removeprefix("city:"))
                return

    def select_place(self, place_id: str) -> None:
        self.catalog.place(place_id)
        self.selected = place_id
        self.draw(self.canvas.winfo_width(), self.canvas.winfo_height())
        self.on_select(place_id)


class WorldMapWindow:
    def __init__(
        self,
        root: tk.Tk,
        catalog: WorldCatalog,
        worker: WorldWorker | None = None,
        *,
        now_ns: Callable[[], int] = time.monotonic_ns,
    ) -> None:
        self.root = root
        self.catalog = catalog
        self.worker = worker
        self.pending: Future[WorldUpdate] | None = None
        self.update: WorldUpdate | None = None
        self.now_ns = now_ns
        self.clock = SlowClock(now_ns())
        self.paused = False
        self.ai_waiting = False
        self.closed = False
        self.pending_action: WorldAction | None = None
        self.reserved_seconds = 0
        self.reservation_key = ""
        self.reservation_sequence = 0
        self.wait_error = False
        self.supply_error = False
        self.supply_command: SupplyAction | None = None
        self.supply_request_key = ""
        self.supply_sequence = 0
        self.offer_panel: tk.Toplevel | None = None
        self.deferred: tuple[WorldAction, int] | None = None
        self.clock_after: str | None = None
        self.poll_after: str | None = None
        self.dialogue: ConversationPanel | None = None
        self.dialogue_running = False
        self.dialogue_recovery = False
        self.dialogue_next: WorldAction | None = None
        self.failed_dialogue_action: WorldAction = "say"
        self.dialogue_key = ""
        self.dialogue_sequence = 0
        self.dialogue_npc = self.dialogue_text = self.dialogue_input = ""
        self.want_reply = False
        self.dialogue_cancelled = False
        self.social_panel: SocialPanel | None = None
        self.social_command: SocialAction | None = None
        self.social_key = ""
        self.social_sequence = 0
        self.social_error = False
        self.transport_panel: TransportPanel | None = None
        self.transport_command: tuple[str, str] | None = None
        self.transport_key = ""
        self.transport_sequence = 0
        self.transport_running = False
        self.transport_next = False
        self.transport_error = False
        root.title("Reverie Saga — 세계 지도")
        root.geometry("1080x760")
        root.minsize(780, 560)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<Escape>", self.toggle_pause)
        root.bind("<Destroy>", self.destroyed, add=True)
        ttk.Label(root, text="세계 지도 · 도시를 선택해 지리와 교역 정보를 확인하세요").pack(
            anchor="w", padx=12, pady=8
        )
        self.details = tk.StringVar(root)
        ttk.Label(root, textvariable=self.details, wraplength=740, justify="left").pack(
            side="bottom", anchor="w", padx=12, pady=12
        )
        self.status = tk.StringVar(root, "")
        self.controls = ttk.Frame(root)
        self.controls.pack(side="bottom", fill="x", padx=12, pady=6)
        ttk.Label(self.controls, textvariable=self.status).pack(anchor="w")
        self.action_controls = ttk.Frame(self.controls)
        self.action_controls.pack(fill="x")
        self.route_ids: dict[str, str] = {}
        self.destination = tk.StringVar(root)
        self.routes = ttk.Combobox(
            self.action_controls, state="readonly", textvariable=self.destination
        )
        self.routes.grid(row=0, column=0, padx=4, pady=3)
        self.buttons: list[ttk.Button] = []
        actions: tuple[tuple[str, WorldAction, int], ...] = (
            ("한 걸음 앞으로", "walk", 1),
            ("한 걸음 돌아가기", "walk", -1),
            ("저장", "save", 1),
            ("불러오기", "load", 1),
        )
        for index, (label, action, direction) in enumerate(actions):
            button = ttk.Button(
                self.action_controls, text=label, command=partial(self.send, action, direction)
            )
            button.grid(
                row=0 if index < 2 else 1,
                column=index + 1 if index < 2 else index - 2,
                padx=4,
                pady=3,
            )
            self.buttons.append(button)
        self.retry_time = ttk.Button(
            self.action_controls, text="시간 반영 재시도", command=partial(self.send, "wait")
        )
        self.retry_time.grid(row=1, column=2, padx=4, pady=3)
        self.inventory_panel: tk.Toplevel | None = None
        self.inventory_text = tk.StringVar(root, "")
        self.resident_text = tk.StringVar(root, "")
        self.supply_text = tk.StringVar(root, "")
        ttk.Label(root, textvariable=self.supply_text, wraplength=1000).pack(
            side="bottom", fill="x", padx=12, pady=4
        )
        self.offer_button = ttk.Button(
            self.action_controls,
            text="보급 의뢰 대화"
            if worker is not None and worker.authored_supply
            else "주민의 제안",
            command=self.show_supply_offer,
        )
        self.offer_button.grid(row=0, column=3, padx=4, pady=3)
        self.retry_supply = ttk.Button(
            self.action_controls, text="거래 반영 재시도", command=partial(self.send, "supply")
        )
        if worker is not None and worker.conversation:
            self.dialogue = ConversationPanel(
                root,
                self.say,
                self.conversation_action,
                self.confirm_dialogue_supply,
                self.toggle_pause,
                live_npc=worker.live_npc,
            )
            ttk.Button(
                self.action_controls,
                text="주민과 대화" if worker.live_npc else "저장된 대화",
                command=self.dialogue.show,
            ).grid(
                row=1,
                column=4,
                padx=4,
                pady=3,
            )
        ttk.Button(self.action_controls, text="소지품", command=self.show_inventory).grid(
            row=1, column=3, padx=4, pady=3
        )
        if worker is not None and worker.social is not None:
            self.social_panel = SocialPanel(
                root,
                catalog,
                worker.social,
                self.confirm_social,
                partial(self.send, "social"),
                self.toggle_pause,
            )
            ttk.Button(
                self.action_controls, text="종족·세력 관계", command=self.social_panel.show
            ).grid(row=2, column=0, columnspan=2, padx=4, pady=3)
        if worker is not None and worker.transport is not None:
            self.transport_panel = TransportPanel(
                root,
                catalog,
                worker.transport,
                self.confirm_transport,
                partial(self.send, "transport"),
                self.toggle_pause,
            )
            ttk.Button(self.action_controls, text="마차·선박", command=self.show_transport).grid(
                row=2, column=2, columnspan=2, padx=4, pady=3
            )
        ttk.Label(root, textvariable=self.resident_text, wraplength=1000, justify="left").pack(
            side="bottom", fill="x", padx=12, pady=4
        )
        self.pause_panel = ttk.Frame(root, padding=24, relief="raised", borderwidth=3)
        ttk.Label(self.pause_panel, text="일시정지 · 시간이 멈춰 있습니다").pack(pady=8)
        ttk.Button(self.pause_panel, text="계속하기 (ESC)", command=self.toggle_pause).pack()
        self.road = tk.Canvas(root, height=65, background="#25382e", highlightthickness=0)
        self.road.pack(side="bottom", fill="x", padx=12)
        self.road.configure(takefocus=True)
        self.road.bind("<Button-1>", self.focus_road)
        self.road.bind("<KeyPress-Right>", self.walk_key)
        self.road.bind("<KeyPress-Left>", self.walk_key)
        self.map = WorldMapFrame(root, catalog, self.inspect)
        self.map.pack(fill="both", expand=True, padx=8)
        self.inspect(catalog.places[0].id)
        if worker is not None:
            self.send("inspect")
        else:
            for button in self.buttons:
                button.configure(state="disabled")
        self.clock_after = root.after(100, self.clock_tick)

    def inspect(self, place_id: str) -> None:
        place = self.catalog.place(place_id)
        country = next(c for c in self.catalog.countries if c.id == place.country_id)
        continent = next(c for c in self.catalog.continents if c.id == country.continent_id)
        neighbors = " / ".join(
            f"{p.name} {r.distance_km}km" for p, r in self.catalog.neighbors(place.id)
        )
        self.details.set(
            f"{place.name} ({place.role}) · {country.name} · {continent.name}\n"
            f"환경: {continent.environment} · 생활: {country.livelihood}\n"
            f"생산: {country.export} · 수요: {country.need}\n연결: {neighbors}"
        )
        if (
            self.update is not None
            and self.update.social is not None
            and self.worker is not None
            and self.worker.social is not None
        ):
            self.details.set(
                self.details.get()
                + "\n"
                + city_standing(self.update.social, self.worker.social, place_id)
            )

    def confirm_social(self, payload: SocialAction) -> None:
        if (
            self.pending is not None
            or self.paused
            or self.dialogue_running
            or self.dialogue_recovery
            or self.social_error
            or self.social_command is not None
            or self.supply_error
            or self.wait_error
            or self.transport_error
            or self.transport_running
            or self.in_transit
            or bool(self.reserved_seconds)
        ):
            return
        self.social_command = payload
        self.social_sequence += 1
        self.social_key = f"ui-social-{self.social_sequence}"
        self.send("social")

    def focus_road(self, event: tk.Event[tk.Misc]) -> None:
        self.road.focus_set()

    def show_transport(self) -> None:
        if self.transport_panel is not None:
            self.transport_panel.show(self.route_ids.get(self.destination.get(), ""))
            self.dialogue_controls()

    def confirm_transport(self, operation: str, destination: str) -> None:
        if (
            self.pending is not None
            or self.paused
            or self.dialogue_running
            or self.dialogue_recovery
            or self.social_error
            or self.supply_error
            or self.wait_error
            or self.transport_error
            or self.transport_running
            or self.transport_command is not None
            or self.reserved_seconds
        ):
            return
        self.clock.sample(self.now_ns())
        self.transport_running = operation != "wait"
        self.new_transport_stage(operation, destination, flush=True)

    def new_transport_stage(
        self, operation: str, destination: str = "", *, flush: bool = False
    ) -> None:
        self.transport_sequence += 1
        self.transport_command = operation, destination
        self.transport_key = f"ui-transport-{self.transport_sequence}"
        if flush:
            self.send("transport")
        else:
            self.start_request("transport")

    def transport_ack(self, update: WorldUpdate) -> None:
        if update.transport_committed is None or update.journey is None:
            raise ValueError("TRANSPORT_ACK_MISSING")
        continue_intent = self.transport_command is not None and self.transport_command[0] != "wait"
        self.transport_error = False
        self.transport_command = None
        if self.transport_panel is not None:
            self.transport_panel.proposal = None
        self.transport_running = bool(
            continue_intent
            and update.transport_committed
            and update.journey.phase not in ("idle", "blocked")
        )
        self.transport_next = self.transport_running

    def walk_key(self, event: tk.Event[tk.Misc]) -> str:
        if isinstance(event.state, int) and not event.state & (0x0004 | 0x0008 | 0x20000):
            self.send("walk", 1 if event.keysym == "Right" else -1)
        return "break"

    def show_inventory(self) -> None:
        if self.paused or self.update is None:
            return
        if self.inventory_panel is not None and self.inventory_panel.winfo_exists():
            self.inventory_panel.lift()
            return
        panel = tk.Toplevel(self.root)
        self.inventory_panel = panel
        panel.title("소지품")
        ttk.Label(panel, textvariable=self.inventory_text, padding=18, justify="left").pack()
        ttk.Button(panel, text="닫기", command=panel.destroy).pack(pady=8)
        # This panel is nonmodal and retains the same slow-idle clock.
        panel.bind("<Escape>", self.toggle_pause)

    @property
    def in_transit(self) -> bool:
        return (
            self.update is not None
            and self.update.journey is not None
            and self.update.journey.phase != "idle"
        )

    def _clock_mode(self) -> ClockMode:
        if self.paused:
            return "paused"
        if self.ai_waiting or self.pending_action == "generate":
            return "ai_wait"
        if (
            self.dialogue_running
            or self.transport_running
            or self.transport_command is not None
            or self.social_command is not None
            or (
                self.update is not None
                and self.update.conversation is not None
                and self.update.conversation.remaining
            )
            or self.pending_action in ("walk", "supply", "say", "speech", "reply", "social")
        ):
            return "action"
        return "idle"

    def toggle_pause(self, event: tk.Event[tk.Misc] | None = None) -> str:
        self.clock.sample(self.now_ns())
        self.paused = not self.paused
        self.clock.transition(self._clock_mode(), self.now_ns())
        if self.paused:
            self.pause_panel.place(relx=0.5, rely=0.5, anchor="center")
            self.pause_panel.lift()
        else:
            self.pause_panel.place_forget()
            self.resume_deferred()
        self.dialogue_controls()
        if self.paused and self.dialogue is not None:
            self.dialogue.status.set("일시정지 · ESC를 누르면 이어서 진행합니다.")
        return "break"

    def set_ai_waiting(self, waiting: bool) -> None:
        self.clock.sample(self.now_ns())
        self.ai_waiting = waiting
        self.clock.transition(self._clock_mode(), self.now_ns())
        if not waiting:
            self.resume_deferred()

    def destroyed(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget is self.root:
            self.dispose()

    def dispose(self) -> None:
        if not self.closed:
            self.closed = True
            if self.worker is not None:
                self.worker.cancel_conversation()
            for handle in (self.clock_after, self.poll_after):
                if handle is not None:
                    self.root.after_cancel(handle)

    def close(self) -> None:
        self.dispose()
        self.root.quit()

    def clock_tick(self) -> None:
        self.clock_after = None
        try:
            self.advance_clock()
        except Exception as error:
            logging.getLogger(__name__).exception("World clock UI failed")
            self.wait_error = True
            self.status.set(f"시간을 반영하지 못했습니다: {error}")
        finally:
            if not self.closed:
                self.clock_after = self.root.after(100, self.clock_tick)

    def advance_clock(self) -> None:
        self.clock.sample(self.now_ns())
        if (
            not self.closed
            and not self.paused
            and not self.ai_waiting
            and self.worker is not None
            and self.pending is None
            and self.update is not None
            and not self.wait_error
            and not self.supply_error
            and not self.social_error
            and not self.transport_error
            and not self.transport_running
            and not self.dialogue_running
            and not self.dialogue_recovery
            and not (self.update.conversation and self.update.conversation.remaining)
        ):
            self.flush_idle()

    def flush_idle(self) -> bool:
        if self.reserved_seconds:
            return True
        seconds = self.clock.reserve()
        if not seconds:
            return False
        self.reserved_seconds = seconds
        self.reservation_sequence += 1
        self.reservation_key = f"ui-time-{self.reservation_sequence}"
        self.start_request("wait")
        return True

    def resume_deferred(self) -> None:
        if self.transport_next and self.pending is None and not self.paused:
            if not self.transport_error:
                self.transport_next = False
                self.new_transport_stage("advance")
            return
        if self.dialogue_next is not None and self.pending is None and not self.paused:
            if not self.dialogue_recovery and not self.dialogue_cancelled:
                action, self.dialogue_next = self.dialogue_next, None
                self.new_dialogue_stage(action)
            return
        if (
            self.deferred is not None
            and self.pending is None
            and not self.paused
            and not self.ai_waiting
            and not self.wait_error
            and not self.supply_error
        ):
            action, direction = self.deferred
            self.deferred = None
            self.send(action, direction)

    def send(self, action: WorldAction, direction: int = 1) -> None:
        if (
            self.closed
            or self.worker is None
            or self.pending is not None
            or self.paused
            or self.ai_waiting
        ):
            return
        if action not in (
            "inspect",
            "walk",
            "save",
            "load",
            "wait",
            "supply",
            "say",
            "speech",
            "generate",
            "reply",
            "social",
            "transport",
        ):
            raise ValueError("UNKNOWN_WORLD_ACTION")
        if self.dialogue_recovery or (
            self.dialogue_running and action not in ("say", "speech", "generate", "reply", "wait")
        ):
            return
        self.clock.sample(self.now_ns())
        if self.transport_error:
            if action == "transport":
                self.start_request("transport")
            else:
                self.status.set("먼저 같은 여정 처리를 재시도해 주세요.")
            return
        if self.transport_running and action not in ("transport", "wait"):
            return
        if self.social_error:
            if action == "social":
                self.start_request("social")
            else:
                self.status.set("먼저 같은 사회 행동의 반영을 재시도해 주세요.")
            return
        if self.supply_error:
            if action == "supply":
                self.start_request("supply")
            else:
                self.status.set("먼저 거래 반영을 재시도해 주세요.")
            return
        if action == "wait":
            if self.reserved_seconds:
                self.start_request("wait")
            else:
                self.wait_error = False
                self.flush_idle()
            return
        if self.reserved_seconds or self.wait_error:
            self.status.set("먼저 시간 반영을 재시도해 주세요.")
            return
        if (
            self.update is not None
            and not (self.update.conversation and self.update.conversation.remaining)
            and self.flush_idle()
        ):
            self.deferred = (action, direction)
            return
        self.start_request(action, direction)

    def start_request(self, action: WorldAction, direction: int = 1) -> None:
        if self.worker is None:
            return
        destination = self.route_ids.get(self.destination.get(), "")
        if action == "walk" and self.update is not None and self.update.state.destination_id:
            destination = self.update.state.destination_id
        self.pending_action = action
        self.clock.transition(self._clock_mode(), self.now_ns())
        if action == "transport":
            if self.transport_command is None:
                raise ValueError("TRANSPORT_CONFIRMATION_MISSING")
            operation, target = self.transport_command
            self.pending = self.worker.request(
                action, target, request_key=self.transport_key, transport_operation=operation
            )
        elif action == "social":
            self.pending = self.worker.request(
                action, social_action=self.social_command, request_key=self.social_key
            )
        elif action == "supply":
            self.pending = self.worker.request(
                action, supply=self.supply_command, request_key=self.supply_request_key
            )
        elif action in ("say", "speech", "generate", "reply"):
            self.pending = self.worker.request(
                action,
                request_key=self.dialogue_key,
                npc_id=self.dialogue_npc,
                text=self.dialogue_text,
            )
        else:
            self.pending = self.worker.request(
                action,
                destination,
                direction,
                seconds=self.reserved_seconds if action == "wait" else 1,
                request_key=self.reservation_key if action == "wait" else "",
            )
        for button in self.buttons:
            button.configure(state="disabled")
        self.status.set("처리 중…")
        if self.dialogue is not None:
            self.dialogue.status.set(
                "응답을 기다리는 중… 게임 시간은 추가로 흐르지 않습니다."
                if action == "generate"
                else "처리 중…"
            )
        self.dialogue_controls()
        self.poll_after = self.root.after(20, self.poll)

    def poll(self) -> None:
        self.poll_after = None
        if self.pending is None or self.closed:
            return
        if not self.pending.done():
            self.poll_after = self.root.after(20, self.poll)
            return
        pending, self.pending = self.pending, None
        action = self.pending_action
        succeeded = False
        try:
            update = pending.result()
            if action == "social" and update.social_committed is None:
                raise ValueError("SOCIAL_ACK_MISSING")
            if action == "wait":
                if update.wait_committed is None:
                    raise ValueError("WORLD_TIME_ACK_MISSING")
                if not update.wait_committed:
                    self.clock.restore(self.reserved_seconds)
                self.reserved_seconds = 0
                self.wait_error = not update.wait_committed
            if action == "supply":
                self.supply_error = False
            if action == "load" or self.update is None:
                self.clock.reset(self.now_ns())
            self.render(update)
            if action == "transport":
                self.transport_ack(update)
            if action == "social":
                self.social_command = None
                self.social_error = False
                if self.social_panel is not None:
                    self.social_panel.proposal = None
            if action == "supply":
                self.supply_command = None
                self.retry_supply.grid_remove()
            if action in ("say", "speech", "generate", "reply"):
                self.dialogue_ack(action, update)
            succeeded = True
        except Exception as error:
            logging.getLogger(__name__).exception("World request or presentation failed")
            if self.reserved_seconds:
                self.wait_error = True
            if action == "supply":
                self.supply_error = True
                self.retry_supply.grid(row=1, column=4, padx=4, pady=3)
            if action == "social":
                self.social_error = True
            if action == "transport":
                self.transport_error = True
                self.transport_running = self.transport_next = False
            if action in ("say", "speech", "generate", "reply"):
                self.failed_dialogue_action = action
                self.dialogue_running = False
                self.dialogue_next = None
                self.dialogue_recovery = action != "generate" or not (
                    isinstance(error, GenerationError) or str(error).startswith("DIALOGUE_")
                )
                if self.dialogue is not None:
                    code = error.code if isinstance(error, GenerationError) else str(error)
                    notice = dialogue_notice(code)
                    if (
                        action == "generate"
                        and not self.dialogue_recovery
                        and self.worker is not None
                        and self.worker.authored_supply
                    ):
                        notice += " 지도에서 ‘보급 의뢰 대화’를 열어 진행할 수 있습니다."
                    self.dialogue.status.set(notice)
            self.status.set(f"처리하지 못했습니다: {error}")
        finally:
            self.clock.sample(self.now_ns())
            self.pending_action = None
            self.clock.transition(self._clock_mode(), self.now_ns())
            for button in self.buttons:
                button.configure(state="normal")
            self.dialogue_controls()
        if succeeded:
            self.resume_deferred()

    def render(self, update: WorldUpdate) -> None:
        self.update = update
        stacks = "\n".join(f"{item_label(item)}: {count}" for item, count in update.inventory.items)
        self.supply_text.set(update.supply_text)
        self.offer_button.configure(
            state="normal" if update.offers and not self.supply_error else "disabled"
        )
        self.inventory_text.set(
            f"소지금: {update.inventory.gold}\n" + (stacks or "소지품이 없습니다.")
        )
        self.resident_text.set(
            "\n".join(
                f"{resident.name} · {resident.activity} · {resident.site}"
                + (
                    f" · {resident_membership(self.worker.social, resident.resident_id)}"
                    if self.worker is not None and self.worker.social is not None
                    else ""
                )
                for resident in update.residents
            )
        )
        state = update.state
        self.route_ids = {
            f"{p.name} · {r.distance_km}km · {'도보' if r.kind == 'road' else '승선 필요'}": p.id
            for p, r in self.catalog.neighbors(state.place_id)
        }
        values = tuple(self.route_ids)
        self.routes.configure(values=values)
        if self.destination.get() not in values:
            self.destination.set(values[0] if values else "")
        place = self.catalog.place(state.place_id)
        location = place.name
        if update.journey is not None and update.journey.phase != "idle":
            location = f"{self.catalog.place(update.journey.origin_id).name} → {self.catalog.place(update.journey.destination_id).name} · 여정 중"
        if state.destination_id:
            location += f" → {self.catalog.place(state.destination_id).name} · {state.offset_m}m"
        self.status.set(
            f"{location} · 게임 시간 {update.tick}초 · {transport_notice(social_notice(update.notice))}"
        )
        if self.transport_panel is not None:
            self.transport_panel.render(update)
        if self.social_panel is not None and update.social is not None:
            self.social_panel.render(
                update.social,
                state.place_id,
                update.notice if self.pending_action == "social" else "",
            )
        self.inspect(self.map.selected)
        self.road.delete("all")
        if self.dialogue is not None:
            self.dialogue.render(update)
        if update.journey is not None and update.journey.phase != "idle":
            self.road.create_text(
                330,
                32,
                text=f"{'마차' if update.journey.mode == 'carriage' else '선박'} · {update.journey.progress_m}m · {'통행 제한' if update.journey.phase == 'blocked' else '귀환' if update.journey.phase == 'returning' else '여정 진행'}",
                fill="white",
                tags=("journey",),
            )
            return
        # Local 30-metre view:walking changes the ground under the centered player.
        for meter in range(state.offset_m - 15, state.offset_m + 16):
            x = 330 + (meter - state.offset_m) * 20
            self.road.create_line(x, 45, x, 52, fill="#9dba91")
            if meter >= 0 and meter % 5 == 0:
                self.road.create_text(x, 58, text=f"{meter}m", fill="white")
        self.road.create_oval(324, 24, 336, 42, fill="#ffe08a", tags=("player",))

    def dialogue_controls(self) -> None:
        in_transit = (
            self.update is not None
            and self.update.journey is not None
            and self.update.journey.phase != "idle"
        )
        if self.transport_panel is not None:
            self.transport_panel.controls(
                busy=self.paused
                or self.pending is not None
                or self.dialogue_running
                or self.dialogue_recovery
                or self.social_error
                or self.supply_error
                or self.wait_error
                or self.transport_running
                or bool(self.reserved_seconds),
                recovery=self.transport_error,
            )
        if self.social_panel is not None:
            self.social_panel.controls(
                busy=self.paused
                or self.pending is not None
                or self.dialogue_running
                or self.dialogue_recovery
                or self.supply_error
                or self.wait_error
                or in_transit
                or self.transport_error
                or bool(self.reserved_seconds)
                or (self.social_command is not None and not self.social_error),
                recovery=self.social_error,
            )
        if self.dialogue is not None:
            self.dialogue.controls(
                paused=self.paused,
                busy=self.pending is not None
                or self.social_error
                or self.supply_error
                or in_transit
                or self.transport_error,
                running=self.dialogue_running,
                recovery=self.dialogue_recovery,
                generating=self.pending_action == "generate",
            )

    def say(self, npc_id: str, text: str) -> None:
        if (
            self.dialogue is None
            or not self.dialogue.live_npc
            or self.pending is not None
            or self.paused
            or self.dialogue_running
            or self.dialogue_recovery
            or self.social_error
            or self.supply_error
            or self.transport_error
            or self.transport_running
            or self.in_transit
        ):
            return
        normalized = unicodedata.normalize("NFC", text)
        try:
            validate_speech(normalized)
        except ValueError:
            self.dialogue.status.set("1~512글자의 공백이 아닌 발언을 입력해 주세요.")
            return
        self.clock.sample(self.now_ns())
        self.dialogue_npc, self.dialogue_text, self.dialogue_input = npc_id, normalized, text
        self.want_reply, self.dialogue_cancelled, self.dialogue_running = True, False, True
        self.new_dialogue_stage("say", flush=True)

    def new_dialogue_stage(self, action: WorldAction, *, flush: bool = False) -> None:
        self.dialogue_sequence += 1
        self.dialogue_key = f"ui-speech-{self.dialogue_sequence}"
        if flush:
            self.send(action)
        else:
            self.start_request(action)

    def dialogue_ack(self, action: WorldAction, update: WorldUpdate) -> None:
        if action != "generate" and update.speech_committed is None:
            raise ValueError("WORLD_DIALOGUE_ACK_MISSING")
        self.dialogue_recovery = False
        state = update.conversation
        if state is None:
            raise ValueError("WORLD_DIALOGUE_ACK_MISSING")
        if action != "generate" and not update.speech_committed:
            self.dialogue_running = False
            if self.dialogue is not None:
                self.dialogue.status.set(dialogue_notice(update.notice))
            return
        if (
            action == "say"
            and self.dialogue is not None
            and self.dialogue.text() == self.dialogue_input
        ):
            self.dialogue.input.delete("1.0", "end")
        if self.dialogue_cancelled:
            self.dialogue_next = None
        elif state.remaining:
            self.dialogue_next = "speech"
        elif action == "generate":
            if not update.reply_ready:
                raise ValueError("WORLD_DIALOGUE_REPLY_MISSING")
            self.dialogue_next = "reply"
        elif self.want_reply and state.exchanges and not state.exchanges[-1].reply_text:
            self.dialogue_next = "generate"
        else:
            self.dialogue_next = None
        self.dialogue_running = self.dialogue_next is not None
        if self.dialogue is not None:
            self.dialogue.status.set(
                "일시정지 · ESC를 누르면 이어서 진행합니다."
                if self.paused
                else f"발언 진행 중 · 남은 게임 시간 {state.remaining}초"
                if state.remaining
                else "응답을 준비하는 중…"
                if self.dialogue_running
                else "대화를 반영했습니다."
            )

    def conversation_action(self, action: str) -> None:
        if self.worker is None or self.dialogue is None:
            return
        if not self.worker.live_npc and action not in ("speech", "recover"):
            return
        if action == "cancel":
            self.worker.cancel_conversation()
            self.want_reply = False
            self.dialogue_cancelled = True
            self.dialogue_next = None
            return
        if (
            self.paused
            or self.pending is not None
            or self.transport_error
            or self.transport_running
            or self.in_transit
        ):
            return
        if action == "recover" and self.dialogue_recovery:
            if self.pending_action is not None:
                return
            self.dialogue_recovery = False
            self.dialogue_running = True
            self.start_request(self.failed_dialogue_action)
            return
        if self.dialogue_recovery or self.dialogue_running or self.update is None:
            return
        if action == "skip":
            self.want_reply = False
            self.dialogue.status.set(
                "답을 기다리지 않고 계속합니다. 전달한 발언은 기억에 남습니다."
            )
            return
        self.clock.sample(self.now_ns())
        self.want_reply, self.dialogue_cancelled, self.dialogue_running = (
            action == "retry",
            False,
            True,
        )
        self.new_dialogue_stage("generate" if action == "retry" else "speech", flush=True)

    def confirm_dialogue_supply(self, offer: SupplyOffer) -> None:
        self.confirm_supply(offer, None)

    def show_supply_offer(self) -> None:
        if (
            self.paused
            or self.ai_waiting
            or self.pending is not None
            or self.supply_error
            or self.update is None
            or not self.update.offers
        ):
            return
        if self.offer_panel is not None and self.offer_panel.winfo_exists():
            self.offer_panel.lift()
            return
        offer = self.update.offers[0]
        panel = tk.Toplevel(self.root)
        self.offer_panel = panel
        panel.title(offer.npc_name + "의 제안")
        if self.worker is not None and self.worker.authored_supply:
            ttk.Label(panel, text=authored_supply_line(offer), wraplength=480, justify="left").pack(
                padx=18, pady=(14, 0)
            )
        ttk.Label(panel, text=offer.summary, wraplength=480, padding=18, justify="left").pack()
        ttk.Button(
            panel, text="확인하고 진행", command=partial(self.confirm_supply, offer, panel)
        ).pack(pady=6)
        ttk.Button(panel, text="거절 / 닫기", command=panel.destroy).pack(pady=6)
        panel.bind("<Escape>", self.toggle_pause)

    def confirm_supply(self, offer: SupplyOffer, panel: tk.Toplevel | None) -> None:
        if (
            self.paused
            or self.ai_waiting
            or self.pending is not None
            or self.supply_error
            or self.wait_error
            or self.reserved_seconds
            or self.supply_command is not None
            or self.dialogue_running
            or self.dialogue_recovery
            or self.transport_error
            or self.transport_running
            or self.in_transit
        ):
            return
        self.supply_command = offer.action
        self.supply_sequence += 1
        self.supply_request_key = f"ui-supply-{self.supply_sequence}"
        if panel is not None:
            panel.destroy()
        self.send("supply")


def launch_world(
    catalog_path: Path = DEVELOPMENT_WORLD,
    *,
    authored_supply: bool = False,
    live_npc: bool = True,
    knowledge: bool = False,
) -> int:
    try:
        catalog = load_world(catalog_path)
        social = load_social(catalog)
        transport = load_transport(catalog)
    except (OSError, ValueError, TypeError) as error:
        logging.getLogger(__name__).exception("World catalog load failed")
        print(f"세계를 불러오지 못했습니다: {error}", file=sys.stderr)
        return 2
    root = tk.Tk()
    directory = "world-authored-supply-play" if authored_supply else "world-transport-play"
    worker = WorldWorker(
        KNOWLEDGE_WORLD_PATH if knowledge else Path("tmp") / directory / "game.sqlite",
        catalog,
        scenario=AUTHORED_SUPPLY_SCENARIO if authored_supply else SupplyScenario(),
        social=social,
        transport=transport,
        authored_supply=authored_supply,
        live_npc=live_npc,
        knowledge=knowledge,
    )
    try:
        WorldMapWindow(root, catalog, worker)
        root.mainloop()
    finally:
        try:
            worker.close()
        finally:
            root.destroy()
    return 0
