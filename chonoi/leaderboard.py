"""Bảng xếp hạng cục bộ (extension `leaderboard`): top 10, lưu bền vững bằng JSON.

Thứ tự: điểm giảm dần; hòa thì mục ghi trước đứng trước (store luôn lưu đã sắp, sắp ổn định).
Chỉ ghi một mục cho mỗi lượt chuẩn đủ 5 Ngày (không scenario, reason `days_complete`).
"""

import json
import os

from .errors import BadInput

TOP_N = 10
STANDARD_DAYS = 5
DEFAULT_STORE = "leaderboard.json"
_FIELDS = ("name", "score", "days_completed", "seed")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_name(name):
    if not isinstance(name, str) or not name.strip():
        raise BadInput("--player-name phải là chuỗi khác rỗng")
    return name


def _check_entry(e):
    if not isinstance(e, dict) or not isinstance(e.get("name"), str) or not e["name"].strip():
        raise BadInput("mục xếp hạng sai định dạng")
    if not _num(e.get("score")) or isinstance(e.get("days_completed"), bool) or not isinstance(e.get("days_completed"), int) \
            or isinstance(e.get("seed"), bool) or not isinstance(e.get("seed"), int):
        raise BadInput("mục xếp hạng sai định dạng")
    return {k: e[k] for k in _FIELDS}


def load(path):
    """Đọc store; chưa có file -> rỗng. File hỏng -> BadInput."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được bảng xếp hạng {path}: {e}")
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise BadInput(f"bảng xếp hạng {path} phải có mảng entries")
    entries = [_check_entry(e) for e in data["entries"]]
    return sorted(entries, key=lambda e: -e["score"])[:TOP_N]  # sắp ổn định: giữ thứ tự ghi khi hòa


def _write(path, entries):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"entries": entries}, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def add_entry(path, name, score, days_completed, seed):
    entries = load(path)
    entries.append({"name": validate_name(name), "score": score, "days_completed": days_completed, "seed": seed})
    entries = sorted(entries, key=lambda e: -e["score"])[:TOP_N]
    _write(path, entries)
    return entries


def export(store, out):
    _write(out, load(store))


def record_if_standard(store, name, end_row, seed, days, scenario_given):
    """Ghi đúng một mục nếu là lượt chuẩn đủ 5 Ngày; trả True nếu đã ghi."""
    if (days != STANDARD_DAYS or scenario_given or end_row.get("reason") != "days_complete"
            or end_row.get("days_completed") != STANDARD_DAYS):
        return False
    add_entry(store, name, end_row["score"], end_row["days_completed"], seed)
    return True
