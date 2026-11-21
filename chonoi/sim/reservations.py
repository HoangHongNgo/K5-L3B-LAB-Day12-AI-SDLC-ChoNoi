"""Khách đặt trước (`reservations`, mở rộng TICKET-03 mục 2) — lát D.

Bật khi manifest khai `"reservations"` trong `extensions` và có khối `reservations
{count, table_hold_s, price_multiplier, failed_reputation_delta}`. Mọi số đọc từ khối đó.

- Mỗi Ngày công bố `count` đơn R1, R2… (`reservation_announced`): bàn khác nhau, món trong kế hoạch
  (quán độc lập: cả menu), tick đến theo seed trong [table_hold, thời lượng ca − 1], có thể trùng tick.
  `day` công bố sau `phase_start(gather)`; quán độc lập công bố lúc dựng pha.
- Trạng thái `scheduled → holding → waiting → served | failed` (`served`, `failed` là trạng thái cuối).
  Giữ bàn từ `max(0, arrival_tick − table_hold)`; khách mới không ngồi bàn đang giữ.
- Đến giờ: bàn còn khách → fail `occupied`; thiếu kho → fail `stock`; thành công → giữ nguyên liệu,
  `reservation_arrived` rồi `customer_arrived`, kiên nhẫn đầy.
- Giá cuối `floor(giá đã chốt theo fresh × price_multiplier)` rồi mới boa; `served` rồi `reservation_served`.
- Lỡ đơn (`stock`/`occupied`/`burnt`/`patience`/`closing`): nhả hàng/bàn, hủy món, uy tín
  `failed_reputation_delta` đúng một lần, `reservation_failed` thay nhánh rời của khách thường.
  Đóng ca fail các đơn chưa xong theo id.
"""

import math
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id

EXT = "reservations"
FINAL = ("served", "failed")


def enabled(tuning) -> bool:
    return EXT in tuning.get("extensions", []) and EXT in tuning


def _hz(tuning):
    return tuning.get("tick_hz", 60)


def hold_ticks(tuning) -> int:
    return int(round(tuning[EXT]["table_hold_s"] * _hz(tuning)))


def shift_ticks(tuning) -> int:
    return int(round(tuning["quan"]["duration_s"] * _hz(tuning)))


def generate(tuning, streams, menu_ids=None) -> list:
    """Sinh đơn theo seed (stream riêng `reservations`): bàn, món, tick đến lần lượt cho R1, R2…"""
    rng = streams.get("reservations")
    tables = [t["id"] for t in sort_by_id(tuning["quan"]["tables"])]
    dishes = sorted(menu_ids if menu_ids is not None else tuning["menu"])
    lo, hi = hold_ticks(tuning), shift_ticks(tuning) - 1
    out = []
    for i in range(1, tuning[EXT]["count"] + 1):
        if not tables or not dishes:
            break
        tid = rng.choice(tables)
        tables.remove(tid)
        out.append({"id": f"R{i}", "table_id": tid, "dish_id": rng.choice(dishes), "arrival_tick": rng.randint(lo, hi)})
    return out


def validate(entries, tuning):
    """`quan.reservations[] {id,table_id,dish_id,arrival_tick}`: tối đa `count` đơn, bàn khác nhau,
    tick đến nguyên dương nhỏ hơn thời lượng ca chuẩn. Sai -> BadInput (mã 2)."""
    if not isinstance(entries, list):
        raise BadInput("quan.reservations phải là mảng")
    limit = tuning[EXT]["count"] if EXT in tuning else 2
    if len(entries) > limit:
        raise BadInput(f"quan.reservations tối đa {limit} đơn")
    tables = {t["id"] for t in tuning["quan"]["tables"]}
    seen_ids, seen_tables = set(), set()
    for r in entries:
        if not isinstance(r, dict) or set(r) != {"id", "table_id", "dish_id", "arrival_tick"}:
            raise BadInput("mỗi đơn đặt trước cần đúng {id, table_id, dish_id, arrival_tick}")
        if not isinstance(r["id"], str) or not r["id"] or r["id"] in seen_ids:
            raise BadInput(f"đơn đặt trước: id rỗng hoặc trùng: {r['id']!r}")
        if not isinstance(r["table_id"], str) or r["table_id"] not in tables or r["table_id"] in seen_tables:
            raise BadInput(f"đơn {r['id']}: bàn không tồn tại hoặc trùng bàn: {r['table_id']!r}")
        if not isinstance(r["dish_id"], str) or r["dish_id"] not in tuning["menu"]:
            raise BadInput(f"đơn {r['id']}: món không có trong menu: {r['dish_id']!r}")
        t = r["arrival_tick"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t < shift_ticks(tuning)):
            raise BadInput(f"đơn {r['id']}: arrival_tick phải nguyên dương < {shift_ticks(tuning)}")
        seen_ids.add(r["id"])
        seen_tables.add(r["table_id"])


