"""Lát D Phase 3 — bàn giao kho cá thể trong `day` (TICKET-03 mục 1, Contract v1.2 › Scenario).

- Bàn giao trong cùng tick đổi pha, nguyên id/kind/fresh, không hao thêm; quán chạy từ bước sau.
- Hàng thô ở Shop không hao tươi; Shop nhận kho dư dạng cá thể.
- Id `I…` tăng xuyên pha và Ngày; Ngày kế cấp id mới cho mẫu `gather.hold` theo thứ tự mảng.
"""

import unittest
from fractions import Fraction

from helpers import Workdir, read_jsonl, snapshots
from test_p2_day import StubGather, StubQuan, StubShop, StubState, evs, tuning_v11

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.runner import run
from chonoi.sim.day import DaySim

ITEMS = [{"id": "I1", "kind": "ca_loc", "fresh": 97.5}, {"id": "I2", "kind": "bong_sung", "fresh": 31},
         {"id": "I3", "kind": "bong_sung", "fresh": 100}]


class PickingGather(StubGather):
    """Gather giả: mỗi Ngày 'nhặt' thêm một cá thể qua IdAllocator chung (như gather thật cấp I…)."""

    def __init__(self, length, ids, scenario, **kw):
        hold = [dict(it) for it in scenario.get("hold", [])]
        hold.append({"id": ids.new("I"), "kind": "ca_linh", "fresh": 100})
        super().__init__(length, hold, scenario=scenario, **kw)
        self.hold = hold

    def end_data(self):
        return {"reason": "docked", "inventory": {"items": [dict(it) for it in self.items]}}

    @property
    def result(self):
        return {"reason": "docked", "inventory": {"items": [dict(it) for it in self.items]}}


class ItemGather(StubGather):
    """Gather giả trả kho cá thể (schema v1.2)."""

    def end_data(self):
        return {"reason": "docked", "inventory": {"items": [dict(it) for it in self.items]}}

    @property
    def result(self):
        return {"reason": "docked", "inventory": {"items": [dict(it) for it in self.items]}}


class ItemQuan(StubQuan):
    """Quán giả trả kho dư dạng cá thể (đảo thứ tự để kiểm Shop tự sắp theo id)."""

    @property
    def result(self):
        return {"money": self.money, "earned": self.earned, "reputation": self.reputation,
                "stock": [dict(it) for it in reversed(self.kw["inventory"])]}


def run_day(sim, ticks=10_000):
    with Workdir() as w:
        out = w.path("d.jsonl")
        run("day", sim.tuning, {}, 1, [], ticks, out, 1, sim=sim)
        return read_jsonl(out)


class TestItemHandoff(unittest.TestCase):
    def build(self, quan_factory=None, shop_factory=None, items=ITEMS, days=1):
        made = {"gather": [], "quan": [], "shop": []}

        def gather(tuning, sc, streams, ids, **kw):
            g = ItemGather(3, [dict(it) for it in items])
            made["gather"].append(g)
            return g

        def quan(tuning, sc, streams, ids, **kw):
            q = ItemQuan(4, scenario=sc, **kw)
            made["quan"].append(q)
            return q

        def shop(tuning, **kw):
            s = StubShop(2, **kw)
            made["shop"].append(s)
            return s

        f = {"gather": gather, "state": StubState, "quan": quan_factory or quan, "shop": shop_factory or shop}
        sim = DaySim(tuning_v11(), {"quan": {"random_customers": False}}, Streams(1), IdAllocator(), days=days,
                     factories=f)
        return sim, made

    def test_items_handed_to_quan_same_tick_unchanged(self):
        sim, made = self.build()
        rows = run_day(sim)
        names = [(e["tick"], e["name"]) for e in evs(rows)]
        self.assertIn((3, "gather_end"), names)
        self.assertEqual(names[names.index((3, "gather_end")) + 1], (3, "phase_start"))
        inv = made["quan"][0].kw["inventory"]
        self.assertEqual(inv, ITEMS)  # nguyên id, kind, fresh — không hao thêm lúc bàn giao
        self.assertIsNot(inv, made["gather"][0].items)  # bản sao, không dùng chung đối tượng

    def test_real_quan_snapshot_at_handoff_tick_has_exact_items_then_decays(self):
        from chonoi.sim.quan import QuanSim

        def quan(tuning, sc, streams, ids, **kw):
            return QuanSim(tuning, sc, streams, ids, **kw)

        sim, _ = self.build(quan_factory=quan)
        rows = run_day(sim, ticks=5)
        snaps = {r["tick"]: r for r in snapshots(rows)}
        self.assertEqual((snaps[3]["phase"], snaps[3]["phase_tick"]), ("quan", 0))
        self.assertEqual([(it["id"], it["kind"], it["fresh"]) for it in snaps[3]["stock"]],
                         [(it["id"], it["kind"], it["fresh"]) for it in ITEMS])
        # quán chạy từ bước sau: hao 0.25/s = 1/240 mỗi tick ở kho quán
        after = {it["id"]: it["fresh"] for it in snaps[4]["stock"]}
        self.assertAlmostEqual(after["I1"], float(Fraction("97.5") - Fraction(1, 240)), delta=0.01)
        self.assertLess(after["I1"], 97.5)

    def test_shop_gets_item_stock_and_raw_goods_do_not_decay(self):
        from chonoi.sim.shop import ShopSim

        def quan(tuning, sc, streams, ids, **kw):
            return ItemQuan(4, scenario=sc, **kw)

        made = {}

        def shop(tuning, **kw):
            made["shop"] = ShopSim(tuning, **kw)
            return made["shop"]

        sim, _ = self.build(quan_factory=quan, shop_factory=shop)
        rows = run_day(sim, ticks=7 + 30)
        snaps = {r["tick"]: r for r in snapshots(rows)}
        self.assertEqual(snaps[7]["phase"], "shop")
        self.assertEqual(snaps[7]["stock"], ITEMS)  # sắp theo id
        self.assertEqual(snaps[37]["stock"], ITEMS)  # 30 tick ở Shop: không hao tươi


class TestIdsAcrossDays(unittest.TestCase):
    def test_template_hold_gets_new_ids_each_next_day_in_array_order(self):
        made = []

        def gather(tuning, sc, streams, ids, **kw):
            g = PickingGather(3, ids, sc, **kw)
            made.append(g)
            return g

        def quan(tuning, sc, streams, ids, **kw):
            return ItemQuan(2, scenario=sc, **kw)

        def shop(tuning, **kw):
            return StubShop(1, **kw)

        hold = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 40}]
        sim = DaySim(tuning_v11(), {"gather": {"hold": hold}}, Streams(1), IdAllocator(), days=3,
                     factories={"gather": gather, "quan": quan, "shop": shop, "state": StubState})
        run_day(sim)
        holds = [[(it["id"], it["kind"], it["fresh"]) for it in g.hold] for g in made]
        self.assertEqual(holds, [
            [("I1", "ca_loc", 100), ("I2", "bong_sung", 40), ("I3", "ca_linh", 100)],  # Ngày 1 giữ id mẫu
            [("I4", "ca_loc", 100), ("I5", "bong_sung", 40), ("I6", "ca_linh", 100)],  # id mới, kind/fresh mẫu
            [("I7", "ca_loc", 100), ("I8", "bong_sung", 40), ("I9", "ca_linh", 100)],
        ])
        self.assertEqual(hold[0]["id"], "I1")  # mẫu trong scenario không bị sửa


if __name__ == "__main__":
    unittest.main()
