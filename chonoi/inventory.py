"""Versioned inventory validation, freshness and atomic handoff between shifts."""

import json
from decimal import Decimal
from fractions import Fraction
import math
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

KINDS = ("ca_keo", "ca_linh", "ca_loc", "bong_dien_dien", "bong_sung", "keo_neo")  # v1.1: thêm ca_keo, keo_neo
KINDS_P1 = KINDS  # tên cũ, giữ để mã Phase 1 không vỡ


ITEM_KEYS = {"id", "kind", "fresh"}


def validate_items(items, kinds=KINDS_P1, contract_version=None):
    if isinstance(items, list):
        if contract_version in ("1.0", "1.1"):
            raise BadInput("contract trước v1.2 dùng kho đếm theo loại")
        seen_ids = set()
        out = []
        for it in items:
            if not isinstance(it, dict):
                raise BadInput("mỗi cá thể trong items phải là object")
            extra = set(it) - ITEM_KEYS
            if extra:
                raise BadInput(f"cá thể có trường lạ: {sorted(extra)}")
            iid = it.get("id")
            if not isinstance(iid, str) or not iid:
                raise BadInput("cá thể cần id là chuỗi khác rỗng")
            if iid in seen_ids:
                raise BadInput(f"trùng id cá thể: {iid}")
            seen_ids.add(iid)
            k = it.get("kind")
            if not isinstance(k, str) or k not in kinds:
                raise BadInput(f"nguyên liệu lạ: {k}")
            fresh = it.get("fresh")
            if (isinstance(fresh, bool) or not isinstance(fresh, (int, float, Decimal))
                    or (isinstance(fresh, Decimal) and not fresh.is_finite()) or not (0 <= fresh <= 100)):
                raise BadInput(f"độ tươi không hợp lệ cho {iid}: {fresh!r}")
            out.append({"id": iid, "kind": k, "fresh": fresh})
        return out

    if not isinstance(items, dict):
        raise BadInput("items phải là object hoặc mảng")
    if contract_version in ("1.2", "1.3"):
        raise BadInput(f"contract v{contract_version} không chấp nhận kho đếm")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def public_items(items, threshold, *, for_handoff=False):
    result = []
    for item in items:
        fresh = item["fresh"]
        value = int(fresh) if fresh.denominator == 1 else float(fresh)
        # A repeating decimal exported on the low side of an exact tick boundary can
        # spoil one step early when the next process decodes it. Emit the upper neighbor.
        if for_handoff and isinstance(value, float) and Fraction(str(value)) < fresh:
            value = math.nextafter(value, math.inf)
        if value >= threshold and fresh < threshold:
            value = math.nextafter(float(value), -math.inf)
        result.append(dict(item, fresh=value))
    return result


def decay_items(items, amount, threshold, location):
    spoiled = []
    for item in items:
        before = item["fresh"]
        item["fresh"] = max(0, before - amount)
        if item["fresh"] < threshold <= before:
            spoiled.append(item)
    return [("spoiled", {"item_id": item["id"], "kind": item["kind"], "location": location})
            for item in sort_by_id(spoiled)]


def load_item_json(stream):
    """Keep extra decimal digits in fresh only; positions and other gameplay values stay floats."""
    def ordinary(value):
        if isinstance(value, list):
            return [ordinary(v) for v in value]
        return float(value) if isinstance(value, Decimal) else value

    def fields(obj):
        for key, val in obj.items():
            if key == "fresh" and isinstance(val, Decimal) and val != Decimal(str(float(val))):
                continue
            obj[key] = ordinary(val)
        return obj

    try:
        return json.load(stream, parse_float=Decimal, object_hook=fields)
    except ArithmeticError as error:
        raise ValueError("số thập phân không hợp lệ") from error


def read_inventory(path: str, kinds=KINDS_P1, contract_version=None):
    try:
        with open(path, encoding="utf-8") as f:
            data = load_item_json(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_items(data["items"], kinds, contract_version=contract_version)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    if isinstance(items, dict):
        out_items = {k: items[k] for k in sorted(items) if items[k] > 0}
    elif isinstance(items, list):
        out_items = sort_by_id(items)
    else:
        raise BadInput("items phải là object hoặc mảng")
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            if isinstance(out_items, list) and any(isinstance(it["fresh"], Decimal) for it in out_items):
                # JSON's number grammar accepts a decimal literal directly. Avoid a binary float
                # conversion when copying a high-precision external inventory.
                entries = []
                for item in out_items:
                    fields = json.dumps({"id": item["id"], "kind": item["kind"]}, ensure_ascii=False,
                                        separators=(",", ":"))
                    fresh = item["fresh"]
                    encoded = str(fresh) if isinstance(fresh, Decimal) else json.dumps(fresh, allow_nan=False)
                    entries.append(fields[:-1] + ',"fresh":' + encoded + '}')
                f.write('{"items":[' + ','.join(entries) + ']}')
            else:
                json.dump({"items": out_items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
