"""Lát D — vòng ngày (TICKET-02 mục 2): thứ tự event đổi pha, bàn giao kho, trạng thái xuyên Ngày, days_complete.

Dùng sim giả (stub) cùng giao diện chốt sẵn (step/snapshot/done/result) cho gather/quan/shop/DayState để
không phụ thuộc lát A/B/Q/S; một ca dùng GatherSim/QuanSim thật.
"""

import copy
import unittest

from fixtures.fresh import fresh_items, counts
from helpers import Workdir, read_jsonl, snapshots

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.runner import run
from chonoi.sim.day import DaySim, plan_for

IDLE = InputState((0.0, 0.0), {}, set())

# Kế hoạch D1–D5 theo bảng TICKET-02 mục 2 (dishes × số suất, ingredients tổng).
DAY_PLAN = [
    {"day": 1, "dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}, "ingredients": {"ca_loc": 3, "bong_sung": 6}},
    {"day": 2, "dishes": {"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2},
     "ingredients": {"ca_loc": 2, "ca_linh": 6, "bong_dien_dien": 2}},
    {"day": 3, "dishes": {"goi_bong_sung": 2, "canh_chua_ca_loc": 2, "ca_keo_nuong": 2},
     "ingredients": {"bong_sung": 4, "ca_loc": 2, "bong_dien_dien": 2, "ca_keo": 4}},
    {"day": 4, "dishes": {"lau_mam": 1, "ca_loc_nuong_trui": 2, "goi_bong_sung": 1},
     "ingredients": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1, "ca_loc": 2, "bong_sung": 2}},
    {"day": 5, "dishes": {"lau_mam": 1, "lau_ca_linh_dien_dien": 1, "ca_loc_nuong_trui": 1},
     "ingredients": {"ca_linh": 5, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 2, "ca_loc": 1}},
]


# 3 món mới theo TICKET-02 mục 1.3 (dùng khi contract trên main chưa lên v1.1).
NEW_DISHES = {
    "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
    "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
    "lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, "cook_s": 12, "price": 200},
}


def tuning_v11():
    t = copy.deepcopy(load_contract()["tuning"])
    t.pop("reservations", None)  # Isolate the core phase/event ordering.
    for did, dish in NEW_DISHES.items():
        t["menu"].setdefault(did, dish)
    t.setdefault("day_plan", DAY_PLAN)
    return t


# ---------- stub cùng giao diện chốt sẵn ----------

class Stub:
    phase = None
    end_event = None

    def __init__(self, length, **kw):
        self.length, self.steps, self.kw = length, 0, kw
        self.time_left_ticks = length
        self.done = False

    def step(self, inp):
        self.steps += 1
        self.time_left_ticks = self.length - self.steps
        if self.steps >= self.length:
            self.done = True
            return [(self.end_event, self.end_data())]
        return []

    def snapshot(self):
        return {"stub_phase": self.phase, "stub_steps": self.steps}


class StubGather(Stub):
    phase, end_event = "gather", "gather_end"

    def __init__(self, length, items, reason="docked", **kw):
        super().__init__(length, **kw)
        self.items, self.reason = items, reason

    def end_data(self):
        return {"reason": self.reason, "inventory": {"items": dict(self.items)}}

    @property
    def result(self):
        return {"reason": self.reason, "inventory": {"items": dict(self.items)}}


class StubQuan(Stub):
    phase, end_event = "quan", "quan_end"
    income = 50

    def __init__(self, length, **kw):
        super().__init__(length, **kw)
        self.money, self.earned, self.reputation = kw["money"], kw["earned"], kw["reputation"]

    def step(self, inp):
        evs = super().step(inp)
        if self.done:
            self.money += self.income
            self.earned += self.income
        return evs

    def end_data(self):
        return {"reason": "time"}

    @property
    def result(self):
        left = {k: v - 1 for k, v in self.kw["inventory"].items() if v > 1}
        return {"money": self.money, "earned": self.earned, "reputation": self.reputation, "stock": left}


class StubShop(Stub):
    phase, end_event = "shop", "shop_end"

    def __init__(self, length, buy=None, **kw):
        super().__init__(length, **kw)
        self.money, self.earned, self.upgrades = kw["money"], kw["earned"], dict(kw["upgrades"])
        self.buy = buy

    def step(self, inp):
        if self.steps == 0 and self.buy:
            self.upgrades[self.buy] = self.upgrades.get(self.buy, 0) + 1
            self.money -= 10
        return super().step(inp)

    def end_data(self):
        return {"reason": "done"}

    @property
    def result(self):
        return {"money": self.money, "upgrades": dict(self.upgrades)}


class StubState:
    def __init__(self, tuning, block):
        self.money, self.earned = block.get("money", 0), block.get("earned", 0)
        self.reputation = block.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades, self.active_upgrades, self.day = dict(block.get("upgrades", {})), {}, 1
        self.calls = []

    def apply_quan_result(self, r):
        self.calls.append("quan")
        self.money, self.earned, self.reputation = r["money"], r["earned"], r["reputation"]

    def apply_shop_result(self, r):
        self.calls.append("shop")
        self.money, self.upgrades = r["money"], dict(r["upgrades"])

    def start_next_day(self):
        self.calls.append("next")
        self.active_upgrades = dict(self.upgrades)
        self.day += 1
        return {"oxygen_max_ticks": 1800, "hp_max": 3}


class Rig:
    """Dựng DaySim với stub; ghi lại mọi sim đã tạo để kiểm tham số bàn giao."""

    def __init__(self, days=1, g=3, q=4, s=2, items=None, reason="docked", buy=None, scenario=None):
        self.made = {"gather": [], "quan": [], "shop": []}
        items = {"ca_loc": 2, "bong_sung": 3} if items is None else items

        def gather(tuning, sc, streams, ids, **kw):
            sim = StubGather(g, items, reason, scenario=sc, **kw)
            self.made["gather"].append(sim)
            return sim

        def quan(tuning, sc, streams, ids, **kw):
            sim = StubQuan(q, scenario=sc, **kw)
            self.made["quan"].append(sim)
            return sim

        def shop(tuning, **kw):
            sim = StubShop(s, buy=buy, **kw)
            self.made["shop"].append(sim)
            return sim

        self.day_len = g + q + s
        self.sim = DaySim(tuning_v11(), scenario or {}, Streams(1), IdAllocator(), days=days,
                          factories={"gather": gather, "quan": quan, "shop": shop, "state": StubState})

    def run(self, ticks=10_000, snapshot_every=1):
        with Workdir() as w:
            out = w.path("day.jsonl")
            run("day", self.sim.tuning, {}, 1, [], ticks, out, snapshot_every, sim=self.sim)
            return read_jsonl(out)


def evs(rows):
    return [r for r in rows if r["type"] == "event"]


def seq(rows):
    return [(r["tick"], r["phase"], r["name"]) for r in evs(rows)]


class TestPhaseOrder(unittest.TestCase):
    def test_day_one_start_events_at_tick_zero_before_snapshot(self):
        rows = Rig().run()
        self.assertEqual([(r["type"], r.get("name")) for r in rows[:4]],
                         [("event", "day_start"), ("event", "day_plan"), ("event", "phase_start"), ("snapshot", None)])
        first = evs(rows)[:3]
        self.assertTrue(all(e["tick"] == 0 and e["day"] == 1 and e["phase"] == "gather" for e in first))
        self.assertEqual(first[0]["data"], {})
        # ví dụ nguyên văn TICKET-02 mục 4.4 (thứ tự khóa của vỏ event)
        self.assertEqual(list(first[1]), ["type", "tick", "phase", "day", "name", "data"])
        self.assertEqual(first[1]["data"], {"dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
                                            "ingredients": {"bong_sung": 6, "ca_loc": 3}})
        self.assertEqual(first[2]["data"], {})

    def test_phase_switch_same_tick_and_new_phase_runs_next_step(self):
        rig = Rig(g=3, q=4, s=2)
        rows = rig.run()
        self.assertEqual(seq(rows), [
            (0, "gather", "day_start"), (0, "gather", "day_plan"), (0, "gather", "phase_start"),
            (3, "gather", "gather_end"), (3, "quan", "phase_start"),
            (7, "quan", "quan_end"), (7, "shop", "phase_start"),
            (9, "shop", "shop_end"),
        ])
        # quán dựng ở bước 3 nhưng chạy gameplay từ bước sau: đúng 4 bước cho q = 4
        self.assertEqual(rig.made["quan"][0].steps, 4)
        snaps = {r["tick"]: r for r in snapshots(rows)}
        self.assertEqual((snaps[3]["phase"], snaps[3]["phase_tick"]), ("quan", 0))
        self.assertEqual((snaps[4]["phase"], snaps[4]["phase_tick"]), ("quan", 1))
        self.assertEqual(snaps[9]["sim_tick"], 9)

    def test_end_row_days_complete(self):
        rows = Rig().run()
        end = rows[-1]
        self.assertEqual((end["type"], end["mode"], end["state"], end["reason"], end["days_completed"], end["ticks"]),
                         ("end", "day", "finished", "days_complete", 1, 9))

    def test_tick_limit_mid_day(self):
        rows = Rig().run(ticks=5)
        end = rows[-1]
        self.assertEqual((end["reason"], end["state"], end["days_completed"]), ("tick_limit", "playing", 0))

    def test_every_event_envelope_has_day(self):
        rows = Rig(days=2).run()
        self.assertTrue(all("day" in e for e in evs(rows)))
        self.assertEqual({e["day"] for e in evs(rows) if e["name"] == "shop_end"}, {1, 2})


class TestHandoff(unittest.TestCase):
    def test_inventory_and_plan_handed_to_quan_in_memory(self):
        rig = Rig(items={"ca_loc": 2, "bong_sung": 3})
        rig.run()
        q = rig.made["quan"][0].kw
        self.assertEqual(q["inventory"], {"ca_loc": 2, "bong_sung": 3})
        self.assertEqual(sorted(q["menu_ids"]), ["ca_loc_nuong_trui", "goi_bong_sung"])
        self.assertEqual((q["money"], q["earned"]), (0, 0))

    def test_fainted_still_opens_quan_with_empty_stock(self):
        rig = Rig(items={}, reason="fainted")
        rows = rig.run()
        self.assertIn((3, "quan", "phase_start"), seq(rows))
        self.assertEqual(rig.made["quan"][0].kw["inventory"], {})

    def test_shop_gets_money_upgrades_and_leftover_stock(self):
        rig = Rig(items={"ca_loc": 2, "bong_sung": 3})
        rig.run()
        shop = rig.made["shop"][0]
        self.assertEqual((shop.kw["money"], shop.kw["earned"]), (StubQuan.income, StubQuan.income))
        self.assertEqual(shop.kw["stock"], {"ca_loc": 1, "bong_sung": 2})
        self.assertEqual(rig.sim.state.calls, ["quan", "shop"])


class TestMultiDay(unittest.TestCase):
    def test_three_days_order_and_carry_over(self):
        rig = Rig(days=3, buy="oxygen")
        rows = rig.run()
        L = rig.day_len
        starts = [(e["tick"], e["day"]) for e in evs(rows) if e["name"] == "day_start"]
        self.assertEqual(starts, [(0, 1), (L, 2), (2 * L, 3)])
        # Ngày 2 bắt đầu cùng tick shop_end của Ngày 1: shop_end -> day_start -> day_plan -> phase_start(gather)
        at = [(e["day"], e["name"]) for e in evs(rows) if e["tick"] == L]
        self.assertEqual(at, [(1, "shop_end"), (2, "day_start"), (2, "day_plan"), (2, "phase_start")])
        self.assertEqual(evs(rows)[[e["tick"] for e in evs(rows)].index(L) + 2]["data"], plan_for(tuning_v11(), None, 2))
        # cấp mua ở Ngày d chỉ có hiệu lực từ Ngày d+1
        g = rig.made["gather"]
        self.assertEqual([x.kw["day"] for x in g], [1, 2, 3])
        self.assertEqual([x.kw["active_upgrades"] for x in g], [{}, {"oxygen": 1}, {"oxygen": 2}])
        # tiền giữ qua Ngày: +50 mỗi quán, −10 mỗi lần mua
        self.assertEqual([x.kw["money"] for x in rig.made["quan"]], [0, 40, 80])
        end = rows[-1]
        self.assertEqual((end["reason"], end["days_completed"], end["money"], end["earned"]), ("days_complete", 3, 120, 150))
        self.assertEqual(rig.sim.state.calls, ["quan", "shop", "next"] * 2 + ["quan", "shop"])

    def test_scenario_gather_quan_blocks_are_template_every_day(self):
        """TICKET-02 mục 4.3: `day` nhận `gather` và `quan` làm mẫu khởi tạo mỗi Ngày (bản sao riêng)."""
        rig = Rig(days=2, scenario={"gather": {"hold": ["ca_loc"]}, "quan": {"random_customers": False}})
        rig.run()
        g = [x.kw["scenario"] for x in rig.made["gather"]]
        self.assertEqual(g, [{"hold": ["ca_loc"]}] * 2)
        self.assertIsNot(g[0], g[1])
        self.assertEqual([x.kw["scenario"] for x in rig.made["quan"]], [{"random_customers": False}] * 2)

    def test_day_plan_events_d1_to_d5(self):
        """--days 5 công bố đúng kế hoạch D1–D5 (TICKET-02 mục 2)."""
        rows = Rig(days=5).run()
        plans = [(e["day"], e["data"]) for e in evs(rows) if e["name"] == "day_plan"]
        self.assertEqual([d for d, _ in plans], [1, 2, 3, 4, 5])
        for (d, data), want in zip(plans, DAY_PLAN):
            self.assertEqual(data["dishes"], want["dishes"])
            self.assertEqual(data["ingredients"], want["ingredients"])
        self.assertEqual((rows[-1]["reason"], rows[-1]["days_completed"]), ("days_complete", 5))

    def test_snapshot_day_fields_every_phase(self):
        rows = Rig(days=2, buy="hp").run()
        for s in snapshots(rows):
            self.assertEqual(s["mode"], "day")
            for k in ("day", "day_plan", "upgrades", "active_upgrades"):
                self.assertIn(k, s)
        snaps = {r["tick"]: r for r in snapshots(rows)}
        self.assertEqual(snaps[8]["phase"], "shop")
        self.assertEqual(snaps[8]["upgrades"], {"hp": 1})  # cấp vừa mua hiện ngay trong Shop
        self.assertEqual(snaps[8]["active_upgrades"], {})  # nhưng chưa có hiệu lực
        self.assertEqual((snaps[9]["day"], snaps[9]["active_upgrades"]), (2, {"hp": 1}))


class TestPlanAndArgs(unittest.TestCase):
    def test_days_range(self):
        for bad in (0, 6, True, "2"):
            with self.assertRaises(BadInput):
                Rig(days=bad)

    def test_plan_ingredients_computed_when_missing_and_scenario_override(self):
        t = tuning_v11()
        t["day_plan"] = [{"day": 1, "dishes": {"goi_bong_sung": 2, "ca_loc_nuong_trui": 1}}]
        self.assertEqual(plan_for(t, None, 1)["ingredients"], {"bong_sung": 4, "ca_loc": 1})
        over = {"day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 1}, "ingredients": {"ca_loc": 1}}]}
        self.assertEqual(plan_for(t, over, 1)["dishes"], {"ca_loc_nuong_trui": 1})
        by_day = {"day_plan": {"1": {"dishes": {"goi_bong_sung": 1}}}}
        self.assertEqual(plan_for(t, by_day, 1), {"dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 2}})
        with self.assertRaises(BadInput):
            plan_for(t, None, 2)

    def test_declared_ingredients_mismatch_is_bad_input(self):
        t = tuning_v11()
        bad = {"day_plan": {"1": {"dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 3}}}}
        with self.assertRaises(BadInput):
            plan_for(t, bad, 1)
        with self.assertRaises(BadInput):
            plan_for(t, {"day_plan": {"1": {"dishes": {"pho": 1}}}}, 1)


class TestRealGatherQuan(unittest.TestCase):
    """GatherSim/QuanSim thật + Shop/DayState giả: bàn giao kho thật, chạy lại cùng seed giống từng byte."""

    def build(self):
        made = {}

        def shop(tuning, **kw):
            made["shop"] = StubShop(2, **kw)
            return made["shop"]

        scenario = {"gather": {"hold": fresh_items(["ca_loc", "bong_sung", "bong_sung"]), "time_left_ticks": 5},
                    "quan": {"time_left_ticks": 5}}
        return DaySim(tuning_v11(), scenario, Streams(42), IdAllocator(), days=1,
                      factories={"shop": shop, "state": StubState}), made

    def test_real_sims_full_day(self):
        outs = []
        for _ in range(2):
            sim, made = self.build()
            with Workdir() as w:
                out = w.path("d.jsonl")
                run("day", sim.tuning, {}, 42, [], 100, out, 1, sim=sim)
                with open(out, "rb") as f:
                    outs.append(f.read())
                rows = read_jsonl(out)
        self.assertEqual(outs[0], outs[1])
        self.assertEqual([(t, n) for t, _, n in seq(rows)],
                         [(0, "day_start"), (0, "day_plan"), (0, "phase_start"), (5, "gather_end"),
                          (5, "phase_start"), (10, "quan_end"), (10, "phase_start"), (12, "shop_end")])
        snaps = {r["tick"]: r for r in snapshots(rows)}
        self.assertEqual(counts(snaps[5]["stock"]), {"bong_sung": 2, "ca_loc": 1})  # kho bàn giao trong bộ nhớ
        self.assertEqual(counts(made["shop"].kw["stock"]), {"bong_sung": 2, "ca_loc": 1})
        self.assertEqual((rows[-1]["reason"], rows[-1]["days_completed"]), ("days_complete", 1))


if __name__ == "__main__":
    unittest.main()
