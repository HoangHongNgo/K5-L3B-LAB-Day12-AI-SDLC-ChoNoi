"""Kiểm Lát B bằng tuning v1.1, giữ fixture độc lập với manifest đang tích hợp."""

import json
import unittest
from pathlib import Path

from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.gather import GatherSim

FIXTURES = Path(__file__).with_name("fixtures")
ROOT = FIXTURES.parent.parent


def read_fixture(path):
    return json.loads(path.read_text(encoding="utf-8"))


def monster_tuning():
    tuning = read_fixture(ROOT / "game.contract.json")["tuning"]
    tuning["gather"]["monsters"] = read_fixture(FIXTURES / "p2_monster_tuning.json")
    tuning["shop"] = {"max_ticks": 600, "upgrades": {
        "oxygen": [{"level": 1, "price": 200, "oxygen_max_s": 45},
                   {"level": 2, "price": 400, "oxygen_max_s": 60}],
        "hp": [{"level": 1, "price": 250, "hp_max": 4},
               {"level": 2, "price": 500, "hp_max": 5}],
    }}
    return tuning


def gather_session(scenario):
    return Session("gather", monster_tuning(), {"random_fish": False, **scenario}, seed=42)


def monster(pos, **fields):
    return {"id": "M1", "kind": "ca_sau", "pos": pos, "waypoints": [[20, 10], [24, 10]], **fields}


class MonsterMovement(unittest.TestCase):
    def test_default_spawns_and_active_limits_follow_current_day(self):
        tuning = monster_tuning()
        for day, levels, ids, hp, oxygen in [
            (1, {}, ["M1"], 3, 1800),
            (2, {"oxygen": 1, "hp": 1}, ["M1"], 4, 2700),
            (3, {"oxygen": 2, "hp": 2}, ["M1", "M2"], 5, 3600),
        ]:
            with self.subTest(day=day):
                sim = GatherSim(tuning, {"random_fish": False}, Streams(42),
                                day=day, active_upgrades=levels)
                snapshot = sim.snapshot()
                self.assertEqual([m["id"] for m in snapshot["monsters"]], ids)
                player = snapshot["player"]
                self.assertEqual((player["hp"], player["hp_max"]), (hp, hp))
                self.assertEqual((player["oxygen_ticks"], player["oxygen_max_ticks"]), (oxygen, oxygen))
                self.assertEqual(snapshot["hold"], [])

    def test_patrol_reaches_waypoint_and_reverses_next_tick(self):
        session = gather_session({"monsters": [monster([20, 10])]})
        inputs = InputPlayer([])
        for tick in range(240):
            session.step(inputs.advance(tick))
        at_waypoint = session.snapshot()["monsters"][0]
        self.assertEqual((at_waypoint["pos"], at_waypoint["target_idx"]), ([24, 10], 0))
        session.step(inputs.advance(240))
        self.assertAlmostEqual(session.snapshot()["monsters"][0]["pos"][0], 24 - 1 / 60)

    def test_chase_detects_inclusive_depth_and_distance(self):
        inputs = InputPlayer([])
        for pos, want_state, want_x in [
            ([10, 10], "chase", 19.95),
            ([9.999, 10], "patrol", 20 + 1 / 60),
            ([10.01, 9.999], "patrol", 20 + 1 / 60),
        ]:
            with self.subTest(pos=pos):
                session = gather_session({"player": {"pos": pos}, "monsters": [monster([20, 10])]})
                session.step(inputs.advance(0))
                current = session.snapshot()["monsters"][0]
                self.assertEqual(current["state"], want_state)
                self.assertAlmostEqual(current["pos"][0], want_x)

    def test_chase_exits_only_beyond_radius_or_above_species_depth(self):
        for pos, want_state in [([4, 10], "chase"), ([3.999, 10], "patrol"), ([20, 9.999], "patrol")]:
            with self.subTest(pos=pos):
                session = gather_session({"player": {"pos": pos},
                                          "monsters": [monster([20, 10], state="chase")]})
                session.step(InputPlayer([]).advance(0))
                self.assertEqual(session.snapshot()["monsters"][0]["state"], want_state)
