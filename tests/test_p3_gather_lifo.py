"""Lát B — thứ tự bỏ hàng và dữ liệu cá thể trong event Gather."""

import json
import unittest
from pathlib import Path

from fractions import Fraction
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.runner import run
from chonoi.sim.gather import GatherSim
from helpers import Workdir, events, read_jsonl, snapshots, write_json

FIXTURE = Path(__file__).with_name("fixtures") / "p3_b_hold.json"
CONTRACT = FIXTURE.parents[2] / "game.contract.json"


class ActiveCurrentFixture(GatherSim):
    def _finish(self, reason, row_events):
        row_events.append(("current_end", {"direction": 1, "reason": "phase_end"}))
        super()._finish(reason, row_events)


class GatherLifo(unittest.TestCase):
    def setUp(self):
        self.tuning = json.loads(CONTRACT.read_text(encoding="utf-8"))["tuning"]
        self.scenario = json.loads(FIXTURE.read_text(encoding="utf-8"))["gather"]
        decay = Fraction("0.5") / 60
        self.aged = [dict(it, fresh=float(max(0, Fraction(it["fresh"]) - decay))) for it in self.scenario["hold"]]
        self.spoiled = ("spoiled", {"item_id": "I13", "kind": "bong_dien_dien", "location": "hold"})

    def test_hit_drops_half_by_pickup_order_including_spoiled_items(self):
        sim = GatherSim(self.tuning, self.scenario, Streams(42))
        rows = sim.step(InputPlayer([]).advance(0))
        self.assertEqual(rows, [self.spoiled, ("monster_hit", {
            "monster_id": "M1", "hp": 2, "pos": [20, 12],
            "lost": [self.aged[4], self.aged[3]],
        })])
        self.assertEqual(sim.snapshot()["hold"], self.aged[:3])
        self.assertEqual(sim.snapshot()["hold_count"], 3)

    def test_single_spoiled_item_still_occupies_a_slot_after_zero_loss(self):
        self.scenario["hold"] = [self.scenario["hold"][4]]
        sim = GatherSim(self.tuning, self.scenario, Streams(42))
        hit, = sim.step(InputPlayer([]).advance(0))
        self.assertEqual(hit[0], "monster_hit")
        self.assertEqual(hit[1]["lost"], [])
        self.assertEqual(sim.snapshot()["hold_count"], 1)
        self.assertEqual(sim.snapshot()["hold"], [self.aged[4]])

    def test_lethal_hit_drops_remaining_items_and_runner_writes_empty_list(self):
        self.scenario["player"]["hp"] = 1
        with Workdir() as w:
            inv = Path(w.path("inventory.json"))
            write_json(inv, {"items": [self.scenario["hold"][0]]})
            out = w.path("gather.jsonl")
            run("gather", self.tuning, self.scenario, 42, [], 10, out, 10, inventory_out=inv,
                sim=GatherSim(self.tuning, self.scenario, Streams(42)))
            rows = read_jsonl(out)
            self.assertEqual(json.loads(inv.read_text(encoding="utf-8")), {"items": []})

        self.assertEqual([(row["tick"], row["name"], row["data"]) for row in events(rows)], [
            (1, *self.spoiled),
            (1, "monster_hit", {"monster_id": "M1", "hp": 0, "pos": [20, 12],
                                "lost": [self.aged[4], self.aged[3]]}),
            (1, "faint", {"cause": "monster", "hp": 0, "lost": self.aged[2::-1]}),
            (1, "gather_end", {"reason": "fainted", "inventory": {"items": []}}),
        ])
        self.assertEqual(snapshots(rows)[-1]["hold"], [])
        self.assertEqual((rows[-1]["reason"], rows[-1]["ticks"]), ("fainted", 1))

    def test_lethal_choke_skips_monsters_and_drops_all_items_lifo(self):
        self.scenario["player"].update(hp=1, oxygen_ticks=0, zero_oxy_ticks=59)
        sim = GatherSim(self.tuning, self.scenario, Streams(42))
        rows = sim.step(InputPlayer([]).advance(0))
        self.assertEqual(rows, [
            self.spoiled,
            ("choke", {"hp": 0}),
            ("faint", {"cause": "choke", "hp": 0, "lost": self.aged[::-1]}),
            ("gather_end", {"reason": "fainted", "inventory": {"items": []}}),
        ])
        self.assertEqual(sim.snapshot()["monsters"][0]["state"], "patrol")

    def test_active_current_ends_before_faint_and_terminal_inventory(self):
        self.scenario["player"].update(hp=2, oxygen_ticks=0, zero_oxy_ticks=59)
        self.scenario["time_left_ticks"] = 1
        self.scenario["nodes"] = [{"id": "N1", "kind": "bong_sung", "pos": [20, 0], "regrow_ticks": 1}]
        self.scenario["fish"] = [{"id": "F1", "kind": "ca_loc", "pos": [20, 12]}]
        sim = ActiveCurrentFixture(self.tuning, self.scenario, Streams(42))
        rows = sim.step(InputPlayer([{"tick": 0, "catch": True}]).advance(0))
        self.assertEqual([name for name, _ in rows],
                         ["node_regrown", "spoiled", "choke", "monster_hit", "current_end", "faint", "gather_end"])
        self.assertEqual(rows[-1][1], {"reason": "fainted", "inventory": {"items": []}})
        self.assertEqual([fish["id"] for fish in sim.snapshot()["fish"]], ["F1"])
