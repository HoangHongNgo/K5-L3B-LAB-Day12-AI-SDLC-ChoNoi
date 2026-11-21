"""Vòng ngày (`--mode day`, TICKET-02 mục 2): máy pha gather → quan → shop → (Ngày kế | end).

Giao diện chốt sẵn (TASK.md Phase 2): `DaySim(tuning, scenario, streams, *, days=1)` có
`step(inputs) -> events`, `snapshot() -> dict`, `done`, `result`.

- Đầu Ngày phát `day_start` → `day_plan` → `phase_start(gather)` (Ngày 1: ở tick 0, trước snapshot tick 0).
- Pha kết thúc (`gather_end` / `quan_end` / `shop_end`) thì dựng pha kế và phát `phase_start` CÙNG tick;
  pha mới chạy gameplay từ bước sau. Ngày chỉ hoàn tất khi Shop đóng, kể cả Ngày cuối.
- gather → quan: bàn giao kho trong bộ nhớ (schema kho v1.0); ngất thì kho rỗng, quán vẫn mở.
- quan → shop: Shop nhận tiền/earned/cấp và kho dư; sau Shop kho dư bị bỏ, Ngày kế giỏ mới.
- Trạng thái xuyên Ngày (tiền, earned, uy tín, cấp) chỉ đi qua `DayState` (lát S); DaySim không tự tính.

Event trả về dạng (name, data, meta) với meta = {"day", "phase"} để runner ghi vỏ event có `day`.
TICKET-02 mục 4.4: `day_start`/`phase_start` có data `{}`, `day_plan` có `{dishes, ingredients}`; event kết thúc
mang pha cũ; snapshot đổi pha ghi pha mới với `phase_tick: 0`. Mục 4.3: khối `gather`/`quan` của scenario là
mẫu khởi tạo MỖI Ngày; kho/khách/món thuộc kế hoạch kiểm trên kho thực lúc mở quán (mâu thuẫn -> mã 2).
"""

import copy
import inspect

from ..errors import BadInput
from ..ids import IdAllocator

MAX_DAYS = 5


# ---------- factory mặc định: sim thật ----------

def _call_compatible(cls, *args, **kwargs):
    """Gọi constructor chỉ với các tham số từ khóa mà lớp hỗ trợ (tương thích sim trước/sau khi gộp lát)."""
    params = inspect.signature(cls).parameters
    if not any(p.kind is p.VAR_KEYWORD for p in params.values()):
        kwargs = {k: v for k, v in kwargs.items() if k in params}
    return cls(*args, **kwargs)


def _gather_factory(tuning, scenario, streams, ids, *, day, active_upgrades):
    from .gather import GatherSim
    return _call_compatible(GatherSim, tuning, scenario, streams, ids, day=day, active_upgrades=active_upgrades)


def _quan_factory(tuning, scenario, streams, ids, *, inventory, menu_ids, money, earned, reputation):
    from .quan import QuanSim
    return _call_compatible(QuanSim, tuning, scenario, streams, ids, inventory=inventory, menu_ids=menu_ids,
                            money=money, earned=earned, reputation=reputation)


def _shop_factory(tuning, *, money, earned, upgrades, stock):
    try:
        from .shop import ShopSim
    except ImportError:
        raise BadInput("--mode day cần ShopSim (chonoi/sim/shop.py, lát S) — chưa gộp")
    return ShopSim(tuning, money=money, earned=earned, upgrades=upgrades, stock=stock)


def _state_factory(tuning, day_block):
    try:
        from .progress import DayState
    except ImportError:
        raise BadInput("--mode day cần DayState (chonoi/sim/progress.py, lát S) — chưa gộp")
    if hasattr(DayState, "from_scenario"):
        return DayState.from_scenario(tuning, day_block)
    return DayState(tuning, day_block)


DEFAULT_FACTORIES = {"gather": _gather_factory, "quan": _quan_factory, "shop": _shop_factory,
                     "state": _state_factory}


# ---------- kế hoạch ngày ----------

def _override_entry(override, day):
    """`scenario.day.day_plan` ghi đè theo số Ngày: map "<day>" -> {dishes[, ingredients]} hoặc mảng {day,...}."""
    if isinstance(override, list):
        return next((e for e in override if isinstance(e, dict) and e.get("day") == day), None)
    if isinstance(override, dict):
        return override.get(str(day), override.get(day))
    return None


def plan_for(tuning, scenario_day, day):
    """Kế hoạch Ngày `day` = {dishes, ingredients}: preset `tuning.day_plan` (mảng {day,dishes,ingredients}),
    có thể bị `scenario.day.day_plan` ghi đè. Luôn tính lại ingredients = tổng công thức × số suất và so với
    giá trị khai nếu có (lệch -> BadInput, mã 2)."""
    plan = next((e for e in tuning.get("day_plan", []) if e.get("day") == day), None)
    over = _override_entry((scenario_day or {}).get("day_plan"), day)
    if over is not None:
        plan = over
    if not isinstance(plan, dict) or not plan.get("dishes"):
        raise BadInput(f"thiếu day_plan (dishes) cho Ngày {day}")
    menu = tuning["menu"]
    computed = {}
    for did, n in plan["dishes"].items():
        if did not in menu:
            raise BadInput(f"day_plan Ngày {day}: món không có trong menu: {did}")
        if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
            raise BadInput(f"day_plan Ngày {day}: số suất {did} phải là số nguyên dương")
        for k, req in menu[did]["recipe"].items():
            computed[k] = computed.get(k, 0) + req * n
    declared = plan.get("ingredients")
    if declared is not None and {k: v for k, v in declared.items() if v} != computed:
        raise BadInput(f"day_plan Ngày {day}: ingredients {declared} khác công thức x số suất {computed}")
    return {"dishes": dict(sorted(plan["dishes"].items())), "ingredients": dict(sorted(computed.items()))}


