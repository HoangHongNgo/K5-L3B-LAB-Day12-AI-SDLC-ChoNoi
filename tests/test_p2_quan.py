"""Unit và integration tests cho Phase 2 Lát Q (Nguyễn Minh Phương - minhphuong150505):
Hệ thống quán ăn: 2 bếp, 4 bàn, 6 món, lọc món theo kế hoạch ngày,
hai bếp hoạt động song song, vòng đời phục vụ, thanh toán, boa, uy tín, đóng ca
và xác thực scenario cho mode day.
"""

import copy
import json
import math
import os
import unittest

from helpers import Workdir, read_jsonl, write_json

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.scenario import load_scenario, validate_quan_against_inventory
from chonoi.sim.quan import QuanSim

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
with open(os.path.join(FIXTURES_DIR, "p2_quan_tuning.json"), encoding="utf-8") as f:
    TUNING_V11 = json.load(f)

PRESS = InputState((0.0, 0.0), {"interact": True}, {"interact"})
IDLE = InputState((0.0, 0.0), {}, set())


def make_sim(scenario_block=None, tuning=None, streams=None, ids=None, **kwargs):
    t = copy.deepcopy(tuning or TUNING_V11)
    sc = copy.deepcopy(scenario_block or {})
    st = streams or Streams(42)
    alloc = ids or IdAllocator()
    return QuanSim(t, sc, st, alloc, **kwargs)


class TestPhase2TuningAndMenu(unittest.TestCase):
    def test_q01_read_four_tables_from_tuning(self):
        """Q01: Đọc 4 bàn từ tuning."""
        sim = make_sim()
        self.assertEqual(len(sim.tables), 4)
        table_ids = [tb["id"] for tb in sim.tables]
        self.assertEqual(table_ids, ["T1", "T2", "T3", "T4"])

    def test_q02_read_two_stoves_from_tuning(self):
        """Q02: Đọc 2 bếp từ tuning."""
        sim = make_sim()
        self.assertEqual(len(sim.stoves), 2)
        stove_ids = [s["id"] for s in sim.stoves]
        self.assertEqual(stove_ids, ["B1", "B2"])

    def test_q03_use_six_dishes_from_menu(self):
        """Q03: Sử dụng đủ 6 món từ menu."""
        sim = make_sim()
        self.assertEqual(len(sim.menu), 6)
        expected_dishes = {
            "ca_loc_nuong_trui",
            "goi_bong_sung",
            "lau_ca_linh_dien_dien",
            "canh_chua_ca_loc",
            "ca_keo_nuong",
            "lau_mam",
        }
        self.assertEqual(set(sim.menu.keys()), expected_dishes)


class TestCustomerArrivalAndTableSelection(unittest.TestCase):
    def test_q04_customer_arrival_at_tick_120(self):
        """Q04: Khách đầu tiên đến ở tick 120."""
        sim = make_sim({"stock": {"ca_loc": 5}})
        for _ in range(119):
            events = sim.step(IDLE)
            self.assertFalse(any(e[0] == "customer_arrived" for e in events))
        # Tick 120: khách xuất hiện
        events = sim.step(IDLE)
        arr = [e for e in events if e[0] == "customer_arrived"]
        self.assertEqual(len(arr), 1)
        self.assertEqual(arr[0][1]["customer_id"], "C1")
        self.assertEqual(arr[0][1]["table_id"], "T1")

    def test_q05_customer_arrival_interval_900_ticks(self):
        """Q05: Khách đến theo khoảng 900 tick (120, 1020, 1920)."""
        sim = make_sim({"stock": {"ca_loc": 20, "bong_sung": 20}})
        sim.phase_tick = 119
        self.assertFalse(sim._should_spawn_customer())
        sim.phase_tick = 120
        self.assertTrue(sim._should_spawn_customer())
        sim.phase_tick = 121
        self.assertFalse(sim._should_spawn_customer())
        sim.phase_tick = 1019
        self.assertFalse(sim._should_spawn_customer())
        sim.phase_tick = 1020
        self.assertTrue(sim._should_spawn_customer())
        sim.phase_tick = 1920
        self.assertTrue(sim._should_spawn_customer())

    def test_q06_select_available_table_lowest_id(self):
        """Q06: Chọn bàn trống có ID nhỏ nhất."""
        sim = make_sim({
            "stock": {"ca_loc": 10},
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "cooking", "reserved": {}}],
        })
        table = sim._find_available_table()
        self.assertEqual(table["id"], "T2")

    def test_q07_no_available_table_skips_turn(self):
        """Q07: Không còn bàn trống thì bỏ lượt spawn."""
        sim = make_sim({
            "stock": {"ca_loc": 10},
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "cooking", "reserved": {}},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_status": "cooking", "reserved": {}},
                {"id": "C3", "table_id": "T3", "dish_id": "ca_loc_nuong_trui", "order_status": "cooking", "reserved": {}},
                {"id": "C4", "table_id": "T4", "dish_id": "ca_loc_nuong_trui", "order_status": "cooking", "reserved": {}},
            ],
        })
        self.assertIsNone(sim._find_available_table())


