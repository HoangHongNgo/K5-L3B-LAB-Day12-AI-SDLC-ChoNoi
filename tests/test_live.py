"""Test cửa sổ chơi trực tiếp (chonoi.live). Chỉ dành cho starter Python: nhóm đổi ngôn ngữ thì xóa file này."""

import json
import time
import unittest
import urllib.error
import urllib.request
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


class LiveDayTest(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.session.done = False
        self.session.sim = SimpleNamespace(phase="gather", reason=None)
        self.session.initial_rows.return_value = []
        self.session.step.return_value = []
        self.state = {"mode": "day", "day": 1, "phase": "gather", "tick": 0}
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
