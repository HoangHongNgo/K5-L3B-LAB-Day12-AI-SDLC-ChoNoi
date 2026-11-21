"""Real campaign transitions, ID continuity, and deterministic P4 soak results."""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.day import DaySim
from tools.soak import campaign


class SoakTest(unittest.TestCase):
    def test_real_phases_and_ids_across_plan_rollover(self):
        tuning = load_contract()["tuning"]
        with self.assertRaises(BadInput):
            DaySim(tuning, {}, Streams(7), days=6)
        scenario = {"gather": {"hold": [{"id": "I7", "kind": "ca_loc", "fresh": 100}]}}
        sim = DaySim(tuning, scenario, Streams(7), days=10, repeat_plan=True)
        inputs = LiveInputs()
        previous_max = 0
        for day in range(1, 11):
            self.assertEqual((sim.day, sim.phase), (day, "gather"))
            self.assertEqual(sim.plan["dishes"], tuning["day_plan"][(day - 1) % 5]["dishes"])
            self.assertEqual(sim.snapshot()["hold"][0]["id"], f"I{day + 6}")
            schools = [int(f["id"][1:]) for f in sim.snapshot()["fish"]]
            self.assertGreater(min(schools), previous_max)
            previous_max = max(schools)
            for button, phase in [("interact", "quan"), (None, "shop"), ("shop_done", None)]:
                if button:
                    inputs.set(**{button: True})
                    inputs.set(**{button: False})
                events = sim.step(inputs.advance())
                if button is None:
                    while sim.phase == "quan":
                        sim.step(inputs.advance())
                if phase:
                    self.assertEqual(sim.phase, phase)
                else:
                    self.assertIn(("shop_end", {"reason": "done"}, {"day": day, "phase": "shop"}), events)
            self.assertEqual(sim.days_completed, day)
        self.assertTrue(sim.done)
        self.assertEqual(sim.reason, "days_complete")

    def test_seeded_gameplay_results_repeat(self):
        tuning = load_contract()["tuning"]
        runs = []
        for _ in range(2):
            results = []
            campaign(tuning, 7, 2, results)
            runs.append(results)
        self.assertEqual(runs[0], runs[1])
        self.assertEqual([row["day"] for row in runs[0]], [1, 2])
        self.assertGreater(runs[0][0]["earned"], 0)
        self.assertGreater(runs[0][1]["earned"], runs[0][0]["earned"])
