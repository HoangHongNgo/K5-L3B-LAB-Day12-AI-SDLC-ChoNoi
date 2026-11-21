"""Đọc game.contract.json và kiểm dải hợp lệ của tuning (Test Contract v1.1)."""

import json
import os

from .errors import BadInput

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")


CONTRACT_VERSION = "1.1"
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
INGREDIENTS = tuple(sorted(NODE_KINDS + FISH_KINDS))
DAYS = 5


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
    if c.get("contract_version") != CONTRACT_VERSION:
        raise BadInput(f"contract_version phải là {CONTRACT_VERSION!r}, đang là {c.get('contract_version')!r}")
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
    """Dải hợp lệ (PRD mục 13.2) cộng khóa v1.1."""
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
    if not isinstance(fy, dict) or set(fy) != set(FISH_KINDS):
        raise BadInput(f"tuning.gather.fish_yield phải có đúng các loài {list(FISH_KINDS)}")
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
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải thuộc {list(NODE_KINDS)}")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if kinds != set(NODE_KINDS):
        raise BadInput(f"tuning.gather.nodes phải có ít nhất một nút mỗi loại {list(NODE_KINDS)}")
    _validate_fish(g, b)
    _validate_monsters_tuning(g, b)


def _per_kind(name, m):
    if not isinstance(m, dict) or set(m) != set(FISH_KINDS):
        raise BadInput(f"tuning.gather.{name} phải có đúng các loài {list(FISH_KINDS)}")


def _range(name, r, lo, hi):
    """[a, b] với lo <= a < b <= hi."""
    if not (isinstance(r, list) and len(r) == 2 and all(_num(c) for c in r) and lo <= r[0] < r[1] <= hi):
        raise BadInput(f"tuning.gather.{name} phải là [a, b] với {lo} <= a < b <= {hi}, đang là {r!r}")


def _validate_fish(g, b):
    """Cá bơi/sinh (mục 4.1): số đàn đầu ca, tốc độ, dải x/độ sâu, điểm sinh, trọng số."""
    _between("gather.fish_speed", g.get("fish_speed"), 0.1, 10)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_max", g.get("fish_max"), 1, 99)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 100)
    _range("fish_x", g.get("fish_x"), *b["x"])
    fx = g["fish_x"]
    for name in ("fish_depths", "fish_spawn_depths", "fish_weights"):
        _per_kind(name, g.get(name))
    for k in FISH_KINDS:
        _range(f"fish_depths.{k}", g["fish_depths"][k], g["surface_depth"], b["d"][1])
        lo, hi = g["fish_depths"][k]
        ds = g["fish_spawn_depths"][k]
        if not (isinstance(ds, list) and ds and all(_num(d) and lo <= d <= hi for d in ds)):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải là mảng độ sâu nằm trong fish_depths.{k}")
        w = g["fish_weights"][k]
        if not _num(w) or w <= 0:
            raise BadInput(f"tuning.gather.fish_weights.{k} phải > 0")
    xs = g.get("fish_spawn_x")
    if not (isinstance(xs, list) and xs and all(_num(x) and fx[0] <= x <= fx[1] for x in xs)
            and len(set(xs)) == len(xs)):
        raise BadInput("tuning.gather.fish_spawn_x phải là mảng x khác nhau nằm trong fish_x")
    points = len(xs) * sum(len(g["fish_spawn_depths"][k]) for k in FISH_KINDS)
    _int_between("gather.fish_initial", g.get("fish_initial"), 1, min(g["fish_max"], points))