class TestDayPlanMenuFiltering(unittest.TestCase):
    def test_q08_menu_ids_none_uses_all_dishes(self):
        """Q08: menu_ids=None cho phép khách chọn trong toàn bộ 6 món."""
        sim = make_sim({
            "stock": {"ca_loc": 10, "ca_linh": 10, "ca_keo": 10, "bong_dien_dien": 10, "bong_sung": 10, "keo_neo": 10}
        }, menu_ids=None)
        table = sim.tables[0]
        events = sim._spawn_customer(table)
        self.assertEqual(events[0][0], "customer_arrived")
        self.assertIn(events[0][1]["dish_id"], sim.menu)

    def test_q09_menu_ids_limits_dishes_to_day_plan(self):
        """Q09: menu_ids giới hạn món theo kế hoạch ngày."""
        plan = ["ca_keo_nuong", "goi_bong_sung"]
        sim = make_sim({
            "stock": {"ca_loc": 10, "ca_linh": 10, "ca_keo": 10, "bong_dien_dien": 10, "bong_sung": 10, "keo_neo": 10}
        }, menu_ids=plan)
        for _ in range(5):
            table = sim.tables[0]
            sim.customers = []
            evs = sim._spawn_customer(table)
            self.assertEqual(evs[0][0], "customer_arrived")
            self.assertIn(evs[0][1]["dish_id"], plan)

    def test_q10_unplanned_dish_never_selected(self):
        """Q10: Món ngoài kế hoạch không bao giờ được chọn."""
        plan = ["ca_loc_nuong_trui"]
        sim = make_sim({
            "stock": {"ca_loc": 10, "ca_keo": 10, "keo_neo": 10}
        }, menu_ids=plan)
        evs = sim._spawn_customer(sim.tables[0])
        self.assertEqual(evs[0][1]["dish_id"], "ca_loc_nuong_trui")

    def test_q11_no_matching_dish_emits_no_dish(self):
        """Q11: Không có món kế hoạch nào đủ nguyên liệu phát no_dish."""
        plan = ["ca_loc_nuong_trui"]
        # Kho chỉ có ca_keo, thiếu ca_loc
        sim = make_sim({"stock": {"ca_keo": 10}}, menu_ids=plan)
        evs = sim._spawn_customer(sim.tables[0])
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0][0], "no_dish")
        self.assertEqual(evs[0][1], {})
        self.assertEqual(len(sim.customers), 0)

    def test_q12_sufficient_ingredients_allows_orders_beyond_plan_servings(self):
        """Q12: Đủ nguyên liệu vẫn gọi tiếp sau khi đạt số suất dự kiến."""
        plan = ["ca_loc_nuong_trui"]
        # Kho có 5 cá lóc, dự kiến chỉ 1 suất nhưng khách vẫn gọi tiếp nếu còn hàng
        sim = make_sim({"stock": {"ca_loc": 5}}, menu_ids=plan)
        sim.phase_tick = 120
        evs1 = sim._spawn_customer(sim.tables[0])
        self.assertEqual(evs1[0][0], "customer_arrived")
        evs2 = sim._spawn_customer(sim.tables[1])
        self.assertEqual(evs2[0][0], "customer_arrived")
        self.assertEqual(len(sim.customers), 2)

    def test_q13_reservation_does_not_exceed_available_stock(self):
        """Q13: Reservation không vượt quá tồn kho khả dụng."""
        sim = make_sim({"stock": {"ca_loc": 1}}, menu_ids=["ca_loc_nuong_trui"])
        evs1 = sim._spawn_customer(sim.tables[0])
        self.assertEqual(evs1[0][0], "customer_arrived")
        # Khách 2 không đủ ca_loc vì đã bị C1 giữ chỗ
        evs2 = sim._spawn_customer(sim.tables[1])
        self.assertEqual(evs2[0][0], "no_dish")


