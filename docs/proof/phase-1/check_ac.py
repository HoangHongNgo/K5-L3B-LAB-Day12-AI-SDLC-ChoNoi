"""Kiểm chứng tái lập 12 AC Phase 1 bằng headless (hộp đen) theo PRD-0 + Test Contract v1.0.

Chạy từ gốc repo:
    PYTHONPATH=tests:. python3 docs/proof/phase-1/check_ac.py > docs/proof/phase-1/contract.log

Mỗi dòng: `AC-P1-xx PASS|FAIL <mô tả>: <số liệu thật>`. Mã thoát 0 khi mọi kiểm tra PASS.
Output smoke hai tiến trình được ghi vào docs/proof/phase-1/{gather.jsonl,catch.json,quan.jsonl}.
"""

import filecmp
import json
import math
import os
import re
import shutil
import subprocess
import sys

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

PROOF = os.path.join(ROOT, "docs", "proof", "phase-1")
with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
    CONTRACT = json.load(f)
T = CONTRACT["tuning"]
G, Q, MENU, HZ = T["gather"], T["quan"], T["menu"], T["tick_hz"]
FAILS = []


def check(ac, ok, what, data):
    print(f"{ac} {'PASS' if ok else 'FAIL'} {what}: {data}")
    if not ok:
        FAILS.append(ac)


def ev(rows, name):
    return [(e["tick"], e["data"]) for e in events(rows, name)]


def run(w, mode, block, fr=(), ticks=5, extra=(), tag="o"):
    sc = write_json(w.path(f"{tag}-sc.json"), {mode: block})
    inp = write_json(w.path(f"{tag}-in.json"), frames(*fr))
    out = w.path(f"{tag}.jsonl")
    code, err = run_headless("--mode", mode, "--seed", "1", "--ticks", str(ticks), "--snapshot-every", "1",
                             "--scenario", sc, "--inputs", inp, "--out", out, *extra)
    assert code == 0, err
    return read_jsonl(out)


def snap(rows, tick):
    return [s for s in snapshots(rows) if s["tick"] == tick][0]


def press(t, b="interact"):
    return [{"tick": t, b: True}, {"tick": t + 1, b: False}]


def ac01(w):
    req = {"contract_version", "team", "team_size", "headless_cmd", "run_cmd", "build_cmd", "tuning"}
    with open(os.path.join(ROOT, "TEAM.md"), encoding="utf-8") as f:
        members = [ln for ln in f if re.match(r"^\| .+ \| \S+ \| ", ln) and "GitHub handle" not in ln
                   and not ln.startswith("|---")]
    sample = os.path.join(ROOT, "docs", "contracts", "inventory.sample.json")
    code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", sample,
                             "--out", w.path("s.jsonl"))
    stock = snapshots(read_jsonl(w.path("s.jsonl")))[0]["stock"] if code == 0 else None
    with open(sample, encoding="utf-8") as f:
        items = json.load(f)["items"]
    ok = (req <= set(CONTRACT) and CONTRACT["contract_version"] in ("1.0", "1.1") and T["tick_hz"] == 60
          and CONTRACT["team_size"] == len(members) and stock == items)
    check("AC-P1-01", ok, "khóa Test Contract (v1.0, regression ở v1.1), team_size khớp TEAM.md, quán nạp kho mẫu",
          {"version": CONTRACT["contract_version"], "team_size": CONTRACT["team_size"],
           "TEAM.md": len(members), "stock": stock})


