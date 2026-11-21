"""Run the handoff across real processes and compare it with the same day transition."""
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]


def smoke():
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        inventory, scenario, inputs, output = [work / name for name in
                                               ("inventory.json", "scenario.json", "inputs.json", "out.jsonl")]

        def run(mode, ticks, *flags, expected=0):
            proc = subprocess.run([sys.executable, "-m", "chonoi.headless", "--mode", mode,
                                   "--seed", "1", "--ticks", str(ticks), "--snapshot-every", "1",
                                   "--out", str(output), *map(str, flags)], cwd=ROOT, capture_output=True, text=True)
            assert proc.returncode == expected, (proc.returncode, proc.stderr)
            return [json.loads(line) for line in output.read_text().splitlines()] if not expected else []

        item = {"id": "I1", "kind": "ca_linh", "fresh": 30}
        gather = {"hold": [item], "random_fish": False, "monsters": []}
        scenario.write_text(json.dumps({"gather": gather}))
        inventory.write_text("preserve destination")
        rows = run("gather", 1, "--scenario", scenario, "--inventory-out", inventory)
        assert inventory.read_text() == "preserve destination"
        crossed = [r for r in rows if r.get("name") == "spoiled"]
        assert len(crossed) == 1 and crossed[0]["tick"] == 1
        assert crossed[0]["data"] == {"item_id": "I1", "kind": "ca_linh", "location": "hold"}

        item["fresh"] = 100
        scenario.write_text(json.dumps({"gather": gather}))
        inputs.write_text(json.dumps({"frames": [{"tick": 0, "interact": True}]}))
        rows = run("gather", 1, "--scenario", scenario, "--inputs", inputs, "--inventory-out", inventory)
        file_items = json.loads(inventory.read_text())["items"]
        terminal = next(r for r in rows if r.get("name") == "gather_end")
        assert terminal["data"]["inventory"] == {"items": file_items}
        assert file_items[0]["id"] == "I1" and file_items[0]["kind"] == "ca_linh"
        assert math.isclose(file_items[0]["fresh"], 100 - .5 / 60, abs_tol=1e-12)
        rows = run("quan", 0, "--inventory", inventory)
        quan = next(r for r in rows if r["type"] == "snapshot")
        assert quan["stock"] == file_items
        rows = run("day", 1, "--scenario", scenario, "--inputs", inputs)
        day = next(r for r in rows if r["type"] == "snapshot" and r["phase"] == "quan")
        assert day["tick"] == 1 and day["phase_tick"] == 0 and day["stock"] == file_items
        inventory.write_text('{"items":{"ca_linh":1}}')
        run("quan", 0, "--inventory", inventory, expected=2)
        return {"spoiled": crossed[0], "gather_end": terminal, "quan_tick_zero_stock": quan["stock"],
                "day_handoff": {"tick": day["tick"], "phase_tick": day["phase_tick"], "stock": day["stock"]},
                "partial_run_preserved_destination": True, "count_inventory_exit": 2}


if __name__ == "__main__":
    print(json.dumps(smoke(), ensure_ascii=False, indent=2))