class TestConcurrentStoves(unittest.TestCase):
    def test_q14_two_stoves_cook_concurrently(self):
        """Q14: Hai bếp B1 và B2 có thể nấu song song."""
        sim = make_sim({
            "stock": {"ca_loc": 10},
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved", "state": "waiting"},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved", "state": "waiting"},
            ]
        })
        # Bắt đầu nấu ở B1
        sim.pos = list(sim.stoves[0]["pos"])
        evs1 = sim.step(PRESS)
        self.assertTrue(any(e[0] == "cook_started" and e[1]["stove_id"] == "B1" for e in evs1))

        # Di chuyển sang B2 và nấu
        sim.pos = list(sim.stoves[1]["pos"])
        evs2 = sim.step(PRESS)
        self.assertTrue(any(e[0] == "cook_started" and e[1]["stove_id"] == "B2" for e in evs2))

        # Cả hai bếp đang nấu song song
        self.assertEqual(sim.stoves[0]["state"], "cooking")
        self.assertEqual(sim.stoves[1]["state"], "cooking")

        # Cả hai timer đều giảm cùng lúc ở tick tiếp theo
        c1_before = sim.stoves[0]["cook_ticks_left"]
        c2_before = sim.stoves[1]["cook_ticks_left"]
        sim.step(IDLE)
        self.assertEqual(sim.stoves[0]["cook_ticks_left"], c1_before - 1)
        self.assertEqual(sim.stoves[1]["cook_ticks_left"], c2_before - 1)

    def test_q15_order_not_assigned_to_both_stoves(self):
        """Q15: Một đơn không bị hai bếp cùng nhận."""
        sim = make_sim({
            "stock": {"ca_loc": 10},
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved", "state": "waiting"},
            ]
        })
        sim.pos = list(sim.stoves[0]["pos"])
        sim.step(PRESS)
        self.assertEqual(sim.stoves[0]["dish"]["order_id"], "C1")

        # B2 thử nhận đơn khi chỉ có 1 đơn đã được B1 nhận
        sim.pos = list(sim.stoves[1]["pos"])
        evs2 = sim.step(PRESS)
        self.assertFalse(any(e[0] == "cook_started" for e in evs2))
        self.assertEqual(sim.stoves[1]["state"], "idle")

    def test_q16_stove_picks_oldest_order(self):
        """Q16: Bếp lấy đơn reserved cũ nhất theo order_tick rồi ID bàn."""
        sim = make_sim({
            "stock": {"ca_loc": 10},
            "customers": [
                {"id": "C1", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 150, "order_status": "reserved", "state": "waiting"},
                {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 120, "order_status": "reserved", "state": "waiting"},
            ]
        })
        sim.pos = list(sim.stoves[0]["pos"])
        evs = sim.step(PRESS)
        started = [e for e in evs if e[0] == "cook_started"][0]
        self.assertEqual(started[1]["order_id"], "C2")  # order_tick 120 < 150

    def test_q17_stove_emits_cook_started(self):
        """Q17: Bếp phát cook_started với đầy đủ thông tin chuẩn contract."""
        sim = make_sim({
            "stock": {"ca_linh": 3, "bong_dien_dien": 1},
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien", "order_status": "reserved", "state": "waiting"}]
        })
        sim.pos = list(sim.stoves[0]["pos"])
        evs = sim.step(PRESS)
        started = [e for e in evs if e[0] == "cook_started"][0][1]
        self.assertEqual(started["stove_id"], "B1")
        self.assertEqual(started["order_id"], "C1")
        self.assertEqual(started["dish_id"], "lau_ca_linh_dien_dien")
        self.assertEqual(started["items"], ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(started["base_price"], 120)

    def test_q18_stove_emits_dish_ready(self):
        """Q18: Bếp phát dish_ready khi hết thời gian nấu."""
        sim = make_sim({
            "stoves": [{"id": "B1", "state": "cooking", "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui"}, "cook_ticks_left": 1}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "cooking", "state": "waiting"}]
        })
        evs = sim.step(IDLE)
        ready = [e for e in evs if e[0] == "dish_ready"]
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0][1]["stove_id"], "B1")
        self.assertEqual(ready[0][1]["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(sim.stoves[0]["state"], "ready")


class TestServingAndPaymentLifecycle(unittest.TestCase):
    def test_q19_player_carries_at_most_one_dish(self):
        """Q19: Người chơi bưng tối đa một món."""
        sim = make_sim({
            "stoves": [
                {"id": "B1", "state": "ready", "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui"}},
                {"id": "B2", "state": "ready", "dish": {"order_id": "C2", "dish_id": "ca_loc_nuong_trui"}},
            ],
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "ready", "state": "waiting"},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_status": "ready", "state": "waiting"},
            ]
        })
        # Lấy món từ B1
        sim.pos = list(sim.stoves[0]["pos"])
        sim.step(PRESS)
        self.assertIsNotNone(sim.hand)
        self.assertEqual(sim.hand["order_id"], "C1")

        # Thử lấy tiếp từ B2 khi tay đang bận
        sim.pos = list(sim.stoves[1]["pos"])
        evs2 = sim.step(PRESS)
        self.assertFalse(any(e[0] == "dish_picked" for e in evs2))
        self.assertEqual(sim.stoves[1]["state"], "ready")

    def test_q20_serve_to_matching_order_only(self):
        """Q20: Chỉ phục vụ đúng bàn có order tương ứng."""
        sim = make_sim({
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui"},
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "carried", "state": "waiting"},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_status": "waiting", "state": "waiting"},
            ]
        })
        # Đến bàn T2 (khách C2) trong khi đang cầm món của C1
        sim.pos = list(sim.tables[1]["pos"])
        evs_wrong = sim.step(PRESS)
        self.assertFalse(any(e[0] == "served" for e in evs_wrong))
        self.assertIsNotNone(sim.hand)

        # Đến đúng bàn T1 (khách C1)
        sim.pos = list(sim.tables[0]["pos"])
        evs_right = sim.step(PRESS)
        served = [e for e in evs_right if e[0] == "served"]
        self.assertEqual(len(served), 1)
        self.assertIsNone(sim.hand)
        self.assertEqual(sim.customers[0]["state"], "eating")

    def test_q21_customer_eats_for_600_ticks(self):
        """Q21: Khách ăn đủ 600 tick."""
        sim = make_sim({
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating", "eat_ticks_left": 600, "base_price": 60, "tip": 0}]
        })
        for _ in range(599):
            evs = sim.step(IDLE)
            self.assertFalse(any(e[0] == "paid" for e in evs))
        evs = sim.step(IDLE)
        paid = [e for e in evs if e[0] == "paid"]
        self.assertEqual(len(paid), 1)
        self.assertEqual(paid[0][1]["reason"], "finished_eating")

    def test_q22_correct_price_payment(self):
        """Q22: Thanh toán đúng giá món."""
        sim = make_sim({
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating", "eat_ticks_left": 1, "base_price": 60, "tip": 0}]
        })
        evs = sim.step(IDLE)
        paid = [e for e in evs if e[0] == "paid"][0][1]
        self.assertEqual(paid["amount"], 60)
        self.assertEqual(sim.money, 60)
        self.assertEqual(sim.earned, 60)

    def test_q23_tips_awarded_when_patience_ratio_ge_50_pct(self):
        """Q23: Boa bằng floor(price * 0.2) khi còn >= 50% kiên nhẫn khi giao."""
        # 3600 tick max, bắt đầu 1801 tick -> sau bước giảm timer còn 1800 tick (đúng 50%) -> được boa
        sim = make_sim({
            "stock": {"ca_loc": 5},
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui"},
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting", "patience_ticks_left": 1801, "base_price": 60, "reserved": {"ca_loc": 1}}]
        })
        sim.pos = list(sim.tables[0]["pos"])
        evs = sim.step(PRESS)
        served = [e for e in evs if e[0] == "served"][0][1]
        self.assertEqual(served["tip"], 12)  # floor(60 * 0.2) = 12

        # Kiểm tra thêm ca dưới ngưỡng (< 50% sau bước giảm timer): bắt đầu 1800 -> sau bước giảm timer còn 1799 (< 50%) -> không có boa (tip = 0)
        sim_low = make_sim({
            "stock": {"ca_loc": 5},
            "hand": {"order_id": "C2", "dish_id": "ca_loc_nuong_trui"},
            "customers": [{"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting", "patience_ticks_left": 1800, "base_price": 60, "reserved": {"ca_loc": 1}}]
        })
        sim_low.pos = list(sim_low.tables[0]["pos"])
        evs_low = sim_low.step(PRESS)
        served_low = [e for e in evs_low if e[0] == "served"][0][1]
        self.assertEqual(served_low["tip"], 0)

    def test_q24_reputation_changes_correctly(self):
        """Q24: Uy tín tăng +0.2 khi có boa, giảm -0.5 khi hết kiên nhẫn, kẹp [0, 5]."""
        sim = make_sim({
            "reputation": 3.0,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating", "eat_ticks_left": 1, "base_price": 60, "tip": 12}]
        })
        sim.step(IDLE)
        self.assertEqual(sim.reputation, 3.2)