def _validate_monsters_tuning(g, b):
    """`gather.monsters` (mục 4.1): loài, điểm sinh, bất tử, tỷ lệ rơi hàng."""
    m = g.get("monsters")
    if not isinstance(m, dict):
        raise BadInput("tuning.gather.monsters phải là object")
    species = m.get("species")
    if not isinstance(species, dict) or not species:
        raise BadInput("tuning.gather.monsters.species phải là object không rỗng")
    for kind, sp in species.items():
        name = f"gather.monsters.species.{kind}"
        if not isinstance(sp, dict):
            raise BadInput(f"tuning.{name} phải là object")
        for key in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            _between(f"{name}.{key}", sp.get(key), 0, 1000)
        _int_between(f"{name}.recoil_ticks", sp.get("recoil_ticks"), 1, 100_000)
        _range(f"monsters.species.{kind}.depths", sp.get("depths"), *b["d"])
        if sp["exit_radius"] < sp["detect_radius"]:
            raise BadInput(f"tuning.{name}.exit_radius phải >= detect_radius")
    _int_between("gather.monsters.invuln_ticks", m.get("invuln_ticks"), 0, 100_000)
    _between("gather.monsters.loss_ratio", m.get("loss_ratio"), 0, 1)
    spawns = m.get("spawns")
    if not isinstance(spawns, list) or not spawns:
        raise BadInput("tuning.gather.monsters.spawns phải là mảng không rỗng")
    seen = set()
    for sp in spawns:
        if not isinstance(sp, dict) or not isinstance(sp.get("id"), str) or not sp["id"] or sp["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns: mỗi phần tử cần id duy nhất")
        seen.add(sp["id"])
        name = f"gather.monsters.spawns.{sp['id']}"
        if sp.get("kind") not in species:
            raise BadInput(f"tuning.{name}.kind phải thuộc species")
        _int_between(f"{name}.from_day", sp.get("from_day"), 1, DAYS)
        depths = species[sp["kind"]]["depths"]
        lim = {"x": b["x"], "d": [max(b["d"][0], depths[0]), min(b["d"][1], depths[1])]}
        wps = sp.get("waypoints")
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"tuning.{name}.waypoints phải có hai tọa độ")
        for i, wp in enumerate(wps):
            _pos_in(f"{name}.waypoints[{i}]", wp, lim, ("x", "d"))
        _pos_in(f"{name}.pos", sp.get("pos"), lim, ("x", "d"))
        if sp["pos"] != wps[0]:
            raise BadInput(f"tuning.{name}.pos phải bằng waypoint đầu")


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
    if kinds != set(INGREDIENTS):
        raise BadInput(f"nguyên liệu thu được phải đúng 6 loại {list(INGREDIENTS)}")
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
    burn = q.get("burn_s")
    if burn is not None and not (_num(burn) and burn > 0):
        raise BadInput("quan.burn_s phải là null (lõi) hoặc số dương (mở rộng burn)")
    _validate_quan_layout(q)
    _validate_reputation(q)
    _int_between("quan.carry_limit", q.get("carry_limit"), 1, 10)
    _validate_menu(menu, g)
    _validate_day_plan(t.get("day_plan"), menu)
    _validate_shop(t.get("shop"), g)


def plan_ingredients(dishes, menu):
    """Tổng nguyên liệu của một kế hoạch: Σ công thức × số suất, khóa sắp theo id."""
    out = {}
    for dish, n in dishes.items():
        for k, v in menu[dish]["recipe"].items():
            out[k] = out.get(k, 0) + v * n
    return {k: out[k] for k in sorted(out)}


def check_dishes(name, dishes, menu):
    """`dishes` là map id món -> số suất nguyên dương, id thuộc menu."""
    if not isinstance(dishes, dict) or not dishes:
        raise BadInput(f"{name}.dishes phải là object không rỗng")
    for dish, n in dishes.items():
        if dish not in menu:
            raise BadInput(f"{name}.dishes: món không có trong menu: {dish!r}")
        if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
            raise BadInput(f"{name}.dishes.{dish} phải là số nguyên dương")