def ac02(w):
    rows = run(w, "gather", {"player": {"pos": [20, 10], "oxygen_ticks": 1}, "fish": [], "nodes": []}, ticks=62)
    empty, choke = ev(rows, "oxygen_empty"), ev(rows, "choke")
    check("AC-P1-02", empty == [(1, {"oxygen_ticks": 0})] and choke == [(60, {"hp": G["hp_max"] - 1})],
          "chạm oxy 0 ở t=1, ngạt ở t+59", {"oxygen_empty": empty, "choke": choke})
    rows = run(w, "gather", {"player": {"pos": [20, 0.51], "vel": [0, -4], "oxygen_ticks": 0,
                                        "zero_oxy_ticks": 59}, "fish": [], "nodes": []},
               [{"tick": 0, "move": [0, -1]}], ticks=1, tag="b")
    s = snap(rows, 1)["player"]
    ok = (ev(rows, "choke") == [] and len(ev(rows, "surface")) == 1 and s["oxygen_ticks"] == G["oxygen_refill_per_tick"]
          and s["zero_oxy_ticks"] == 0 and s["hp"] == G["hp_max"])
    check("AC-P1-02", ok, "nổi lên đúng bước đáng lẽ ngạt thì hồi oxy, không ngạt",
          {"surface": ev(rows, "surface"), "oxygen": s["oxygen_ticks"], "hp": s["hp"]})