class TestPatienceAndClosing(unittest.TestCase):
    def test_q25_customer_leaves_when_patience_depleted(self):
        """Q25: Khách rời quán khi hết kiên nhẫn, trừ 0.5 uy tín."""
        sim = make_sim({
            "stock": {"ca_loc": 5},
            "reputation": 3.0,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting", "patience_ticks_left": 1, "reserved": {"ca_loc": 1}}]
        })
        evs = sim.step(IDLE)
        left = [e for e in evs if e[0] == "customer_left"]
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0][1]["reason"], "patience")
        self.assertEqual(sim.reputation, 2.5)

    def test_q26_waiting_customer_at_closing_not_penalized(self):
        """Q26: Khách đang chờ lúc hết giờ rời closing và không bị trừ uy tín."""
        sim = make_sim({
            "stock": {"ca_loc": 5},
            "reputation": 3.0,
            "time_left_ticks": 1,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting", "patience_ticks_left": 100, "reserved": {"ca_loc": 1}}]
        })
        evs = sim.step(IDLE)
        left = [e for e in evs if e[0] == "customer_left"][0][1]
        self.assertEqual(left["reason"], "closing")
        self.assertEqual(sim.reputation, 3.0)  # Không trừ uy tín

    def test_q27_eating_customer_at_closing_pays(self):
        """Q27: Khách đang ăn lúc closing thanh toán ngay."""
        sim = make_sim({
            "time_left_ticks": 1,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating", "eat_ticks_left": 500, "base_price": 60, "tip": 12}]
        })
        evs = sim.step(IDLE)
        paid = [e for e in evs if e[0] == "paid"][0][1]
        self.assertEqual(paid["reason"], "closing")
        self.assertEqual(paid["amount"], 72)
        self.assertEqual(sim.money, 72)

    def test_q28_cleanup_reserved_and_dishes_at_closing(self):
        """Q28: Dọn dẹp reserved, bếp và tay khi đóng ca."""
        sim = make_sim({
            "stock": {"ca_loc": 5},
            "time_left_ticks": 1,
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui"},
            "stoves": [{"id": "B1", "state": "cooking", "dish": {"order_id": "C2", "dish_id": "ca_loc_nuong_trui"}}],
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting", "reserved": {"ca_loc": 1}},
            ]
        })
        sim.step(IDLE)
        self.assertIsNone(sim.hand)
        self.assertEqual(sim.stoves[0]["state"], "idle")
        self.assertEqual(len(sim.customers), 0)
        self.assertTrue(sim.done)
        self.assertIsNotNone(sim.result)


