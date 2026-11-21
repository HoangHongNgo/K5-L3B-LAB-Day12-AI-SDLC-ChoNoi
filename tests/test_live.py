"""Test cửa sổ chơi trực tiếp (chonoi.live). Chỉ dành cho starter Python: nhóm đổi ngôn ngữ thì xóa file này."""

import json
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read()


def _post(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


class LiveServerTest(unittest.TestCase):
    def test_item_stock_includes_freshness_tuning_for_hud(self):
        tuning = load_contract()["tuning"]
        freshness = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}
        tuning["freshness"] = freshness
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 29.99}]
        game = LiveGame("quan", tuning, {}, 42, inventory=stock)

        snapshot = json.loads(game.state_json())
        self.assertEqual(snapshot["freshness"], freshness)
        self.assertEqual(snapshot["stock"], stock)


    def test_standalone_menu_pause_and_restart_keep_game_time(self):
        game = LiveGame("gather", load_contract()["tuning"], {}, 1, start_in_menu=True)
        def read():
            return json.loads(game.state_json())

        game.set_input({"interact": True})
        game._tick_once()
        menu = read()
        self.assertTrue(menu["menu_pending"])
        self.assertEqual(menu["tick"], 0)
        game.continue_intro(menu)
        game._tick_once()
        playing = read()
        self.assertFalse(playing["finished"])
        self.assertLess(playing["time_left_ticks"], menu["time_left_ticks"])
        game.set_input({"pause": True})
        game._tick_once()
        game.set_input({"pause": False})
        game._tick_once()
        paused = read()
        self.assertEqual(paused["state"], "paused")
        self.assertEqual(paused["time_left_ticks"], playing["time_left_ticks"])
        game.set_input({"pause": True})
        game._tick_once()
        self.assertLess(read()["time_left_ticks"], paused["time_left_ticks"])
        game.restart()
        self.assertTrue(read()["menu_pending"])
        self.assertEqual(read()["tick"], 0)

    def test_state_input_and_clean_stop(self):
        tuning = load_contract()["tuning"]
        server = LiveServer(LiveGame("gather", tuning, {}, 1), port=0)  # cổng ngẫu nhiên
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            code, body = _get(base + "/state")
            self.assertEqual(code, 200)
            st = json.loads(body)
            self.assertIn("tick", st)
            self.assertEqual(st["mode"], "gather")
            self.assertEqual(st["player"]["pos"], [2, 0])
            self.assertEqual(_post(base + "/input", {"move": [1, 0], "interact": False, "catch": False}), 200)
            self.assertEqual(_post(base + "/input", {"move": [5, 0]}), 400)
            code, html = _get(base + "/")
            self.assertEqual(code, 200)
            self.assertIn(b"<canvas", html)
            deadline = time.time() + 3
            while time.time() < deadline:
                st2 = json.loads(_get(base + "/state")[1])
                if st2["tick"] > st["tick"] + 3 and st2["player"]["pos"][0] > st["player"]["pos"][0]:
                    break
                time.sleep(0.05)
            self.assertGreater(st2["tick"], st["tick"], "mô phỏng phải chạy nền")
            self.assertGreater(st2["player"]["pos"][0], st["player"]["pos"][0], "input phải tác động tới sim")
        finally:
            server.stop()
        self.assertFalse(server.game._thread.is_alive())
        self.assertFalse(server._thread.is_alive())


class LiveServiceTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.tuning["quan"]["first_customer_tick"] = 4
        self.tuning["quan"]["duration_s"] = 1
        self.fish = "ca_loc_nuong_trui"
        self.salad = "goi_bong_sung"

    @staticmethod
    def state(game):
        return json.loads(game.state_json())

    def open_day(self, hold):
        game = LiveGame("day", self.tuning, {"gather": {"hold": hold}}, 1)
        game.continue_intro(self.state(game))
        game.set_input({"interact": True})
        game._tick_once()
        state = self.state(game)
        self.assertEqual(state["phase"], "quan")
        self.assertTrue(state["intro_pending"])
        return game, state

    def test_planned_menu_is_validated_before_opening_and_limits_new_orders(self):
        game, state = self.open_day(["ca_loc", "bong_sung", "bong_sung", "bong_dien_dien"])
        self.assertEqual(state["opening_menu"], [self.fish, self.salad])
        self.assertFalse(state["can_wait"])
        for invalid in [None, "all", [1], [{}], [self.salad, self.salad], ["canh_chua_ca_loc"], []]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                game.continue_intro({**state, "menu_ids": invalid})
            self.assertEqual(self.state(game), state)
        with self.assertRaises(ValueError):
            game.continue_intro({**state, "tick": state["tick"] - 1, "menu_ids": [self.fish]})
        game.continue_intro({**state, "menu_ids": [self.salad]})
        self.assertNotIn("opening_menu", self.state(game))
        with self.assertRaises(ValueError):
            game.continue_intro({**state, "menu_ids": [self.fish]})
        game.wait_for_customer(state)
        playing = self.state(game)
        self.assertEqual([c["dish_id"] for c in playing["customers"]], [self.salad])
        self.assertNotEqual(playing["tick"], state["tick"])
        self.assertFalse(playing["can_wait"])
        with self.assertRaises(ValueError):
            game.wait_for_customer(state)
        self.assertEqual(self.state(game), playing)

    def test_opening_menu_uses_unreserved_fresh_items_and_preserves_prior_order(self):
        scenario = {
            "stock": [{"kind": "ca_loc", "id": "I1", "fresh": 100},
                      {"kind": "ca_loc", "id": "I2", "fresh": 10},
                      {"kind": "bong_sung", "id": "I3", "fresh": 100},
                      {"kind": "bong_sung", "id": "I4", "fresh": 100}],
            "customers": [{"id": "C7", "table_id": "T1", "dish_id": self.fish,
                           "reserved": ["I1"], "order_status": "reserved"}],
        }
        game = LiveGame("quan", self.tuning, scenario, 1, start_in_menu=True)
        state = self.state(game)
        self.assertEqual(state["opening_menu"], [self.salad])
        self.assertEqual(state["opening_stock"], {"bong_sung": 2})
        self.assertEqual(state["available_stock"], {"bong_sung": 2})
        game.continue_intro({**state, "menu_ids": [self.salad]})
        for _ in range(self.tuning["quan"]["first_customer_tick"]):
            game._tick_once()
        by_table = {c["table_id"]: c for c in self.state(game)["customers"]}
        self.assertEqual(by_table["T1"]["reserved"], ["I1"])
        self.assertEqual(by_table["T1"]["dish_id"], self.fish)
        self.assertEqual(by_table["T2"]["dish_id"], self.salad)

    def test_wait_runs_normal_ticks_to_arrival_and_discards_pending_inputs(self):
        scenario = {"stock": {"ca_loc": 2}}
        game = LiveGame("quan", self.tuning, scenario, 42, start_in_menu=True)
        control = LiveGame("quan", self.tuning, scenario, 42, start_in_menu=True)
        for session in (game, control):
            session.continue_intro(self.state(session))
        state = self.state(game)
        self.assertTrue(state["can_wait"])
        self.assertFalse(state["wait_to_close"])
        for wrong in [{"phase": "shop"}, {"day": 7}, {"service_id": "other"}]:
            with self.assertRaises(ValueError):
                game.wait_for_customer({**state, **wrong})
            self.assertEqual(self.state(game), state)
        game.set_input({"move": [1, 0], "interact": True})
        game.wait_for_customer(state)
        for _ in range(self.tuning["quan"]["first_customer_tick"]):
            control._tick_once()
        self.assertEqual(self.state(game), self.state(control))
        game._tick_once()
        control._tick_once()
        self.assertEqual(self.state(game), self.state(control))

    def test_empty_menu_finishes_quan_and_day_wait_stops_at_shop_intro(self):
        for mode in ("quan", "day"):
            with self.subTest(mode=mode):
                if mode == "day":
                    game, state = self.open_day([])
                else:
                    game = LiveGame(mode, self.tuning, {}, 1, start_in_menu=True)
                    state = self.state(game)
                self.assertEqual(state["opening_menu"], [])
                with self.assertRaises(ValueError):
                    game.wait_for_customer(state)
                game.continue_intro({**state, "menu_ids": []})
                self.assertTrue(self.state(game)["wait_to_close"])
                game.wait_for_customer(state)
                end = self.state(game)
                self.assertIn("quan_end", [event["name"] for event in end["events"]])
                self.assertFalse(end.get("can_wait", False))
                if mode == "day":
                    self.assertEqual((end["phase"], end["phase_tick"], end["intro_pending"]), ("shop", 0, True))
                else:
                    self.assertTrue(end["finished"])

    def test_pause_and_restart_invalidate_wait_and_stale_opening(self):
        game = LiveGame("quan", self.tuning, {}, 1, start_in_menu=True)
        opening = self.state(game)
        game.continue_intro(opening)
        game.set_input({"pause": True})
        game._tick_once()
        paused = self.state(game)
        self.assertFalse(paused["can_wait"])
        with self.assertRaises(ValueError):
            game.wait_for_customer(opening)
        self.assertEqual(self.state(game), paused)
        game.restart()
        with self.assertRaises(ValueError):
            game.continue_intro({**opening, "menu_ids": []})
        game.continue_intro(self.state(game))
        with self.assertRaises(ValueError):
            game.wait_for_customer(opening)

    def test_wait_label_accounts_for_schedule_and_items_spoiling_before_arrival(self):
        for scenario in [
            {"stock": {"ca_loc": 1}, "random_customers": False},
            {"stock": [{"kind": "ca_loc", "id": "I1", "fresh": 30.01}]},
        ]:
            with self.subTest(scenario=scenario):
                game = LiveGame("quan", self.tuning, scenario, 1, start_in_menu=True)
                opening = self.state(game)
                game.continue_intro(opening)
                self.assertTrue(self.state(game)["wait_to_close"])
                self.assertEqual(self.state(game)["stock"], opening["stock"])
                game.wait_for_customer(opening)
                self.assertTrue(self.state(game)["finished"])
        self.tuning["quan"]["first_customer_tick"] = self.tuning["quan"]["duration_s"] * 60
        game = LiveGame("quan", self.tuning, {"stock": {"ca_loc": 1}}, 1)
        self.assertTrue(self.state(game)["wait_to_close"])

    def test_gather_net_metadata_matches_active_tier(self):
        tiers = json.loads((Path(__file__).parent / "fixtures/p2_net_upgrades.json").read_text())
        self.tuning["shop"]["upgrades"]["net"] = tiers
        tier = tiers[0]
        game = LiveGame("day", self.tuning, {"day": {"upgrades": {"net": tier["level"]}}}, 1)
        self.assertEqual(self.state(game)["active_net"], tier)
        plain = LiveGame("gather", self.tuning, {}, 1)
        self.assertNotIn("active_net", self.state(plain))


