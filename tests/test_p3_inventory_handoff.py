"""Boundary coverage across the real Gather, file adapter, Quan and Day implementations."""
import json
import unittest
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.inventory import read_inventory, write_inventory
from chonoi.runner import Session
from chonoi.scenario import load_scenario, validate_quan_against_inventory

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
        self.assertAlmostEqual(evening.snapshot()["stock"][1]["fresh"], 30, places=12)
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
            self.assertAlmostEqual(day.snapshot()["stock"][0]["fresh"], float(42 - Fraction(3, 240)), places=12)
            day.step(SHOP_DONE)

    def test_input_just_below_the_next_exact_boundary_spoils_on_tick_one(self):
        value = 30.004166666666666
        self.assertLess(Fraction(str(value)), 30 + Fraction(1, 240))
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": value}]
        evening = Session("quan", self.tuning, {"random_customers": False, "random_reservations": False},
                          1, inventory=stock)
        self.assertEqual([row["name"] for row in evening.step(IDLE)], ["spoiled"])
        self.assertLess(evening.snapshot()["stock"][0]["fresh"], 30)

    def test_only_ascii_numeric_suffix_advances_the_item_allocator(self):
        ids = IdAllocator()
        ids.reserve("I٩")
        ids.reserve("I10\n")
        ids.reserve("I3")
        self.assertEqual(ids.new("I"), "I4")

    def test_day_opening_rejects_conflicting_order_and_table_links(self):
        dish = "ca_loc_nuong_trui"
        order = {"id": "C1", "table_id": "T1", "dish_id": dish, "order_status": "assigned"}
        payload = {"order_id": "C1", "dish_id": dish}
        for block in [
            {"stoves": [{"id": "B1", "state": "ready", "dish": payload, "order_id": "C99"}]},
            {"hand": dict(payload, customer_id="C99")},
            {"hand": payload, "tables": [{"id": "T1", "customer_id": "C99"}]},
            {"hand": {"dish_id": dish}},
        ]:
            with self.subTest(block=block), self.assertRaises(BadInput):
                validate_quan_against_inventory(dict(block, customers=[order]), [], self.tuning)

    def test_day_opening_keeps_explicit_reservations_linked_to_reissued_items(self):
        dish = "ca_loc_nuong_trui"
        sc = {"day": {"day_plan": {str(n): {"dishes": {dish: 1}} for n in (1, 2)}},
              "gather": {"hold": [{"id": "I9", "kind": "ca_loc", "fresh": 90}], "time_left_ticks": 1},
              "quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": dish, "reserved": ["I9"]}],
                       "time_left_ticks": 1, "random_customers": False, "random_reservations": False}}
        day = Session("day", self.tuning, sc, 1, days=2)
        for expected in ("I9", "I10"):
            day.step(IDLE)
            self.assertEqual(day.snapshot()["customers"][0]["reserved"], [expected])
            day.step(IDLE)
            day.step(SHOP_DONE)
        self.assertEqual(sc["quan"]["customers"][0]["reserved"], ["I9"])

    def test_reservation_must_offer_a_dish_on_the_current_day_plan(self):
        booking = {"id": "R1", "table_id": "T1", "dish_id": "goi_bong_sung", "arrival_tick": 3}
        sc = {"day": {"day_plan": {"1": {"dishes": {"ca_loc_nuong_trui": 1}}}},
              "quan": {"reservations": [booking]}}
        with self.assertRaises(BadInput):
            Session("day", self.tuning, sc, 1)

    def test_external_decimal_below_30_stays_spoiled_when_copied_and_loaded(self):
        raw = '{"items":[{"id":"I1","kind":"ca_loc","fresh":29.999999999999999999}]}'
        with TemporaryDirectory() as temp:
            source, copied = Path(temp, "source.json"), Path(temp, "copied.json")
            source.write_text(raw)
            items = read_inventory(source, contract_version="1.3")
            write_inventory(copied, items)
            evening = Session("quan", self.tuning, {}, 1, inventory=read_inventory(copied, contract_version="1.3"))
            self.assertLess(evening.snapshot()["stock"][0]["fresh"], 30)
            self.assertEqual(evening.sim._available_stock(), {})
            self.assertFalse([e for e in evening.step(IDLE) if e["name"] == "spoiled"])
            source.write_text('{"gather":{"hold":' + raw.split(":", 1)[1][:-1] + '}}')
            morning = Session("gather", self.tuning, load_scenario(source, "gather", self.tuning), 1)
            self.assertLess(morning.snapshot()["hold"][0]["fresh"], 30)
            self.assertFalse([e for e in morning.step(IDLE) if e["name"] == "spoiled"])

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