def announced(entries) -> list:
    return [("reservation_announced", {"reservation_id": r["id"], "table_id": r["table_id"],
                                       "dish_id": r["dish_id"], "arrival_tick": r["arrival_tick"]})
            for r in sort_by_id(entries)]


def snapshot_entries(entries, state="scheduled") -> list:
    return [{"id": r["id"], "table_id": r["table_id"], "dish_id": r["dish_id"], "arrival_tick": r["arrival_tick"],
             "state": r.get("state", state), "order_id": r.get("order_id")} for r in sort_by_id(entries)]


class ReservationBook:
    """Sổ đặt trước của một ca quán. Gọi từ QuanSim qua các móc nhỏ; mọi luật đặt trước nằm ở đây."""

    def __init__(self, tuning, entries, phase_tick=0):
        c = tuning[EXT]
        self.hold = hold_ticks(tuning)
        self.mult = Fraction(str(c["price_multiplier"]))
        self.delta = c["failed_reputation_delta"]
        self.items = [dict(id=r["id"], table_id=r["table_id"], dish_id=r["dish_id"], arrival_tick=r["arrival_tick"],
                           state="scheduled", order_id=None) for r in sort_by_id(entries)]
        self.update_holds(phase_tick)  # giữ từ tick 0 thì hiện ngay trong snapshot dựng quán

    # --- đọc ---
    def snapshot(self):
        return snapshot_entries(self.items)

    def held_tables(self):
        return {r["table_id"] for r in self.items if r["state"] == "holding"}

    def table_reservation(self, table_id):
        r = next((r for r in self.items if r["table_id"] == table_id and r["state"] in ("holding", "waiting")), None)
        return r["id"] if r else None

    def by_id(self, rid):
        return next((r for r in self.items if r["id"] == rid), None)

    # --- luật ---
    def update_holds(self, phase_tick):
        for r in self.items:
            if r["state"] == "scheduled" and phase_tick >= max(0, r["arrival_tick"] - self.hold):
                r["state"] = "holding"

    def fail(self, quan, r, reason) -> list:
        """Lỡ đơn: nhả hàng/bàn, hủy món, uy tín đổi đúng một lần (đơn đã ở trạng thái cuối thì bỏ qua)."""
        if r["state"] in FINAL:
            return []
        c = quan._customer(r["order_id"]) if r["order_id"] else None
        if c is not None:
            quan._remove_customer(c)
        r["state"] = "failed"
        quan._add_reputation(self.delta)
        return [("reservation_failed", {"reservation_id": r["id"], "reason": reason, "reputation": quan.reputation})]

    def process(self, quan) -> list:
        """Khi ca còn giờ, trước lượt khách thường: cập nhật giữ bàn rồi xử lý khách đặt theo id."""
        self.update_holds(quan.phase_tick)
        events = []
        for r in self.items:
            if r["state"] in ("scheduled", "holding") and quan.phase_tick >= r["arrival_tick"]:
                events.extend(self._arrive(quan, r))
        return events

    def _arrive(self, quan, r) -> list:
        if any(c["table_id"] == r["table_id"] for c in quan.customers):
            return self.fail(quan, r, "occupied")
        reserved = quan._reserve_recipe(self_recipe(quan, r["dish_id"]))
        if reserved is None:
            return self.fail(quan, r, "stock")
        cid = quan.ids.new("C")
        quan.customers.append({
            "id": cid, "table_id": r["table_id"], "dish_id": r["dish_id"], "order_tick": quan.phase_tick,
            "state": "waiting", "patience_ticks_left": int(round(quan.t["patience_s"] * quan.tick_hz)),
            "eat_ticks_left": 0, "order_status": "reserved", "reserved": reserved, "base_price": None, "tip": 0,
            "reservation_id": r["id"],
        })
        r["state"], r["order_id"] = "waiting", cid
        return [("reservation_arrived", {"reservation_id": r["id"], "order_id": cid}),
                ("customer_arrived", {"order_id": cid, "customer_id": cid, "table_id": r["table_id"],
                                      "dish_id": r["dish_id"], "reserved": reserved})]

    def final_price(self, price) -> int:
        return math.floor(price * self.mult)

    def served(self, c, price) -> list:
        r = self.by_id(c["reservation_id"])
        r["state"] = "served"
        return [("reservation_served", {"reservation_id": r["id"], "order_id": c["id"], "base_price": price})]

    def after_spoil(self, quan) -> list:
        """Phần giữ vừa ươn và giữ lại không đủ -> fail `stock` (theo id đặt)."""
        events = []
        for r in self.items:
            c = quan._customer(r["order_id"]) if r["state"] == "waiting" else None
            if c is not None and c.get("order_status") == "unfulfillable":
                events.extend(self.fail(quan, r, "stock"))
        return events

    def close(self, quan) -> list:
        """Đóng ca: fail các đơn chưa phục vụ / chưa fail theo id đặt."""
        events = []
        for r in self.items:
            if r["state"] not in FINAL:
                events.extend(self.fail(quan, r, "closing"))
        return events


def self_recipe(quan, dish_id):
    return dict(quan.menu[dish_id]["recipe"])
