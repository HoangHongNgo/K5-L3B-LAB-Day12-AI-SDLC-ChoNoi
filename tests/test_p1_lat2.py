"""Test hộp đen Lát 2 (haiquanng): hái nút, bắt cá, cập bến, ghi kho — AC-P1-04, 05, 06.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p1_lat2 -v
Mọi số liệu đọc từ game.contract.json; chỉ chạy headless và đọc JSONL / file kho.
"""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


G = tuning()["gather"]
TICK = tuning()["tick_hz"]
REGROW = int(round(G["regrow_s"] * TICK))
CATCH_CD = int(round(G["catch_cooldown_s"] * TICK))
FAR = [80, 0]  # mặt nước, xa bến


def run_gather(w, scenario, input_frames, ticks, inventory_out=None):
    sc = write_json(w.path("sc.json"), {"gather": scenario})
    inp = write_json(w.path("in.json"), frames(*input_frames))
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc, "--inputs", inp,
            "--out", w.path("o.jsonl"), "--snapshot-every", "1"]
    if inventory_out:
        args += ["--inventory-out", inventory_out]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


def press(tick, button="interact"):
    """Cạnh lên ở `tick`, nhả ở tick sau."""
    return [{"tick": tick, button: True}, {"tick": tick + 1, button: False}]


def node(nid, kind, pos, regrow=0):
    return {"id": nid, "kind": kind, "pos": pos, "regrow_ticks": regrow}


def fish(fid, kind, pos):
    return {"id": fid, "kind": kind, "pos": pos}


class Gather(unittest.TestCase):
    """AC-P1-04: hái chỉ ở mặt nước, đúng mép vẫn hái, hold_full không đổi nút, mọc lại sau regrow_s."""

    def test_gather_at_exact_radius(self):
        with Workdir() as w:
            pos = [FAR[0] + G["interact_radius"], 0]
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": [node("N1", "bong_sung", pos)], "fish": []},
                              press(0), 2)
            ev = events(rows, "gather")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["tick"], 1)
            self.assertEqual(ev[0]["data"], {"node_id": "N1", "kind": "bong_sung", "count": G["node_yield"]})
            snap = [s for s in snapshots(rows) if s["tick"] == 1][0]
            self.assertEqual(snap["hold"], ["bong_sung"] * G["node_yield"])
            self.assertEqual(snap["nodes"][0]["ready"], False)
            self.assertEqual(snap["nodes"][0]["regrow_ticks"], REGROW)

    def test_no_gather_underwater(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 1.5]}, "nodes": [node("N1", "bong_sung", [50, 0])],
                                  "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(snapshots(rows)[-1]["hold"], [])

    def test_out_of_radius_nothing(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": [node("N1", "bong_sung", [FAR[0] + 2.01, 0])],
                                  "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(events(rows, "hold_full"), [])

    def test_nearest_then_smallest_id(self):
        with Workdir() as w:
            nodes = [node("N2", "bong_sung", [FAR[0] - 1, 0]), node("N1", "bong_dien_dien", [FAR[0] + 1, 0]),
                     node("N3", "bong_sung", [FAR[0] + 0.5, 0])]
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": nodes, "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N3")
        with Workdir() as w:
            nodes = [node("N2", "bong_sung", [FAR[0] - 1, 0]), node("N1", "bong_dien_dien", [FAR[0] + 1, 0])]
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": nodes, "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N1")

    def test_skip_not_ready_node(self):
        with Workdir() as w:
            nodes = [node("N1", "bong_sung", FAR, regrow=500), node("N2", "bong_dien_dien", [FAR[0] + 1, 0])]
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": nodes, "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")

    def test_hold_full_keeps_node(self):
        with Workdir() as w:
            full = ["ca_loc"] * G["hold_capacity"]
            rows = run_gather(w, {"player": {"pos": FAR}, "hold": full,
                                  "nodes": [node("N1", "bong_sung", FAR)], "fish": []}, press(0), 2)
            self.assertEqual(events(rows, "gather"), [])
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1)
            self.assertEqual(hf[0]["data"], {"action": "gather", "node_id": "N1",
                                             "required": G["node_yield"], "free": 0})
            last = snapshots(rows)[-1]
            self.assertEqual(last["hold"], full)
            self.assertEqual(last["nodes"][0]["ready"], True)
            self.assertEqual(last["nodes"][0]["regrow_ticks"], 0)

    def test_regrow_after_regrow_s(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": [node("N1", "bong_sung", FAR)], "fish": []},
                              press(0), REGROW + 3)
            g = events(rows, "gather")[0]["tick"]
            rg = events(rows, "node_regrown")
            self.assertEqual(len(rg), 1)
            self.assertEqual(rg[0]["tick"] - g, REGROW)
            self.assertEqual(rg[0]["data"], {"node_id": "N1"})

    def test_cannot_regather_while_regrowing(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": FAR}, "nodes": [node("N1", "bong_sung", FAR)], "fish": []},
                              press(0) + press(5), 8)
            self.assertEqual(len(events(rows, "gather")), 1)
            self.assertEqual(snapshots(rows)[-1]["hold"], ["bong_sung"])


if __name__ == "__main__":
    unittest.main()
