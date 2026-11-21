"""AC-P2-13: khối `day` của scenario (Test Contract v1.1, mục 4.3)."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.scenario import load_scenario
from helpers import Workdir, write_json

TUNING = load_contract()["tuning"]


def load(doc, mode="day"):
    with Workdir() as w:
        return load_scenario(write_json(w.path("s.json"), doc), mode, TUNING)


class TestShape(unittest.TestCase):
    """`load_scenario(.., "day", ..)` kiểm rồi trả nguyên scenario; mặc định do DaySim tự điền."""

    def test_no_file_gives_empty(self):
        self.assertEqual(load_scenario(None, "day", TUNING), {})

    def test_ticket_example_is_valid(self):
        r = load({"day": {"money": 200, "earned": 200},
                  "gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}})
        self.assertEqual((r["day"]["money"], r["day"]["earned"]), (200, 200))
        self.assertEqual(r["gather"]["hold"], ["ca_loc", "bong_sung", "bong_sung"])

    def test_single_blocks_are_valid(self):
        load({"gather": {"random_fish": False}})
        load({"quan": {"random_customers": False}})
        load({"day": {"reputation": 4.5, "upgrades": {"oxygen": 1, "hp": 0}}})


class TestMoney(unittest.TestCase):
    def test_money_must_not_exceed_earned(self):
        for day in ({"money": 201, "earned": 200}, {"money": 1, "earned": 0}):
            with self.subTest(day=day), self.assertRaises(BadInput):
                load({"day": day})

    def test_money_alone_needs_earned(self):
        with self.assertRaises(BadInput):
            load({"day": {"money": 50}})  # earned mặc định 0 < money: phải khai cả hai

    def test_earned_alone_ok_and_equal_ok(self):
        load({"day": {"earned": 80}})
        load({"day": {"money": 0, "earned": 0}})
        load({"day": {"money": 400, "earned": 400}})

    def test_bad_types(self):
        for day in ({"money": -1, "earned": 5}, {"money": 1.5, "earned": 5}, {"money": True, "earned": 5},
                    {"money": 0, "earned": "5"}, {"earned": -3}):
            with self.subTest(day=day), self.assertRaises(BadInput):
                load({"day": day})


class TestReputationAndUpgrades(unittest.TestCase):
    def test_reputation_range(self):
        for rep in (-0.1, 5.1, "3", True):
            with self.subTest(rep=rep), self.assertRaises(BadInput):
                load({"day": {"reputation": rep}})
        load({"day": {"reputation": 0}})
        load({"day": {"reputation": 5}})

    def test_upgrades(self):
        load({"day": {"upgrades": {"oxygen": 2, "hp": 2}}})
        for ups in ({"oxygen": 3}, {"hp": -1}, {"hp": 1.0}, {"hp": True}, {"weapon": 1}, [], {"oxygen": "1"}):
            with self.subTest(ups=ups), self.assertRaises(BadInput):
                load({"day": {"upgrades": ups}})

    def test_player_oxygen_checked_against_declared_upgrade(self):
        """gather.player.oxygen_ticks 2700 chỉ hợp lệ nếu day.upgrades có bình oxy cấp 1."""
        gather = {"gather": {"player": {"oxygen_ticks": 2700}}}
        with self.assertRaises(BadInput):
            load(gather)
        load({**gather, "day": {"upgrades": {"oxygen": 1}}})


class TestDayPlanOverride(unittest.TestCase):
    def test_valid_forms(self):
        entry = {"dishes": {"goi_bong_sung": 2, "lau_mam": 1}}
        load({"day": {"day_plan": [dict(entry, day=2)]}})  # mảng như tuning.day_plan
        load({"day": {"day_plan": {"2": entry}}})  # map theo Ngày

    def test_declared_ingredients_must_match(self):
        ok = {"day": 1, "dishes": {"ca_loc_nuong_trui": 1}, "ingredients": {"ca_loc": 1}}
        load({"day": {"day_plan": [ok]}})
        with self.assertRaises(BadInput):
            load({"day": {"day_plan": [dict(ok, ingredients={"ca_loc": 2})]}})

    def test_invalid_plans(self):
        cases = [
            [{"day": 6, "dishes": {"lau_mam": 1}}],
            [{"day": 0, "dishes": {"lau_mam": 1}}],
            [{"day": 1.0, "dishes": {"lau_mam": 1}}],
            [{"day": 1, "dishes": {"lau_mam": 1}}, {"day": 1, "dishes": {"lau_mam": 2}}],  # trùng Ngày
            [{"day": 1}],  # thiếu dishes
            [{"day": 1, "dishes": {}}],
            [{"day": 1, "dishes": {"mon_la": 1}}],
            [{"day": 1, "dishes": {"lau_mam": 0}}],
            "lau_mam",
        ]
        for plan in cases:
            with self.subTest(plan=plan), self.assertRaises(BadInput):
                load({"day": {"day_plan": plan}})


class TestForbiddenAndShape(unittest.TestCase):
    def test_quan_stock_and_reputation_forbidden_in_day(self):
        for key, val in (("stock", {"ca_loc": 1}), ("reputation", 3.0)):
            with self.subTest(key=key), self.assertRaises(BadInput):
                load({"quan": {key: val}})

    def test_quan_stock_and_reputation_still_valid_in_quan_mode(self):
        load({"quan": {"stock": {"ca_loc": 1}, "reputation": 2.0}}, mode="quan")

    def test_unknown_keys_and_blocks(self):
        for doc in ({"day": {"hello": 1}}, {"shop": {}}, {"day": []}, {"gather": {"zzz": 1}}, {"quan": {"zzz": 1}},
                    {"gather": []}):
            with self.subTest(doc=doc), self.assertRaises(BadInput):
                load(doc)

    def test_day_block_rejected_outside_day_mode(self):
        for mode in ("gather", "quan"):
            with self.subTest(mode=mode), self.assertRaises(BadInput):
                load({"day": {"money": 0, "earned": 0}}, mode=mode)

    def test_templates_are_validated_like_single_modes(self):
        with self.assertRaises(BadInput):
            load({"gather": {"hold": ["rau"]}})
        with self.assertRaises(BadInput):
            load({"quan": {"customers": [{"id": "C1", "table_id": "T9", "dish_id": "lau_mam"}]}})
        with self.assertRaises(BadInput):
            load({"gather": {"time_left_ticks": 0}})

    def test_new_kinds_accepted_in_gather_template(self):
        r = load({"gather": {"hold": ["ca_keo", "keo_neo"],
                             "nodes": [{"id": "N5", "kind": "keo_neo", "pos": [76, 0]}],
                             "fish": [{"id": "F1", "kind": "ca_keo", "pos": [30, 25]}]}})
        self.assertEqual(r["gather"]["hold"], ["ca_keo", "keo_neo"])


if __name__ == "__main__":
    unittest.main()