def ac03(w):
    inv = w.path("faint.json")
    rows = run(w, "gather", {"player": {"pos": [20, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                             "hold": ["ca_loc", "bong_sung", "ca_linh"], "fish": [], "nodes": []},
               ticks=3, extra=("--inventory-out", inv))
    with open(inv, encoding="utf-8") as f:
        saved = json.load(f)
    faint, end = ev(rows, "faint"), ev(rows, "gather_end")
    ok = (faint == [(1, {"cause": "choke", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0})]
          and end == [(1, {"reason": "fainted", "inventory": {"items": {}}})] and saved == {"items": {}}
          and rows[-1]["reason"] == "fainted")
    check("AC-P1-03", ok, "Máu 0 -> faint (lost LIFO) -> gather_end fainted, kho rỗng",
          {"faint": faint, "gather_end": end, "file": saved})


def ac04(w):
    edge = [20 + G["interact_radius"], 0]
    regrow = int(round(G["regrow_s"] * HZ))
    rows = run(w, "gather", {"player": {"pos": [20, 0]}, "nodes": [{"id": "N1", "kind": "bong_sung", "pos": edge}],
                             "fish": []}, press(0), ticks=regrow + 2)
    g, rg = ev(rows, "gather"), ev(rows, "node_regrown")
    ok = g == [(1, {"node_id": "N1", "kind": "bong_sung", "amount": G["node_yield"]})] and \
        rg == [(1 + regrow, {"node_id": "N1"})]
    check("AC-P1-04", ok, "hái đúng mép bán kính, payload amount, mọc lại sau regrow_s", {"gather": g, "node_regrown": rg})
    rows = run(w, "gather", {"player": {"pos": [20, 1.5]}, "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
                             "fish": []}, press(0), ticks=2, tag="u")
    check("AC-P1-04", ev(rows, "gather") == [], "dưới nước không hái", ev(rows, "gather"))
    full = ["ca_loc"] * G["hold_capacity"]
    rows = run(w, "gather", {"player": {"pos": [20, 0]}, "hold": full,
                             "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}], "fish": []},
               press(0), ticks=2, tag="f")
    hf, node = ev(rows, "hold_full"), snap(rows, 1)["nodes"][0]
    ok = hf == [(1, {"action": "gather", "node_id": "N1", "required": 1, "free": 0})] and node["ready"]
    check("AC-P1-04", ok, "giỏ đầy -> hold_full, nút vẫn ready", {"hold_full": hf, "ready": node["ready"]})


def ac05(w):
    cd = int(round(G["catch_cooldown_s"] * HZ))
    fish = [{"id": "F1", "kind": "ca_linh", "pos": [50, 10]}, {"id": "F2", "kind": "ca_loc", "pos": [50, 11]}]
    rows = run(w, "gather", {"player": {"pos": [50, 10]}, "nodes": [], "fish": fish},
               press(0, "catch") + press(cd - 1, "catch"), ticks=cd + 1)
    fc = ev(rows, "fish_caught")
    ok = fc == [(1, {"fish_id": "F1", "kind": "ca_linh", "yield": G["fish_yield"]["ca_linh"]})] and \
        [f["id"] for f in snap(rows, 1)["fish"]] == ["F2"]
    check("AC-P1-05", ok, f"bắt cá linh yield 3, xóa đàn; bấm lại ở t+{cd - 1} bị chặn", fc)
    rows = run(w, "gather", {"player": {"pos": [50, 10]}, "nodes": [], "fish": fish},
               press(0, "catch") + press(cd, "catch"), ticks=cd + 2, tag="c")
    fc = ev(rows, "fish_caught")
    ok = [t for t, _ in fc] == [1, 1 + cd] and fc[1][1] == {"fish_id": "F2", "kind": "ca_loc",
                                                           "yield": G["fish_yield"]["ca_loc"]}
    check("AC-P1-05", ok, f"bắt tiếp ở t+{cd} (hết hồi), cá lóc yield 1", fc)
    rows = run(w, "gather", {"player": {"pos": [50, 0]}, "nodes": [], "fish": [fish[0]]}, press(0, "catch"),
               ticks=2, tag="s")
    check("AC-P1-05", ev(rows, "fish_caught") == [], "ở mặt nước không bắt", ev(rows, "fish_caught"))
    hold = ["bong_sung"] * (G["hold_capacity"] - 2)
    rows = run(w, "gather", {"player": {"pos": [50, 10]}, "hold": hold, "nodes": [], "fish": [fish[0]]},
               press(0, "catch"), ticks=2, tag="h")
    s = snap(rows, 1)
    ok = ev(rows, "hold_full") == [(1, {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})] and \
        len(s["fish"]) == 1 and s["player"]["catch_cd_ticks"] == 0
    check("AC-P1-05", ok, "thiếu chỗ -> hold_full, giữ đàn, không hồi chiêu",
          {"hold_full": ev(rows, "hold_full"), "fish": len(s["fish"]), "cd": s["player"]["catch_cd_ticks"]})


def ac06(w):
    dock, dock_in = os.path.join(PROOF, "dock.json"), os.path.join(PROOF, "dock-inputs.json")
    outs = []
    for i in (1, 2):
        g, c, q = w.path(f"g{i}.jsonl"), w.path(f"c{i}.json"), w.path(f"q{i}.jsonl")
        assert run_headless("--mode", "gather", "--seed", "42", "--scenario", dock, "--inputs", dock_in,
                            "--ticks", "1", "--out", g, "--inventory-out", c)[0] == 0
        assert run_headless("--mode", "quan", "--seed", "42", "--inventory", c, "--ticks", "0", "--out", q)[0] == 0
        outs.append((g, c, q))
    with open(outs[0][1], encoding="utf-8") as f:
        items = json.load(f)
    stock = snapshots(read_jsonl(outs[0][2]))[0]["stock"]
    same = all(filecmp.cmp(a, b, shallow=False) for a, b in zip(outs[0], outs[1]))
    for src, name in zip(outs[0], ("gather.jsonl", "catch.json", "quan.jsonl")):
        shutil.copy(src, os.path.join(PROOF, name))
    want = {"bong_sung": 2, "ca_loc": 1}
    check("AC-P1-06", items == {"items": want} and stock == want and same,
          "smoke hai tiến trình seed 42, lặp lại giống từng byte", {"file": items, "stock": stock, "byte_identical": same})
    keep = w.path("keep.json")
    with open(keep, "w", encoding="utf-8") as f:
        f.write('{"items":{"ca_loc":9}}\n')
    assert run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--out", w.path("t.jsonl"),
                        "--inventory-out", keep)[0] == 0
    assert run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--out", w.path("t2.jsonl"),
                        "--inventory-out", w.path("new.json"))[0] == 0
    with open(keep, encoding="utf-8") as f:
        kept = f.read()
    ok = kept == '{"items":{"ca_loc":9}}\n' and not os.path.exists(w.path("new.json")) and \
        read_jsonl(w.path("t.jsonl"))[-1]["reason"] == "tick_limit"
    check("AC-P1-06", ok, "chạm --ticks: không tạo file mới, file có sẵn giữ nguyên", {"kept": kept.strip()})


def ac07(w):
    first, gap = Q["first_customer_tick"], int(round(Q["customer_interval_s"] * HZ))
    rows = run(w, "quan", {"stock": {}}, ticks=first + gap + 1)
    nd = ev(rows, "no_dish")
    check("AC-P1-07", nd == [(first, {}), (first + gap, {})], "kho rỗng -> no_dish {} theo lịch", nd)
    rows = run(w, "quan", {"stock": {"ca_loc": 1}}, ticks=first, tag="a")
    ca = ev(rows, "customer_arrived")
    c = snap(rows, first)["customers"][0]
    ok = len(ca) == 1 and ca[0][0] == first and {"order_id", "table_id", "dish_id"} <= set(ca[0][1]) and \
        ca[0][1]["dish_id"] == "ca_loc_nuong_trui" and c["order_tick"] == first and c["reserved"] == {"ca_loc": 1}
    check("AC-P1-07", ok, "khách đầu ở phase_tick 120, giữ đúng công thức",
          {"event": ca, "order_tick": c["order_tick"], "reserved": c["reserved"]})
    b = {"stock": {"ca_loc": 2, "bong_sung": 4, "ca_linh": 3, "bong_dien_dien": 1}}
    r1 = run(w, "quan", b, ticks=first + 3 * gap, tag="d1")
    r2 = run(w, "quan", b, ticks=first + 3 * gap, tag="d2")
    check("AC-P1-07", filecmp.cmp(w.path("d1.jsonl"), w.path("d2.jsonl"), shallow=False) and r1 == r2,
          "cùng seed -> JSONL giống từng byte", {"customers": len(events(r1, "customer_arrived"))})


def ac08(w):
    c = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 0, "state": "waiting",
         "patience_ticks_left": 1, "order_status": "reserved", "reserved": {"ca_loc": 1}}
    rows = run(w, "quan", {"random_customers": False, "stock": {"ca_loc": 1}, "customers": [c]}, ticks=2)
    left = ev(rows, "customer_left")
    s = snap(rows, 1)
    rep = Q["reputation_initial"] + Q["left_reputation_delta"]
    ok = left == [(1, {**left[0][1], "order_id": "C1", "table_id": "T1", "reason": "patience", "reputation": rep})] \
        and s["customers"] == [] and s["tables"][0]["customer_id"] is None and s["stock"] == {"ca_loc": 1}
    check("AC-P1-08", ok, "hết kiên nhẫn -> customer_left patience, uy tín −0.5, nhả giữ chỗ",
          {"event": left, "reputation": s["reputation"], "stock": s["stock"]})


