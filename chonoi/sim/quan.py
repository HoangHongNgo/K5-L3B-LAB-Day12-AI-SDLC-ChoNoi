"""Buổi tối — Mở Quán (PRD-0 mục F, Quán).

  Lát 3: khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
         bỏ đi (customer_left), no_dish, vòng đời khách.
  Lát 4: interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
         ăn xong trả tiền (paid), boa, uy tín, hết ca (closing, quan_end).
"""

import math
from fractions import Fraction

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


def _order_ref(obj):
    """Chuẩn hóa món trên bếp/tay về {"order_id","dish_id"} hoặc None."""
    """Chuẩn hóa món trên bếp/tay về payload PRD-0 mục D {"order_id","dish_id","base_price"} hoặc None.
    Nhận payload object, hoặc dạng cũ của nhóm: dish là chuỗi kèm order_id/customer_id.
    base_price thiếu sẽ được điền sau khi dựng khách (_fill_payload_prices).
    """
    if obj is None:
        return None
    if isinstance(obj, str):
        return {"order_id": None, "dish_id": obj, "base_price": None}
    dish = obj.get("dish_id") or obj.get("dish")
    if isinstance(dish, dict):
        return _order_ref(dish)
    if dish is None:
        return None
    return {"order_id": obj.get("order_id") or obj.get("customer_id"), "dish_id": dish,
            "base_price": obj.get("base_price")}


# Trạng thái đơn theo PRD-0 mục D; tên cũ của nhóm (cooking/ready/carried) quy về assigned.
LEGACY_ASSIGNED = {"cooking", "ready", "carried"}


