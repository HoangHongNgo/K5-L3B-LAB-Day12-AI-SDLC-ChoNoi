"""Lát S — DayState: trạng thái xuyên Ngày (TICKET-02 mục 2 "Vòng ngày", 4.3, 4.5 "Shop").

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p2_progress -v
"""

import unittest

from test_p2_shop import T, UP

from chonoi.sim.progress import DayState

HZ = T["tick_hz"]
BASE_OXY = int(round(T["gather"]["oxygen_max_s"] * HZ))
BASE_HP = T["gather"]["hp_max"]
Q = T["quan"]


class Init(unittest.TestCase):
    def test_defaults(self):
        s = DayState(T)
        self.assertEqual((s.money, s.earned, s.reputation, s.upgrades, s.active_upgrades, s.day),
                         (0, 0, Q["reputation_initial"], {}, {}, 1))
        self.assertEqual(s.limits(), {"oxygen_max_ticks": BASE_OXY, "hp_max": BASE_HP})

    def test_from_day_block(self):
        s = DayState(T, {"money": 200, "earned": 300, "reputation": 4.5, "upgrades": {"hp": 1}})
        self.assertEqual((s.money, s.earned, s.reputation, s.upgrades), (200, 300, 4.5, {"hp": 1}))
        self.assertEqual(s.active_upgrades, {"hp": 1})  # Ngày 1 dựng ngay khi khởi tạo

    def test_day_block_upgrades_active_from_day_1(self):
        s = DayState(T, {"upgrades": {"hp": 1}})
        self.assertEqual(s.limits(), {"oxygen_max_ticks": BASE_OXY, "hp_max": UP["hp"][0]["hp_max"]})
        self.assertEqual((s.day, s.active_upgrades), (1, {"hp": 1}))

    def test_money_without_earned_defaults_earned_0(self):
        self.assertEqual(DayState(T, {"money": 0}).earned, 0)


class NextDay(unittest.TestCase):
    def test_day_2_base_limits(self):
        s = DayState(T)
        self.assertEqual(s.start_next_day(), {"oxygen_max_ticks": BASE_OXY, "hp_max": BASE_HP})
        self.assertEqual(s.day, 2)

    def test_oxygen_level_1_bought_day_1_applies_day_2(self):
        s = DayState(T)
        price = UP["oxygen"][0]["price"]
        s.apply_quan_result({"money": price, "earned": price, "reputation": 3.0})
        s.apply_shop_result({"money": 0, "upgrades": {"oxygen": 1}})
        self.assertEqual((s.upgrades, s.active_upgrades), ({"oxygen": 1}, {}))  # chưa hiệu lực trong Ngày 1
        lim = s.start_next_day()
        self.assertEqual(lim["oxygen_max_ticks"], int(round(UP["oxygen"][0]["oxygen_max_s"] * HZ)))
        self.assertEqual(lim["oxygen_max_ticks"], 2700)
        self.assertEqual((s.day, s.active_upgrades), (2, {"oxygen": 1}))

    def test_hp_level_2_gives_5(self):
        s = DayState(T)
        s.apply_shop_result({"money": 0, "upgrades": {"hp": 2}})
        self.assertEqual(s.start_next_day()["hp_max"], 5)

    def test_active_is_a_copy(self):
        s = DayState(T)
        s.apply_shop_result({"money": 0, "upgrades": {"hp": 1}})
        s.start_next_day()
        s.upgrades["hp"] = 2
        self.assertEqual(s.active_upgrades, {"hp": 1})


class Carry(unittest.TestCase):
    def test_money_earned_reputation_carry(self):
        s = DayState(T, {"money": 100, "earned": 100})
        s.start_next_day()
        s.apply_quan_result({"money": 250, "earned": 250, "reputation": 3.4})
        s.apply_shop_result({"money": 50, "upgrades": {"oxygen": 1}})
        self.assertEqual((s.money, s.earned, s.reputation), (50, 250, 3.4))
        s.start_next_day()
        self.assertEqual((s.money, s.earned, s.reputation), (50, 250, 3.4))

    def test_reputation_clamped(self):
        s = DayState(T)
        s.apply_quan_result({"money": 0, "earned": 0, "reputation": 7})
        self.assertEqual(s.reputation, Q["reputation_max"])
        s.apply_quan_result({"money": 0, "earned": 0, "reputation": -1})
        self.assertEqual(s.reputation, Q["reputation_min"])

    def test_quan_kwargs(self):
        """Tham số dựng QuanSim của Ngày (giao diện chốt sẵn)."""
        s = DayState(T, {"money": 20, "earned": 30, "reputation": 2.5})
        self.assertEqual(s.quan_kwargs(), {"money": 20, "earned": 30, "reputation": 2.5})

    def test_shop_kwargs(self):
        s = DayState(T, {"money": 20, "earned": 30, "upgrades": {"hp": 1}})
        kw = s.shop_kwargs(stock={"ca_loc": 1})
        self.assertEqual(kw, {"money": 20, "earned": 30, "upgrades": {"hp": 1}, "stock": {"ca_loc": 1}})
        kw["upgrades"]["hp"] = 2
        self.assertEqual(s.upgrades, {"hp": 1})


class DayIntegration(unittest.TestCase):
    """DaySim thật (lát D) dùng ShopSim + DayState thật: Ngày 1 dựng ngay khi khởi tạo."""

    def make(self, day_block=None, days=2):
        import copy as _copy
        from test_p2_day import tuning_v11
        from chonoi.rng import Streams
        from chonoi.sim.day import DaySim
        t = tuning_v11()
        t["shop"] = _copy.deepcopy(T["shop"])
        sc = {"gather": {"time_left_ticks": 2}, "quan": {"time_left_ticks": 2}}
        if day_block:
            sc["day"] = day_block
        return DaySim(t, sc, Streams(42), days=days)

    def test_day_1_builds_and_runs_to_days_complete(self):
        from test_p2_shop import IDLE
        d = self.make()
        self.assertEqual(d.day, 1)
        for _ in range(2 * (2 + 2 + T["shop"]["max_ticks"]) + 5):
            if d.done:
                break
            d.step(IDLE)
        self.assertTrue(d.done)
        self.assertEqual((d.reason, d.days_completed, d.day), ("days_complete", 2, 2))

    def test_day_block_upgrades_active_on_day_1(self):
        d = self.make({"money": 0, "earned": 0, "upgrades": {"hp": 1}})
        snap = d.snapshot()
        self.assertEqual(snap["active_upgrades"], {"hp": 1})
        self.assertEqual(snap["player"]["hp_max"], UP["hp"][0]["hp_max"])

    def test_shop_phase_reputation_is_carried(self):
        from test_p2_shop import IDLE
        d = self.make({"reputation": 4.5}, days=1)
        while d.cur.phase != "shop":
            d.step(IDLE)
        self.assertEqual(d.reputation, 4.5)
        self.assertIn("time_left_ticks", d.cur.snapshot())


if __name__ == "__main__":
    unittest.main()