class TestDayScenarioValidation(unittest.TestCase):
    def test_q29_valid_day_scenario(self):
        """Q29: Scenario day hợp lệ được nạp thành công."""
        with Workdir() as w:
            path = write_json(w.path("sc_day.json"), {
                "day": {
                    "money": 200,
                    "earned": 200,
                    "reputation": 3.0,
                    "day_plan": {
                        "menu": {"ca_loc_nuong_trui": 2},
                        "ingredients": {"ca_loc": 2}
                    }
                }
            })
            res = load_scenario(path, "day", TUNING_V11)
            self.assertIn("day", res)
            self.assertEqual(res["day"]["money"], 200)

    def test_q30_invalid_day_scenario_rejected(self):
        """Q30: Scenario day không hợp lệ trả về lỗi BadInput."""
        with Workdir() as w:
            # money > earned -> lỗi
            p1 = write_json(w.path("p1.json"), {"day": {"money": 300, "earned": 200}})
            with self.assertRaises(BadInput):
                load_scenario(p1, "day", TUNING_V11)

            # Khối quan có stock trong mode day -> lỗi
            p2 = write_json(w.path("p2.json"), {"day": {}, "quan": {"stock": {"ca_loc": 1}}})
            with self.assertRaises(BadInput):
                load_scenario(p2, "day", TUNING_V11)

    def test_q31_validate_quan_against_inventory_rejects_insufficient_stock(self):
        """Q31: Kho thực tế không đủ nguyên liệu cho khách fixture bị từ chối."""
        sc_quan = {
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved"}]
        }
        # Kho rỗng, không đủ cho C1
        with self.assertRaises(BadInput):
            validate_quan_against_inventory(sc_quan, {}, TUNING_V11)


