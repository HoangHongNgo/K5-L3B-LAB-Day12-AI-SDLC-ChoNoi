"""Boundary coverage across the real Gather, file adapter, Quan and Day implementations."""
import json
import unittest
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputState
from chonoi.inventory import read_inventory
from chonoi.runner import Session
from chonoi.scenario import load_scenario

IDLE = InputState((0, 0), {}, set())
INTERACT = InputState((0, 0), {"interact": True}, {"interact"})
SHOP_DONE = InputState((0, 0), {"shop_done": True}, {"shop_done"})


class FreshHandoff(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_new_pickup_starts_fresh_and_spoiled_events_honor_numeric_ids(self):
        old = [{"id": iid, "kind": "ca_loc", "fresh": 30} for iid in ["I10", "I2"]]
        node = self.tuning["gather"]["nodes"][0]
        morning = Session("gather", self.tuning, {"hold": old, "player": {"pos": node["pos"]},
                          "monsters": [], "random_fish": False}, 1)
        rows = morning.step(INTERACT)
        self.assertEqual([(r["name"], r["data"].get("item_id")) for r in rows],
                         [("spoiled", "I2"), ("spoiled", "I10"), ("gather", None)])
        self.assertEqual(morning.snapshot()["hold"][-1], {"id": "I11", "kind": node["kind"], "fresh": 100})
        self.assertEqual(morning.step(IDLE), [])
        self.assertEqual(morning.snapshot()["hold"][-1]["fresh"], float(100 - Fraction(1, 120)))

    def test_file_preserves_exact_spoil_tick_and_writes_once_after_docking(self):
        stock = [{"id": "I10", "kind": "ca_loc", "fresh": 30.025}, {"id": "I2", "kind": "ca_linh", "fresh": 0}]
        morning = Session("gather", self.tuning, {"hold": stock}, 1)
        with TemporaryDirectory() as temp:
            file = Path(temp, "inventory.json")
            file.write_text("existing")
            morning.write_inventory_if_done(file)
            self.assertEqual(file.read_text(), "existing")
            end = next(r for r in morning.step(INTERACT) if r["name"] == "gather_end")
            morning.write_inventory_if_done(file)
            items = read_inventory(file, contract_version="1.3")
            self.assertEqual(items, end["data"]["inventory"]["items"])
            self.assertEqual([item["id"] for item in items], ["I2", "I10"])
            file.write_text("replaced by caller")
            morning.write_inventory_if_done(file)
            self.assertEqual(file.read_text(), "replaced by caller")

        evening = Session("quan", self.tuning, {"random_customers": False, "random_reservations": False}, 1,
                          inventory=items)
        self.assertEqual(evening.snapshot()["stock"], items)
        for _ in range(4):
            self.assertEqual(evening.step(IDLE), [])
        self.assertEqual(evening.snapshot()["stock"][1]["fresh"], 30)
        self.assertEqual([r["data"]["item_id"] for r in evening.step(IDLE) if r["name"] == "spoiled"], ["I10"])

    def test_ids_and_freshness_across_two_real_days(self):
        item = {"id": "I19", "kind": "ca_loc", "fresh": 42}
        sc = {"gather": {"hold": [item], "time_left_ticks": 1},
              "quan": {"time_left_ticks": 1, "random_customers": False, "random_reservations": False}}
        day = Session("day", self.tuning, sc, 8, days=2)
        for iid in ("I19", "I20"):
            self.assertEqual(day.snapshot()["hold"], [dict(item, id=iid)])
            events = day.step(IDLE)
            handoff = next(r["data"]["inventory"]["items"] for r in events if r["name"] == "gather_end")
            self.assertEqual(day.snapshot()["stock"], handoff)
            self.assertEqual(handoff[0]["fresh"], float(42 - Fraction(1, 120)))
            day.step(IDLE)
            self.assertEqual(day.snapshot()["stock"][0]["fresh"], float(42 - Fraction(3, 240)))
            day.step(SHOP_DONE)

    def test_count_files_and_legacy_scenarios_fail_on_v12_and_v13(self):
        with TemporaryDirectory() as temp:
            path = Path(temp, "input.json")
            path.write_text(json.dumps({"items": {"ca_loc": 1}}))
            for version in ("1.2", "1.3"):
                with self.subTest(version=version), self.assertRaises(BadInput):
                    read_inventory(path, contract_version=version)
            for mode, block in (("gather", {"hold": ["ca_loc"]}), ("quan", {"stock": {"ca_loc": 1}})):
                path.write_text(json.dumps({mode: block}))
                with self.subTest(mode=mode), self.assertRaises(BadInput):
                    load_scenario(path, mode, self.tuning)
