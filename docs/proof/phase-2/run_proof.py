"""Sinh bằng chứng Phase 2 (TICKET-02 mục 5, DoD) vào docs/proof/phase-2/, tái lập được.

Chạy từ gốc repo, trên commit sẽ gắn tag `phase-2`:
    python3 docs/proof/phase-2/run_proof.py

Ghi ra (mỗi file có dòng commit đã chạy):
- revision.txt                     commit + contract_version
- tests.log                        toàn bộ unittest
- integration.{jsonl,json,quan.jsonl,txt}
                                   smoke gather --inventory-out -> quan --inventory (seed 42, dock.json Phase 1)
- day-1.jsonl, day-3.jsonl         --mode day --days 1 / --days 3 (seed 42, không input: hết giờ từng pha)
- cmp.txt                          chạy hai lần cùng seed, so từng byte
- timing.txt                       thời gian headless 1 Ngày không pause (yêu cầu ≤ 20 s, ≤ 22.200 tick)
- summary.txt                      tóm tắt PASS / FAIL / CHƯA CHẠY ĐƯỢC từng mục (ghi trung thực)

Mục nào chưa chạy được (ví dụ contract chưa lên v1.1, chưa có cờ --days) được ghi CHƯA CHẠY ĐƯỢC
kèm stderr thật, không bỏ qua. Ảnh HUD/menu/pause và số FPS do RachalHys gửi, thêm tay vào thư mục này.
"""

import filecmp
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "docs", "proof", "phase-2")
P1 = os.path.join(ROOT, "docs", "proof", "phase-1")
TMP = os.path.join(OUT, ".tmp")
SUMMARY = []


def headless_cmd():
    import shlex
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return shlex.split(json.load(f)["headless_cmd"])


def run(*args):
    t0 = time.perf_counter()
    p = subprocess.run([*headless_cmd(), *args], cwd=ROOT, capture_output=True, text=True)
    err = p.stderr.strip().splitlines()
    return p.returncode, (err[-1] if err else ""), time.perf_counter() - t0


def note(item, status, detail):
    line = f"{item}: {status} — {detail}"
    SUMMARY.append(line)
    print(line)


def out(name):
    return os.path.join(OUT, name)


def main():
    os.makedirs(TMP, exist_ok=True)
    rev = subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", ROOT, "status", "--porcelain", "--", "chonoi", "tests",
                                     "game.contract.json"], text=True).strip()
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        version = json.load(f)["contract_version"]
    with open(out("revision.txt"), "w", encoding="utf-8") as f:
        f.write(f"{rev}\ncontract_version {version}\n{'có thay đổi chưa commit trong chonoi/tests/contract' if dirty else 'cây sạch'}\n")
    header = f"# commit {rev} · contract {version}\n"

    # 1. toàn bộ test
    p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT,
                       env=dict(os.environ, PYTHONPATH="tests:."), capture_output=True, text=True)
    with open(out("tests.log"), "w", encoding="utf-8") as f:
        f.write(header + p.stderr)
    last = [ln for ln in p.stderr.splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
    note("tests.log", "PASS" if p.returncode == 0 else "FAIL", " · ".join(last[-2:]))

    # 2. smoke tích hợp gather -> quan (TICKET-02 phút 20)
    g, inv, q = out("integration.jsonl"), out("integration.json"), out("integration.quan.jsonl")
    c1, e1, _ = run("--mode", "gather", "--seed", "42", "--scenario", os.path.join(P1, "dock.json"),
                    "--inputs", os.path.join(P1, "dock-inputs.json"), "--ticks", "1", "--out", g, "--inventory-out", inv)
    c2, e2, _ = run("--mode", "quan", "--seed", "42", "--inventory", inv, "--ticks", "0", "--out", q)
    if c1 == 0 and c2 == 0:
        with open(inv, encoding="utf-8") as f:
            items = json.load(f)["items"]
        with open(q, encoding="utf-8") as f:
            stock = json.loads(f.readline())["stock"]
        ok = items == stock
        detail = f"kho {items} · quán tick 0 stock {stock}"
        note("integration", "PASS" if ok else "FAIL", detail)
    else:
        detail = f"gather exit {c1} {e1} · quan exit {c2} {e2}"
        note("integration", "FAIL", detail)
    with open(out("integration.txt"), "w", encoding="utf-8") as f:
        f.write(header + detail + "\n")

    # 3. day --days 1 / 3, lặp cùng seed, thời gian 1 Ngày
    for days in (1, 3):
        path = out(f"day-{days}.jsonl")
        code, err, secs = run("--mode", "day", "--days", str(days), "--seed", "42", "--ticks", str(22200 * days + 10),
                              "--out", path)
        if code != 0:
            note(f"day-{days}.jsonl", "CHƯA CHẠY ĐƯỢC", f"exit {code}: {err}")
            if os.path.exists(path):
                os.remove(path)
            continue
        with open(path, encoding="utf-8") as f:
            rows = [json.loads(ln) for ln in f]
        end = rows[-1]
        plans = [r["data"] for r in rows if r.get("type") == "event" and r.get("name") == "day_plan"]
        note(f"day-{days}.jsonl", "PASS" if end.get("days_completed") == days and end.get("reason") == "days_complete"
             else "FAIL", f"end {end.get('reason')} days_completed {end.get('days_completed')} · ticks {end.get('ticks')} "
             f"· {len(plans)} day_plan · {secs:.2f} s")
        if days == 1:
            again = os.path.join(TMP, "day-1-again.jsonl")
            run("--mode", "day", "--days", "1", "--seed", "42", "--ticks", "22210", "--out", again)
            same = os.path.exists(again) and filecmp.cmp(path, again, shallow=False)
            with open(out("cmp.txt"), "w", encoding="utf-8") as f:
                f.write(header + f"day --days 1 seed 42 chạy hai lần: {'giống từng byte' if same else 'KHÁC'}\n")
            note("cmp.txt", "PASS" if same else "FAIL", "hai lần cùng seed giống từng byte" if same else "khác")
            with open(out("timing.txt"), "w", encoding="utf-8") as f:
                f.write(header + f"headless 1 Ngày: {secs:.2f} s, {end.get('ticks')} tick (yêu cầu ≤ 20 s, ≤ 22.200 tick)\n")
            note("timing.txt", "PASS" if secs <= 20 and end.get("ticks", 10**9) <= 22200 else "FAIL",
                 f"{secs:.2f} s, {end.get('ticks')} tick")

    with open(out("summary.txt"), "w", encoding="utf-8") as f:
        f.write(header + "\n".join(SUMMARY) + "\n")
    for name in os.listdir(TMP):
        os.remove(os.path.join(TMP, name))
    os.rmdir(TMP)


if __name__ == "__main__":
    main()
