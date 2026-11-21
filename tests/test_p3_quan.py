"""Unit và integration tests cho Phase 3 Lát Q (Nguyễn Minh Phương - minhphuong150505):
TICKET-03 — Change Request "Mùa Nước Nổi" (Test Contract v1.2):
- Kho cá thể (item-based inventory) thay cho kho đếm
- Giữ chỗ theo Item IDs (ưu tiên cá thể tươi nhất, hòa theo ID)
- Hao tươi trong Quán (0.25 / s = 1/240 điểm mỗi tick)
- Phát hiện và phát event 'spoiled' khi fresh từ >= 30 giảm xuống < 30 (theo thứ tự id)
- Cơ chế thử giữ lại (re-reservation) khi hàng đang giữ bị ươn
- Chốt giá theo độ tươi trung bình lúc bắt đầu nấu (cook_started có mảng cá thể)
- Boa tính trên giá đã chốt
- Scenario validation cho v1.2
- Kiểm tra tính tất định (determinism byte-by-byte)
"""

import copy
import json
import math
import os
import unittest
from fractions import Fraction

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.inventory import read_inventory, validate_items, write_inventory
from chonoi.rng import Streams
from chonoi.scenario import load_scenario, validate_quan_against_inventory
from chonoi.sim.quan import QuanSim

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
with open(os.path.join(FIXTURES_DIR, "p3_quan_tuning.json"), encoding="utf-8") as f:
    TUNING_V12 = json.load(f)

PRESS = InputState((0.0, 0.0), {"interact": True}, {"interact"})
IDLE = InputState((0.0, 0.0), {}, set())


def make_sim(scenario_block=None, tuning=None, streams=None, ids=None, **kwargs):
    t = copy.deepcopy(tuning or TUNING_V12)
    sc = copy.deepcopy(scenario_block or {})
    st = streams or Streams(42)
    alloc = ids or IdAllocator()
    return QuanSim(t, sc, st, alloc, **kwargs)


class TestP3ItemInventorySchema(unittest.TestCase):
    """Nhóm A: Xác thực kho cá thể và schema file kho v1.2."""

    def test_item_inventory_file_valid(self):
        """Đọc file kho cá thể hợp lệ chứa items."""
        with Workdir() as w:
            path = w.path("inv.json")
            data = {"items": [
                {"id": "I1", "kind": "ca_linh", "fresh": 100},
                {"id": "I2", "kind": "ca_loc", "fresh": 97.5}
            ]}
            write_json(path, data)
            items = read_inventory(path, contract_version="1.2")
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0]["id"], "I1")
            self.assertEqual(items[1]["fresh"], 97.5)

    def test_item_inventory_count_based_rejected_under_v12(self):
        """Kho đếm bị từ chối với BadInput khi chạy contract v1.2."""
        with Workdir() as w:
            path = w.path("inv_count.json")
            write_json(path, {"items": {"ca_loc": 2}})
            with self.assertRaises(BadInput):
                read_inventory(path, contract_version="1.2")

    def test_item_inventory_duplicate_id_rejected(self):
        """Hai cá thể trùng ID bị từ chối."""
        with Workdir() as w:
            path = w.path("inv_dup.json")
            write_json(path, {"items": [
                {"id": "I1", "kind": "ca_loc", "fresh": 100},
                {"id": "I1", "kind": "ca_linh", "fresh": 90}
            ]})
            with self.assertRaises(BadInput):
                read_inventory(path, contract_version="1.2")

    def test_item_inventory_invalid_kind_rejected(self):
        """Nguyên liệu lạ không thuộc kinds bị từ chối."""
        with Workdir() as w:
            path = w.path("inv_bad.json")
            write_json(path, {"items": [{"id": "I1", "kind": "tom_hum", "fresh": 100}]})
            with self.assertRaises(BadInput):
                read_inventory(path, contract_version="1.2")

    def test_item_inventory_freshness_out_of_bounds_rejected(self):
        """Độ tươi ngoài khoảng [0, 100] bị từ chối."""
        with Workdir() as w:
            path = w.path("inv_oob.json")
            write_json(path, {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 105}]})
            with self.assertRaises(BadInput):
                read_inventory(path, contract_version="1.2")

    def test_item_inventory_atomic_write(self):
        """write_inventory ghi file kho cá thể nguyên tử."""
        with Workdir() as w:
            path = w.path("out.json")
            items = [{"id": "I1", "kind": "ca_linh", "fresh": 100}]
            write_inventory(path, items)
            read_back = read_inventory(path, contract_version="1.2")
            self.assertEqual(read_back, items)


