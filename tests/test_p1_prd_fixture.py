"""Fixture quán đúng PRD-0 mục D (hộp đen qua headless).

- Payload món (bếp, tay) là {order_id, dish_id, base_price}, order_id = id khách.
- Trạng thái đơn: reserved / assigned / unfulfillable / served.
- Mã 2 cho fixture mâu thuẫn theo mục D.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p1_prd_fixture -v
"""

import json
import math
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

with open("game.contract.json", encoding="utf-8") as _f:
    TUNING = json.load(_f)["tuning"]
Q = TUNING["quan"]
MENU = TUNING["menu"]
HZ = TUNING["tick_hz"]
PATIENCE = int(round(Q["patience_s"] * HZ))
EAT = int(round(Q["eat_s"] * HZ))
STOVE = Q["stoves"][0]
TABLE = Q["tables"][0]
DISH = "goi_bong_sung"
PRICE = MENU[DISH]["price"]


def payload(cid="C1", dish=DISH):
    return {"order_id": cid, "dish_id": dish, "base_price": MENU[dish]["price"]}


def customer(**kw):
    c = {"id": "C1", "table_id": TABLE["id"], "dish_id": DISH, "order_tick": 0, "state": "waiting"}
    c.update(kw)
    return c


def near(pos):
    return [pos[0], pos[1] - 1 if pos[1] - 1 >= Q["bounds"]["z"][0] else pos[1] + 1]


def run(block, frame_list=(), ticks=3):
    """Trả (mã thoát, stderr, rows hoặc None)."""
    with Workdir() as w:
        sc = write_json(w.path("sc.json"), {"quan": dict({"random_customers": False}, **block)})
        inp = write_json(w.path("in.json"), frames(*frame_list))
        out = w.path("o.jsonl")
        code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--snapshot-every", "1",
                                 "--scenario", sc, "--inputs", inp, "--out", out)
        return code, err, (read_jsonl(out) if code == 0 else None)


def snap(rows, tick):
    return [s for s in snapshots(rows) if s["tick"] == tick][0]


PRESS = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}]


class AcceptPrdFixtures(unittest.TestCase):
    def test_hand_payload_serve_with_tip_at_threshold(self):
        """Tay cầm payload có base_price, đơn assigned; phục vụ ở đúng ngưỡng 50% kiên nhẫn thì có boa."""
        threshold = int(math.ceil(PATIENCE * Q["tip_min_patience_ratio"]))
        code, err, rows = run({"player": {"pos": near(TABLE["pos"])}, "stock": {}, "hand": payload(),
                               "customers": [customer(order_status="assigned", reserved={},
                                                      patience_ticks_left=threshold + 1)]},
                              PRESS, ticks=2)
        self.assertEqual(code, 0, err)
        served = events(rows, "served")
        self.assertEqual(len(served), 1)
        self.assertEqual(served[0]["data"], {"order_id": "C1", "table_id": TABLE["id"], "dish_id": DISH,
                                             "patience_ticks_left": threshold, "base_price": PRICE,
                                             "tip": math.floor(PRICE * Q["tip_rate"])})
        s = snap(rows, 1)
        self.assertIsNone(s["hand"])
        self.assertEqual((s["customers"][0]["state"], s["customers"][0]["order_status"]), ("eating", "served"))

    def test_hand_base_price_is_the_settled_price(self):
        """Giá đã chốt nằm trong payload món; served dùng base_price của payload."""
        p = dict(payload(), base_price=PRICE + 5)
        code, err, rows = run({"player": {"pos": near(TABLE["pos"])}, "stock": {}, "hand": p,
                               "customers": [customer(order_status="assigned", reserved={})]}, PRESS, ticks=2)
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "served")[0]["data"]["base_price"], PRICE + 5)

    def test_cooking_stove_payload_becomes_ready(self):
        code, err, rows = run({"stock": {},
                               "stoves": [{"id": STOVE["id"], "state": "cooking", "dish": payload(),
                                           "cook_ticks_left": 3}],
                               "customers": [customer(order_status="assigned")]}, ticks=4)
        self.assertEqual(code, 0, err)
        ready = events(rows, "dish_ready")
        self.assertEqual([(e["tick"], e["data"]) for e in ready],
                         [(3, {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": DISH})])
        s = snap(rows, 3)
        self.assertEqual(s["stoves"][0]["dish"], payload())
        self.assertEqual(s["customers"][0]["order_status"], "assigned")

    def test_ready_stove_payload_pick_to_hand(self):
        code, err, rows = run({"player": {"pos": near(STOVE["pos"])}, "stock": {},
                               "stoves": [{"id": STOVE["id"], "state": "ready", "dish": payload(),
                                           "ready_ticks": 4}],
                               "customers": [customer(order_status="assigned")]}, PRESS, ticks=2)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(events(rows, "dish_picked")), 1)
        s = snap(rows, 1)
        self.assertEqual(s["hand"], payload())
        self.assertEqual(s["stoves"][0]["dish"], None)
        self.assertEqual(s["customers"][0]["order_status"], "assigned")

    def test_unfulfillable_waits_and_is_not_cooked(self):
        code, err, rows = run({"player": {"pos": near(STOVE["pos"])}, "stock": {"bong_sung": 2},
                               "customers": [customer(order_status="unfulfillable", reserved={})]}, PRESS, ticks=2)
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "cook_started"), [])
        self.assertEqual(snap(rows, 1)["customers"][0]["order_status"], "unfulfillable")

    def test_eating_customer_from_prd_fixture(self):
        code, err, rows = run({"stock": {}, "customers": [customer(state="eating", order_status="served",
                                                                   eat_ticks_left=1, base_price=PRICE, tip=0)]},
                              ticks=2)
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "finished_eating")


