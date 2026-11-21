"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.tick_hz = tuning.get("tick_hz", 60)
        self.phase_tick = 0
        self.rng = streams
        self.ids = ids
        self.random_customers = scenario.get("random_customers", True)
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = []
        self._init_customers(scenario.get("customers", []))
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.phase_tick += 1
        # TODO(nhóm): giảm kiên nhẫn / nấu / ăn; bếp chín -> ready; xử lý khách theo thứ tự PRD-0 mục F.
        self._move(inp)
        # TODO(nhóm): tối đa MỘT interact, chọn đối tượng theo (khoảng cách, bếp trước bàn, id).
        # Khách mới theo lịch (first_customer_tick, customer_interval_s)
        if self._should_spawn_customer():
            table = self._find_available_table()
            if table is not None:
                events.extend(self._spawn_customer(table))
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _should_spawn_customer(self) -> bool:
        if not self.random_customers:
            return False
        first_tick = self.t["first_customer_tick"]
        interval_ticks = int(round(self.t["customer_interval_s"] * self.tick_hz))
        if self.phase_tick < first_tick:
            return False
        return (self.phase_tick - first_tick) % interval_ticks == 0

    def _find_available_table(self):
        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in self.tables if tb["id"] not in occupied]
        if not free_tables:
            return None
        return sort_by_id(free_tables)[0]

    def _spawn_customer(self, table):
        events = []
        avail = self._available_stock()
        valid_dishes = []
        for did in sorted(self.menu.keys()):
            recipe = self.menu[did]["recipe"]
            if all(avail.get(k, 0) >= req for k, req in recipe.items()):
                valid_dishes.append(did)

        if not valid_dishes:
            events.append(("no_dish", {"table_id": table["id"]}))
            return events

        rng = self.rng.get("customers")
        chosen_dish = rng.choice(valid_dishes)
        recipe = dict(self.menu[chosen_dish]["recipe"])

        customer_id = self.ids.new("C")
        pat_ticks = int(round(self.t["patience_s"] * self.tick_hz))
        new_customer = {
            "id": customer_id,
            "table_id": table["id"],
            "dish_id": chosen_dish,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": pat_ticks,
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": recipe,
            "base_price": None,
            "tip": 0,
        }
        self.customers.append(new_customer)
        events.append((
            "customer_arrived",
            {
                "customer_id": customer_id,
                "table_id": table["id"],
                "dish_id": chosen_dish,
                "reserved": recipe,
            }
        ))
        return events

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])

    def _init_customers(self, scenario_customers):
        pat_ticks = int(round(self.t["patience_s"] * 60))
        for c in scenario_customers:
            cust = {
                "id": c["id"],
                "table_id": c["table_id"],
                "dish_id": c["dish_id"],
                "order_tick": c.get("order_tick", 0),
                "state": c.get("state", "waiting"),
                "patience_ticks_left": c.get("patience_ticks_left", pat_ticks),
                "eat_ticks_left": c.get("eat_ticks_left", 0),
                "order_status": c.get("order_status", "reserved" if c.get("state", "waiting") == "waiting" else "served"),
                "reserved": dict(c["reserved"]) if "reserved" in c else None,
                "base_price": c.get("base_price", None),
                "tip": c.get("tip", 0),
            }
            self.customers.append(cust)
            self.ids.reserve(cust["id"])
        self._infer_customer_reservations()

    def _available_stock(self) -> dict:
        """Kho khả dụng = stock - tổng nguyên liệu đang được giữ (reserved)."""
        reserved_totals = {}
        for c in self.customers:
            if c.get("order_status") == "reserved":
                res = c.get("reserved") or {}
                for k, v in res.items():
                    if v > 0:
                        reserved_totals[k] = reserved_totals.get(k, 0) + v
        return {k: max(0, self.stock.get(k, 0) - reserved_totals.get(k, 0)) for k in self.stock}

    def _infer_customer_reservations(self):
        """Khách fixture thiếu reserved được suy ra theo công thức món ăn (order_tick tăng dần, rồi id bàn)."""
        unreserved = [c for c in self.customers if not c.get("reserved") and c.get("order_status") == "reserved"]
        unreserved.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
        for c in unreserved:
            recipe = self.menu[c["dish_id"]]["recipe"]
            avail = self._available_stock()
            for k, req in recipe.items():
                if avail.get(k, 0) < req:
                    from ..errors import BadInput
                    raise BadInput(f"không đủ kho để giữ nguyên liệu cho khách {c['id']} (món {c['dish_id']})")
            c["reserved"] = dict(recipe)

        for c in self.customers:
            if not c.get("reserved"):
                c["reserved"] = {}

        self._check_total_reservations()

    def _check_total_reservations(self):
        reserved_totals = {}
        for c in self.customers:
            if c.get("order_status") == "reserved":
                res = c.get("reserved") or {}
                for k, v in res.items():
                    if v > 0:
                        reserved_totals[k] = reserved_totals.get(k, 0) + v
        for k, v in reserved_totals.items():
            if v > self.stock.get(k, 0):
                from ..errors import BadInput
                raise BadInput(f"tổng nguyên liệu giữ vượt quá kho thực tế cho {k}: giữ {v}, kho có {self.stock.get(k, 0)}")
