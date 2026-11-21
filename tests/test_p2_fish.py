"""Lát A — Cá bơi, phản xạ mép, đàn ban đầu, sinh cá, N5/N6, catch theo vị trí trước khi bơi
(TICKET-02 mục 1.1, 4.1, 4.3, 4.4, 4.5 "Gather").

Khóa v1.1 của gather lấy từ tests/fixtures/p2_fish_tuning.json cho tới khi contract v1.1 có.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p2_fish -v
"""

import copy
import json
import math
import os
import unittest

from helpers import ROOT

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.scenario import _validate_gather
from chonoi.sim.gather import GatherSim


def tuning(**over):
    t = copy.deepcopy(load_contract()["tuning"])
    with open(os.path.join(ROOT, "tests", "fixtures", "p2_fish_tuning.json"), encoding="utf-8") as f:
        t["gather"].update(json.load(f))
    t["gather"].pop("monsters", None)
    t["gather"].update(over)
    return t


T = tuning()
G = T["gather"]
HZ = T["tick_hz"]
STEP = G["fish_speed"] / HZ
IDLE = InputState((0.0, 0.0), {}, set())
CATCH = InputState((0.0, 0.0), {"catch": True}, {"catch"})


def sim(scenario, t=T, seed=1):
    return GatherSim(t, dict({"player": {"pos": [50, 0]}}, **scenario), Streams(seed), IdAllocator())


def school(fid="F1", kind="ca_linh", pos=(50, 5), heading=0, age=0):
    return {"id": fid, "kind": kind, "pos": list(pos), "heading_deg": heading, "age_ticks": age}


def fish(s, fid="F1"):
    return next(f for f in s.snapshot()["fish"] if f["id"] == fid)


def run(s, n, inp=IDLE):
    out = []
    for _ in range(n):
        out.extend(s.step(inp))
    return out


def spawn_points(kind=None):
    kinds = [kind] if kind else sorted(G["fish_spawn_depths"])
    return [(k, [x, d]) for k in kinds for x in G["fish_spawn_x"] for d in G["fish_spawn_depths"][k]]


class Swim(unittest.TestCase):
    def test_straight_line_speed(self):
        s = sim({"fish": [school(heading=0)]})
        run(s, 60)
        f = fish(s)
        self.assertAlmostEqual(f["pos"][0], 50 + G["fish_speed"], places=6)
        self.assertAlmostEqual(f["pos"][1], 5, places=6)
        self.assertEqual(f["age_ticks"], 60)

    def test_heading_90_is_down(self):
        s = sim({"fish": [school(heading=90, pos=(50, 5))]})
        run(s, 1)
        self.assertAlmostEqual(fish(s)["pos"][1], 5 + STEP, places=6)

    def test_reflect_x_edge(self):
        hi = G["fish_x"][1]
        start = hi - STEP / 2
        s = sim({"fish": [school(pos=(start, 5), heading=0)]})
        run(s, 1)
        f = fish(s)
        self.assertAlmostEqual(f["pos"][0], hi - STEP / 2, places=6)
        self.assertAlmostEqual(f["heading_deg"] % 360, 180, places=6)

    def test_reflect_depth_edge_of_species(self):
        lo, hi = G["fish_depths"]["ca_linh"]
        s = sim({"fish": [school(pos=(50, hi - STEP / 4), heading=90)]})
        run(s, 1)
        f = fish(s)
        self.assertAlmostEqual(f["pos"][1], hi - 3 * STEP / 4, places=6)
        self.assertAlmostEqual(f["heading_deg"] % 360, 270, places=6)

    def test_corner_flips_both(self):
        hi_x, hi_d = G["fish_x"][1], G["fish_depths"]["ca_linh"][1]
        eps = STEP / (4 * math.sqrt(2))
        s = sim({"fish": [school(pos=(hi_x - eps, hi_d - eps), heading=45)]})
        run(s, 1)
        f = fish(s)
        self.assertLessEqual(f["pos"][0], hi_x)
        self.assertLessEqual(f["pos"][1], hi_d)
        self.assertAlmostEqual(f["heading_deg"] % 360, 225, places=6)

    def test_turn_on_swim_step_120_before_moving(self):
        turn = G["fish_turn_ticks"]
        s = sim({"fish": [school(age=turn - 2)]})
        run(s, 1)
        self.assertEqual(fish(s)["heading_deg"], 0)  # bước bơi thứ 119: chưa đổi
        before = list(fish(s)["pos"])
        run(s, 1)  # bước bơi thứ 120: đổi hướng rồi mới đi
        f = fish(s)
        h = math.radians(f["heading_deg"])
        self.assertAlmostEqual(f["pos"][0], before[0] + STEP * math.cos(h), places=6)
        self.assertAlmostEqual(f["pos"][1], before[1] + STEP * math.sin(h), places=6)
        self.assertEqual(f["age_ticks"], turn)
        other = sim({"fish": [school(age=turn - 2)]})
        run(other, 2)
        self.assertEqual(fish(other)["heading_deg"], f["heading_deg"])  # cùng seed, cùng hướng

    def test_random_fish_false_static_and_no_spawn(self):
        s = sim({"random_fish": False, "fish": [school()]})
        ev = run(s, G["fish_spawn_ticks"] + 1)
        self.assertEqual(fish(s)["pos"], [50, 5])
        self.assertEqual([e for e in ev if e[0] == "fish_spawned"], [])
        self.assertEqual(len(s.snapshot()["fish"]), 1)

    def test_fish_do_not_move_on_the_finishing_step(self):
        s = sim({"fish": [school()], "time_left_ticks": 1})
        run(s, 1)
        self.assertTrue(s.done)
        self.assertEqual(fish(s)["pos"], [50, 5])


