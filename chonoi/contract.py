"""Đọc game.contract.json và kiểm dải hợp lệ của tuning P1 (PRD mục 13.2, Test Contract)."""

import json
import os

from .errors import BadInput

PLANT_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


def load_contract(path=DEFAULT_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    validate_tuning(c.get("tuning"))
    return c


def _int_between(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải là số nguyên trong [{lo}, {hi}], đang là {v!r}")


def _pos_in(name, pos, bounds, keys):
    if (not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos)):
        raise BadInput(f"tuning.{name} phải là [số, số]")
    for c, k in zip(pos, keys):
        lo, hi = bounds[k]
        if not (lo <= c <= hi):
            raise BadInput(f"tuning.{name} nằm ngoài vùng {k} ∈ [{lo}, {hi}]")


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def _validate_gather(g):
    """Dải hợp lệ P1 theo PRD mục 13.2."""
    _between("gather.duration_s", g.get("duration_s"), 60, 600)
    _bounds("gather", g.get("bounds"), ("x", "d"))
    b = g["bounds"]
    _between("gather.dock_radius", g.get("dock_radius"), 0.5, 5)
    _between("gather.interact_radius", g.get("interact_radius"), 0.5, 5)
    _between("gather.catch_radius", g.get("catch_radius"), 0.5, 5)
    _between("gather.swim_speed", g.get("swim_speed"), 1, 10)
    _between("gather.catch_cooldown_s", g.get("catch_cooldown_s"), 0, 10)
    _between("gather.oxygen_max_s", g.get("oxygen_max_s"), 10, 120)
    _int_between("gather.ramp_max_ticks", g.get("ramp_max_ticks"), 0, 6)
    _int_between("gather.hold_capacity", g.get("hold_capacity"), 4, 30)
    _int_between("gather.hp_max", g.get("hp_max"), 1, 99)
    _int_between("gather.oxygen_refill_per_tick", g.get("oxygen_refill_per_tick"), 1, 10_000)
    _int_between("gather.choke_interval_ticks", g.get("choke_interval_ticks"), 1, 10_000)
    _int_between("gather.node_yield", g.get("node_yield"), 1, 12)
    _between("gather.regrow_s", g.get("regrow_s"), 0.1, 600)
    _between("gather.surface_depth", g.get("surface_depth"), 0, 5)
    _pos_in("gather.dock_pos", g.get("dock_pos"), b, ("x", "d"))
    _pos_in("gather.start_pos", g.get("start_pos"), b, ("x", "d"))
    if not _num(g.get("start_heading_deg")):
        raise BadInput("tuning.gather.start_heading_deg phải là số")
    fy = g.get("fish_yield")
    if not isinstance(fy, dict) or not {"ca_linh", "ca_loc"} <= set(fy):
        raise BadInput("tuning.gather.fish_yield phải có ca_linh và ca_loc")
    for k, v in fy.items():
        _int_between(f"gather.fish_yield.{k}", v, 1, g["hold_capacity"])
    nodes = g.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise BadInput("tuning.gather.nodes phải là mảng không rỗng")
    seen, kinds = set(), set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or n["id"] in seen:
            raise BadInput("tuning.gather.nodes: mỗi nút cần id duy nhất")
        seen.add(n["id"])
        if n.get("kind") not in PLANT_KINDS:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải là một trong {PLANT_KINDS}")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if not {"bong_dien_dien", "bong_sung"} <= kinds:
        raise BadInput("tuning.gather.nodes phải có ít nhất một nút mỗi loại (bong_dien_dien, bong_sung)")
    fish = g.get("fish_initial")
    if "fish_speed" in g:  # v1.1: đàn bơi/sinh, fish_initial là số đàn đầu ca
        _validate_fish_v11(g)
        return
    if not isinstance(fish, list) or len(fish) != 6:
        raise BadInput("tuning.gather.fish_initial phải là danh sách đúng 6 đàn")
    seen = set()
    for f in fish:
        if not isinstance(f, dict) or not isinstance(f.get("id"), str) or f["id"] in seen:
            raise BadInput("tuning.gather.fish_initial: mỗi đàn cần id duy nhất")
        seen.add(f["id"])
        if f.get("kind") not in fy:
            raise BadInput(f"tuning.gather.fish_initial.{f['id']}: kind phải thuộc fish_yield")
        _pos_in(f"gather.fish_initial.{f['id']}.pos", f.get("pos"), b, ("x", "d"))
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"tuning.gather.fish_initial.{f['id']}: đàn cá phải ở dưới nước")


