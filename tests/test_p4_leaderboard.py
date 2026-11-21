"""Extension leaderboard: top 10 bền vững, hòa giữ thứ tự ghi, cặp cờ headless, xuất qua run_cmd."""

import json
import os
import shlex
import subprocess
import tempfile
import unittest

from chonoi import leaderboard as lb
from chonoi.errors import BadInput
from helpers import ROOT, headless_cmd, run_headless, write_json


def run_cmd():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return shlex.split(json.load(f)["run_cmd"])


class TestStore(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.store = os.path.join(self.dir.name, "lb.json")

    def test_sorted_desc_ties_keep_insertion_order_and_top10(self):
        for i, score in enumerate([100, 300, 100, 300, 50]):
            lb.add_entry(self.store, f"P{i}", score, 5, i)
        self.assertEqual([e["name"] for e in lb.load(self.store)], ["P1", "P3", "P0", "P2", "P4"])
        for i in range(10):  # 15 mục -> chỉ giữ 10, mục điểm thấp nhất rơi
            lb.add_entry(self.store, f"Q{i}", 200, 5, i)
        names = [e["name"] for e in lb.load(self.store)]
        self.assertEqual(len(names), 10)
        self.assertEqual(names[:2], ["P1", "P3"])
        self.assertNotIn("P4", names)
        self.assertEqual(names[2:], [f"Q{i}" for i in range(8)])  # hòa 200: ghi trước đứng trước, sau khi mở lại

    def test_unicode_name_and_blank_rejected(self):
        lb.add_entry(self.store, "Út Sen", 10, 5, 42)
        self.assertEqual(lb.load(self.store)[0]["name"], "Út Sen")
        for bad in ("", "   ", None, 5):
            with self.assertRaises(BadInput):
                lb.add_entry(self.store, bad, 1, 5, 1)

    def test_corrupt_store_is_bad_input(self):
        with open(self.store, "w") as f:
            f.write("{nope")
        with self.assertRaises(BadInput):
            lb.load(self.store)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.p = lambda n: os.path.join(self.dir.name, n)

    def day(self, *extra, days="5", seed="42", ticks="400000"):
        return run_headless("--mode", "day", "--seed", seed, "--days", days, "--ticks", ticks,
                            "--out", self.p("o.jsonl"), *extra)

    def test_standard_run_writes_exactly_one_entry_and_export(self):
        code, err = self.day("--leaderboard", self.p("s.json"), "--player-name", "Út Sen")
        self.assertEqual(code, 0, err)
        entries = lb.load(self.p("s.json"))
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["days_completed"], 5)
        self.assertEqual(entries[0]["seed"], 42)
        out = subprocess.run(run_cmd() + ["--export-leaderboard", self.p("e.json"), "--leaderboard", self.p("s.json")],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        with open(self.p("e.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"entries": entries})

    def test_non_standard_runs_write_nothing(self):
        self.assertEqual(self.day("--leaderboard", self.p("s.json"), "--player-name", "A", days="2")[0], 0)
        self.assertFalse(os.path.exists(self.p("s.json")))
        write_json(self.p("sc.json"), {})
        code, _ = self.day("--leaderboard", self.p("s.json"), "--player-name", "A", "--scenario", self.p("sc.json"))
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.p("s.json")))

    def test_flag_pair_and_mode_errors_exit_2(self):
        self.assertEqual(self.day("--leaderboard", self.p("s.json"))[0], 2)
        self.assertEqual(self.day("--player-name", "A")[0], 2)
        self.assertEqual(self.day("--leaderboard", self.p("s.json"), "--player-name", " ")[0], 2)
        code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--out", self.p("o.jsonl"),
                               "--leaderboard", self.p("s.json"), "--player-name", "A")
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(self.p("s.json")))


if __name__ == "__main__":
    unittest.main()