def _validate_quan_opening(tuning, quan_block, inventory, menu_ids):
    """Kiểm kho/khách/bếp/món kế hoạch trên kho thực lúc mở quán (hàm của lát Q, khi đã gộp)."""
    try:
        from ..scenario import validate_quan_against_inventory
    except ImportError:
        return
    validate_quan_against_inventory(quan_block, inventory, tuning, list(menu_ids))


# ---------- máy pha ----------

class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids=None, *, days=1, factories=None):
        if isinstance(days, bool) or not isinstance(days, int) or not (1 <= days <= MAX_DAYS):
            raise BadInput(f"--days phải là số nguyên trong [1, {MAX_DAYS}]")
        self.tuning = tuning
        self.scenario = scenario or {}
        self.streams = streams
        self.ids = IdAllocator() if ids is None else ids
        self.days = days
        self.f = dict(DEFAULT_FACTORIES, **(factories or {}))
        self.state = self.f["state"](tuning, self.scenario.get("day", {}))
        self.day = getattr(self.state, "day", 1)
        self.days_completed = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.plan = None
        self.cur = None
        self.done = False
        self.reason = None
        self.initial_events = self._start_day()  # runner ghi ở tick 0, trước snapshot tick 0

    # --- thuộc tính runner đọc cho phần chung của snapshot / end ---
    @property
    def phase(self):
        return self.cur.phase

    @property
    def time_left_ticks(self):
        return self.cur.time_left_ticks

    def _live(self, key):
        """Tiền/earned/uy tín: quán và Shop cập nhật trực tiếp; buổi sáng lấy từ DayState."""
        if self.cur.phase in ("quan", "shop") and hasattr(self.cur, key):
            return getattr(self.cur, key)
        return getattr(self.state, key)

    @property
    def money(self):
        return self._live("money")

    @property
    def earned(self):
        return self._live("earned")

    @property
    def reputation(self):
        return self._live("reputation")

    @property
    def result(self) -> dict:
        return {"days_completed": self.days_completed, "money": self.state.money, "earned": self.state.earned,
                "reputation": self.state.reputation, "upgrades": dict(self.state.upgrades)}

    def snapshot(self) -> dict:
        snap = dict(self.cur.snapshot())
        upgrades = getattr(self.cur, "upgrades", None) if self.cur.phase == "shop" else None
        snap.update(day=self.day, day_plan=self.plan,
                    upgrades=dict(upgrades if upgrades is not None else self.state.upgrades),
                    active_upgrades=dict(self.state.active_upgrades))
        return snap

    # --- một bước ---
    def step(self, inp):
        self.sim_tick += 1
        self.phase_tick += 1
        phase = self.cur.phase
        out = [self._ev(name, data, phase) for name, data in self.cur.step(inp)]
        if self.cur.done:
            out.extend(self._advance(phase))
        return out

    def _ev(self, name, data, phase=None):
        return (name, data, {"day": self.day, "phase": phase or self.cur.phase})

    def _phase_start(self, sim):
        self.cur = sim
        self.phase_tick = 0
        return [self._ev("phase_start", {})]

    def _start_day(self):
        self.plan = plan_for(self.tuning, self.scenario.get("day"), self.day)
        gather = self.f["gather"](self.tuning, copy.deepcopy(self.scenario.get("gather", {})), self.streams,
                                  self.ids, day=self.day, active_upgrades=dict(self.state.active_upgrades))
        self.cur = gather
        evs = [self._ev("day_start", {}, "gather"), self._ev("day_plan", copy.deepcopy(self.plan), "gather")]
        return evs + self._phase_start(gather)

    def _result(self):
        res = getattr(self.cur, "result", None)
        if res is None and self.cur.phase == "quan":
            # QuanSim trước khi gộp lát Q chưa có `result`: đọc trạng thái cuối theo cùng khóa.
            c = self.cur
            res = {"money": c.money, "earned": c.earned, "reputation": c.reputation,
                   "stock": {k: v for k, v in sorted(c.stock.items()) if v > 0}}
        return res

    def _advance(self, phase):
        res = self._result()
        if phase == "gather":
            block = copy.deepcopy(self.scenario.get("quan", {}))
            items, menu_ids = dict(res["inventory"]["items"]), list(self.plan["dishes"])
            if self.f["quan"] is _quan_factory:
                _validate_quan_opening(self.tuning, block, items, menu_ids)
            quan = self.f["quan"](self.tuning, block, self.streams, self.ids, inventory=items, menu_ids=menu_ids,
                                  money=self.state.money, earned=self.state.earned,
                                  reputation=self.state.reputation)
            return self._phase_start(quan)
        if phase == "quan":
            self.state.apply_quan_result(res)
            shop = self.f["shop"](self.tuning, money=self.state.money, earned=self.state.earned,
                                  upgrades=dict(self.state.upgrades), stock=dict(res.get("stock", {})))
            return self._phase_start(shop)
        # shop đóng: Ngày hoàn tất; kho dư bị bỏ.
        self.state.apply_shop_result(res)
        self.days_completed += 1
        if self.days_completed >= self.days:
            self.done = True
            self.reason = "days_complete"
            return []
        self.state.start_next_day()  # sao upgrades -> active_upgrades, hồi oxy/Máu theo cấp (lát S)
        next_day = getattr(self.state, "day", None)
        self.day = next_day if isinstance(next_day, int) and next_day > self.day else self.day + 1
        return self._start_day()
