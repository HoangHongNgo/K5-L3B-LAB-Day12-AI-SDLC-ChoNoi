"""Run one uninterrupted, seeded campaign with a repeating menu and real player inputs."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
from time import perf_counter
import traceback

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.day import DaySim


def approach(position, destination, radius, action):
    delta = [b - a for a, b in zip(position, destination)]
    length = math.hypot(*delta)
    if length <= radius:
        return (0, 0), action
    return (delta[0] / length, delta[1] / length), None


def forage(snapshot, tuning):
    """Collect a batch for an inexpensive dish in today's menu, then moor."""
    g = tuning["gather"]
    pos = snapshot["player"]["pos"]
    dishes = snapshot["day_plan"]["dishes"]
    dish = min(dishes, key=lambda d: (sum(tuning["menu"][d]["recipe"].values()), d))
    recipe = tuning["menu"][dish]["recipe"]
    hold = Counter(it["kind"] if isinstance(it, dict) else it for it in snapshot["hold"])
    missing = {kind for kind, amount in recipe.items() if hold[kind] < amount}
    fish = [f for f in snapshot["fish"] if f["kind"] in missing]
    plants = [n for n in snapshot["nodes"] if n["kind"] in missing and n["ready"]]
    targets = plants + fish
    if targets and snapshot["hold_count"] < snapshot["hold_capacity"]:
        target = min(targets, key=lambda t: math.dist(pos, t["pos"]))
        if target["kind"] in g["fish_yield"]:
            return approach(pos, target["pos"], g["catch_radius"] * .8, "catch")
        # Ascend before approaching floating plants, so interact is valid.
        if not snapshot["player"]["at_surface"]:
            return approach(pos, [pos[0], g["dock_pos"][1]], 0, None)
        return approach(pos, target["pos"], g["interact_radius"] * .8, "interact")
    return approach(pos, g["dock_pos"], g["dock_radius"] * .8, "interact")


def serve(snapshot, tuning):
    """Cook the oldest reserved order and carry it to the customer's real table."""
    hand = snapshot["hand"]
    guests = snapshot["customers"]
    if hand:
        destinations = [table for table in snapshot["tables"] if table["customer_id"] == hand["order_id"]]
    else:
        destinations = [s for s in snapshot["stoves"] if s["state"] == "ready"]
        if not destinations and any(c["order_status"] == "reserved" for c in guests):
            destinations = [s for s in snapshot["stoves"] if s["state"] == "idle"]
    if not destinations:
        return (0, 0), None
    pos = snapshot["player"]["pos"]
    target = min(destinations, key=lambda d: math.dist(pos, d["pos"]))
    return approach(pos, target["pos"], tuning["quan"]["interact_radius"] * .7, "interact")


def campaign(tuning, seed, days, results):
    sim = DaySim(tuning, {}, Streams(seed), days=days, repeat_plan=True)
    session = Session("day", tuning, {}, seed, sim=sim)
    buttons = LiveInputs()
    next_decision = 0
    decision_interval = max(1, tuning["tick_hz"] // 10)
    limit = days * (math.ceil((tuning["gather"]["duration_s"] + tuning["quan"]["duration_s"])
                              * tuning["tick_hz"]) + tuning["shop"]["max_ticks"] + 3)
    while not session.done and session.tick < limit:
        if session.tick >= next_decision:
            snap = session.snapshot()
            phase = snap["phase"]
            if phase == "shop":
                levels = tuning["shop"]["upgrades"].get("oxygen", [])
                owned = snap["upgrades"].get("oxygen", 0)
                upgrade = next((u for u in levels if u["level"] == owned + 1), None)
                if upgrade and snap["money"] >= upgrade["price"]:
                    buttons.set(buy="oxygen")
                move, action = (0, 0), "shop_done"
            else:
                move, action = forage(snap, tuning) if phase == "gather" else serve(snap, tuning)
            buttons.set(move=move)
            if action:
                buttons.set(**{action: True})
                buttons.set(**{action: False})
            next_decision = session.tick + decision_interval
        for event in session.step(buttons.advance()):
            if event["name"] == "phase_start":
                next_decision = session.tick
            if event["name"] == "shop_end":
                totals = session.end_row()
                results.append({"day": event["day"], **{k: totals[k] for k in ("earned", "reputation", "score")}})
    if not session.done or session.sim.days_completed != days or len(results) != days:
        raise RuntimeError(f"Chỉ hoàn tất {len(results)}/{days} ngày sau {session.tick} tick")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--days", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.days < 1:
        parser.error("--days phải là số nguyên dương")
    started = perf_counter()
    results = []
    crashes = 0
    try:
        campaign(load_contract()["tuning"], args.seed, args.days, results)
    except Exception:
        crashes = 1
        traceback.print_exc()
    report = {"days": args.days, "days_completed": len(results), "crashes": crashes,
              "results": results, "duration_s": round(perf_counter() - started, 6)}
    try:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"Không ghi được {args.out}: {error}", file=sys.stderr)
        return 1
    return crashes


if __name__ == "__main__":
    sys.exit(main())