def ac09(w):
    dish = "ca_loc_nuong_trui"
    price, cook, eat = MENU[dish]["price"], int(round(MENU[dish]["cook_s"] * HZ)), int(round(Q["eat_s"] * HZ))
    stove, table = Q["stoves"][0]["pos"], Q["tables"][0]["pos"]
    c = {"id": "C1", "table_id": "T1", "dish_id": dish, "order_tick": 0, "state": "waiting"}
    pick = cook + 1
    fr = press(0) + press(pick)
    # đi từ bếp tới cạnh bàn: tới x của bàn trước, rồi z
    fr += [{"tick": pick + 5, "move": [1, 0]}]
    tx = pick + 5 + int(round((table[0] - stove[0]) / Q["walk_speed"] * HZ)) + Q["ramp_max_ticks"]
    fr += [{"tick": tx, "move": [0, -1]}]
    tz = tx + int(round((stove[1] - 1 - table[1] - 1) / Q["walk_speed"] * HZ)) + Q["ramp_max_ticks"]
    fr += [{"tick": tz, "move": [0, 0]}] + press(tz + 10)
    rows = run(w, "quan", {"random_customers": False, "player": {"pos": [stove[0], stove[1] - 1]},
                           "stock": {"ca_loc": 1}, "customers": [c]}, fr, ticks=tz + 11 + eat + 2)
    seq = [(e["tick"], e["name"]) for e in events(rows)]
    names = [n for _, n in seq]
    cs = ev(rows, "cook_started")
    served, paid = ev(rows, "served"), ev(rows, "paid")
    tip = math.floor(price * Q["tip_rate"])
    end = rows[-1]
    rep = Q["reputation_initial"] + Q["tip_reputation"]
    ok = (names == ["cook_started", "dish_ready", "dish_picked", "served", "paid"]
          and cs[0][1]["items"] == ["ca_loc"] and cs[0][1]["base_price"] == price
          and paid[0][0] - served[0][0] == eat and served[0][1]["tip"] == tip
          and paid[0][1] == {"order_id": "C1", "table_id": "T1", "base_price": price, "tip": tip,
                             "amount": price + tip, "reason": "finished_eating"}
          and (end["money"], end["earned"]) == (price + tip, price + tip)
          and abs(end["reputation"] - rep) <= 0.01
          and end["score"] == price + tip + T["score"]["reputation_multiplier"] * math.floor(rep))
    check("AC-P1-09", ok, "nấu -> bưng -> phục vụ -> ăn 600 tick -> paid; tiền, uy tín, điểm",
          {"events": seq, "money": end["money"], "reputation": end["reputation"], "score": end["score"]})
    # ngưỡng boa: tỷ lệ kiên nhẫn sau bước 1 đúng 50% có boa, thấp hơn 1 tick thì 0
    patience = int(round(Q["patience_s"] * HZ))
    thr = int(math.ceil(patience * Q["tip_min_patience_ratio"]))
    tips = []
    for left in (thr + 1, thr):
        cc = dict(c, order_status="assigned", patience_ticks_left=left)
        r = run(w, "quan", {"random_customers": False, "player": {"pos": [table[0], table[1] + 1]}, "stock": {},
                            "hand": {"order_id": "C1", "dish_id": dish, "base_price": price}, "customers": [cc]},
                press(0), ticks=1, tag=f"tip{left}")
        tips.append(ev(r, "served")[0][1]["tip"])
    check("AC-P1-09", tips == [tip, 0], "boa ở đúng ngưỡng 50% và 0 ngay dưới ngưỡng (fixture hand theo mục D)",
          {"tips": tips})