def _format_fresh(val):
    if isinstance(val, (int, float, str, Fraction)):
        f = float(val)
        if f.is_integer():
            return int(f)
        return round(f, 4)
    return val


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids=None, *, inventory=None, menu_ids=None,
                 money=0, earned=0, reputation=None, ctx=None, **kwargs):
        if ids is None:
            from ..ids import IdAllocator
            ids = IdAllocator()
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
        raw_inv = inventory if inventory is not None else scenario.get("stock", {})
        if isinstance(raw_inv, list):
            self.is_item_inventory = True
            raw_items = raw_inv
        elif isinstance(raw_inv, dict) and "items" in raw_inv and isinstance(raw_inv["items"], list):
            self.is_item_inventory = True
            raw_items = raw_inv["items"]
        else:
            custs = scenario.get("customers", [])
            if (tuning.get("contract_version") == "1.2"
                or "freshness" in tuning
                or any(isinstance(c.get("reserved"), list) for c in custs)):
                self.is_item_inventory = True
                raw_items = []
                if isinstance(raw_inv, dict):
                    for k, count in raw_inv.items():
                        for idx in range(count):
                            raw_items.append({"id": f"I_{k}_{idx+1}", "kind": k, "fresh": 100})
            else:
                self.is_item_inventory = False
                raw_items = None

        if self.is_item_inventory:
            self.items = []
            for it in (raw_items or []):
                self.items.append({
                    "id": str(it["id"]),
                    "kind": it["kind"],
                    "fresh": Fraction(str(it["fresh"])),
                })
            self.stock = {k: sum(1 for it in self.items if it["kind"] == k and it["fresh"] >= Fraction(30))
                          for k in sorted(set(it["kind"] for it in self.items))}
        else:
            self.items = None
            self.stock = dict(raw_inv if isinstance(raw_inv, dict) else {})

        self.hand = _order_ref(scenario.get("hand"))
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        if reputation is not None:
            self.reputation = float(reputation)
        else:
            self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.start_reputation = self.reputation

        self.stoves = []
        for s in self._merge(t["stoves"], scenario.get("stoves", [])):
            dish = _order_ref(s) if s.get("state", "idle") != "idle" else None
            state = s.get("state", "idle") if dish is not None else "idle"
            self.stoves.append({
                "id": s["id"],
                "pos": s["pos"],
                "state": state,
                "dish": dish,
                "cook_ticks_left": s.get("cook_ticks_left", 0),
                "ready_ticks": s.get("ready_ticks", 0),
            })
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = []
        self._init_customers(scenario.get("customers", []))
        self._fill_payload_prices()
        self.money = money
        self.earned = earned
        self.shift_earned = 0
        self.tips = 0
        self.menu_ids = menu_ids
        self.ctx = ctx or {}
        self.stats_served = 0
        self.stats_left = 0
        self.dish_served_counts = {}
        self.done = False
        self.reason = None
        self.result = None

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
        if self.is_item_inventory:
            stock_data = [{"id": it["id"], "kind": it["kind"], "fresh": _format_fresh(it["fresh"])}
                          for it in sorted(self.items, key=lambda x: id_key(x["id"]))]
        else:
            stock_data = {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
        return {
            "player": {"pos": self.pos},
            "stock": stock_data,
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def stats(self) -> dict:
        best_dish = None
        if self.dish_served_counts:
            best_count = max(self.dish_served_counts.values())
            best_dishes = [d for d, c in self.dish_served_counts.items() if c == best_count]
            best_dish = sorted(best_dishes)[0]
        return {
            "served": self.stats_served,
            "left": self.stats_left,
            "money_shift": self.shift_earned,
            "tips": self.tips,
            "reputation_delta": round(self.reputation - self.start_reputation, 3),
            "best_dish": best_dish,
        }

    def step(self, inp):
        """Một bước theo TICKET-03 / PRD-0 mục F (1 đồng hồ → 2 hao tươi & spoiled & re-reserve → 3 bếp → 4 di chuyển & interact → 5 trả tiền/kiên nhẫn/đóng ca → 6 lịch)."""
        events = []
        # 1. Đồng hồ, timer ca, nấu, ăn, kiên nhẫn.
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.phase_tick += 1
        self._tick_timers()
        self._update_customer_patience()
        # 2. Hao tươi kho thô, spoiled events, re-reservation
        events.extend(self._decay_freshness_and_handle_spoiled())
        # 3. Bếp chín -> ready
        events.extend(self._update_stoves())
        # 4. Di chuyển người chơi & interact
        self._move(inp)
        if inp.pressed("interact"):
            events.extend(self._interact())
        # 5. Khách ăn xong trả tiền, hết kiên nhẫn rời, hoặc dọn cuối ca
        closing = self.time_left_ticks <= 0
        events.extend(self._settle_customers(closing))
        if closing:
            for s in self.stoves:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
            self.hand = None
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            if self.is_item_inventory:
                stock_result = [{"id": it["id"], "kind": it["kind"], "fresh": _format_fresh(it["fresh"])}
                                for it in sorted(self.items, key=lambda x: id_key(x["id"]))]
            else:
                stock_result = {k: v for k, v in sorted(self.stock.items()) if v > 0}
            self.result = {
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation,
                "stock": stock_result,
                "stats": self.stats(),
            }
            return events
        # 6. Khách mới theo lịch (first_customer_tick, customer_interval_s)
        if self._should_spawn_customer():
            table = self._find_available_table()
            if table is not None:
                events.extend(self._spawn_customer(table))
        return events

    def _tick_timers(self):
        """Giảm cook/eat; ready_ticks chỉ tăng cho món đã ready từ đầu bước."""
        for s in self.stoves:
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
            elif s["state"] == "ready":
                s["ready_ticks"] += 1
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)

    def _update_stoves(self) -> list:
        """Theo id bếp, món nấu xong chuyển ready với ready_ticks = 0."""
        events = []
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] <= 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                events.append(("dish_ready", self._stove_data(s)))
        return events

    def _interact(self) -> list:
        """Chọn đúng một đối tượng theo (khoảng cách, bếp trước bàn, id); không tương tác được thì bỏ lượt."""
        r = self.t["interact_radius"]
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                cands.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                cands.append((d, 1, id_key(tb["id"]), "table", tb))
        if not cands:
            return []
        _, _, _, kind, obj = min(cands, key=lambda c: c[:3])
        if kind == "table":
            return self._serve(obj)
        if obj["state"] == "idle":
            return self._start_cooking(obj)
        if obj["state"] == "ready":
            return self._pick_dish(obj)
        return []

    def _decay_freshness_and_handle_spoiled(self) -> list:
        if not self.is_item_inventory:
            return []
        decay = Fraction(1, 240)
        spoiled_items = []
        for it in self.items:
            old_fresh = it["fresh"]
            new_fresh = max(Fraction(0), old_fresh - decay)
            it["fresh"] = new_fresh
            if old_fresh >= Fraction(30) and new_fresh < Fraction(30):
                spoiled_items.append(it)

        events = []
        if spoiled_items:
            spoiled_items.sort(key=lambda x: id_key(x["id"]))
            for it in spoiled_items:
                events.append(("spoiled", {
                    "item_id": it["id"],
                    "kind": it["kind"],
                    "location": "stock",
                }))

            spoiled_ids = {it["id"] for it in spoiled_items}
            # Xử lý các đơn có reserved bị ươn
            aff_custs = [c for c in self.customers if c.get("order_status") == "reserved"
                         and isinstance(c.get("reserved"), list)
                         and any(iid in spoiled_ids for iid in c["reserved"])]
            aff_custs.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))

            for c in aff_custs:
                c["reserved"] = []  # Nhả toàn bộ giữ chỗ của đơn
                recipe = self.menu[c["dish_id"]]["recipe"]
                other_reserved = {iid for oc in self.customers if oc is not c
                                  and oc.get("order_status") == "reserved"
                                  and isinstance(oc.get("reserved"), list)
                                  for iid in oc["reserved"]}
                can_re_reserve = True
                chosen_items = []
                for k, req in recipe.items():
                    cands = [it for it in self.items if it["kind"] == k and it["fresh"] >= Fraction(30) and it["id"] not in other_reserved]
                    cands.sort(key=lambda it: (-it["fresh"], id_key(it["id"])))
                    if len(cands) < req:
                        can_re_reserve = False
                        break
                    chosen = cands[:req]
                    chosen_items.extend(chosen)
                    for it in chosen:
                        other_reserved.add(it["id"])
                if can_re_reserve:
                    c["reserved"] = sorted([it["id"] for it in chosen_items], key=id_key)
                else:
                    c["order_status"] = "unfulfillable"
                    c["reserved"] = []
        return events

    def _start_cooking(self, stove) -> list:
        """Bếp idle lấy đơn reserved cũ nhất (order_tick, id bàn), tiêu nguyên liệu giữ, chốt giá."""
        orders = [c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"]
        if not orders:
            return []
        c = min(orders, key=lambda o: (o["order_tick"], id_key(o["table_id"])))
        dish = self.menu[c["dish_id"]]

        if self.is_item_inventory:
            used_ids = set(c["reserved"] if isinstance(c["reserved"], list) else [])
            used_items = [it for it in self.items if it["id"] in used_ids]
            if used_items:
                avg_fresh = sum(it["fresh"] for it in used_items) / len(used_items)
            else:
                avg_fresh = Fraction(100)
            base_price = math.floor(int(dish["price"]) * avg_fresh / 100)
            self.items = [it for it in self.items if it["id"] not in used_ids]
            c["reserved"] = []
            c["order_status"] = "assigned"
            c["base_price"] = base_price
            stove["state"] = "cooking"
            stove["dish"] = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": c["base_price"]}
            stove["cook_ticks_left"] = int(round(dish["cook_s"] * self.tick_hz))
            stove["ready_ticks"] = 0
            items = [{"id": it["id"], "kind": it["kind"], "fresh": _format_fresh(it["fresh"])}
                     for it in sorted(used_items, key=lambda x: (x["kind"], id_key(x["id"])))]
            return [("cook_started", dict(self._stove_data(stove), items=items, base_price=c["base_price"]))]

        used = dict(c["reserved"] or dish["recipe"])
        for k, n in used.items():
            self.stock[k] = self.stock.get(k, 0) - n
        c["reserved"] = {}
        c["order_status"] = "assigned"
        c["base_price"] = dish["price"]
        stove["state"] = "cooking"
        stove["dish"] = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": c["base_price"]}
        stove["cook_ticks_left"] = int(round(dish["cook_s"] * self.tick_hz))
        stove["ready_ticks"] = 0
        items = sorted(k for k, n in used.items() for _ in range(n))
        return [("cook_started", dict(self._stove_data(stove), items=items, base_price=c["base_price"]))]

    def _pick_dish(self, stove) -> list:
        """Bếp ready giao món cho tay trống (carry_limit 1) rồi về idle; tay đầy thì bỏ lượt."""
        if self.hand is not None or self.t.get("carry_limit", 1) < 1:
            return []
        data = self._stove_data(stove)
        self.hand = dict(stove["dish"])
        stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        return [("dish_picked", data)]

    def _serve(self, table) -> list:
        """Bàn nhận đúng order_id trên tay: khách ăn với timer đầy, chốt boa theo kiên nhẫn sau bước 1."""
        c = next((x for x in self.customers if x["table_id"] == table["id"]), None)
        if c is None or self.hand is None or c["state"] != "waiting" or self.hand["order_id"] != c["id"]:
            return []
        price = self.hand.get("base_price")
        if price is None:
            price = c["base_price"] if c["base_price"] is not None else self.menu[c["dish_id"]]["price"]
        patience_max = int(round(self.t["patience_s"] * self.tick_hz))
        ratio = Fraction(c["patience_ticks_left"], patience_max)
        tip = 0
        if ratio >= Fraction(str(self.t.get("tip_min_patience_ratio", 0.5))):
            tip = math.floor(price * Fraction(str(self.t.get("tip_rate", 0.2))))
        self.hand = None
        c.update(state="eating", order_status="served", base_price=price, tip=tip,
                 eat_ticks_left=int(round(self.t.get("eat_s", 10.0) * self.tick_hz)))
        return [("served", {"order_id": c["id"], "table_id": c["table_id"],
                            "dish_id": c["dish_id"], "patience_ticks_left": c["patience_ticks_left"],
                            "base_price": price, "tip": tip})]

    def _settle_customers(self, closing) -> list:
        """Theo id bàn: ăn xong -> paid; còn giờ mà hết kiên nhẫn -> rời patience;
        hết ca: đang ăn -> paid closing, đang chờ -> rời closing (không trừ uy tín)."""
        events = []
        for c in sorted(self.customers, key=lambda x: id_key(x["table_id"])):
            if c["state"] == "eating":
                if c["eat_ticks_left"] <= 0:
                    events.extend(self._pay(c, "finished_eating"))
                elif closing:
                    events.extend(self._pay(c, "closing"))
            elif closing:
                events.extend(self._expire_customer(c, reason="closing"))
            elif c["patience_ticks_left"] <= 0:
                events.extend(self._expire_customer(c, reason="patience"))
        return events

    def _pay(self, c, reason) -> list:
        tip = c["tip"] or 0
        if c["base_price"] is None:
            c["base_price"] = self.menu[c["dish_id"]]["price"]
        amount = c["base_price"] + tip
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        self.tips += tip
        self.stats_served += 1
        self.dish_served_counts[c["dish_id"]] = self.dish_served_counts.get(c["dish_id"], 0) + 1
        if tip > 0:
            self._add_reputation(self.t.get("tip_reputation", 0.2))
        self._remove_customer(c)
        return [("paid", {"order_id": c["id"], "table_id": c["table_id"],
                          "base_price": c["base_price"], "tip": tip, "amount": amount, "reason": reason})]

    def _add_reputation(self, delta):
        rmin, rmax = self.t.get("reputation_min", 0), self.t.get("reputation_max", 5)
        self.reputation = max(rmin, min(rmax, round(self.reputation + delta, 6)))

    def _remove_customer(self, c):
        """Khách rời bàn: nhả giữ thô, bỏ món của đơn đang nấu/ready/trên tay (nguyên liệu đã dùng không hoàn)."""
        self._release_reserved(c)
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == c["id"]:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand is not None and self.hand["order_id"] == c["id"]:
            self.hand = None
        self.customers = [x for x in self.customers if x is not c]

    def _customer(self, cid):
        return next((c for c in self.customers if c["id"] == cid), None)

    @staticmethod
    def _stove_data(stove):
        return {"stove_id": stove["id"], "order_id": stove["dish"]["order_id"], "dish_id": stove["dish"]["dish_id"]}

    def _update_customer_patience(self):
        """Bước 1: khách chờ giảm kiên nhẫn (không âm) từ bước sau khi đến; việc rời quán xét ở bước 4."""
        for c in self.customers:
            if c.get("state") == "waiting" and c.get("order_tick") != self.phase_tick:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)

    def _expire_customer(self, customer, reason="patience") -> list:
        if reason == "patience":
            self.stats_left += 1
            self._add_reputation(self.t.get("left_reputation_delta", -0.5))
        self._remove_customer(customer)
        return [("customer_left", {"order_id": customer["id"], "customer_id": customer["id"],
                                   "table_id": customer["table_id"], "reason": reason,
                                   "reputation": self.reputation})]

    def _release_reserved(self, customer):
        customer["reserved"] = [] if self.is_item_inventory else {}

    def _should_spawn_customer(self) -> bool:
        if not self.random_customers:
            return False
        first_tick = self.t["first_customer_tick"]
        interval_ticks = int(round(self.t["customer_interval_s"] * self.tick_hz))
        if self.phase_tick < first_tick:
            return False
        return (self.phase_tick - first_tick) % interval_ticks == 0

    def _find_available_table(self):
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        free_tables = [tb for tb in self.tables if tb["id"] not in occupied]
        if not free_tables:
            return None
        return sort_by_id(free_tables)[0]

    def _spawn_customer(self, table):
        events = []
        avail = self._available_stock()

        allowed_menu = self.menu_ids
        if allowed_menu is None and "plan_dishes" in self.ctx:
            allowed_menu = self.ctx["plan_dishes"]

        if allowed_menu is not None:
            candidates = [did for did in sorted(self.menu.keys()) if did in allowed_menu]
        else:
            candidates = sorted(self.menu.keys())

        valid_dishes = []
        for did in candidates:
            recipe = self.menu[did]["recipe"]
            if all(avail.get(k, 0) >= req for k, req in recipe.items()):
                valid_dishes.append(did)

        if not valid_dishes:
            events.append(("no_dish", {}))  # PRD-0 mục E: {} khi có bàn mà thiếu món
            return events

        rng = self.rng.get("customers")
        chosen_dish = rng.choice(valid_dishes)
        recipe = dict(self.menu[chosen_dish]["recipe"])

        customer_id = self.ids.new("C")
        pat_ticks = int(round(self.t["patience_s"] * self.tick_hz))

        if self.is_item_inventory:
            reserved_ids = {iid for c in self.customers if c.get("order_status") == "reserved"
                            and isinstance(c.get("reserved"), list) for iid in c["reserved"]}
            chosen_items = []
            for k, req in recipe.items():
                cands = [it for it in self.items if it["kind"] == k and it["fresh"] >= Fraction(30) and it["id"] not in reserved_ids]
                cands.sort(key=lambda it: (-it["fresh"], id_key(it["id"])))
                chosen = cands[:req]
                chosen_items.extend(chosen)
                for it in chosen:
                    reserved_ids.add(it["id"])
            chosen_ids = sorted([it["id"] for it in chosen_items], key=id_key)
            reserved_val = chosen_ids
        else:
            reserved_val = recipe

        new_customer = {
            "id": customer_id,
            "table_id": table["id"],
            "dish_id": chosen_dish,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": pat_ticks,
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": reserved_val,
            "base_price": None,
            "tip": 0,
        }
        self.customers.append(new_customer)
        events.append((
            "customer_arrived",
            {  # PRD-0 mục E: order_id, table_id, dish_id; giữ customer_id/reserved cho hợp đồng nhóm
                "order_id": customer_id,
                "customer_id": customer_id,
                "table_id": table["id"],
                "dish_id": chosen_dish,
                "reserved": reserved_val,
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
            res = c.get("reserved")
            if isinstance(res, list):
                res_val = list(res)
            elif isinstance(res, dict):
                res_val = dict(res)
            else:
                res_val = None
            cust = {
                "id": c["id"],
                "table_id": c["table_id"],
                "dish_id": c["dish_id"],
                "order_tick": c.get("order_tick", 0),
                "state": c.get("state", "waiting"),
                "patience_ticks_left": c.get("patience_ticks_left", pat_ticks),
                "eat_ticks_left": c.get("eat_ticks_left", 0),
                "order_status": self._norm_status(c),
                "reserved": res_val,
                "base_price": c.get("base_price", None),
                "tip": c.get("tip", 0),
            }
            self.customers.append(cust)
            self.ids.reserve(cust["id"])
        self._infer_customer_reservations()

    @staticmethod
    def _norm_status(c):
        status = c.get("order_status", "reserved" if c.get("state", "waiting") == "waiting" else "served")
        return "assigned" if status in LEGACY_ASSIGNED else status

    def _fill_payload_prices(self):
        """Payload món thiếu base_price (dạng cũ) lấy giá đã chốt của đơn, không có thì giá menu."""
        for d in [s["dish"] for s in self.stoves] + [self.hand]:
            if d is not None and d.get("base_price") is None:
                c = self._customer(d["order_id"])
                d["base_price"] = (c["base_price"] if c is not None and c["base_price"] is not None
                                   else self.menu[d["dish_id"]]["price"])
            if d is not None and d.get("order_id") is not None:
                c = self._customer(d["order_id"])
                if c is not None and c["base_price"] is None:
                    c["base_price"] = d["base_price"]

    def _available_stock(self) -> dict:
        """Kho khả dụng = stock - tổng nguyên liệu đang được giữ (reserved)."""
        if self.is_item_inventory:
            reserved_ids = {iid for c in self.customers if c.get("order_status") == "reserved"
                            and isinstance(c.get("reserved"), list) for iid in c["reserved"]}
            avail = {}
            for it in self.items:
                if it["fresh"] >= Fraction(30) and it["id"] not in reserved_ids:
                    avail[it["kind"]] = avail.get(it["kind"], 0) + 1
            return avail
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
        unreserved = [c for c in self.customers if c.get("reserved") is None and c.get("order_status") == "reserved"]
        unreserved.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))

        if self.is_item_inventory:
            for c in unreserved:
                recipe = self.menu[c["dish_id"]]["recipe"]
                other_reserved = {iid for oc in self.customers if oc is not c
                                  and oc.get("order_status") == "reserved"
                                  and isinstance(oc.get("reserved"), list)
                                  for iid in oc["reserved"]}
                chosen_items = []
                for k, req in recipe.items():
                    cands = [it for it in self.items if it["kind"] == k and it["fresh"] >= Fraction(30) and it["id"] not in other_reserved]
                    cands.sort(key=lambda it: (-it["fresh"], id_key(it["id"])))
                    if len(cands) < req:
                        from ..errors import BadInput
                        raise BadInput(f"không đủ kho để giữ nguyên liệu cho khách {c['id']} (món {c['dish_id']})")
                    chosen = cands[:req]
                    chosen_items.extend(chosen)
                    for it in chosen:
                        other_reserved.add(it["id"])
                c["reserved"] = sorted([it["id"] for it in chosen_items], key=id_key)

            for c in self.customers:
                if c.get("reserved") is None:
                    c["reserved"] = []
            self._check_total_reservations()
            return

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
        if self.is_item_inventory:
            reserved_ids = []
            for c in self.customers:
                if c.get("order_status") == "reserved" and isinstance(c.get("reserved"), list):
                    reserved_ids.extend(c["reserved"])
            if len(reserved_ids) != len(set(reserved_ids)):
                from ..errors import BadInput
                raise BadInput("trùng lặp nguyên liệu giữ chỗ giữa các khách")
            item_map = {it["id"]: it for it in self.items}
            for iid in reserved_ids:
                if iid not in item_map:
                    from ..errors import BadInput
                    raise BadInput(f"nguyên liệu giữ chỗ {iid} không tồn tại trong kho")
                if item_map[iid]["fresh"] < Fraction(30):
                    from ..errors import BadInput
                    raise BadInput(f"nguyên liệu giữ chỗ {iid} bị ươn (fresh < 30)")
            return

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