class TestP3ReservationByItemIds(unittest.TestCase):
    """Nhóm B: Giữ chỗ theo Item IDs, ưu tiên cá thể tươi nhất và hòa theo ID."""

    def test_reserve_chooses_freshest_items_and_breaks_ties_by_id(self):
        """Khách gọi món chọn item tươi nhất, nếu hòa chọn ID nhỏ hơn."""
        # 3 cá lóc: I1 (fresh 80), I2 (fresh 95), I3 (fresh 95)
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 80},
            {"id": "I2", "kind": "ca_loc", "fresh": 95},
            {"id": "I3", "kind": "ca_loc", "fresh": 95},
        ]
        sim = make_sim({"stock": stock}, menu_ids=["ca_loc_nuong_trui"])
        evs = sim._spawn_customer(sim.tables[0])
        self.assertEqual(evs[0][0], "customer_arrived")
        c = sim.customers[0]
        # I2 và I3 cùng fresh 95 > I1 (80); I2 có id nhỏ hơn I3 -> chọn I2
        self.assertEqual(c["reserved"], ["I2"])

    def test_reserve_never_selects_spoiled_items(self):
        """Hàng ươn (fresh < 30) không được chọn để giữ chỗ."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 29.5},
            {"id": "I2", "kind": "ca_loc", "fresh": 20.0},
        ]
        sim = make_sim({"stock": stock}, menu_ids=["ca_loc_nuong_trui"])
        evs = sim._spawn_customer(sim.tables[0])
        # Không có món nào đủ nguyên liệu tươi -> phát no_dish
        self.assertEqual(evs[0][0], "no_dish")
        self.assertEqual(len(sim.customers), 0)

    def test_multiple_customers_reserve_disjoint_item_ids(self):
        """Nhiều khách gọi món giữ các cá thể độc lập, không dùng chung."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 90},
            {"id": "I2", "kind": "ca_loc", "fresh": 85},
        ]
        sim = make_sim({"stock": stock}, menu_ids=["ca_loc_nuong_trui"])
        sim.phase_tick = 120
        sim._spawn_customer(sim.tables[0])
        sim._spawn_customer(sim.tables[1])
        c1 = sim.customers[0]
        c2 = sim.customers[1]
        self.assertEqual(c1["reserved"], ["I1"])
        self.assertEqual(c2["reserved"], ["I2"])
        # Khách thứ 3 đến thiếu cá lóc -> no_dish
        evs3 = sim._spawn_customer(sim.tables[2])
        self.assertEqual(evs3[0][0], "no_dish")

    def test_infer_customer_reservations_from_scenario(self):
        """Khách trong scenario thiếu reserved được tự động giữ cá thể tươi nhất theo thứ tự."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 90},
            {"id": "I2", "kind": "ca_loc", "fresh": 95},
        ]
        sc = {
            "stock": stock,
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 10},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 20},
            ]
        }
        sim = make_sim(sc)
        c1 = next(c for c in sim.customers if c["id"] == "C1")
        c2 = next(c for c in sim.customers if c["id"] == "C2")
        # C1 đến trước (tick 10) lấy cá thể tươi nhất I2 (95)
        self.assertEqual(c1["reserved"], ["I2"])
        # C2 đến sau (tick 20) lấy I1 (90)
        self.assertEqual(c2["reserved"], ["I1"])


class TestP3FreshnessDecayAndSpoiled(unittest.TestCase):
    """Nhóm C: Hao tươi kho thô (1/240 điểm/tick) và event spoiled tại ngưỡng 30."""

    def test_freshness_decay_rate_in_quan(self):
        """Kho quán hao đúng 0.25 điểm mỗi giây (1/240 điểm mỗi tick)."""
        stock = [{"id": "I1", "kind": "ca_linh", "fresh": 100}]
        sim = make_sim({"stock": stock, "random_customers": False})
        # Chạy 240 tick (4 giây)
        for _ in range(240):
            sim.step(IDLE)
        # 100 - 240 * (1/240) = 99
        snap = sim.snapshot()
        self.assertEqual(snap["stock"][0]["fresh"], 99)

    def test_freshness_clamps_at_zero(self):
        """Độ tươi kẹp tại 0, không âm."""
        # Bắt đầu tại fresh = 1/240
        stock = [{"id": "I1", "kind": "ca_linh", "fresh": 0.004166666666666667}]
        sim = make_sim({"stock": stock, "random_customers": False})
        sim.items[0]["fresh"] = Fraction(1, 240)
        sim.step(IDLE)
        self.assertEqual(sim.items[0]["fresh"], Fraction(0))
        sim.step(IDLE)
        self.assertEqual(sim.items[0]["fresh"], Fraction(0))

    def test_spoiled_emitted_exactly_once_when_crossing_threshold_30(self):
        """Event spoiled phát đúng một lần khi độ tươi giảm từ >= 30 xuống < 30."""
        # Bắt đầu đúng 30.0 -> sau 1 tick giảm xuống 30 - 1/240 = 29.9958 < 30
        stock = [{"id": "I1", "kind": "ca_linh", "fresh": 30}]
        sim = make_sim({"stock": stock, "random_customers": False})
        evs = sim.step(IDLE)
        spoiled = [e for e in evs if e[0] == "spoiled"]
        self.assertEqual(len(spoiled), 1)
        self.assertEqual(spoiled[0][1], {"item_id": "I1", "kind": "ca_linh", "location": "stock"})

        # Tick tiếp theo không phát lại spoiled
        evs2 = sim.step(IDLE)
        self.assertFalse(any(e[0] == "spoiled" for e in evs2))

    def test_multiple_spoiled_emitted_in_id_order(self):
        """Nhiều item cùng ươn phát spoiled theo thứ tự ID."""
        stock = [
            {"id": "I3", "kind": "ca_loc", "fresh": 30},
            {"id": "I1", "kind": "ca_linh", "fresh": 30},
            {"id": "I2", "kind": "bong_sung", "fresh": 30},
        ]
        sim = make_sim({"stock": stock, "random_customers": False})
        evs = sim.step(IDLE)
        spoiled_ids = [e[1]["item_id"] for e in evs if e[0] == "spoiled"]
        self.assertEqual(spoiled_ids, ["I1", "I2", "I3"])

    def test_cooked_dishes_do_not_decay(self):
        """Món đang nấu trên bếp không hao tươi theo kho thô."""
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 100}]
        sim = make_sim({
            "player": {"pos": [2, 8]},
            "stock": stock,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]
        })
        # Bắt đầu nấu ở tick 1: bước 2 cá lóc hao 1 tick còn 100 - 1/240, giá chốt = floor(60 * 99.9958 / 100) = 59
        evs = sim.step(PRESS)
        self.assertTrue(any(e[0] == "cook_started" for e in evs))
        self.assertEqual(sim.stoves[0]["dish"]["base_price"], 59)
        # Kho thô đã tiêu thụ I1
        self.assertEqual(len(sim.items), 0)
        # Nấu trong 360 tick: giá món chín trên bếp không đổi
        for _ in range(360):
            sim.step(IDLE)
        self.assertEqual(sim.stoves[0]["dish"]["base_price"], 59)


class TestP3ReReservationOnSpoilage(unittest.TestCase):
    """Nhóm D: Cơ chế thử giữ lại (re-reservation) khi hàng đang giữ bị ươn."""

    def test_re_reserve_when_held_item_spoils_and_backup_available(self):
        """Hàng đang giữ bị ươn nhưng kho còn hàng dự phòng -> tự động giữ lại hàng mới tươi nhất."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 30},  # Đang giữ, sẽ ươn ở tick 1
            {"id": "I2", "kind": "ca_loc", "fresh": 85},  # Hàng dự phòng tươi
        ]
        sc = {
            "stock": stock,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]
        }
        sim = make_sim(sc, random_customers=False)
        evs = sim.step(IDLE)
        # Phát spoiled cho I1
        self.assertTrue(any(e[0] == "spoiled" and e[1]["item_id"] == "I1" for e in evs))
        # C1 được giữ lại I2 tươi nhất
        c1 = sim.customers[0]
        self.assertEqual(c1["order_status"], "reserved")
        self.assertEqual(c1["reserved"], ["I2"])

    def test_order_becomes_unfulfillable_when_no_backup_available(self):
        """Hàng đang giữ bị ươn và kho không còn hàng dự phòng -> order_status thành unfulfillable."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 30},  # Đang giữ, sẽ ươn ở tick 1
        ]
        sc = {
            "stock": stock,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]
        }
        sim = make_sim(sc, random_customers=False)
        evs = sim.step(IDLE)
        self.assertTrue(any(e[0] == "spoiled" for e in evs))
        c1 = sim.customers[0]
        self.assertEqual(c1["order_status"], "unfulfillable")
        self.assertEqual(c1["reserved"], [])
        # Khách vẫn ngồi tại bàn chờ đến hết kiên nhẫn
        self.assertEqual(c1["state"], "waiting")

    def test_re_reserve_priority_by_order_tick_then_table(self):
        """Hai đơn cùng bị ươn: đơn có order_tick nhỏ hơn được giữ hàng dự phòng trước."""
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 30},
            {"id": "I2", "kind": "ca_loc", "fresh": 30},
            {"id": "I3", "kind": "ca_loc", "fresh": 90},  # Chỉ còn 1 con cá lóc dự phòng
        ]
        sc = {
            "stock": stock,
            "customers": [
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 20, "reserved": ["I2"]},
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 10, "reserved": ["I1"]},
            ]
        }
        sim = make_sim(sc, random_customers=False)
        sim.step(IDLE)
        c1 = next(c for c in sim.customers if c["id"] == "C1")
        c2 = next(c for c in sim.customers if c["id"] == "C2")
        # C1 (tick 10) được giữ I3
        self.assertEqual(c1["order_status"], "reserved")
        self.assertEqual(c1["reserved"], ["I3"])
        # C2 (tick 20) không còn hàng -> unfulfillable
        self.assertEqual(c2["order_status"], "unfulfillable")
        self.assertEqual(c2["reserved"], [])


class TestP3FreshnessPricingAndPayment(unittest.TestCase):
    """Nhóm E: Chốt giá theo độ tươi lúc bắt đầu nấu và thanh toán."""

    def test_price_locked_at_cook_started_based_on_avg_freshness(self):
        """Giá chốt = floor(giá niêm yết * avg_fresh / 100) theo độ tươi tại thời điểm bắt đầu nấu."""
        # Món ca_loc_nuong_trui giá menu 60. Cá lóc ban đầu fresh = 80.
        # Ở tick 1: bước 2 hao tươi 1 tick còn 80 - 1/240.
        # Giá chốt ở bước 4 = floor(60 * (80 - 1/240) / 100) = 47.
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 80}]
        sim = make_sim({
            "player": {"pos": [2, 8]},
            "stock": stock,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]
        })
        evs = sim.step(PRESS)
        cook = [e for e in evs if e[0] == "cook_started"][0][1]
        self.assertEqual(cook["base_price"], 47)
        self.assertEqual(cook["items"][0]["id"], "I1")

    def test_multi_ingredient_avg_freshness_pricing(self):
        """Món nhiều nguyên liệu chốt theo trung bình độ tươi của các cá thể dùng."""
        # Món goi_bong_sung giá menu 40, cần 2 bông súng.
        # Ban đầu I1: 90, I2: 70. Ở tick 1 bước 2 hao còn avg = 80 - 1/240.
        # Giá chốt = floor(40 * (80 - 1/240) / 100) = 31.
        stock = [
            {"id": "I1", "kind": "bong_sung", "fresh": 90},
            {"id": "I2", "kind": "bong_sung", "fresh": 70},
        ]
        sim = make_sim({
            "player": {"pos": [2, 8]},
            "stock": stock,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "reserved": ["I1", "I2"]}]
        })
        evs = sim.step(PRESS)
        cook = [e for e in evs if e[0] == "cook_started"][0][1]
        self.assertEqual(cook["base_price"], 31)
        # Items sắp theo kind rồi id
        self.assertEqual(cook["items"][0]["id"], "I1")
        self.assertEqual(cook["items"][1]["id"], "I2")

    def test_tip_calculated_from_locked_freshness_price(self):
        """Boa tính bằng floor(base_price * 0.2) trên giá đã chốt theo độ tươi."""
        # base_price = 48. Tip = floor(48 * 0.2) = 9.
        stock = []
        sim = make_sim({
            "player": {"pos": [9, 2]},
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 48},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "state": "waiting", "order_status": "assigned", "base_price": 48,
                "patience_ticks_left": 3600
            }]
        })
        evs = sim.step(PRESS)
        served = [e for e in evs if e[0] == "served"][0][1]
        self.assertEqual(served["base_price"], 48)
        self.assertEqual(served["tip"], 9)

    def test_payment_and_shift_end_result_in_v12(self):
        """Thanh toán hoàn tất và snapshot/result cuối ca đúng schema v1.2."""
        stock = [{"id": "I9", "kind": "ca_linh", "fresh": 95}]
        sim = make_sim({
            "player": {"pos": [9, 2]},
            "stock": stock,
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 48},
            "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "state": "waiting", "order_status": "assigned", "base_price": 48,
                "patience_ticks_left": 3600
            }]
        })
        sim.step(PRESS)
        c1 = sim.customers[0]
        c1["eat_ticks_left"] = 1
        evs = sim.step(IDLE)
        paid = [e for e in evs if e[0] == "paid"][0][1]
        self.assertEqual(paid["amount"], 48 + 9)

        # Chạy tới hết ca
        sim.time_left_ticks = 1
        sim.step(IDLE)
        self.assertTrue(sim.done)
        # result.stock là mảng cá thể
        self.assertIsInstance(sim.result["stock"], list)
        self.assertEqual(sim.result["stock"][0]["id"], "I9")


class TestP3ScenarioValidation(unittest.TestCase):
    """Nhóm F: Xác thực scenario v1.2 trong chonoi/scenario.py."""

    def test_scenario_with_item_stock_accepted(self):
        """Scenario có stock dạng mảng cá thể được chấp nhận."""
        sc = {
            "quan": {
                "stock": [
                    {"id": "I1", "kind": "ca_loc", "fresh": 100},
                    {"id": "I2", "kind": "bong_sung", "fresh": 80}
                ]
            }
        }
        with Workdir() as w:
            p = w.path("sc.json")
            write_json(p, sc)
            loaded = load_scenario(p, "quan", TUNING_V12)
            self.assertEqual(len(loaded["stock"]), 2)

    def test_scenario_rejects_reserved_pointing_to_spoiled_item(self):
        """Scenario có reserved trỏ tới cá thể bị ươn (fresh < 30) bị từ chối với BadInput."""
        sc = {
            "quan": {
                "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 25}],
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]
            }
        }
        with Workdir() as w:
            p = w.path("sc_spoiled.json")
            write_json(p, sc)
            with self.assertRaises(BadInput):
                load_scenario(p, "quan", TUNING_V12)

    def test_scenario_rejects_shared_reserved_items(self):
        """Scenario có hai khách cùng giữ chung 1 cá thể bị từ chối."""
        sc = {
            "quan": {
                "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                "customers": [
                    {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
                    {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
                ]
            }
        }
        with Workdir() as w:
            p = w.path("sc_dup.json")
            write_json(p, sc)
            with self.assertRaises(BadInput):
                load_scenario(p, "quan", TUNING_V12)

    def test_validate_quan_against_item_inventory(self):
        """validate_quan_against_inventory hoạt động đúng với kho cá thể."""
        inv = {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}
        sc_quan = {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}
        # Đủ kho -> không lỗi
        validate_quan_against_inventory(sc_quan, inv, TUNING_V12)
        # Thiếu kho -> BadInput
        sc_quan_excess = {"customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"},
            {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui"}
        ]}
        with self.assertRaises(BadInput):
            validate_quan_against_inventory(sc_quan_excess, inv, TUNING_V12)

    def test_validate_quan_against_inventory_with_item_id_reservations(self):
        """validate_quan_against_inventory hỗ trợ đúng khách có reserved là danh sách item IDs."""
        inv = {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 90}]}
        sc_quan = {"customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}
        ]}
        validate_quan_against_inventory(sc_quan, inv, TUNING_V12)

    def test_validate_quan_against_inventory_rejects_spoiled_reserved_item(self):
        """validate_quan_against_inventory từ chối khách giữ item có độ tươi < 30."""
        inv = {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 25}]}
        sc_quan = {"customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}
        ]}
        with self.assertRaises(BadInput):
            validate_quan_against_inventory(sc_quan, inv, TUNING_V12)

    def test_validate_quan_against_inventory_rejects_shared_reserved_item(self):
        """validate_quan_against_inventory từ chối hai khách cùng giữ một item ID."""
        inv = {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 95}]}
        sc_quan = {"customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
            {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}
        ]}
        with self.assertRaises(BadInput):
            validate_quan_against_inventory(sc_quan, inv, TUNING_V12)

    def test_validate_quan_against_inventory_rejects_non_reserved_with_items(self):
        """validate_quan_against_inventory từ chối khách không ở trạng thái reserved nhưng lại giữ đồ."""
        inv = {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 95}]}
        sc_quan = {"customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating", "order_status": "served", "reserved": ["I1"]}
        ]}
        with self.assertRaises(BadInput):
            validate_quan_against_inventory(sc_quan, inv, TUNING_V12)

    def test_quansim_forward_compatible_with_contract_v13(self):
        """QuanSim tự động kích hoạt kho cá thể khi tuning có contract_version v1.3."""
        tuning_v13 = dict(TUNING_V12, contract_version="1.3")
        streams = Streams(42)
        sim = QuanSim(tuning_v13, {"stock": {"ca_loc": 2}}, streams)
        self.assertTrue(sim.is_item_inventory)
        self.assertEqual(len(sim.items), 2)


class TestP3QuanInventoryHandoff(unittest.TestCase):
    def test_rejects_incompatible_reservations_before_writing_output(self):
        fish = {"id": "I1", "kind": "ca_loc", "fresh": 100}
        cases = (
            ("giữ theo số lượng trên kho cá thể", [fish], {"ca_loc": 1}),
            ("ID trên kho đếm", {"ca_loc": 1}, ["I1"]),
            ("mảng rỗng trên kho đếm", {"ca_loc": 1}, []),
            ("sai công thức", [dict(fish, kind="ca_linh")], ["I1"]),
            ("ID không có trong kho", [fish], ["I2"]),
            ("cá thể đã ươn", [dict(fish, fresh=29)], ["I1"]),
        )
        for description, stock, reserved in cases:
            for external in (False, True):
                with self.subTest(case=description, external=external), Workdir() as w:
                    quan = {"customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "reserved": reserved,
                    }]}
                    inventory_args = []
                    if external:
                        inventory = write_json(w.path("kho.json"), {"items": stock})
                        inventory_args = ["--inventory", inventory]
                    else:
                        quan["stock"] = stock
                    scenario = write_json(w.path("scenario.json"), {"quan": quan})
                    out = w.path("out.jsonl")
                    code, stderr = run_headless(
                        "--mode", "quan", "--seed", "42", "--ticks", "0",
                        "--scenario", scenario, "--out", out, *inventory_args,
                    )
                    self.assertEqual(code, 2, stderr)
                    self.assertFalse(os.path.exists(out))

    def test_cooking_consumes_the_reserved_item_from_inventory_file(self):
        tuning = load_contract()["tuning"]
        stove = tuning["quan"]["stoves"][0]
        fish = {"id": "I1", "kind": "ca_loc", "fresh": 100}
        for reservation in ({"reserved": ["I1"]}, {}):
            with self.subTest(reservation=reservation), Workdir() as w:
                scenario = write_json(w.path("scenario.json"), {"quan": {
                    "player": {"pos": stove["pos"]},
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        **reservation,
                    }],
                }})
                inventory = write_json(w.path("kho.json"), {"items": [fish]})
                inputs = write_json(w.path("inputs.json"), frames({"tick": 0, "interact": True}))
                out = w.path("out.jsonl")
                code, stderr = run_headless(
                    "--mode", "quan", "--seed", "42", "--ticks", "1",
                    "--scenario", scenario, "--inventory", inventory, "--inputs", inputs, "--out", out,
                )
                self.assertEqual(code, 0, stderr)
                rows = read_jsonl(out)
                cooked, = events(rows, "cook_started")
                self.assertEqual([item["id"] for item in cooked["data"]["items"]], ["I1"])
                initial, final = snapshots(rows)
                self.assertEqual(initial["stock"], [fish])
                self.assertEqual(final["stock"], [])


class TestP3Determinism(unittest.TestCase):
    """Nhóm G: Kiểm tra tính tất định byte-by-byte khi chạy headless với Contract v1.2."""

    def test_deterministic_jsonl_output(self):
        """Chạy 2 lần với cùng seed và scenario v1.2 cho JSONL giống hệt từng byte."""
        scenario_path = os.path.join(FIXTURES_DIR, "p3_quan_scenario.json")
        with Workdir() as w:
            out1 = w.path("out1.jsonl")
            out2 = w.path("out2.jsonl")
            code1, _ = run_headless(
                "--mode", "quan", "--seed", "123", "--ticks", "65",
                "--scenario", scenario_path,
                "--out", out1
            )
            code2, _ = run_headless(
                "--mode", "quan", "--seed", "123", "--ticks", "65",
                "--scenario", scenario_path,
                "--out", out2
            )
            self.assertEqual(code1, 0)
            self.assertEqual(code2, 0)
            with open(out1, "rb") as f1, open(out2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read())


if __name__ == "__main__":
    unittest.main()