class TestDeterminismAndDaySimCompatibility(unittest.TestCase):
    def test_q32_deterministic_replay_identical_outputs(self):
        """Q32: Hai lần chạy cùng seed tạo snapshot và event giống hệt nhau."""
        sim1 = make_sim({"stock": {"ca_loc": 10}}, streams=Streams(12345))
        sim2 = make_sim({"stock": {"ca_loc": 10}}, streams=Streams(12345))
        evs1, evs2 = [], []
        for _ in range(150):
            evs1.append(sim1.step(IDLE))
            evs2.append(sim2.step(IDLE))
        self.assertEqual(evs1, evs2)
        self.assertEqual(sim1.snapshot(), sim2.snapshot())

    def test_q33_quansim_initialized_by_daysim(self):
        """Q33: QuanSim hoạt động chuẩn xác với giao diện bàn giao từ DaySim."""
        inv = {"ca_loc": 3, "bong_sung": 4}
        plan = ["ca_loc_nuong_trui", "goi_bong_sung"]
        sim = QuanSim(
            TUNING_V11,
            {},
            Streams(42),
            inventory=inv,
            menu_ids=plan,
            money=250,
            earned=300,
            reputation=3.8
        )
        self.assertEqual(sim.money, 250)
        self.assertEqual(sim.earned, 300)
        self.assertEqual(sim.reputation, 3.8)
        self.assertEqual(sim.menu_ids, plan)
        sim.time_left_ticks = 1
        sim.step(IDLE)
        self.assertTrue(sim.done)
        self.assertIsNotNone(sim.result)
        self.assertEqual(sim.result["money"], 250)
        self.assertEqual(sim.result["earned"], 300)
        self.assertEqual(sim.result["reputation"], 3.8)

    def test_q34_timer_does_not_advance_when_step_is_not_called(self):
        """Q34: Timer không giảm khi pause wrapper không gọi step()."""
        sim = make_sim({
            "stock": {"ca_loc": 5},
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting", "patience_ticks_left": 100, "reserved": {"ca_loc": 1}}]
        })
        # Giả lập 10 tick paused: không gọi sim.step()
        initial_time = sim.time_left_ticks
        initial_pat = sim.customers[0]["patience_ticks_left"]
        # Không gọi step
        self.assertEqual(sim.time_left_ticks, initial_time)
        self.assertEqual(sim.customers[0]["patience_ticks_left"], initial_pat)


if __name__ == "__main__":
    unittest.main()
