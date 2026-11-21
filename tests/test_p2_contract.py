"""AC-P2-01: contract v1.1 (số chuẩn, 6 nguyên liệu/món, day_plan, shop, monsters) và dải hợp lệ."""

import copy
import json
import unittest

from chonoi.contract import (DAYS, DEFAULT_PATH, FISH_KINDS, INGREDIENTS, NODE_KINDS, load_contract,
                             plan_ingredients, validate_tuning)
from chonoi.errors import BadInput


def manifest():
    with open(DEFAULT_PATH, encoding="utf-8") as f:
        return json.load(f)


def mutate(fn):
    t = copy.deepcopy(manifest()["tuning"])
    fn(t)
    return t


class TestStandardNumbers(unittest.TestCase):
    def setUp(self):
        self.m = manifest()
        self.t = self.m["tuning"]

    def test_manifest_v11(self):
        self.assertIn(self.m["contract_version"], ("1.2","1.3"))
        self.assertEqual(self.m["team_size"], 6)
        self.assertIn("net", self.m["extensions"])  # mở rộng net (haiquanng) đã bật
        load_contract()

    def test_gather_standard_numbers(self):
        g = self.t["gather"]
        self.assertEqual((g["duration_s"], g["oxygen_max_s"], g["hp_max"], g["hold_capacity"]), (180, 30, 3, 12))
        self.assertEqual(g["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        self.assertEqual([(n["id"], n["kind"], n["pos"]) for n in g["nodes"][4:]],
                         [("N5", "keo_neo", [76, 0]), ("N6", "keo_neo", [90, 0])])
        self.assertEqual((g["fish_initial"], g["fish_max"], g["fish_turn_ticks"], g["fish_spawn_ticks"]),
                         (8, 12, 120, 360))
        self.assertEqual(g["fish_x"], [4, 96])
        self.assertEqual(g["fish_spawn_x"], [15, 30, 45, 60, 75, 90])
        self.assertEqual(sum(g["fish_weights"].values()), 100)
        points = len(g["fish_spawn_x"]) * sum(len(v) for v in g["fish_spawn_depths"].values())
        self.assertEqual(points, 36)  # 36 cặp loài-vị trí

    def test_monsters_standard(self):
        m = self.t["gather"]["monsters"]
        self.assertEqual((m["invuln_ticks"], m["loss_ratio"]), (90, 0.5))
        self.assertEqual([(s["id"], s["from_day"], s["waypoints"]) for s in m["spawns"]],
                         [("M1", 1, [[60, 24], [64, 24]]), ("M2", 3, [[85, 18], [89, 18]])])
        self.assertEqual(m["species"]["ca_sau"]["depths"], [10, 30])

    def test_quan_layout_and_menu(self):
        q = self.t["quan"]
        self.assertEqual([s["id"] for s in q["stoves"]], ["B1", "B2"])
        self.assertEqual([s["id"] for s in q["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertEqual(len(self.t["menu"]), 6)
        used = {k for d in self.t["menu"].values() for k in d["recipe"]}
        self.assertEqual(used, set(INGREDIENTS))
        self.assertEqual(set(INGREDIENTS), set(NODE_KINDS) | set(FISH_KINDS))
        self.assertEqual(self.t["menu"]["lau_mam"]["price"], 200)

    def test_day_plan_matches_ticket(self):
        plan = self.t["day_plan"]
        self.assertEqual([p["day"] for p in plan], list(range(1, DAYS + 1)))
        self.assertEqual(plan[0]["ingredients"], {"bong_sung": 6, "ca_loc": 3})
        self.assertEqual(plan[2]["ingredients"], {"bong_dien_dien": 2, "bong_sung": 4, "ca_keo": 4, "ca_loc": 2})
        self.assertEqual(plan[3]["ingredients"],
                         {"bong_dien_dien": 1, "bong_sung": 2, "ca_keo": 1, "ca_linh": 2, "ca_loc": 2, "keo_neo": 1})
        self.assertEqual(plan[4]["ingredients"],
                         {"bong_dien_dien": 2, "ca_keo": 1, "ca_linh": 5, "ca_loc": 1, "keo_neo": 1})
        for p in plan:
            self.assertEqual(p["ingredients"], plan_ingredients(p["dishes"], self.t["menu"]))

    def test_shop_standard(self):
        s = self.t["shop"]
        self.assertEqual(s["max_ticks"], 600)
        self.assertEqual([(u["level"], u["price"], u["oxygen_max_s"]) for u in s["upgrades"]["oxygen"]],
                         [(1, 200, 45), (2, 400, 60)])
        self.assertEqual([(u["level"], u["price"], u["hp_max"]) for u in s["upgrades"]["hp"]],
                         [(1, 250, 4), (2, 500, 5)])


class TestV11Rejected(unittest.TestCase):
    def assertRejected(self, fn):
        with self.assertRaises(BadInput):
            validate_tuning(mutate(fn))

    def test_fish_keys(self):
        self.assertRejected(lambda t: t["gather"].update(fish_initial=[]))  # v1.0: danh sách
        self.assertRejected(lambda t: t["gather"].update(fish_initial=13))  # vượt fish_max
        self.assertRejected(lambda t: t["gather"].update(fish_initial=0))
        self.assertRejected(lambda t: t["gather"].pop("fish_speed"))
        self.assertRejected(lambda t: t["gather"].update(fish_x=[4, 101]))
        self.assertRejected(lambda t: t["gather"].update(fish_spawn_x=[15, 15]))
        self.assertRejected(lambda t: t["gather"]["fish_depths"].pop("ca_keo"))
        self.assertRejected(lambda t: t["gather"]["fish_spawn_depths"].update(ca_keo=[5]))  # ngoài dải loài
        self.assertRejected(lambda t: t["gather"]["fish_weights"].update(ca_loc=0))
        self.assertRejected(lambda t: t["gather"]["fish_yield"].pop("ca_keo"))

    def test_nodes_need_every_kind(self):
        self.assertRejected(lambda t: t["gather"].update(nodes=t["gather"]["nodes"][:4]))  # thiếu keo_neo
        self.assertRejected(lambda t: t["gather"]["nodes"][4].update(kind="rau"))

    def test_monsters(self):
        self.assertRejected(lambda t: t["gather"].pop("monsters"))
        self.assertRejected(lambda t: t["gather"]["monsters"].update(loss_ratio=1.5))
        self.assertRejected(lambda t: t["gather"]["monsters"]["spawns"][0].update(pos=[61, 24]))  # lệch waypoint đầu
        self.assertRejected(lambda t: t["gather"]["monsters"]["spawns"][0].update(waypoints=[[60, 5], [64, 5]],
                                                                                  pos=[60, 5]))  # ngoài dải độ sâu
        self.assertRejected(lambda t: t["gather"]["monsters"]["spawns"][1].update(from_day=6))
        self.assertRejected(lambda t: t["gather"]["monsters"]["spawns"][1].update(id="M1"))
        self.assertRejected(lambda t: t["gather"]["monsters"]["species"]["ca_sau"].update(exit_radius=5))

    def test_menu_needs_six_ingredients(self):
        self.assertRejected(lambda t: t["menu"].pop("lau_mam"))  # day_plan còn tham chiếu món đã xóa
        self.assertRejected(lambda t: t["menu"]["goi_bong_sung"].update(recipe={"rau": 1}))

    def test_day_plan(self):
        self.assertRejected(lambda t: t.pop("day_plan"))
        self.assertRejected(lambda t: t.update(day_plan=t["day_plan"][:4]))
        self.assertRejected(lambda t: t["day_plan"][0]["ingredients"].update(ca_loc=4))  # sai tổng
        self.assertRejected(lambda t: t["day_plan"][0]["dishes"].update(goi_bong_sung=4))  # đổi suất mà không tính lại
        self.assertRejected(lambda t: t["day_plan"][1].update(day=1))
        self.assertRejected(lambda t: t["day_plan"][0]["dishes"].update(mon_la=1))
        self.assertRejected(lambda t: t["day_plan"][0]["dishes"].update(goi_bong_sung=0))

    def test_shop(self):
        self.assertRejected(lambda t: t.pop("shop"))
        self.assertRejected(lambda t: t["shop"].update(max_ticks=0))
        self.assertRejected(lambda t: t["shop"]["upgrades"].pop("hp"))
        self.assertRejected(lambda t: t["shop"]["upgrades"]["oxygen"][1].update(level=3))
        self.assertRejected(lambda t: t["shop"]["upgrades"]["oxygen"][1].update(oxygen_max_s=45))  # không tăng
        self.assertRejected(lambda t: t["shop"]["upgrades"]["hp"][0].update(hp_max=3))  # không hơn cơ sở
        self.assertRejected(lambda t: t["shop"]["upgrades"]["hp"][0].update(price=0))

    def test_burn_s(self):
        validate_tuning(mutate(lambda t: t["quan"].update(burn_s=20)))  # mở rộng burn
        self.assertRejected(lambda t: t["quan"].update(burn_s=0))
        self.assertRejected(lambda t: t["quan"].update(burn_s="20"))

    def test_load_contract_rejects_old_version(self):
        import os
        import tempfile
        m = manifest()
        m["contract_version"] = "1.0"
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(m, f)
            with self.assertRaises(BadInput):
                load_contract(p)


if __name__ == "__main__":
    unittest.main()
