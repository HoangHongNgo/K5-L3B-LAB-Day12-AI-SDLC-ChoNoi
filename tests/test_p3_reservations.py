"""Mở rộng `reservations` (TICKET-03 mục 2) — lát D: R1/R2, giữ bàn, đến giờ, giá ×1.5, lỡ đơn đúng một lần.

Tuning bật mở rộng bằng số của ticket (contract trên main chưa khai khối `reservations`).
"""

import copy
import math
import unittest
from fractions import Fraction

from test_p2_day import StubShop, StubState, tuning_v11
from test_p3_day import ItemGather, run_day

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.day import DaySim
from chonoi.sim.quan import QuanSim
from chonoi.sim.reservations import generate, validate

IDLE = InputState((0.0, 0.0), {}, set())
PRESS = InputState((0.0, 0.0), {"interact": True}, {"interact"})
RES = {"count": 2, "table_hold_s": 30, "price_multiplier": 1.5, "failed_reputation_delta": -1}


def tuning_res(base=None):
    t = copy.deepcopy(base or load_contract()["tuning"])
    t["extensions"] = sorted(set(t.get("extensions", [])) | {"reservations"})
    t["reservations"] = dict(RES)
    return t


T = tuning_res()
TABLES = {tb["id"]: tb["pos"] for tb in T["quan"]["tables"]}


