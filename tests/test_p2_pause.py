"""AC-P2-12: pause ở lớp bọc chung `chonoi/sim/pause.py` cho cả ba mode (Test Contract v1.1, mục 4.2)."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import BUTTONS_V11, InputPlayer, InputState, load_frames
from chonoi.runner import Session
from chonoi.sim.pause import PauseSim
from fixtures.fresh import stocked
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

TUNING = load_contract()["tuning"]
GATHER = {"random_fish": False, "monsters": []}
KHO = stocked(bong_sung=2, ca_loc=1)


def play(session, frame_list, ticks):
    """Chạy `ticks` bước; trả [(tick_ngoài, name)], và danh sách snapshot sau mỗi bước."""
    ip = InputPlayer(frame_list)
    evs, snaps = [], []
    for k in range(ticks):
        for row in session.step(ip.advance(k)):
            evs.append((row["tick"], row["name"]))
        snaps.append(copy.deepcopy(session.snapshot()))  # snapshot có thể trả tham chiếu tới state sống
    return evs, snaps


class FakeSim:
    """Sim giả ghi lại input nhận được; đủ giao diện step/snapshot/done."""

    mode, phase = "day", "gather"
    money = earned = 0
    reputation = 3.0
    time_left_ticks = 10

    def __init__(self):
        self.done = False
        self.seen = []

    def step(self, inp):
        self.seen.append((inp.pressed("interact"), inp.buy))
        return [("tick", {}, {"phase": "quan", "day": 2})]

    def snapshot(self):
        return {}


class TestPauseWrapper(unittest.TestCase):
    def inp(self, *edges, buy=None):
        return InputState((0.0, 0.0), {}, set(edges), buy)

    def test_enter_pause_does_not_run_sim_and_emits_paused(self):
        sim, w = FakeSim(), None
        w = PauseSim(sim)
        self.assertEqual(w.step(self.inp("pause", "interact")), [("paused", {})])
        self.assertTrue(w.paused)
        self.assertEqual(sim.seen, [])
        self.assertEqual(w.sim_tick, 0)

    def test_paused_ignores_action_edges_and_buy(self):
        sim = FakeSim()
        w = PauseSim(sim)
        w.step(self.inp("pause"))
        self.assertEqual(w.step(self.inp("interact", buy="oxygen")), [])
        self.assertEqual(w.step(self.inp("catch", "shop_done")), [])
        self.assertEqual(sim.seen, [])

    def test_resume_runs_gameplay_in_same_step(self):
        sim = FakeSim()
        w = PauseSim(sim)
        w.step(self.inp("pause"))
        evs = w.step(self.inp("pause", "interact", buy="hp"))
        self.assertEqual([e[0] for e in evs], ["resumed", "tick"])
        self.assertEqual(sim.seen, [(True, "hp")])  # cạnh hành động của bước resume vẫn chạy
        self.assertFalse(w.paused)
        self.assertEqual(w.sim_tick, 1)

    def test_events_with_context_pass_through(self):
        w = PauseSim(FakeSim())
        self.assertEqual(w.step(self.inp())[0][2], {"phase": "quan", "day": 2})

    def test_pause_edge_ignored_once_sim_done(self):
        sim = FakeSim()
        sim.done = True
        w = PauseSim(sim)
        w.step(self.inp("pause"))
        self.assertFalse(w.paused)

    def test_clock_attributes_prefer_inner(self):
        sim = FakeSim()
        sim.phase_tick = 7
        sim.sim_tick = 99
        w = PauseSim(sim)
        self.assertEqual((w.sim_tick, w.phase_tick), (99, 7))
        self.assertEqual(w.mode, "day")  # chuyển tiếp thuộc tính


class TestPauseGather(unittest.TestCase):
    def session(self):
        return Session("gather", TUNING, GATHER, seed=1)

    def test_pause_freezes_clock_and_position(self):
        fr = [{"tick": 0, "move": [0, 1]}, {"tick": 5, "pause": True}, {"tick": 6, "pause": False},
              {"tick": 20, "pause": True}, {"tick": 21, "pause": False}]
        s = self.session()
        evs, snaps = play(s, fr, 30)
        self.assertEqual([e for e in evs if e[1] in ("paused", "resumed")],
                         [(6, "paused"), (21, "resumed")])  # tick sự kiện = k + 1
        before = snaps[5]  # sau bước 5 (bước vào pause)
        self.assertEqual(before["state"], "paused")
        self.assertEqual(before["sim_tick"], 5)
        for i in range(6, 20):  # đang pause: mọi thứ đứng yên, tick ngoài vẫn chạy
            snap = snaps[i]
            self.assertEqual(snap["tick"], i + 1)
            self.assertEqual((snap["sim_tick"], snap["state"]), (5, "paused"))
            self.assertEqual(snap["time_left_ticks"], before["time_left_ticks"])
            self.assertEqual(snap["player"]["pos"], before["player"]["pos"])
            self.assertEqual(snap["player"]["oxygen_ticks"], before["player"]["oxygen_ticks"])
        after = snaps[20]  # bước 20 là cạnh resume: gameplay chạy ngay trong bước
        self.assertEqual((after["state"], after["sim_tick"]), ("playing", 6))
        self.assertEqual(after["time_left_ticks"], before["time_left_ticks"] - 1)
        self.assertGreater(after["player"]["pos"][1], before["player"]["pos"][1])

    def test_pause_edge_preempts_interact_at_dock(self):
        """Cạnh pause xét trước: interact cùng bước không cập bến."""
        s = self.session()
        evs, _ = play(s, [{"tick": 0, "pause": True, "interact": True}], 3)
        self.assertEqual(evs, [(1, "paused")])
        self.assertFalse(s.done)

    def test_actions_while_paused_are_ignored_and_not_queued(self):
        fr = [{"tick": 0, "pause": True}, {"tick": 1, "pause": False}, {"tick": 2, "interact": True},
              {"tick": 3, "interact": False}, {"tick": 4, "pause": True}]
        s = self.session()
        evs, _ = play(s, fr, 6)
        self.assertEqual([e[1] for e in evs], ["paused", "resumed"])
        self.assertFalse(s.done, "interact bấm lúc pause không được dồn lại để cập bến sau khi resume")

    def test_held_pause_makes_no_new_edge(self):
        s = self.session()
        evs, _ = play(s, [{"tick": 0, "pause": True}], 10)  # giữ pause suốt: chỉ một cạnh lên
        self.assertEqual([e[1] for e in evs], ["paused"])

    def test_resume_then_docked_keeps_working(self):
        fr = [{"tick": 0, "pause": True}, {"tick": 1, "pause": False}, {"tick": 2, "pause": True},
              {"tick": 3, "interact": True, "pause": False}]
        s = self.session()
        evs, _ = play(s, fr, 5)
        self.assertEqual([e[1] for e in evs], ["paused", "resumed", "gather_end"])
        self.assertTrue(s.done)

    def test_end_row_and_sim_tick_exclude_paused_steps(self):
        fr = [{"tick": 0, "pause": True}, {"tick": 1, "pause": False}, {"tick": 10, "pause": True},
              {"tick": 11, "interact": True, "pause": False}]
        s = self.session()
        play(s, fr, 12)
        end = s.end_row()
        self.assertEqual(end["ticks"], 12)
        self.assertEqual(end["sim_tick"], 2)  # chỉ hai bước gameplay: bước resume (tick 10) và bước docked (tick 11)
        self.assertEqual(end["reason"], "docked")


class TestPauseQuan(unittest.TestCase):
    def test_customer_schedule_follows_phase_tick_not_outer_tick(self):
        first = TUNING["quan"]["first_customer_tick"]
        pause_len = 25
        fr = [{"tick": 10, "pause": True}, {"tick": 11, "pause": False},
              {"tick": 10 + pause_len, "pause": True}, {"tick": 11 + pause_len, "pause": False}]
        s = Session("quan", TUNING, {}, seed=1, inventory=KHO)
        evs, snaps = play(s, fr, first + pause_len + 5)
        arrived = [t for t, n in evs if n == "customer_arrived"]
        self.assertEqual(arrived[0], first + pause_len)
        resumed_at = [t for t, n in evs if n == "resumed"][0]
        self.assertEqual(snaps[resumed_at - 1]["phase_tick"], snaps[10]["phase_tick"] + 1)
        self.assertEqual(snaps[20]["state"], "paused")
        self.assertEqual(snaps[10 + 5]["phase_tick"], snaps[10]["phase_tick"])  # đứng yên trong pause


class TestPauseHeadless(unittest.TestCase):
    def test_inputs_file_accepts_pause_and_buy_and_output_is_deterministic(self):
        fr = frames({"tick": 0, "move": [0, 1]}, {"tick": 3, "pause": True}, {"tick": 4, "pause": False},
                    {"tick": 8, "pause": True, "buy": "oxygen", "shop_done": True, "attack": True, "photo": True},
                    {"tick": 9, "pause": False}, {"tick": 12, "pause": True}, {"tick": 13, "pause": False},
                    {"tick": 16, "pause": True}, {"tick": 17, "pause": False})
        outs = []
        with Workdir() as w:
            inp = write_json(w.path("in.json"), fr)
            for i in range(2):
                out = w.path(f"o{i}.jsonl")
                code, err = run_headless("--mode", "gather", "--seed", "3", "--ticks", "20", "--snapshot-every", "1", "--inputs", inp,
                                         "--out", out)
                self.assertEqual(code, 0, err)
                with open(out, "rb") as f:
                    outs.append(f.read())
            rows = read_jsonl(out)
        self.assertEqual(outs[0], outs[1])
        self.assertEqual([r["name"] for r in events(rows) if r["name"] in ("paused", "resumed")],
                         ["paused", "resumed", "paused", "resumed"])
        snaps = snapshots(rows)
        paused = [s for s in snaps if s["state"] == "paused"]
        self.assertTrue(paused)
        self.assertTrue(all(s["sim_tick"] < s["tick"] for s in paused))
        self.assertEqual(rows[-1]["ticks"], 20)

    def test_bad_buy_value_is_exit_2(self):
        for bad in ("", 5, True):
            with self.subTest(buy=bad), Workdir() as w:
                inp = write_json(w.path("in.json"), frames({"tick": 0, "buy": bad}))
                code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--inputs", inp,
                                       "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2)

    def test_v10_loader_still_rejects_v11_buttons(self):
        with Workdir() as w:
            inp = write_json(w.path("in.json"), frames({"tick": 0, "pause": True}))
            with self.assertRaises(Exception):
                load_frames(inp)  # mặc định v1.0
            load_frames(inp, BUTTONS_V11)


if __name__ == "__main__":
    unittest.main()