class Initial(unittest.TestCase):
    def test_eight_schools_at_distinct_spawn_points(self):
        s = sim({})
        fs = s.snapshot()["fish"]
        self.assertEqual(len(fs), G["fish_initial"])
        self.assertEqual([f["id"] for f in fs], [f"F{i}" for i in range(1, 9)])
        pts = {tuple(f["pos"]) for f in fs}
        self.assertEqual(len(pts), 8)
        for f in fs:
            self.assertIn(f["pos"][0], G["fish_spawn_x"])
            self.assertIn(f["pos"][1], G["fish_spawn_depths"][f["kind"]])
            self.assertEqual(f["age_ticks"], 0)

    def test_same_seed_same_layout_other_seed_differs(self):
        a = sim({}, seed=7).snapshot()["fish"]
        self.assertEqual(a, sim({}, seed=7).snapshot()["fish"])
        layouts = {json.dumps(sim({}, seed=k).snapshot()["fish"]) for k in range(5)}
        self.assertGreater(len(layouts), 1)

    def test_v10_contract_keeps_static_preset(self):
        t = copy.deepcopy(load_contract()["tuning"])
        if "fish_speed" in t["gather"]:
            self.skipTest("contract đã lên v1.1")
        s = GatherSim(t, {}, Streams(1), IdAllocator())
        before = s.snapshot()["fish"]
        run(s, 400)
        self.assertEqual(s.snapshot()["fish"], before)