def stock(*kinds, fresh=100):
    return [{"id": f"I{i}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds, 1)]


def make(reservations=None, items=(), **block):
    sc = dict({"random_customers": False, "stock": list(items)}, **block)
    if reservations is not None:
        sc["reservations"] = reservations
    return QuanSim(T, sc, Streams(1), IdAllocator())


def step_until(sim, tick, inp=IDLE):
    evs = []
    while sim.phase_tick < tick and not sim.done:
        evs += sim.step(inp)
    return evs


def names(evs):
    return [e[0] for e in evs]


R1 = {"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 2000}
R2 = {"id": "R2", "table_id": "T2", "dish_id": "goi_bong_sung", "arrival_tick": 2000}


class TestAnnounceAndGenerate(unittest.TestCase):
    def test_generate_two_distinct_tables_plan_dishes_tick_range_by_seed(self):
        for seed in range(20):
            rs = generate(T, Streams(seed), ["ca_loc_nuong_trui", "goi_bong_sung"])
            self.assertEqual([r["id"] for r in rs], ["R1", "R2"])
            self.assertNotEqual(rs[0]["table_id"], rs[1]["table_id"])
            for r in rs:
                self.assertIn(r["dish_id"], ("ca_loc_nuong_trui", "goi_bong_sung"))
                self.assertTrue(1800 <= r["arrival_tick"] <= 10799)
        self.assertEqual(generate(T, Streams(5), None), generate(T, Streams(5), None))  # theo seed

    def test_standalone_quan_announces_at_build_with_full_menu(self):
        sim = QuanSim(T, {"random_customers": False}, Streams(3), IdAllocator())
        self.assertEqual(names(sim.initial_events), ["reservation_announced"] * 2)
        d = sim.initial_events[0][1]
        self.assertEqual(set(d), {"reservation_id", "table_id", "dish_id", "arrival_tick"})
        self.assertEqual(sim.snapshot()["reservations"][0]["state"], "scheduled")

    def test_random_reservations_false_and_disabled_extension(self):
        sim = QuanSim(T, {"random_reservations": False}, Streams(1), IdAllocator())
        self.assertEqual((sim.initial_events, sim.snapshot()["reservations"]), ([], []))
        disabled = tuning_res()
        disabled["extensions"].remove("reservations")
        plain = QuanSim(disabled, {}, Streams(1), IdAllocator())
        self.assertNotIn("reservations", plain.snapshot())

    def test_validate_scenario_entries(self):
        validate([R1, R2], T)
        for bad in ([R1, dict(R2, table_id="T1")], [R1, dict(R2, id="R1")], [dict(R1, arrival_tick=0)],
                    [dict(R1, arrival_tick=10800)], [dict(R1, dish_id="pho")], [R1, R2, dict(R2, id="R3")],
                    [dict(R1, extra=1)]):
            with self.assertRaises(BadInput):
                validate(bad, T)


class TestHoldAndArrive(unittest.TestCase):
    def test_hold_starts_at_arrival_minus_hold_and_from_tick_zero(self):
        sim = make([dict(R1, arrival_tick=2000), dict(R2, arrival_tick=1000)], stock("ca_loc", "bong_sung", "bong_sung"))
        snap = sim.snapshot()
        self.assertEqual([r["state"] for r in snap["reservations"]], ["scheduled", "holding"])  # R2 giữ từ tick 0
        self.assertEqual({tb["id"]: tb["reservation_id"] for tb in snap["tables"]}["T2"], "R2")
        step_until(sim, 199)
        self.assertEqual(sim.snapshot()["reservations"][0]["state"], "scheduled")
        step_until(sim, 200)
        self.assertEqual(sim.snapshot()["reservations"][0]["state"], "holding")

    def test_regular_customer_skips_held_table(self):
        sim = QuanSim(T, {"stock": stock("ca_loc", "ca_loc"), "reservations": [dict(R1, arrival_tick=1000)],
                          "random_customers": True}, Streams(1), IdAllocator())
        evs = step_until(sim, T["quan"]["first_customer_tick"])
        arrived = [d for n, d in evs if n == "customer_arrived"]
        self.assertEqual(arrived[0]["table_id"], "T2")  # T1 đang giữ cho R1

    def test_arrive_success_reserves_then_events_in_order(self):
        sim = make([R1], stock("ca_loc"))
        evs = step_until(sim, 2000)
        self.assertEqual(names(evs), ["reservation_arrived", "customer_arrived"])
        self.assertEqual(evs[0][1]["reservation_id"], "R1")
        cid = evs[0][1]["order_id"]
        snap = sim.snapshot()
        c = snap["customers"][0]
        self.assertEqual((c["id"], c["reservation_id"], c["reserved"], c["patience_ticks_left"]), (cid, "R1", ["I1"], 3600))
        self.assertEqual(snap["reservations"][0]["state"], "waiting")
        self.assertEqual({tb["id"]: tb["reservation_id"] for tb in snap["tables"]}["T1"], "R1")

    def test_fail_occupied(self):
        sim = QuanSim(T, {"stock": stock("ca_loc", "ca_loc"), "reservations": [dict(R1, arrival_tick=2000)],
                          "random_customers": True}, Streams(1), IdAllocator())
        evs = step_until(sim, 2000)  # khách thường đến tick 120 ngồi T1 (chưa giữ), còn ngồi tới 2000
        failed = [d for n, d in evs if n == "reservation_failed"]
        self.assertEqual(failed, [{"reservation_id": "R1", "reason": "occupied", "reputation": 2.0}])

    def test_fail_stock_once(self):
        sim = make([R1, R2], stock("ca_loc"))
        evs = step_until(sim, 2000)
        self.assertEqual(names(evs), ["reservation_arrived", "customer_arrived", "reservation_failed"])
        self.assertEqual(evs[2][1], {"reservation_id": "R2", "reason": "stock", "reputation": 2.0})
        self.assertEqual(names(step_until(sim, 2100)), [])  # trạng thái cuối, không phạt thêm
        self.assertEqual(sim.book.fail(sim, sim.book.by_id("R2"), "closing"), [])  # gọi lại cũng không phạt
        self.assertEqual(sim.reputation, 2.0)


class TestServeAndFail(unittest.TestCase):
    def arrived(self):
        sim = make([R1], stock("ca_loc", fresh=80))
        evs = step_until(sim, 2000)
        return sim, evs[0][1]["order_id"]

    def test_price_times_multiplier_then_tip_then_reservation_served(self):
        sim, cid = self.arrived()
        c = sim._customer(cid)
        evs = sim._start_cooking(sim.stoves[0])  # tiêu id đang giữ, chốt giá theo fresh
        chot = evs[0][1]["base_price"]
        fresh = Fraction(80) - Fraction(2000, 240)  # kho quán hao 1/240 mỗi tick suốt 2000 tick chờ
        self.assertEqual(chot, math.floor(60 * fresh / 100))  # ca_loc giá 60
        sim.stoves[0].update(state="ready")
        sim.pos = list(sim.stoves[0]["pos"])
        sim.step(PRESS)  # bưng
        sim.pos = list(TABLES["T1"])
        evs = sim.step(PRESS)
        self.assertEqual(names(evs)[:2], ["served", "reservation_served"])
        final = math.floor(chot * 1.5)
        self.assertEqual(evs[0][1]["base_price"], final)
        self.assertEqual(evs[0][1]["tip"], math.floor(final * 0.2))
        self.assertEqual(evs[1][1], {"reservation_id": "R1", "order_id": cid, "base_price": final})
        self.assertEqual(sim.snapshot()["reservations"][0]["state"], "served")
        self.assertEqual(c["base_price"], final)

    def test_fail_patience_releases_items_no_customer_left(self):
        sim, cid = self.arrived()
        sim._customer(cid)["patience_ticks_left"] = 1
        evs = sim.step(IDLE)
        self.assertEqual(names(evs), ["reservation_failed"])
        self.assertEqual(evs[0][1]["reason"], "patience")
        self.assertEqual(sim.reputation, 2.0)
        self.assertEqual(sim.customers, [])
        self.assertEqual(sim._reserve_recipe({"ca_loc": 1}), ["I1"])  # hàng đã nhả

    def test_closing_fails_unfinished_by_id_before_quan_end(self):
        sim = make([dict(R2, arrival_tick=50), dict(R1, arrival_tick=60)], stock("ca_loc", "bong_sung", "bong_sung"),
                   time_left_ticks=55)
        evs = step_until(sim, 55)
        tail = [(n, d.get("reservation_id"), d.get("reason")) for n, d in evs if n != "customer_arrived"]
        self.assertEqual(tail, [("reservation_arrived", "R2", None), ("reservation_failed", "R1", "closing"),
                                ("reservation_failed", "R2", "closing"), ("quan_end", None, "time")])
        self.assertEqual(sim.reputation, 1.0)  # −1 cho mỗi đơn, đúng một lần

    def test_spoiled_hold_and_no_replacement_fails_stock(self):
        sim = make([R1], [{"id": "I1", "kind": "ca_loc", "fresh": 30}])
        # I1 ở đúng 30: ươn ở bước đầu -> lúc R1 đến không còn hàng dùng được -> fail stock
        evs = step_until(sim, 2000)
        self.assertIn(("reservation_failed", {"reservation_id": "R1", "reason": "stock", "reputation": 2.0}), evs)


class TestDayReservations(unittest.TestCase):
    def test_day_announces_after_phase_start_gather_and_hands_to_quan(self):
        made = {}

        def gather(tuning, sc, streams, ids, **kw):
            return ItemGather(3, stock("ca_loc", "bong_sung", "bong_sung"))

        def quan(tuning, sc, streams, ids, **kw):
            made["quan"] = QuanSim(tuning, sc, streams, ids, **kw)
            return made["quan"]

        sim = DaySim(tuning_res(tuning_v11()), {"quan": {"random_customers": False}}, Streams(4), IdAllocator(),
                     factories={"gather": gather, "quan": quan, "shop": lambda t, **kw: StubShop(1, **kw),
                                "state": StubState})
        rows = run_day(sim, ticks=5)
        ev0 = [(r["name"], r["phase"]) for r in rows if r["type"] == "event" and r["tick"] == 0]
        self.assertEqual(ev0, [("day_start", "gather"), ("day_plan", "gather"), ("phase_start", "gather"),
                               ("reservation_announced", "gather"), ("reservation_announced", "gather")])
        plan = set(tuning_v11()["day_plan"][0]["dishes"])
        snap0 = next(r for r in rows if r["type"] == "snapshot")
        self.assertEqual([r["state"] for r in snap0["reservations"]], ["scheduled", "scheduled"])
        self.assertTrue(all(r["dish_id"] in plan for r in snap0["reservations"]))
        q = made["quan"]
        self.assertEqual(q.initial_events, [])  # quán trong day không công bố lại
        self.assertEqual([r["id"] for r in q.snapshot()["reservations"]], ["R1", "R2"])


if __name__ == "__main__":
    unittest.main()