def resolve_day_plan(tuning, overrides=None):
    """Kế hoạch 5 Ngày hiệu lực: preset của contract, áp `overrides` (mảng `{day, dishes, ingredients?}` của
    scenario `day.day_plan`). `ingredients` luôn tính lại từ `dishes`; nếu override có khai thì phải khớp,
    sai → BadInput. Trả mảng 5 phần tử `{day, dishes, ingredients}`."""
    menu = tuning["menu"]
    plan = {e["day"]: {"day": e["day"], "dishes": dict(e["dishes"]), "ingredients": dict(e["ingredients"])}
            for e in tuning["day_plan"]}
    if overrides is None:
        return [plan[d] for d in sorted(plan)]
    if not isinstance(overrides, list):
        raise BadInput("day.day_plan phải là mảng {day, dishes, ingredients?}")
    seen = set()
    for i, o in enumerate(overrides):
        name = f"day.day_plan[{i}]"
        if not isinstance(o, dict) or not {"day", "dishes"} <= set(o) or set(o) - {"day", "dishes", "ingredients"}:
            raise BadInput(f"{name} phải có day, dishes và (tùy chọn) ingredients")
        d = o["day"]
        if isinstance(d, bool) or not isinstance(d, int) or d not in plan or d in seen:
            raise BadInput(f"{name}.day phải là số nguyên 1..{DAYS}, không trùng")
        seen.add(d)
        check_dishes(name, o["dishes"], menu)
        want = plan_ingredients(o["dishes"], menu)
        if "ingredients" in o and o["ingredients"] != want:
            raise BadInput(f"{name}.ingredients không khớp công thức × số suất (cần {want})")
        plan[d] = {"day": d, "dishes": dict(o["dishes"]), "ingredients": want}
    return [plan[d] for d in sorted(plan)]


def _validate_day_plan(plan, menu):
    if not isinstance(plan, list) or len(plan) != DAYS:
        raise BadInput(f"tuning.day_plan phải là mảng đúng {DAYS} Ngày")
    for i, entry in enumerate(plan, start=1):
        name = f"day_plan[{i}]"
        if not isinstance(entry, dict) or set(entry) != {"day", "dishes", "ingredients"} or entry["day"] != i:
            raise BadInput(f"tuning.{name} phải là object {{day: {i}, dishes, ingredients}}")
        check_dishes(f"tuning.{name}", entry["dishes"], menu)
        want = plan_ingredients(entry["dishes"], menu)
        if entry["ingredients"] != want:
            raise BadInput(f"tuning.{name}.ingredients phải bằng tổng công thức × số suất ({want})")


UPGRADE_FIELDS = {"oxygen": "oxygen_max_s", "hp": "hp_max"}


def _validate_shop(shop, g):
    if not isinstance(shop, dict) or set(shop) != {"max_ticks", "upgrades"}:
        raise BadInput("tuning.shop phải có đúng max_ticks và upgrades")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 1_000_000)
    ups = shop["upgrades"]
    if not isinstance(ups, dict) or not set(UPGRADE_FIELDS) <= set(ups):
        raise BadInput("tuning.shop.upgrades phải có oxygen và hp")
    for kind, field in UPGRADE_FIELDS.items():
        levels = ups[kind]
        if not isinstance(levels, list) or not levels:
            raise BadInput(f"tuning.shop.upgrades.{kind} phải là mảng không rỗng")
        prev = g["oxygen_max_s"] if kind == "oxygen" else g["hp_max"]
        for i, lv in enumerate(levels, start=1):
            name = f"shop.upgrades.{kind}[{i}]"
            if not isinstance(lv, dict) or set(lv) != {"level", "price", field} or lv["level"] != i:
                raise BadInput(f"tuning.{name} phải là object {{level: {i}, price, {field}}}")
            _int_between(f"{name}.price", lv["price"], 1, 1_000_000)
            if not _num(lv[field]) or lv[field] <= prev:
                raise BadInput(f"tuning.{name}.{field} phải lớn hơn cấp trước ({prev})")
            if kind == "hp":
                _int_between(f"{name}.hp_max", lv["hp_max"], 1, 99)
            prev = lv[field]