def ac10(w):
    dish = "goi_bong_sung"
    price = MENU[dish]["price"]
    eating = {"id": "C1", "table_id": "T1", "dish_id": dish, "order_tick": 0, "state": "eating",
              "order_status": "served", "eat_ticks_left": 5, "base_price": price, "tip": 0}
    rows = run(w, "quan", {"random_customers": False, "time_left_ticks": 1, "stock": {}, "customers": [eating]},
               ticks=3)
    seq = [(e["name"], e["data"].get("reason")) for e in events(rows)]
    s = snap(rows, 1)
    ok = seq == [("paid", "closing"), ("quan_end", "time")] and s["tables"][0]["customer_id"] is None
    check("AC-P1-10", ok, "hết ca: khách đang ăn trả closing, dọn bàn trước quan_end", seq)
    waiting = {"id": "C1", "table_id": "T1", "dish_id": dish, "order_tick": 0, "state": "waiting",
               "patience_ticks_left": 1, "order_status": "reserved", "reserved": {"bong_sung": 2}}
    rows = run(w, "quan", {"random_customers": False, "time_left_ticks": 1, "stock": {"bong_sung": 2},
                           "customers": [waiting]}, ticks=3, tag="w")
    left = ev(rows, "customer_left")
    ok = [d["reason"] for _, d in left] == ["closing"] and rows[-1]["reputation"] == Q["reputation_initial"] and \
        [e["name"] for e in events(rows)][-1] == "quan_end"
    check("AC-P1-10", ok, "hết ca: khách chờ rời closing, không trừ uy tín",
          {"customer_left": left, "reputation": rows[-1]["reputation"]})
    table = Q["tables"][0]["pos"]
    carried = dict(waiting, order_status="assigned", reserved={}, patience_ticks_left=100)
    rows = run(w, "quan", {"random_customers": False, "time_left_ticks": 1, "stock": {},
                           "player": {"pos": [table[0], table[1] + 1]},
                           "hand": {"order_id": "C1", "dish_id": dish, "base_price": price},
                           "customers": [carried]}, press(0), ticks=3, tag="l")
    seq = [(e["name"], e["data"].get("reason")) for e in events(rows)]
    check("AC-P1-10", seq == [("served", None), ("paid", "closing"), ("quan_end", "time")],
          "giao đúng món ở bước cuối -> served rồi paid closing", seq)


