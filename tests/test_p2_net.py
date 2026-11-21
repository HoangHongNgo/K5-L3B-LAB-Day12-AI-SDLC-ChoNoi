"""Mở rộng `net` — Vợt hút cá (TICKET-02 mục 3, 4.1 `shop.upgrades.net[] {level,price,catch_radius,max_schools}`).

Cấp 1: 4.0 m, tối đa 2 đàn/lần; cấp 2: 6.0 m, tối đa 3 đàn/lần. Từ cấp 1 duyệt theo id, đếm số đàn bắt
thành công; đàn thiếu chỗ phát hold_full và giữ lại, xét đàn kế. Có đàn bắt thành công mới đặt hồi.
Cấp 0 dùng luật gần nhất của lõi. Cấp lấy từ active_upgrades (có hiệu lực từ Ngày kế).
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p2_net -v
"""

import copy
import json
import os
import unittest

from fixtures.fresh import fresh_items
from helpers import ROOT
from test_p2_fish import CATCH, school, tuning
from test_p2_shop import inp

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from chonoi.sim.shop import ShopSim
from test_p2_shop import T as SHOP_T

with open(os.path.join(ROOT, "tests", "fixtures", "p2_net_upgrades.json"), encoding="utf-8") as f:
    NET = json.load(f)
T = tuning()
T["shop"] = copy.deepcopy(SHOP_T["shop"])
T["shop"]["upgrades"]["net"] = NET
G = T["gather"]
CD = int(round(G["catch_cooldown_s"] * T["tick_hz"]))
P = [50, 10]


def sim(fish, level, hold=()):
    s = {"player": {"pos": list(P)}, "fish": fish, "hold": fresh_items(hold)}
    return GatherSim(T, s, Streams(1), IdAllocator(), active_upgrades={"net": level} if level else {})


def loc(fid, dx, kind="ca_loc"):
    return school(fid, kind, (P[0] + dx, P[1]))


class Net(unittest.TestCase):
    def test_level1_by_id_up_to_two(self):
        s = sim([loc("F3", 0.5), loc("F1", 3.9), loc("F2", -2)], 1)
        ev = s.step(CATCH)
        self.assertEqual([(n, d["fish_id"]) for n, d in ev], [("fish_caught", "F1"), ("fish_caught", "F2")])
        snap = s.snapshot()
        self.assertEqual([f["id"] for f in snap["fish"]], ["F3"])
        self.assertEqual(snap["player"]["catch_cd_ticks"], CD)

    def test_radius_edge_inclusive(self):
        r = NET[0]["catch_radius"]
        s = sim([loc("F1", r), loc("F2", r + 0.01)], 1)
        self.assertEqual([d["fish_id"] for _, d in s.step(CATCH)], ["F1"])

    def test_hold_full_skips_to_next(self):
        hold = ["bong_sung"] * (G["hold_capacity"] - 2)
        s = sim([school("F1", "ca_linh", (P[0] + 1, P[1])), loc("F2", 1.5), loc("F3", 2)], 1, hold)
        ev = s.step(CATCH)
        self.assertEqual([(n, d.get("fish_id")) for n, d in ev],
                         [("hold_full", "F1"), ("fish_caught", "F2"), ("fish_caught", "F3")])
        self.assertEqual(ev[0][1], {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
        self.assertEqual(s.snapshot()["player"]["catch_cd_ticks"], CD)

    def test_no_success_no_cooldown(self):
        hold = ["bong_sung"] * G["hold_capacity"]
        s = sim([loc("F1", 1), loc("F2", 2)], 1, hold)
        ev = s.step(CATCH)
        self.assertEqual([n for n, _ in ev], ["hold_full", "hold_full"])
        self.assertEqual(s.snapshot()["player"]["catch_cd_ticks"], 0)
        self.assertEqual(len(s.snapshot()["fish"]), 2)

    def test_level2_radius_6_up_to_three(self):
        s = sim([loc(f"F{i}", d) for i, d in enumerate((5.9, -5, 1, 2), start=1)], 2)
        self.assertEqual([d["fish_id"] for _, d in s.step(CATCH)], ["F1", "F2", "F3"])

    def test_level0_core_nearest_rule(self):
        s = sim([loc("F1", 1.9), loc("F2", 0.5), loc("F3", 3)], 0)
        self.assertEqual([d["fish_id"] for _, d in s.step(CATCH)], ["F2"])

    def test_surface_and_cooldown_still_apply(self):
        s = GatherSim(T, {"player": {"pos": [50, 0]}, "fish": [school("F1", "ca_linh", (50, 3))]},
                      Streams(1), IdAllocator(), active_upgrades={"net": 1})
        self.assertEqual(s.step(CATCH), [])
        s = sim([loc("F1", 1), loc("F2", 2), loc("F3", 3)], 1)
        s.step(CATCH)
        from chonoi.inputs import InputState
        self.assertEqual(s.step(InputState((0.0, 0.0), {"catch": True}, {"catch"})), [])  # đang hồi

    def test_net_without_tuning_is_core_rule(self):
        t = copy.deepcopy(T)
        del t["shop"]["upgrades"]["net"]
        s = GatherSim(t, {"player": {"pos": list(P)}, "fish": [loc("F1", 1.9), loc("F2", 0.5)]},
                      Streams(1), IdAllocator(), active_upgrades={"net": 1})
        self.assertEqual([d["fish_id"] for _, d in s.step(CATCH)], ["F2"])


class ContractEnablesNet(unittest.TestCase):
    """Manifest khai mở rộng net (TICKET-02 mục 3, 4.1): extensions và shop.upgrades.net trong contract."""

    def test_contract_declares_net(self):
        from chonoi.contract import load_contract
        c = load_contract()
        self.assertIn("net", c["extensions"])
        self.assertEqual(c["tuning"]["shop"]["upgrades"]["net"], NET)

    def test_day_shop_sells_net_with_contract_numbers(self):
        from chonoi.contract import load_contract
        t = load_contract()["tuning"]
        s = ShopSim(t, money=250, earned=250, upgrades={}, stock={})
        self.assertEqual(s.step(inp("net")), [("bought", {"upgrade": "net", "level": 1, "price": 250, "money": 0})])


class ShopNet(unittest.TestCase):
    def test_buy_net_levels(self):
        s = ShopSim(T, money=750, earned=750, upgrades={}, stock={})
        self.assertEqual(s.step(inp("net")), [("bought", {"upgrade": "net", "level": 1, "price": 250, "money": 500})])
        self.assertEqual(s.step(inp("net"))[0][1]["level"], 2)
        self.assertEqual(s.step(inp("net")), [("buy_failed", {"action": "net", "reason": "max_level"})])


if __name__ == "__main__":
    unittest.main()