def _validate_fish_v11(g):
    """Khóa cá v1.1 (TICKET-02 mục 1.1, 4.1)."""
    b = g["bounds"]
    species = set(g["fish_yield"])
    _between("gather.fish_speed", g.get("fish_speed"), 0, 10)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_max", g.get("fish_max"), 1, 100)
    _int_between("gather.fish_initial", g.get("fish_initial"), 0, g["fish_max"])
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 100)
    fx = g.get("fish_x")
    if not (isinstance(fx, list) and len(fx) == 2 and all(_num(c) for c in fx)
            and b["x"][0] <= fx[0] < fx[1] <= b["x"][1]):
        raise BadInput("tuning.gather.fish_x phải là [lo, hi] trong bounds.x")
    for key in ("fish_depths", "fish_spawn_depths", "fish_weights"):
        m = g.get(key)
        if not isinstance(m, dict) or set(m) != species:
            raise BadInput(f"tuning.gather.{key} phải có đúng các loài của fish_yield {sorted(species)}")
    for k, (lo, hi) in g["fish_depths"].items():
        if not (_num(lo) and _num(hi) and g["surface_depth"] < lo < hi <= b["d"][1]):
            raise BadInput(f"tuning.gather.fish_depths.{k} phải là [lo, hi] dưới mặt nước, trong bounds.d")
    xs = g.get("fish_spawn_x")
    if not isinstance(xs, list) or not xs or not all(_num(x) and fx[0] <= x <= fx[1] for x in xs):
        raise BadInput("tuning.gather.fish_spawn_x phải là danh sách x trong fish_x")
    for k, ds in g["fish_spawn_depths"].items():
        lo, hi = g["fish_depths"][k]
        if not isinstance(ds, list) or not ds or not all(_num(d) and lo <= d <= hi for d in ds):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải nằm trong fish_depths.{k}")
    w = g["fish_weights"]
    if not all(_num(v) and v >= 0 for v in w.values()) or sum(w.values()) <= 0:
        raise BadInput("tuning.gather.fish_weights phải là số ≥ 0, tổng > 0")


def _validate_shop(shop, gather):
    if not isinstance(shop, dict):
        raise BadInput("tuning.shop phải là object")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 100_000)
    ups = shop.get("upgrades")
    if not isinstance(ups, dict) or not {"oxygen", "hp"} <= set(ups):
        raise BadInput("tuning.shop.upgrades phải có oxygen và hp")
    fields = {"oxygen": "oxygen_max_s", "hp": "hp_max", "net": "catch_radius", "weapon": "weapon_radius"}
    for name, levels in ups.items():
        if not isinstance(levels, list) or not levels:
            raise BadInput(f"tuning.shop.upgrades.{name} phải là mảng cấp không rỗng")
        for i, e in enumerate(levels, start=1):
            if not isinstance(e, dict) or e.get("level") != i:
                raise BadInput(f"tuning.shop.upgrades.{name}: cấp phải là 1, 2, … theo thứ tự")
            _int_between(f"shop.upgrades.{name}[{i}].price", e.get("price"), 1, 10**9)
            if name in fields and not _num(e.get(fields[name])):
                raise BadInput(f"tuning.shop.upgrades.{name}[{i}] thiếu {fields[name]}")
    for e in ups["oxygen"]:
        _between(f"shop.upgrades.oxygen[{e['level']}].oxygen_max_s", e["oxygen_max_s"], 10, 120)
    for e in ups["hp"]:
        _int_between(f"shop.upgrades.hp[{e['level']}].hp_max", e["hp_max"], 1, 99)
    for e in ups.get("net", []):
        _between(f"shop.upgrades.net[{e['level']}].catch_radius", e["catch_radius"], 0.5, 10)
        _int_between(f"shop.upgrades.net[{e['level']}].max_schools", e.get("max_schools"), 1, 12)


def _validate_day_plan(plan, menu):
    if not isinstance(plan, list) or [e.get("day") if isinstance(e, dict) else None for e in plan] != [1, 2, 3, 4, 5]:
        raise BadInput("tuning.day_plan phải là 5 object day 1..5 theo thứ tự")
    for e in plan:
        dishes, ing = e.get("dishes"), e.get("ingredients")
        if not isinstance(dishes, dict) or not dishes or not isinstance(ing, dict):
            raise BadInput(f"tuning.day_plan.D{e['day']} cần dishes và ingredients")
        want = {}
        for d, n in dishes.items():
            if d not in menu:
                raise BadInput(f"tuning.day_plan.D{e['day']}: món {d!r} không có trong menu")
            if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
                raise BadInput(f"tuning.day_plan.D{e['day']}.dishes.{d} phải là số nguyên dương")
            for k, a in menu[d]["recipe"].items():
                want[k] = want.get(k, 0) + a * n
        if ing != want:
            raise BadInput(f"tuning.day_plan.D{e['day']}.ingredients phải bằng tổng công thức × số suất: {want}")


