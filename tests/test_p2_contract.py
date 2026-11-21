"""Lát C (phần contract v1.1 + cờ --days) — TICKET-02 mục 1, 2, 4.1.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p2_contract -v
"""

import copy
import json
import time
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput

C = load_contract()
T = C["tuning"]


def broken(mutate):
    t = copy.deepcopy(T)
    mutate(t)
    with self_raises():
        validate_tuning(t)


class self_raises:
    def __enter__(self):
        return self

    def __exit__(self, typ, val, tb):
        if typ is None:
            raise AssertionError("validate_tuning không báo lỗi")
        return issubclass(typ, BadInput)


class ContractV11(unittest.TestCase):
    def test_version_and_extensions(self):
        self.assertEqual(C["contract_version"], "1.1")
        self.assertEqual(C["extensions"], ["net"])

    def test_standard_numbers(self):
        g, q = T["gather"], T["quan"]
        self.assertEqual(g["fish_initial"], 8)
        self.assertEqual(g["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        self.assertEqual([n["id"] for n in g["nodes"]], ["N1", "N2", "N3", "N4", "N5", "N6"])
        self.assertEqual([s["id"] for s in q["stoves"]], ["B1", "B2"])
        self.assertEqual([s["id"] for s in q["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertEqual(len(T["menu"]), 6)
        self.assertEqual([e["day"] for e in T["day_plan"]], [1, 2, 3, 4, 5])
        self.assertEqual(T["shop"]["max_ticks"], 600)
        self.assertEqual([u["oxygen_max_s"] for u in T["shop"]["upgrades"]["oxygen"]], [45, 60])
        self.assertEqual([u["hp_max"] for u in T["shop"]["upgrades"]["hp"]], [4, 5])
        self.assertEqual([s["id"] for s in g["monsters"]["spawns"]], ["M1", "M2"])
        self.assertEqual(T["menu"]["lau_mam"], {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1},
                                               "cook_s": 12, "price": 200})

    def test_day_plan_ingredients_must_match_recipes(self):
        broken(lambda t: t["day_plan"][0]["ingredients"].update(ca_loc=4))

    def test_day_plan_unknown_dish(self):
        broken(lambda t: t["day_plan"][1]["dishes"].update(pho=1))

    def test_shop_levels_and_prices(self):
        broken(lambda t: t["shop"]["upgrades"]["oxygen"][1].update(level=3))
        broken(lambda t: t["shop"]["upgrades"]["hp"][0].update(price=0))
        broken(lambda t: t["shop"].update(max_ticks=0))

    def test_fish_keys(self):
        broken(lambda t: t["gather"]["fish_depths"].pop("ca_keo"))
        broken(lambda t: t["gather"].update(fish_x=[-1, 96]))
        broken(lambda t: t["gather"]["fish_spawn_depths"].update(ca_linh=[5, 15]))  # ngoài dải [3, 12]
        broken(lambda t: t["gather"].update(fish_initial=13))  # vượt fish_max

    def test_v10_fish_list_still_valid(self):
        t = copy.deepcopy(T)
        for k in ("fish_speed", "fish_turn_ticks", "fish_max", "fish_spawn_ticks", "fish_spawn_clearance", "fish_x",
                  "fish_depths", "fish_spawn_x", "fish_spawn_depths", "fish_weights"):
            del t["gather"][k]
        t["gather"]["fish_initial"] = [{"id": f"F{i}", "kind": "ca_loc", "pos": [10 * i, 10]} for i in range(1, 7)]
        validate_tuning(t)


class DaysFlag(unittest.TestCase):
    def run_day(self, *extra, scenario=None):
        with Workdir() as w:
            args = ["--mode", "day", "--seed", "42", "--out", w.path("o.jsonl"), *extra]
            if scenario is not None:
                args += ["--scenario", write_json(w.path("sc.json"), scenario)]
            code, err = run_headless(*args)
            return code, err, (read_jsonl(w.path("o.jsonl")) if code == 0 else None)

    def test_days_only_with_day_mode(self):
        with Workdir() as w:
            code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--days", "1",
                                   "--out", w.path("o.jsonl"))
            self.assertEqual(code, 2)

    def test_days_range(self):
        for bad in ("0", "6", "x"):
            self.assertEqual(self.run_day("--ticks", "0", "--days", bad)[0], 2, bad)

    def test_one_day_completes_within_limits(self):
        t0 = time.perf_counter()
        code, err, rows = self.run_day("--ticks", "22200")
        secs = time.perf_counter() - t0
        self.assertEqual(code, 0, err)
        end = rows[-1]
        self.assertEqual((end["reason"], end["days_completed"]), ("days_complete", 1))
        self.assertLessEqual(end["ticks"], 22200)
        self.assertLessEqual(secs, 20)
        plan = [e for e in events(rows, "day_plan")]
        self.assertEqual(plan[0]["tick"], 0)
        self.assertEqual(plan[0]["data"], {"dishes": T["day_plan"][0]["dishes"],
                                           "ingredients": T["day_plan"][0]["ingredients"]})

    def test_three_days_and_upgrade_applies_next_day(self):
        sc = {"day": {"money": 400, "earned": 400}, "gather": {"time_left_ticks": 2}, "quan": {"time_left_ticks": 2}}
        code, err, rows = self.run_day("--ticks", "5000", "--days", "3", scenario=sc)
        self.assertEqual(code, 0, err)
        self.assertEqual((rows[-1]["reason"], rows[-1]["days_completed"]), ("days_complete", 3))
        self.assertEqual([e["data"]["dishes"] for e in events(rows, "day_plan")],
                         [T["day_plan"][i]["dishes"] for i in range(3)])
        self.assertEqual(sorted({s["day"] for s in snapshots(rows)}), [1, 2, 3])

    def test_same_seed_byte_identical(self):
        sc = {"gather": {"time_left_ticks": 30}, "quan": {"time_left_ticks": 30}}
        with Workdir() as w:
            outs = []
            for i in (1, 2):
                p = w.path(f"o{i}.jsonl")
                code, err = run_headless("--mode", "day", "--seed", "7", "--ticks", "2000", "--out", p,
                                         "--scenario", write_json(w.path("sc.json"), sc))
                self.assertEqual(code, 0, err)
                outs.append(open(p, "rb").read())
            self.assertEqual(outs[0], outs[1])


class Inventory6Kinds(unittest.TestCase):
    def test_quan_reads_new_kinds(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_keo": 2, "keo_neo": 1}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], {"ca_keo": 2, "keo_neo": 1})


if __name__ == "__main__":
    unittest.main()
