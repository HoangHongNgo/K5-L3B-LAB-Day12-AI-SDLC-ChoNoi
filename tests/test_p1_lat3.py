"""Unit và black-box tests cho Lát 3 (Nguyễn Minh Phương - minhphuong150505):
Hệ thống khách hàng, đặt món, giữ nguyên liệu và kiên nhẫn.
"""

import json
import os
import unittest

from helpers import (Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json)


class ScenarioValidation(unittest.TestCase):
    def test_quan_valid_customer_fixture(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 2},
                    "customers": [{
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                        "order_tick": 0,
                        "reserved": {"ca_loc": 1}
                    }]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)

    def test_quan_valid_customer_fixture_missing_reserved(self):
        """Khách fixture thiếu reserved nhưng hợp lệ và suy ra được."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 2},
                    "customers": [{
                        "id": "C1",
                        "table_id": "T1",
                        "dish_id": "ca_loc_nuong_trui",
                    }]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)

    def test_quan_customer_duplicate_table(self):
        """1. Hai khách cùng sử dụng một bàn -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 2},
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"},
                        {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
                    ]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_nonexistent_table(self):
        """2. Khách sử dụng bàn không tồn tại -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [
                        {"id": "C1", "table_id": "T99", "dish_id": "ca_loc_nuong_trui"}
                    ]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_nonexistent_dish(self):
        """3. Khách sử dụng món không tồn tại trong menu -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "mon_khong_ton_tai"}
                    ]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--scenario", sc, "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_invalid_id(self):
        """4. Customer ID không hợp lệ hoặc trùng -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            # ID rỗng
            sc1 = write_json(w.path("sc1.json"), {
                "quan": {
                    "customers": [{"id": "", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc1, "--out", out)[0], 2)
            # Trùng ID
            sc2 = write_json(w.path("sc2.json"), {
                "quan": {
                    "tables": [{"id": "T1"}, {"id": "T2"}],  # T2 not in defaults
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"},
                        {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
                    ]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc2, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_reserved_invalid_format(self):
        """5. reserved có số lượng âm, kiểu sai hoặc nguyên liệu không hợp lệ -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            # Số lượng âm
            sc1 = write_json(w.path("sc1.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": {"ca_loc": -1}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc1, "--out", out)[0], 2)

            # Nguyên liệu lạ
            sc2 = write_json(w.path("sc2.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": {"nguyen_lieu_la": 1}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc2, "--out", out)[0], 2)

            # Kiểu sai (boolean)
            sc3 = write_json(w.path("sc3.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": {"ca_loc": True}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc3, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_reserved_recipe_mismatch(self):
        """6. Nguyên liệu giữ không phù hợp công thức -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            # ca_loc_nuong_trui cần {"ca_loc": 1}, nhưng giữ bong_sung
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"bong_sung": 2, "ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": {"bong_sung": 1}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_reserved_exceeds_stock(self):
        """7. Tổng nguyên liệu giữ vượt quá kho thực tế trong scenario -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            # Cần 1 ca_loc nhưng kho chỉ có 0
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 0},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "reserved": {"ca_loc": 1}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_customer_order_status_contradiction(self):
        """8. Trạng thái đơn hàng mâu thuẫn với nguyên liệu giữ -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            # order_status là cooking mà vẫn có reserved
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {"ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "cooking", "reserved": {"ca_loc": 1}}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_stove_and_hand_share_order(self):
        """9. Bếp và tay cùng giữ một đơn -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": {},
                    "stoves": [{"id": "B1", "state": "cooking", "dish": "ca_loc_nuong_trui", "order_id": "C1"}],
                    "hand": {"dish": "ca_loc_nuong_trui", "order_id": "C1"},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "cooking"}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_quan_reference_nonexistent_customer(self):
        """10. Tham chiếu order/customer không tồn tại -> mã 2."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stoves": [{"id": "B1", "state": "cooking", "dish": "ca_loc_nuong_trui", "order_id": "C999"}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "cooking"}]
                }
            })
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                          "--scenario", sc, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
