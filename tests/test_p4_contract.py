"""Contract v1.3 manifest, command validation and v1.2-compatible inventory tests."""

import copy
import io
import json
import os
import unittest
from unittest import mock

from chonoi import headless
from chonoi.contract import CONTRACT_VERSION, DEFAULT_PATH, load_contract
from chonoi.errors import BadInput
from chonoi.inventory import read_inventory
from helpers import Workdir, read_jsonl, run_headless, snapshots, write_json


def base_manifest():
    with open(DEFAULT_PATH, encoding="utf-8") as f:
        return json.load(f)


class TestContractV13(unittest.TestCase):
    def test_manifest_and_loader_declare_v13_and_commands(self):
        raw = base_manifest()
        self.assertEqual(CONTRACT_VERSION, "1.3")
        self.assertEqual(raw["contract_version"], "1.3")
        self.assertEqual(raw["bench_cmd"], "node tools/bench.mjs")
        self.assertEqual(raw["soak_cmd"], "python3 -m tools.soak")

        loaded = load_contract()
        self.assertEqual(loaded["contract_version"], "1.3")
        self.assertEqual(loaded["bench_cmd"], "node tools/bench.mjs")
        self.assertEqual(loaded["soak_cmd"], "python3 -m tools.soak")
        self.assertEqual(loaded["tuning"]["extensions"], raw["extensions"])

    def test_loader_preserves_configured_commands(self):
        custom = copy.deepcopy(base_manifest())
        custom["bench_cmd"] = "custom-bench --fast"
        custom["soak_cmd"] = "custom-soak --days 10"
        with Workdir() as w:
            p = write_json(w.path("contract.json"), custom)
            loaded = load_contract(p)
        self.assertEqual(loaded["bench_cmd"], "custom-bench --fast")
        self.assertEqual(loaded["soak_cmd"], "custom-soak --days 10")

    def test_loader_rejects_non_object_manifest(self):
        for bad in ([], None, "contract", 123, True):
            with self.subTest(manifest=bad), Workdir() as w:
                p = write_json(w.path("contract.json"), bad)
                with self.assertRaises(BadInput):
                    load_contract(p)

    def test_loader_rejects_non_v13_versions(self):
        for bad_version in ("1.0", "1.1", "1.2", "1.4", 1.3, None, True):
            m = copy.deepcopy(base_manifest())
            m["contract_version"] = bad_version
            with self.subTest(version=bad_version), Workdir() as w:
                p = write_json(w.path("contract.json"), m)
                with self.assertRaises(BadInput) as ctx:
                    load_contract(p)
                self.assertIn("contract_version", str(ctx.exception))

        missing = copy.deepcopy(base_manifest())
        missing.pop("contract_version")
        with Workdir() as w:
            p = write_json(w.path("contract.json"), missing)
            with self.assertRaises(BadInput) as ctx:
                load_contract(p)
            self.assertIn("contract_version", str(ctx.exception))

    def test_loader_rejects_missing_empty_whitespace_and_invalid_command_types(self):
        bad_values = [None, "", "   ", "\t\n", 123, True, False, ["node", "tools/bench.mjs"], {"cmd": "x"}]
        for field in ("bench_cmd", "soak_cmd"):
            missing = copy.deepcopy(base_manifest())
            missing.pop(field)
            with self.subTest(field=field, case="missing"), Workdir() as w:
                p = write_json(w.path("contract.json"), missing)
                with self.assertRaises(BadInput) as ctx:
                    load_contract(p)
                self.assertIn(field, str(ctx.exception))

            for val in bad_values:
                mutated = copy.deepcopy(base_manifest())
                mutated[field] = val
                with self.subTest(field=field, value=val), Workdir() as w:
                    p = write_json(w.path("contract.json"), mutated)
                    with self.assertRaises(BadInput) as ctx:
                        load_contract(p)
                    self.assertIn(field, str(ctx.exception))

    def test_headless_exits_2_on_invalid_v13_commands_or_manifest(self):
        cases = [
            ("non_object", []),
            ("missing_bench_cmd", {k: v for k, v in base_manifest().items() if k != "bench_cmd"}),
            ("blank_soak_cmd", dict(base_manifest(), soak_cmd="   ")),
        ]
        orig = load_contract
        for name, doc in cases:
            with self.subTest(case=name), Workdir() as w:
                p = write_json(w.path("contract.json"), doc)
                out = w.path("out.jsonl")
                err = io.StringIO()
                with mock.patch.object(headless, "load_contract", lambda path=p: orig(path)), \
                        mock.patch("sys.stderr", err):
                    code = headless.main(["--mode", "gather", "--seed", "1", "--ticks", "1", "--out", out])
                self.assertEqual(code, 2)
                self.assertNotIn("Traceback", err.getvalue())
                self.assertFalse(os.path.exists(out))

    def test_v13_accepts_item_inventory_and_rejects_count_inventory(self):
        contract = load_contract()
        self.assertEqual(contract["contract_version"], "1.3")
        with Workdir() as w:
            item_inv = write_json(w.path("items.json"), {
                "items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
            })
            loaded_items = read_inventory(item_inv, contract_version=contract["contract_version"])
            self.assertEqual(loaded_items, [{"id": "I1", "kind": "ca_loc", "fresh": 100}])

            out = w.path("quan.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1",
                                     "--inventory", item_inv, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(snapshots(rows)[0]["stock"], [{"id": "I1", "kind": "ca_loc", "fresh": 100}])

            count_inv = write_json(w.path("counts.json"), {"items": {"ca_loc": 1}})
            with self.assertRaises(BadInput):
                read_inventory(count_inv, contract_version=contract["contract_version"])

            bad_out = w.path("bad.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1",
                                     "--inventory", count_inv, "--out", bad_out)
            self.assertEqual(code, 2, err)
            self.assertNotIn("Traceback", err)
            self.assertFalse(os.path.exists(bad_out))


if __name__ == "__main__":
    unittest.main()
