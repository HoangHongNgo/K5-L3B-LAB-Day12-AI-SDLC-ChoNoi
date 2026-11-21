"""Lát S — Shop (TICKET-02 mục 2 "Shop và nâng cấp", 4.2, 4.4, 4.5).

Shop chưa có mode headless riêng (chạy trong `day`), nên test gọi thẳng ShopSim.
Số liệu lấy từ contract; khối `shop` dùng fixture theo ticket cho tới khi contract v1.1 có khóa này.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p2_shop -v
"""

import copy
import json
import os
import unittest

from helpers import ROOT

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.sim.shop import ShopSim


def tuning():
    t = copy.deepcopy(load_contract()["tuning"])
    if "shop" not in t:
        with open(os.path.join(ROOT, "tests", "fixtures", "p2_shop_tuning.json"), encoding="utf-8") as f:
            t["shop"] = json.load(f)
    return t


T = tuning()
UP = T["shop"]["upgrades"]
MAX = T["shop"]["max_ticks"]


def inp(buy=None, done=False):
    s = InputState((0.0, 0.0), {"shop_done": done}, {"shop_done"} if done else set())
    s.buy = buy
    return s


IDLE = inp()


def shop(money=0, earned=None, upgrades=None, stock=None):
    return ShopSim(T, money=money, earned=money if earned is None else earned,
                   upgrades=upgrades or {}, stock=stock or {})


class Buy(unittest.TestCase):
    def test_exact_price_buys_and_keeps_earned(self):
        price = UP["oxygen"][0]["price"]
        s = shop(money=price, earned=price + 50)
        ev = s.step(inp("oxygen"))
        self.assertEqual(ev, [("bought", {"upgrade": "oxygen", "level": 1, "price": price, "money": 0})])
        self.assertEqual((s.money, s.earned, s.upgrades), (0, price + 50, {"oxygen": 1}))

    def test_two_levels_in_a_row(self):
        p1, p2 = UP["hp"][0]["price"], UP["hp"][1]["price"]
        s = shop(money=p1 + p2)
        self.assertEqual(s.step(inp("hp"))[0][1]["level"], 1)
        self.assertEqual(s.step(inp("hp")), [("bought", {"upgrade": "hp", "level": 2, "price": p2, "money": 0})])
        self.assertEqual(s.upgrades, {"hp": 2})

    def test_max_level(self):
        s = shop(money=10_000, upgrades={"oxygen": len(UP["oxygen"])})
        self.assertEqual(s.step(inp("oxygen")), [("buy_failed", {"action": "oxygen", "reason": "max_level"})])
        self.assertEqual((s.money, s.upgrades), (10_000, {"oxygen": len(UP["oxygen"])}))

    def test_funds(self):
        price = UP["hp"][0]["price"]
        s = shop(money=price - 1)
        self.assertEqual(s.step(inp("hp")), [("buy_failed", {"action": "hp", "reason": "funds"})])
        self.assertEqual((s.money, s.upgrades), (price - 1, {}))

    def test_unknown_command(self):
        s = shop(money=10_000)
        self.assertEqual(s.step(inp("thuyen_may")), [("buy_failed", {"action": "thuyen_may", "reason": "unknown"})])
        self.assertEqual(s.money, 10_000)

    def test_disabled_extension_is_ignored(self):
        """Mở rộng chưa bật (không có trong shop.upgrades): bỏ qua, không phát event."""
        s = shop(money=10_000)
        for cmd in ("net", "weapon", "buy:ca_loc", "sell:ca_loc"):
            self.assertEqual(s.step(inp(cmd)), [], cmd)
        self.assertEqual((s.money, s.upgrades), (10_000, {}))

    def test_input_upgrades_not_mutated(self):
        start = {"hp": 1}
        s = ShopSim(T, money=10_000, earned=10_000, upgrades=start, stock={})
        s.step(inp("hp"))
        self.assertEqual(start, {"hp": 1})
        self.assertEqual(s.result["upgrades"], {"hp": 2})


class Close(unittest.TestCase):
    def test_buy_before_shop_done_same_step(self):
        price = UP["oxygen"][0]["price"]
        s = shop(money=price)
        ev = s.step(inp("oxygen", done=True))
        self.assertEqual([n for n, _ in ev], ["bought", "shop_end"])
        self.assertEqual(ev[1][1], {"reason": "done"})
        self.assertTrue(s.done)
        self.assertEqual(s.reason, "done")

    def test_auto_close_after_max_ticks(self):
        s = shop()
        for _ in range(MAX - 1):
            self.assertEqual(s.step(IDLE), [])
        self.assertFalse(s.done)
        self.assertEqual(s.time_left_ticks, 1)
        self.assertEqual(s.step(IDLE), [("shop_end", {"reason": "time"})])
        self.assertTrue(s.done)
        self.assertEqual(s.reason, "time")

    def test_button_on_last_step_is_done(self):
        s = shop()
        for _ in range(MAX - 1):
            s.step(IDLE)
        self.assertEqual(s.step(inp(done=True)), [("shop_end", {"reason": "done"})])

    def test_buy_on_last_step_before_time(self):
        price = UP["hp"][0]["price"]
        s = shop(money=price)
        for _ in range(MAX - 1):
            s.step(IDLE)
        self.assertEqual([n for n, _ in s.step(inp("hp"))], ["bought", "shop_end"])

    def test_no_events_after_done(self):
        s = shop(money=10_000)
        s.step(inp(done=True))
        self.assertEqual(s.step(inp("hp")), [])
        self.assertEqual(s.upgrades, {})


class Snapshot(unittest.TestCase):
    def test_snapshot_and_result(self):
        s = shop(money=300, earned=500, upgrades={"hp": 1}, stock={"ca_loc": 1, "bong_sung": 0})
        snap = s.snapshot()
        self.assertEqual(snap["stock"], {"ca_loc": 1})
        self.assertEqual(snap["upgrades"], {"hp": 1})
        self.assertEqual(s.time_left_ticks, MAX)
        s.step(IDLE)
        self.assertEqual(s.time_left_ticks, MAX - 1)
        self.assertEqual(s.result, {"money": 300, "earned": 500, "upgrades": {"hp": 1}, "stock": {"ca_loc": 1}})
        self.assertEqual((s.mode, s.phase), ("shop", "shop"))

    def test_prices_read_from_tuning(self):
        t = copy.deepcopy(T)
        t["shop"]["upgrades"]["oxygen"][0]["price"] = 7
        s = ShopSim(t, money=7, earned=7, upgrades={}, stock={})
        self.assertEqual(s.step(inp("oxygen"))[0][0], "bought")


if __name__ == "__main__":
    unittest.main()