class SnapshotUsesPrdStatuses(unittest.TestCase):
    def test_cook_pick_serve_statuses_and_payloads(self):
        cook = int(round(MENU[DISH]["cook_s"] * HZ))
        fr = PRESS + [{"tick": cook + 1, "interact": True}, {"tick": cook + 2, "interact": False}]
        code, err, rows = run({"player": {"pos": near(STOVE["pos"])}, "stock": {"bong_sung": 2},
                               "customers": [customer()]}, fr, ticks=cook + 3)
        self.assertEqual(code, 0, err)
        s1 = snap(rows, 1)
        self.assertEqual(s1["customers"][0]["order_status"], "assigned")
        self.assertEqual(s1["customers"][0]["reserved"], {})
        self.assertEqual(s1["stoves"][0]["dish"], payload())
        sp = snap(rows, cook + 2)
        self.assertEqual(sp["hand"], payload())
        self.assertEqual(sp["customers"][0]["order_status"], "assigned")


class RejectContradictions(unittest.TestCase):
    def assertExit2(self, block):
        code, err, _ = run(block, ticks=0)
        self.assertEqual(code, 2, (block, err))

    def test_assigned_without_dish(self):
        self.assertExit2({"stock": {}, "customers": [customer(order_status="assigned", reserved={})]})

    def test_assigned_with_reserved(self):
        self.assertExit2({"stock": {"bong_sung": 2}, "hand": payload(),
                          "customers": [customer(order_status="assigned", reserved={"bong_sung": 2})]})

    def test_cooking_stove_needs_positive_timer(self):
        self.assertExit2({"stock": {}, "stoves": [{"id": STOVE["id"], "state": "cooking", "dish": payload(),
                                                    "cook_ticks_left": 0}],
                          "customers": [customer(order_status="assigned")]})

    def test_stove_dish_not_matching_order(self):
        self.assertExit2({"stock": {}, "stoves": [{"id": STOVE["id"], "state": "cooking",
                                                    "dish": payload(dish="ca_loc_nuong_trui"),
                                                    "cook_ticks_left": 5}],
                          "customers": [customer(order_status="assigned")]})

    def test_hand_dish_not_matching_order(self):
        self.assertExit2({"stock": {}, "hand": payload(dish="ca_loc_nuong_trui"),
                          "customers": [customer(order_status="assigned")]})

    def test_payload_unknown_field(self):
        self.assertExit2({"stock": {}, "hand": dict(payload(), x=1),
                          "customers": [customer(order_status="assigned")]})

    def test_unfulfillable_with_dish(self):
        self.assertExit2({"stock": {}, "hand": payload(),
                          "customers": [customer(order_status="unfulfillable", reserved={})]})

    def test_eating_without_timer_or_price(self):
        self.assertExit2({"stock": {}, "customers": [customer(state="eating", order_status="served",
                                                              eat_ticks_left=0, base_price=PRICE, tip=0)]})
        self.assertExit2({"stock": {}, "customers": [customer(state="eating", order_status="served",
                                                              eat_ticks_left=5, tip=0)]})


if __name__ == "__main__":
    unittest.main()