class Spawn(unittest.TestCase):
    def test_spawn_at_360_after_swim(self):
        s = sim({"fish": [school()]})
        ev = run(s, G["fish_spawn_ticks"] - 1)
        self.assertEqual([e for e in ev if e[0] == "fish_spawned"], [])
        ev = run(s, 1)
        sp = [d for n, d in ev if n == "fish_spawned"]
        self.assertEqual(len(sp), 1)
        self.assertEqual(sp[0]["id"], "F2")
        kind, pos = sp[0]["kind"], sp[0]["pos"]
        self.assertIn((kind, pos), spawn_points())
        new = fish(s, "F2")
        self.assertEqual((new["pos"], new["age_ticks"]), (pos, 0))  # chưa bơi ở bước sinh
        run(s, 1)
        self.assertEqual(fish(s, "F2")["age_ticks"], 1)

    def test_spawn_every_360_up_to_max(self):
        t = tuning(fish_speed=0)
        s = sim({"fish": [school(pos=(50, 3))]}, t)
        ev = run(s, G["fish_spawn_ticks"] * 13)
        self.assertEqual(len([e for e in ev if e[0] == "fish_spawned"]), G["fish_max"] - 1)
        self.assertEqual(len(s.snapshot()["fish"]), G["fish_max"])

    def test_skip_when_no_point_clear(self):
        t = tuning(fish_speed=0, fish_max=100)
        fs = [school(f"F{i}", k, p) for i, (k, p) in enumerate(spawn_points(), start=1)]
        s = sim({"fish": fs}, t)
        ev = run(s, G["fish_spawn_ticks"])
        self.assertEqual([e for e in ev if e[0] == "fish_spawned"], [])

    def test_only_species_with_free_points(self):
        t = tuning(fish_speed=0, fish_max=100)
        taken = spawn_points("ca_linh") + spawn_points("ca_loc")
        fs = [school(f"F{i}", k, p) for i, (k, p) in enumerate(taken, start=1)]
        for seed in range(6):
            s = sim({"fish": copy.deepcopy(fs)}, t, seed=seed)
            sp = [d for n, d in run(s, G["fish_spawn_ticks"]) if n == "fish_spawned"]
            self.assertEqual(sp[0]["kind"], "ca_keo", seed)

    def test_clearance_strictly_greater(self):
        """Điểm cách đàn đang sống đúng clearance (không > ) thì không hợp lệ."""
        t = tuning(fish_speed=0, fish_max=100)
        c = G["fish_spawn_clearance"]
        pts = spawn_points()
        fs = [school(f"F{i}", k, [p[0], p[1] + c] if k == "ca_keo" and p[1] == 24 else p)
              for i, (k, p) in enumerate(pts, start=1) if not (k == "ca_keo" and p[1] == 27)]
        # mọi điểm ca_keo d=24 bị đàn ở d=25 chiếm đúng 1 m; điểm d=27 cách đàn d=25 đúng 2 m -> còn trống
        s = sim({"fish": fs}, t)
        sp = [d for n, d in run(s, G["fish_spawn_ticks"]) if n == "fish_spawned"]
        self.assertEqual(sp[0]["kind"], "ca_keo")
        self.assertEqual(sp[0]["pos"][1], 27)


class CatchAndNodes(unittest.TestCase):
    def test_catch_uses_position_before_swim(self):
        r = G["catch_radius"]
        s = sim({"player": {"pos": [50 - r, 5]}, "fish": [school(pos=(50, 5), heading=0)]})
        ev = s.step(CATCH)
        self.assertEqual([n for n, _ in ev], ["fish_caught"])

    def test_fish_entering_range_after_swim_not_caught_that_step(self):
        r = G["catch_radius"]
        s = sim({"player": {"pos": [50 - r - STEP / 2, 5]}, "fish": [school(pos=(50, 5), heading=180)]})
        self.assertEqual(s.step(CATCH), [])

    def test_ca_keo_yield_2(self):
        s = sim({"player": {"pos": [50, 24]}, "fish": [school(kind="ca_keo", pos=(50, 24))]})
        ev = s.step(CATCH)
        self.assertEqual(ev, [("fish_caught", {"fish_id": "F1", "kind": "ca_keo", "yield": 2})])

    def test_keo_neo_node(self):
        s = GatherSim(T, {"player": {"pos": [76, 0]}}, Streams(1), IdAllocator())
        press = InputState((0.0, 0.0), {"interact": True}, {"interact"})
        self.assertEqual(s.step(press)[0], ("gather", {"node_id": "N5", "kind": "keo_neo", "amount": 1}))


class Scenario(unittest.TestCase):
    def test_age_ticks_and_new_kinds_validate(self):
        _validate_gather({"fish": [school(kind="ca_keo", pos=(50, 24), age=5)],
                          "nodes": [{"id": "N9", "kind": "keo_neo", "pos": [70, 0]}],
                          "hold": ["ca_keo", "keo_neo"]}, T)

    def test_bad_age_ticks(self):
        for bad in (-1, 1.5, "3", True):
            with self.assertRaises(BadInput):
                _validate_gather({"fish": [school(age=bad)]}, T)


if __name__ == "__main__":
    unittest.main()
