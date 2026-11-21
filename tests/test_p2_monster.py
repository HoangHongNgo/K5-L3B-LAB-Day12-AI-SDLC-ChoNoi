"""Kiểm Lát B bằng tuning v1.1, giữ fixture độc lập với manifest đang tích hợp."""

import io
import json
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from chonoi.errors import BadInput
from chonoi.headless import main as headless_main
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.scenario import load_scenario
from chonoi.sim.gather import GatherSim
from fixtures.fresh import after_tick, fresh_items, stocked, kinds
from helpers import Workdir, events, read_jsonl, snapshots, write_json

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


def one_step(session, *frames):
    return [(row["name"], row["data"]) for row in session.step(InputPlayer(frames).advance(0))]


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


    def test_decimal_coordinates_preserve_inclusive_detection_and_exit(self):
        for player_x, monster_x, state in [(6.1, 16.1, "patrol"), (16.2, 32.2, "chase")]:
            with self.subTest(player_x=player_x, state=state):
                session = gather_session({
                    "player": {"pos": [player_x, 10]},
                    "monsters": [monster([monster_x, 10], state=state)],
                })
                one_step(session)
                self.assertEqual(session.snapshot()["monsters"][0]["state"], "chase")


class MonsterDamage(unittest.TestCase):
    def test_hit_selects_closest_then_numeric_id_and_drops_half_lifo(self):
        scenario = read_fixture(FIXTURES / "p2_monster_hit.json")["gather"]
        session = gather_session(scenario)
        self.assertEqual(one_step(session), [("monster_hit", {
            "monster_id": "M2", "hp": 2, "lost": after_tick(scenario["hold"], monster_tuning())[-1:-3:-1], "pos": [20, 10],
        })])
        snapshot = session.snapshot()
        self.assertEqual(kinds(snapshot["hold"]), ["ca_loc", "bong_sung", "ca_linh"])
        self.assertEqual(snapshot["player"]["invuln_ticks"], 90)
        self.assertEqual([(m["id"], m["state"]) for m in snapshot["monsters"]],
                         [("M1", "chase"), ("M2", "recoil"), ("M10", "chase")])
        hit_monster = snapshot["monsters"][1]
        self.assertEqual((hit_monster["state_ticks_left"], hit_monster["recoil_dir"]), (60, [1, 0]))

    def test_hit_uses_post_move_player_and_monster_positions(self):
        for player, move, start_x in [
            ({"pos": [20, 10]}, [0, 0], 21.55),
            ({"pos": [1.05, 10]}, [0, 0], 2.60),
            ({"pos": [20, 9.95], "vel": [0, 4]}, [0, 1], 21),
        ]:
            with self.subTest(player=player):
                session = gather_session({"player": player, "monsters": [monster([start_x, 10])]})
                rows = one_step(session, {"tick": 0, "move": move})
                self.assertEqual([name for name, _ in rows], ["monster_hit"])
                self.assertEqual(rows[0][1]["pos"], session.snapshot()["player"]["pos"])

    def test_decimal_coordinates_preserve_id_tie_after_movement(self):
        session = gather_session({
            "player": {"pos": [1.65, 10]},
            "monsters": [monster([2.7, 10]), monster([0.6, 10], id="M2")],
        })
        self.assertEqual(one_step(session)[0][1]["monster_id"], "M1")

    def test_player_just_above_species_depth_cannot_be_hit(self):
        session = gather_session({
            "player": {"pos": [20, 9.999]},
            "monsters": [monster([20, 10], state="chase")],
        })
        self.assertEqual(one_step(session), [])
        self.assertEqual(session.snapshot()["player"]["hp"], 3)
        self.assertEqual(session.snapshot()["monsters"][0]["state"], "patrol")

    def test_invulnerability_expires_on_the_ninetieth_tick(self):
        session = gather_session({
            "player": {"pos": [20, 10], "invuln_ticks": 90},
            "monsters": [monster([20, 10])],
        })
        inputs = InputPlayer([])
        for tick in range(89):
            self.assertEqual(session.step(inputs.advance(tick)), [])
        self.assertEqual(session.snapshot()["monsters"][0]["state"], "chase")
        self.assertEqual(session.snapshot()["player"]["invuln_ticks"], 1)
        self.assertEqual([row["name"] for row in session.step(inputs.advance(89))], ["monster_hit"])
        self.assertEqual(session.snapshot()["player"]["hp"], 2)

    def test_recoil_runs_sixty_steps_in_the_locked_direction(self):
        session = gather_session({"player": {"pos": [20, 10]}, "monsters": [monster([20, 10])]})
        inputs = InputPlayer([{"tick": 1, "move": [0, 1]}])
        session.step(inputs.advance(0))
        self.assertEqual(session.snapshot()["monsters"][0]["pos"], [20, 10])
        session.step(inputs.advance(1))
        after_one = session.snapshot()["monsters"][0]
        self.assertAlmostEqual(after_one["pos"][0], 20 + 2 / 60)
        self.assertEqual(after_one["state_ticks_left"], 59)
        for tick in range(2, 60):
            session.step(inputs.advance(tick))
        self.assertEqual(session.snapshot()["monsters"][0]["state_ticks_left"], 1)
        session.step(inputs.advance(60))
        last = session.snapshot()["monsters"][0]
        self.assertAlmostEqual(last["pos"][0], 22)
        self.assertEqual((last["pos"][1], last["state"], last["recoil_dir"]), (10, "patrol", None))

    def test_final_recoil_tick_is_safe_and_the_next_tick_can_hit(self):
        session = gather_session({
            "player": {"pos": [20, 10]},
            "monsters": [monster([20, 10], state="recoil", state_ticks_left=1, recoil_dir=[1, 0])],
        })
        inputs = InputPlayer([])
        self.assertEqual(session.step(inputs.advance(0)), [])
        self.assertEqual(session.snapshot()["monsters"][0]["state"], "patrol")
        self.assertEqual([row["name"] for row in session.step(inputs.advance(1))], ["monster_hit"])

    def test_recoil_clamps_to_map_and_species_bounds(self):
        session = gather_session({
            "monsters": [monster([99.99, 10.01], state="recoil", state_ticks_left=2, recoil_dir=[0.6, -0.8])],
        })
        one_step(session)
        self.assertEqual(session.snapshot()["monsters"][0]["pos"], [100, 10])

    def test_choke_ignores_invulnerability_without_spilling_items(self):
        hold = ["ca_loc", "ca_linh", "bong_sung"]
        session = gather_session({
            "player": {"pos": [20, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "invuln_ticks": 2},
            "hold": fresh_items(hold),
            "monsters": [monster([20, 10])],
        })
        self.assertEqual(one_step(session), [("choke", {"hp": 2})])
        self.assertEqual(kinds(session.snapshot()["hold"]), hold)
        self.assertEqual(session.snapshot()["player"]["invuln_ticks"], 1)

    def test_lethal_choke_finishes_before_monster_moves(self):
        session = gather_session({
            "player": {"pos": [20, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
            "hold": fresh_items(["ca_loc"]),
            "monsters": [monster([21, 10])],
        })
        self.assertEqual(one_step(session), [
            ("choke", {"hp": 0}),
            ("faint", {"cause": "choke", "lost": after_tick(fresh_items(["ca_loc"]), monster_tuning()), "hp": 0}),
            ("gather_end", {"reason": "fainted", "inventory": {"items": []}}),
        ])
        self.assertEqual(session.snapshot()["monsters"][0]["pos"], [21, 10])
        self.assertEqual(session.sim.result["inventory"], {"items": []})

    def test_nonlethal_hit_precedes_timeout_and_keeps_remaining_stock(self):
        session = gather_session({
            "player": {"pos": [20, 10]}, "hold": fresh_items(["ca_loc", "bong_sung"]), "time_left_ticks": 1,
            "monsters": [monster([20, 10])],
        })
        rows = one_step(session)
        self.assertEqual([name for name, _ in rows], ["monster_hit", "gather_end"])
        self.assertEqual(rows[-1][1], {"reason": "time", "inventory": {"items": session.snapshot()["hold"]}})


class MonsterHeadless(unittest.TestCase):
    def run_cli(self, workdir, fixture, *args):
        scenario = write_json(workdir.path("scenario.json"), {"gather": fixture})
        contract = read_fixture(ROOT / "game.contract.json")
        contract["tuning"] = monster_tuning()
        with patch("chonoi.headless.load_contract", return_value=contract):
            return headless_main([
                "--mode", "gather", "--seed", "42", "--ticks", "10", "--scenario", scenario,
                "--out", workdir.path("out.jsonl"), *args,
            ])

    def test_lethal_hit_after_choke_stops_catch_and_writes_empty_inventory(self):
        scenario = read_fixture(FIXTURES / "p2_monster_hit.json")["gather"]
        scenario["player"].update(hp=2, oxygen_ticks=0, zero_oxy_ticks=59)
        scenario["time_left_ticks"] = 1
        scenario["fish"] = [{"id": "F1", "kind": "ca_loc", "pos": [20, 10]}]
        with Workdir() as w:
            inventory = Path(w.path("catch.json"))
            write_json(inventory, {"items": stocked(ca_loc=2)})
            inputs = write_json(w.path("inputs.json"), {"frames": [{"tick": 0, "catch": True}]})
            self.assertEqual(self.run_cli(w, scenario, "--inventory-out", str(inventory), "--inputs", inputs), 0)
            rows = read_jsonl(w.path("out.jsonl"))
            self.assertEqual(read_fixture(inventory), {"items": []})

        self.assertEqual([(e["name"], e["data"], e["tick"]) for e in events(rows)], [
            ("choke", {"hp": 1}, 1),
            ("monster_hit", {"monster_id": "M2", "hp": 0,
                             "lost": after_tick(scenario["hold"], monster_tuning())[-1:-3:-1], "pos": [20, 10]}, 1),
            ("faint", {"cause": "monster", "lost": after_tick(scenario["hold"], monster_tuning())[2::-1], "hp": 0}, 1),
            ("gather_end", {"reason": "fainted", "inventory": {"items": []}}, 1),
        ])
        final = snapshots(rows)[-1]
        self.assertEqual((final["player"]["hp"], final["hold"], [f["id"] for f in final["fish"]]), (0, [], ["F1"]))
        self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("fainted", 1))

    def test_fixture_for_recoil_reaches_headless_snapshot(self):
        scenario = {"random_fish": False, "monsters": [
            monster([20, 10], target_idx=0, state="recoil", state_ticks_left=15, recoil_dir=[-1, 0]),
        ]}
        with Workdir() as w:
            self.assertEqual(self.run_cli(w, scenario), 0)
            rows = read_jsonl(w.path("out.jsonl"))
        first = snapshots(rows)[0]["monsters"][0]
        self.assertEqual((first["target_idx"], first["state"], first["state_ticks_left"], first["recoil_dir"]),
                         (0, "recoil", 15, [-1, 0]))

    def test_scenario_validation_accepts_only_stats_within_active_limits(self):
        tuning = monster_tuning()
        levels = {"oxygen": 2, "hp": 2}
        player = {"hp": 5, "oxygen_ticks": 3600}
        with Workdir() as w:
            path = w.path("upgraded.json")
            write_json(path, {"gather": {"player": player}})
            with self.assertRaises(BadInput):
                load_scenario(path, "gather", tuning)
            loaded = load_scenario(path, "gather", tuning, active_upgrades=levels)
            self.assertEqual(loaded["player"], player)
            for field in ("hp", "oxygen_ticks"):
                with self.subTest(field=field):
                    write_json(path, {"gather": {"player": {**player, field: player[field] + 1}}})
                    with self.assertRaises(BadInput):
                        load_scenario(path, "gather", tuning, active_upgrades=levels)

    def test_malformed_monster_fixtures_exit_before_output(self):
        cases = [
            [monster([20, 9])],
            [monster([20, 10], kind="unknown")],
            [monster([20, 10], waypoints=[[20, 10]])],
            [monster([20, 10], target_idx=True)],
            [monster([20, 10], state="recoil", state_ticks_left=0, recoil_dir=[1, 0])],
            [monster([20, 10], state="recoil", state_ticks_left=2, recoil_dir=[1, 1])],
            [monster([20, 10], recoil_dir=[1, 0])],
            [monster([20, 10]), monster([20, 10])],
        ]
        for monsters in cases:
            with self.subTest(monsters=monsters), Workdir() as w:
                with redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(self.run_cli(w, {"monsters": monsters}), 2)
                self.assertIn("monsters", stderr.getvalue())
                self.assertFalse(Path(w.path("out.jsonl")).exists())