class LiveDayTest(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.session.done = False
        room = SimpleNamespace(menu_ids=[], menu={}, _available_stock=lambda: {})
        self.session.sim = SimpleNamespace(phase="gather", reason=None, cur=room)
        self.session.initial_rows.return_value = []
        self.session.step.return_value = []
        self.state = {"mode": "day", "day": 1, "phase": "gather", "tick": 0, "state": "playing"}
        self.session.snapshot.side_effect = lambda: dict(self.state)
        tuning = load_contract()["tuning"]
        with patch("chonoi.live.Session", return_value=self.session) as build:
            self.game = LiveGame("day", tuning, {}, 42)
        build.assert_called_once_with("day", tuning, {}, 42, None, days=5)

    def test_intro_gates_ticks_and_ignores_inputs_until_current_intro_is_dismissed(self):
        self.game.set_input({"move": [1, 0], "interact": True})
        self.game._tick_once()
        self.session.step.assert_not_called()
        with self.assertRaisesRegex(ValueError, "đã thay đổi"):
            self.game.continue_intro({**self.state, "phase": "quan"})
        self.game.continue_intro(self.state)
        self.game._tick_once()
        inp = self.session.step.call_args.args[0]
        self.assertEqual(inp.move, (0, 0))
        self.assertFalse(inp.pressed("interact"))

        self.state.update(phase="quan", tick=1, reputation=3, customers=[])
        self.session.step.return_value = [{"name": "phase_start", "phase": "quan", "data": {}}]
        self.game.set_input({"move": [1, 0], "interact": True})
        self.game._tick_once()
        self.assertTrue(json.loads(self.game.state_json())["intro_pending"])
        self.game._tick_once()
        self.assertEqual(self.session.step.call_count, 2)
        self.game.continue_intro(self.state)
        self.session.step.return_value = []
        self.game._tick_once()
        inp = self.session.step.call_args.args[0]
        self.assertEqual(inp.move, (0, 0))
        self.assertFalse(inp.held["interact"])

    def test_shift_stats_outlive_recent_event_buffer_and_buy_is_one_shot(self):
        self.game.continue_intro(self.state)
        self.state.update(phase="quan", reputation=3, customers=[{"id": "C1", "dish_id": "goi_bong_sung"}])
        self.session.step.return_value = [{"name": "phase_start", "phase": "quan", "data": {}}]
        self.game._tick_once()
        self.game.continue_intro(self.state)

        self.session.step.return_value = [
            {"name": "paid", "data": {"order_id": "C1", "amount": 48, "tip": 8}},
            {"name": "customer_left", "data": {"order_id": "C2"}},
            *[{"name": "no_dish", "data": {}}] * 45,
            {"name": "quan_end", "day": 1, "data": {"reputation": 2.7}},
            {"name": "phase_start", "phase": "shop", "data": {}},
        ]
        self.game._tick_once()
        self.state.update(phase="shop", tick=2)
        self.session.sim.phase = "shop"
        self.game.tuning.setdefault("shop", {"max_ticks": 600, "upgrades": {}})
        snapshot = json.loads(self.game.state_json())
        self.assertFalse(any(e["name"] == "paid" for e in snapshot["events"]))
        self.assertEqual(snapshot["best_sellers"], {"goi_bong_sung": 1})
        self.assertEqual(snapshot["day_result"], {
            "day": 1, "served": 1, "left": 1, "shift_earned": 48, "tips": 8, "reputation_delta": -0.3,
        })

        self.game.continue_intro(self.state)
        self.session.step.return_value = []
        self.game.set_input({"buy": "oxygen", "shop_done": True})
        self.game._tick_once()
        inp = self.session.step.call_args.args[0]
        self.assertEqual(inp.buy, "oxygen")
        self.assertTrue(inp.pressed("shop_done"))
        self.game._tick_once()
        self.assertIsNone(getattr(self.session.step.call_args.args[0], "buy", None))


if __name__ == "__main__":
    unittest.main()