def _validate_quan_layout(q):
    """Bếp/bàn: id duy nhất (không trùng giữa bếp và bàn), vị trí trong bounds; start_pos trong bounds."""
    b = q["bounds"]
    _pos_in("quan.start_pos", q.get("start_pos"), b, ("x", "z"))
    seen = set()
    for key in ("stoves", "tables"):
        items = q.get(key)
        if not isinstance(items, list) or not items:
            raise BadInput(f"tuning.quan.{key} phải là mảng không rỗng")
        for it in items:
            if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not it["id"] or it["id"] in seen:
                raise BadInput(f"tuning.quan.{key}: mỗi phần tử cần id chuỗi duy nhất")
            seen.add(it["id"])
            _pos_in(f"quan.{key}.{it['id']}.pos", it.get("pos"), b, ("x", "z"))


def _validate_reputation(q):
    lo, hi, init = q.get("reputation_min"), q.get("reputation_max"), q.get("reputation_initial")
    if not (_num(lo) and _num(hi) and _num(init) and lo < hi and lo <= init <= hi):
        raise BadInput("tuning.quan: cần reputation_min < reputation_max và reputation_initial nằm giữa hai mức")


def _validate_menu(menu, gather):
    if not menu:
        raise BadInput("tuning.menu không được rỗng")
    kinds = {n["kind"] for n in gather["nodes"]} | set(gather["fish_yield"])
    for dish_id, d in menu.items():
        if not isinstance(d, dict):
            raise BadInput(f"menu.{dish_id} phải là object")
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
        recipe = d.get("recipe")
        if not isinstance(recipe, dict) or not recipe:
            raise BadInput(f"menu.{dish_id}.recipe phải là object không rỗng")
        for k, n in recipe.items():
            if k not in kinds:
                raise BadInput(f"menu.{dish_id}.recipe: nguyên liệu {k!r} không thu được ở gather")
            if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
                raise BadInput(f"menu.{dish_id}.recipe.{k} phải là số nguyên > 0")


def validate_tuning(t):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    if t.get("tick_hz") != 60 or isinstance(t.get("tick_hz"), bool):
        raise BadInput(f"tuning.tick_hz phải là 60, đang là {t.get('tick_hz')!r}")
    score = t.get("score")
    if not isinstance(score, dict) or not _num(score.get("reputation_multiplier")) or score["reputation_multiplier"] < 0:
        raise BadInput("tuning.score.reputation_multiplier phải là số ≥ 0")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_gather(g)
    # Quán: dải hợp lệ P1 (PRD mục 13.2)
    _between("quan.duration_s", q.get("duration_s"), 60, 600)
    _bounds("quan", q.get("bounds"), ("x", "z"))
    _between("quan.patience_s", q.get("patience_s"), 20, 180)
    _between("quan.walk_speed", q.get("walk_speed"), 1, 10)
    _between("quan.interact_radius", q.get("interact_radius"), 0.5, 5)
    _int_between("quan.ramp_max_ticks", q.get("ramp_max_ticks", 6), 0, 6)
    _between("quan.eat_s", q.get("eat_s"), 0.1, 600)
    _between("quan.customer_interval_s", q.get("customer_interval_s"), 0.1, 600)
    _int_between("quan.first_customer_tick", q.get("first_customer_tick"), 1, int(q["duration_s"] * 60) - 1)
    if not (_num(q.get("tip_rate")) and q["tip_rate"] > 0 and _num(q.get("left_reputation_delta"))
            and q["left_reputation_delta"] < 0):
        raise BadInput("tip_rate phải > 0 và left_reputation_delta phải < 0")
    ratio = q.get("tip_min_patience_ratio")
    if not (_num(ratio) and 0 < ratio <= 1):
        raise BadInput("quan.tip_min_patience_ratio phải thuộc (0, 1]")
    if not (_num(q.get("tip_reputation")) and q["tip_reputation"] > 0):
        raise BadInput("quan.tip_reputation phải > 0")
    if q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null ở Phase 1")
    _validate_quan_layout(q)
    _validate_reputation(q)
    _int_between("quan.carry_limit", q.get("carry_limit"), 1, 10)
    _validate_menu(menu, g)
    if "shop" in t:
        _validate_shop(t["shop"], g)
    if "day_plan" in t:
        _validate_day_plan(t["day_plan"], menu)
