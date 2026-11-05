"""Nonmodal social inspection and concrete confirmation of supported actions."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
import tkinter as tk
from tkinter import ttk

from contracts.world_social import SocialAction
from domain.world import WorldCatalog
from domain.world_social import HOSTILE_THRESHOLD, SocialCatalog, SocialState, reaction


def social_notice(code: str) -> str:
    return {
        "SOCIAL_ENTRY_DENIED": "해당 도시와 적대 중이라 입장이 제한됩니다. 평판과 관계를 확인해 주세요.",
        "SOCIAL_CONTRACT_DENIED": "이 지역과 적대 중이라 새 보급 의뢰를 받을 수 없습니다. 화해를 요청할 수 있습니다.",
        "SOCIAL_IDENTITY_LOCKED": "이미 정한 종족과 국적은 이 저장에서 다시 바꿀 수 없습니다.",
        "SOCIAL_IDENTITY": "유효한 종족과 국적을 선택해 주세요.",
        "SOCIAL_NOTHING_TO_REPAIR": "회복할 나쁜 평판이 없습니다. 화해로 좋은 평판을 쌓을 수는 없습니다.",
        "SOCIAL_OUT_OF_REACH": "도시에 도착한 뒤 행동해 주세요.",
        "DIALOGUE_SPEAKING": "먼저 진행 중인 말을 마쳐 주세요.",
    }.get(code, code)


def city_standing(state: SocialState, catalog: SocialCatalog, place_id: str) -> str:
    local = catalog.local(place_id)
    scores = dict(state.reputation)
    score = reaction(state, catalog, place_id)
    access = "입장·새 의뢰 제한" if score <= HOSTILE_THRESHOLD else "입장·새 의뢰 가능"
    return (
        f"{local.name} 평판 {scores[local.id]:+d} · 국가 평판 "
        f"{scores[catalog.national(local.country_id).id]:+d} · 종합 {score:+d}\n{access}"
    )


def resident_membership(catalog: SocialCatalog, npc_id: str) -> str:
    identity = next(r for r in catalog.residents if r.npc_id == npc_id)
    ancestry = next(a for a in catalog.ancestries if a.id == identity.ancestry_id)
    return f"{ancestry.name} · {catalog.local(identity.place_id).name}"


class SocialPanel:
    def __init__(
        self,
        root: tk.Tk,
        world: WorldCatalog,
        catalog: SocialCatalog,
        confirm: Callable[[SocialAction], None],
        retry: Callable[[], None],
        pause: Callable[[tk.Event[tk.Misc]], str],
    ) -> None:
        self.world, self.catalog, self.confirm_callback = world, catalog, confirm
        self.panel = tk.Toplevel(root)
        self.panel.title("종족·소속·세력 관계")
        self.panel.geometry("680x640")
        self.panel.minsize(480, 520)
        self.panel.protocol("WM_DELETE_WINDOW", self.panel.withdraw)
        self.panel.bind("<Escape>", pause)
        self.panel.withdraw()
        self.state: SocialState | None = None
        self.proposal: SocialAction | None = None
        self.ancestries = {a.name: a.id for a in catalog.ancestries}
        self.countries = {"국적 없음": "none", **{c.name: c.id for c in world.countries}}
        self.ancestry = tk.StringVar(self.panel, next(iter(self.ancestries)))
        self.country = tk.StringVar(self.panel, "국적 없음")
        self.info = tk.Text(self.panel, wrap="word", height=14, state="disabled")
        self.info.pack(fill="both", expand=True, padx=12, pady=8)
        selectors = ttk.Frame(self.panel)
        selectors.pack(fill="x", padx=12)
        self.ancestry_box = ttk.Combobox(
            selectors, textvariable=self.ancestry, values=tuple(self.ancestries), state="readonly"
        )
        self.country_box = ttk.Combobox(
            selectors, textvariable=self.country, values=tuple(self.countries), state="readonly"
        )
        self.ancestry_box.pack(side="left", expand=True, fill="x", padx=3)
        self.country_box.pack(side="left", expand=True, fill="x", padx=3)
        self.ancestry_box.bind("<<ComboboxSelected>>", self.selection_changed)
        self.country_box.bind("<<ComboboxSelected>>", self.selection_changed)
        controls = ttk.Frame(self.panel)
        controls.pack(fill="x", padx=12, pady=8)
        self.buttons: dict[str, ttk.Button] = {}
        for action, label in (
            ("identify", "종족·국적 정하기"),
            ("protest", "지역 조합에 항의"),
            ("reconcile", "화해 요청"),
        ):
            button = ttk.Button(controls, text=label, command=partial(self.propose, action))
            button.pack(side="left", expand=True, fill="x", padx=3)
            self.buttons[action] = button
        self.terms = tk.StringVar(
            self.panel, "종족은 인격을 결정하지 않습니다. 평판은 실제 행동으로 변합니다."
        )
        self.terms_label = ttk.Label(
            self.panel, textvariable=self.terms, wraplength=630, justify="left"
        )
        self.terms_label.pack(fill="x", padx=12, pady=4)
        self.confirm = ttk.Button(
            self.panel, text="조건을 확인하고 실행", command=self.execute, state="disabled"
        )
        self.confirm.pack(pady=4)
        self.retry = ttk.Button(
            self.panel, text="같은 행동 반영 재시도", command=retry, state="disabled"
        )
        self.retry.pack(pady=4)
        self.panel.bind("<Configure>", self.resize, add=True)

    def resize(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget is self.panel:
            self.terms_label.configure(wraplength=max(200, event.width - 24))

    def show(self) -> None:
        self.panel.deiconify()
        self.panel.lift()

    def selection_changed(self, event: tk.Event[tk.Misc]) -> None:
        self.proposal = None
        self.confirm.configure(state="disabled")
        self.terms.set("선택한 종족·국적의 조건을 다시 확인해 주세요.")

    def propose(self, operation: str) -> None:
        if self.state is None:
            return
        if operation == "identify":
            self.proposal = SocialAction(
                operation, self.ancestries[self.ancestry.get()], self.countries[self.country.get()]
            )
            self.terms.set(
                f"종족: {self.ancestry.get()} · 국적: {self.country.get()}\n이 저장에서는 다시 변경할 수 없습니다. 정체성을 기록하며 1초가 흐릅니다."
            )
        else:
            self.proposal = SocialAction(operation)
            self.terms.set(
                "현재 도시의 조합에 항의합니다. 지역 평판 -15, 국가 평판 -5, 행동 시간 5초. 종합 관계 -30 이하면 입장·새 의뢰가 제한됩니다."
                if operation == "protest"
                else "현재 도시의 조합에 화해를 요청합니다. 나쁜 지역 평판 +5, 국가 평판 +1, 행동 시간 10초. 0을 넘겨 올리지 않으며 좋은 평판은 보존합니다."
            )
        self.confirm.configure(state="normal")

    def execute(self) -> None:
        if self.proposal is not None:
            self.confirm_callback(self.proposal)

    def render(self, state: SocialState, place_id: str, notice: str) -> None:
        self.state = state
        ancestry = next(
            (a.name for a in self.catalog.ancestries if a.id == state.ancestry_id), "미선택"
        )
        citizenship = next(
            (c.name for c in self.world.countries if c.id == state.country_id),
            "국적 없음" if state.country_id == "none" else "미선택",
        )
        if state.ancestry_id:
            self.ancestry.set(ancestry)
            self.country.set(citizenship)
        lines = [
            f"내 종족: {ancestry} · 국적: {citizenship}",
            city_standing(state, self.catalog, place_id),
            "",
            "도시별 관계 (종족·국적·평판은 서로 다른 정보입니다)",
        ]
        lines.extend(
            f"{p.name}: {reaction(state, self.catalog, p.id):+d}" for p in self.world.places
        )
        lines.extend(("", "국가 간 외교 (공개된 초기 관계)"))
        names = {c.id: c.name for c in self.world.countries}
        lines.extend(
            f"{names[r.first]} / {names[r.second]}: {'우호' if r.score > 0 else '적대' if r.score < 0 else '중립'} · {r.reason}"
            for r in self.catalog.diplomacy
        )
        lines.extend(("", "함께 사는 종족"))
        lines.extend(f"{a.name}: {a.culture}" for a in self.catalog.ancestries)
        self.info.configure(state="normal")
        self.info.delete("1.0", "end")
        self.info.insert("1.0", "\n".join(lines))
        self.info.configure(state="disabled")
        if notice:
            self.terms.set(social_notice(notice))

    def controls(self, *, busy: bool, recovery: bool) -> None:
        for name, button in self.buttons.items():
            enabled = (
                not busy
                and not recovery
                and self.state is not None
                and not (name == "identify" and self.state.ancestry_id)
            )
            button.configure(state="normal" if enabled else "disabled")
        self.ancestry_box.configure(
            state="disabled"
            if busy or recovery or (self.state and self.state.ancestry_id)
            else "readonly"
        )
        self.country_box.configure(
            state="disabled"
            if busy or recovery or (self.state and self.state.ancestry_id)
            else "readonly"
        )
        self.confirm.configure(
            state="normal"
            if self.proposal is not None and not busy and not recovery
            else "disabled"
        )
        self.retry.configure(state="normal" if recovery and not busy else "disabled")
