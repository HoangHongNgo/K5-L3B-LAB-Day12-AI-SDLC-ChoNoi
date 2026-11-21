"""AC-P2-11 (phần CLI): cờ `--mode day` và `--days` (Test Contract v1.1, mục 4.1)."""

import os
import unittest

from helpers import ROOT, Workdir, frames, read_jsonl, run_headless, write_json

HAS_DAY = os.path.exists(os.path.join(ROOT, "chonoi", "sim", "day.py"))


def day(*extra, out="o.jsonl", ticks="1"):
    return ["--mode", "day", "--seed", "1", "--ticks", ticks, *extra]


class TestDaysFlag(unittest.TestCase):
    def check(self, args, want, w):
        out = w.path("o.jsonl")
        code, err = run_headless(*args, "--out", out)
        self.assertEqual(code, want, err)
        return out

    def test_days_out_of_range_or_not_int_is_exit_2(self):
        for bad in ("0", "6", "-1", "abc", "1.5", "10"):
            with self.subTest(days=bad), Workdir() as w:
                out = self.check(day("--days", bad), 2, w)
                self.assertFalse(os.path.exists(out), "mã 2 phải xảy ra TRƯỚC khi ghi đầu ra")

    def test_days_only_valid_with_day(self):
        for mode in ("gather", "quan"):
            with self.subTest(mode=mode), Workdir() as w:
                out = self.check(["--mode", mode, "--seed", "1", "--ticks", "1", "--days", "1"], 2, w)
                self.assertFalse(os.path.exists(out))

    def test_valid_days_pass_validation(self):
        """1..5 hợp lệ. Khi lát D chưa gộp (chưa có day.py) CLI báo chưa hỗ trợ (mã 1) chứ không phải mã 2."""
        for n in ("1", "3", "5"):
            with self.subTest(days=n), Workdir() as w:
                code, err = run_headless(*day("--days", n), "--out", w.path("o.jsonl"))
                self.assertIn(code, (0, 1), err)
                if not HAS_DAY:
                    self.assertEqual(code, 1)
                    self.assertIn("day", err)

    def test_days_default_is_valid(self):
        with Workdir() as w:
            code, err = run_headless(*day(), "--out", w.path("o.jsonl"))
            self.assertIn(code, (0, 1), err)

    def test_inventory_files_are_for_standalone_modes_only(self):
        with Workdir() as w:
            kho = write_json(w.path("kho.json"), {"items": {"ca_loc": 1}})
            code, _ = run_headless(*day("--inventory", kho), "--out", w.path("o.jsonl"))
            self.assertEqual(code, 2)
            code, _ = run_headless(*day("--inventory-out", w.path("k2.json")), "--out", w.path("o.jsonl"))
            self.assertEqual(code, 2)

    def test_day_scenario_errors_are_exit_2(self):
        cases = {
            "money_gt_earned": {"day": {"money": 10, "earned": 5}},
            "quan_stock": {"quan": {"stock": {"ca_loc": 1}}},
            "quan_reputation": {"quan": {"reputation": 3}},
            "bad_plan": {"day": {"day_plan": [{"day": 1, "dishes": {"mon_la": 1}}]}},
            "plan_ingredients_mismatch": {"day": {"day_plan": [{"day": 1, "dishes": {"lau_mam": 1},
                                                                "ingredients": {"ca_loc": 1}}]}},
        }
        for name, doc in cases.items():
            with self.subTest(case=name), Workdir() as w:
                out = w.path("o.jsonl")
                sc = write_json(w.path("sc.json"), doc)
                code, err = run_headless(*day("--scenario", sc), "--out", out)
                self.assertEqual(code, 2, err)
                self.assertFalse(os.path.exists(out))

    def test_ticket_example_scenario_passes_validation(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"day": {"money": 200, "earned": 200},
                                                "gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"],
                                                           "random_fish": False}})
            code, err = run_headless(*day("--scenario", sc), "--out", w.path("o.jsonl"))
            self.assertIn(code, (0, 1), err)

    def test_day_inputs_accept_v11_fields(self):
        with Workdir() as w:
            inp = write_json(w.path("in.json"), frames({"tick": 0, "shop_done": True, "buy": "hp", "pause": True}))
            code, err = run_headless(*day("--inputs", inp), "--out", w.path("o.jsonl"))
            self.assertIn(code, (0, 1), err)


@unittest.skipUnless(HAS_DAY, "chờ lát D (chonoi/sim/day.py)")
class TestDayOutputEnvelope(unittest.TestCase):
    def test_every_event_has_day_and_end_has_days_completed(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            code, err = run_headless(*day("--days", "1", ticks="200"), "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
        for r in rows:
            if r["type"] == "event":
                self.assertIn("day", r)
        self.assertIn("days_completed", rows[-1])


if __name__ == "__main__":
    unittest.main()
