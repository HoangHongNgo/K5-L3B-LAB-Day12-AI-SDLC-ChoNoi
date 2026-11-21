"""File kho (schema v1.0, Contract G; từ v1.1 có 6 nguyên liệu): {"items": {id: số nguyên >= 0}}.

Đọc: từ chối sai schema / id lạ / số âm (BadInput -> mã 2).
Ghi: bỏ mục bằng 0, qua file tạm cùng thư mục rồi thay thế, byte-ổn-định.
"""

import json
import os
import tempfile

from .errors import BadInput

KINDS = ("ca_keo", "ca_linh", "ca_loc", "bong_dien_dien", "bong_sung", "keo_neo")  # v1.1: thêm ca_keo, keo_neo
KINDS_P1 = KINDS  # tên cũ, giữ để mã Phase 1 không vỡ


ITEM_KEYS = {"id", "kind", "fresh"}


def validate_items(items, kinds=KINDS_P1, contract_version=None):
    if isinstance(items, list):
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
            if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not (0 <= fresh <= 100):
                raise BadInput(f"độ tươi không hợp lệ cho {iid}: {fresh!r}")
            out.append({"id": iid, "kind": k, "fresh": fresh})
        return out

    if not isinstance(items, dict):
        raise BadInput("items phải là object hoặc mảng")
    if contract_version == "1.2":
        raise BadInput("contract v1.2 không chấp nhận kho đếm")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def read_inventory(path: str, kinds=KINDS_P1, contract_version=None):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
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
        out_items = items
    else:
        out_items = items
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": out_items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