def ac11(w):
    with open(os.path.join(ROOT, "chonoi", "web", "index.html"), encoding="utf-8") as f:
        html = f.read()
    gather_fields = ["time_left_ticks", "oxygen_ticks", "hp", "hold"]
    quan_fields = ["stock", "reserved", "patience_ticks_left", "dish_id", "cook_ticks_left", "hand", "money",
                   "reputation"]
    missing = [k for k in gather_fields + quan_fields if k not in html]
    g = snapshots(run(w, "gather", {}, ticks=0))[0]
    q = snapshots(run(w, "quan", {}, ticks=0, tag="q"))[0]
    snap_ok = all(k in g or k in g["player"] for k in gather_fields) and \
        all(k in q for k in ("stock", "hand", "stoves", "customers", "money", "reputation"))
    check("AC-P1-11", not missing and snap_ok,
          "[chỉ kiểm tĩnh, dò chuỗi] index.html tham chiếu trường PRD mục 2, snapshot có dữ liệu; cần chơi thử + ảnh để kết luận",
          {"index.html thiếu": missing, "snapshot đủ trường": snap_ok})


def ac12(w):
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        readme = f.read()
    block = re.search(r"```bash\n(git clone.*?)```", readme, re.S)
    cmds = [ln for ln in block.group(1).splitlines() if ln.strip()] if block else []
    clone = w.path("clone")
    subprocess.run(["git", "clone", "-q", ROOT, clone], check=True)
    subprocess.run(["git", "-C", clone, "checkout", "-q", subprocess.check_output(
        ["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()], check=True)
    test = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=clone,
                          env=dict(os.environ, PYTHONPATH="tests:."), capture_output=True, text=True)
    ran = re.search(r"Ran (\d+) tests", test.stderr)
    ok = 0 < len(cmds) <= 3 and "PYTHONPATH=tests:. python3 -m unittest discover -s tests" in readme and \
        test.returncode == 0 and all(k in readme for k in ("WASD", "Space", "floor"))
    check("AC-P1-12", ok, "README ≤ 3 lệnh, phím, công thức điểm; test 1 lệnh chạy xanh trên clone sạch",
          {"lệnh khởi động": len(cmds), "test clone sạch": (test.returncode, ran.group(1) if ran else None)})


if __name__ == "__main__":
    rev = subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()
    print(f"Revision: {rev}")
    for fn in (ac01, ac02, ac03, ac04, ac05, ac06, ac07, ac08, ac09, ac10, ac11, ac12):
        with Workdir() as w:
            try:
                fn(w)
            except Exception as e:  # ghi lỗi thật thay vì dừng cả bộ
                check(fn.__name__.upper().replace("AC", "AC-P1-"), False, "lỗi khi chạy", repr(e))
    print(f"Tổng: {'tất cả PASS' if not FAILS else 'FAIL ở ' + ', '.join(sorted(set(FAILS)))}")
    sys.exit(1 if FAILS else 0)
