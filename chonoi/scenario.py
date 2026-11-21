"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import math

from .errors import BadInput
from .inventory import KINDS_P1, load_item_json, validate_items
from .sim.gather import gather_limits
from .sim.monsters import INACTIVE_STATES, MONSTER_STATES, monster_bounds

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers", "reservations", "random_reservations",
             "reputation", "time_left_ticks"}
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def _validate_day_plan_entry(plan, tuning, label="day_plan"):
    if not isinstance(plan, dict):
        raise BadInput(f"{label} phải là object")
    menu = tuning["menu"]
    if "dishes" in plan:
        menu_items = plan["dishes"]
    elif "menu" in plan:
        menu_items = plan["menu"]
    else:
        menu_items = {k: v for k, v in plan.items() if k not in ("ingredients", "menu", "dishes")}
    if not isinstance(menu_items, dict) or not menu_items:
        raise BadInput(f"{label}.menu/dishes phải là object khác rỗng chứa dish_id: số suất")
    expected_ingredients = {}
    for did, servings in menu_items.items():
        if did not in menu:
            raise BadInput(f"{label}: món không có trong menu: {did}")
        if isinstance(servings, bool) or not isinstance(servings, int) or servings <= 0:
            raise BadInput(f"{label}: số suất cho {did} phải là số nguyên dương")
        recipe = menu[did]["recipe"]
        for k, req in recipe.items():
            expected_ingredients[k] = expected_ingredients.get(k, 0) + req * servings

    if "ingredients" in plan:
        declared = plan["ingredients"]
        if not isinstance(declared, dict):
            raise BadInput(f"{label}.ingredients phải là object")
        cleaned_declared = {k: v for k, v in declared.items() if v > 0}
        if cleaned_declared != expected_ingredients:
            raise BadInput(f"{label}.ingredients không khớp công thức ({cleaned_declared} != {expected_ingredients})")


def _validate_day(b, tuning):
    if not isinstance(b, dict):
        raise BadInput("khối day phải là object")
    extra = set(b) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ trong khối day: {sorted(extra)}")
    if "money" in b:
        _nonneg_int("day.money", b["money"])
    if "earned" in b:
        _nonneg_int("day.earned", b["earned"])
    if "money" in b and "earned" in b:
        if b["money"] > b["earned"]:
            raise BadInput("day: money không được lớn hơn earned (0 <= money <= earned)")
    elif "money" in b and "earned" not in b:
        raise BadInput("day: có money thì phải khai earned phù hợp (0 <= money <= earned)")

    if "reputation" in b:
        rep = b["reputation"]
        rmin = tuning.get("quan", {}).get("reputation_min", 0)
        rmax = tuning.get("quan", {}).get("reputation_max", 5)
        if not _num(rep) or not (rmin <= rep <= rmax):
            raise BadInput(f"day.reputation phải là số trong [{rmin}, {rmax}]")

    if "upgrades" in b:
        ups = b["upgrades"]
        if not isinstance(ups, dict):
            raise BadInput("day.upgrades phải là object")
        shop = tuning["shop"]["upgrades"]
        for kind, level in ups.items():
            if kind not in shop:
                raise BadInput(f"day.upgrades: nâng cấp lạ {kind!r} (có {sorted(shop)})")
            if isinstance(level, bool) or not isinstance(level, int) or not (0 <= level <= len(shop[kind])):
                raise BadInput(f"day.upgrades.{kind} phải là số nguyên trong [0, {len(shop[kind])}]")

    if "day_plan" in b:
        dp = b["day_plan"]
        if isinstance(dp, list):  # dạng mảng như tuning.day_plan: [{day, dishes, ingredients?}]
            seen = set()
            for i, entry in enumerate(dp):
                d = entry.get("day") if isinstance(entry, dict) else None
                if isinstance(d, bool) or not isinstance(d, int) or not (1 <= d <= 5) or d in seen:
                    raise BadInput(f"day.day_plan[{i}].day phải là số nguyên 1..5, không trùng")
                seen.add(d)
                _validate_day_plan_entry({k: v for k, v in entry.items() if k != "day"}, tuning,
                                         label=f"day_plan[{i}]")
            return
        if not isinstance(dp, dict):
            raise BadInput("day.day_plan phải là object hoặc mảng")
        if "dishes" in dp or "menu" in dp:
            _validate_day_plan_entry(dp, tuning, label="day_plan")
        elif all(isinstance(v, dict) for v in dp.values()) and not any(k in tuning["menu"] for k in dp):
            for day_key, day_entry in dp.items():
                _validate_day_plan_entry(day_entry, tuning, label=f"day_plan.{day_key}")
        else:
            _validate_day_plan_entry(dp, tuning, label="day_plan")


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def _read_scenario(path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = load_item_json(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict):
        raise BadInput("scenario phải là object")
    return data


def _check_block(block, mode: str, tuning: dict, *, active_upgrades=None) -> dict:
    """Kiểm một khối `gather`/`quan` (dùng chung cho mode đơn và mẫu của `day`)."""
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning, active_upgrades=active_upgrades)
    else:
        _validate_quan(block, tuning)
    return block


def load_scenario(path, mode: str, tuning: dict, *, active_upgrades=None) -> dict:
    """Trả về đúng khối của mode (gather/quan). Mode `day`: trả nguyên scenario `{day, gather, quan}` đã kiểm
    (DaySim tự điền mặc định)."""
    if path is None:
        return {}
    data = _read_scenario(path)
    if mode == "day":
        if not set(data) <= {"day", "gather", "quan"}:
            raise BadInput("scenario cho mode day chỉ được có các khối 'day', 'gather', 'quan'")
        day_block = data.get("day", {})
        if "day" in data:
            _validate_day(day_block, tuning)
        quan = data.get("quan", {})
        if isinstance(quan, dict):
            if "stock" in quan:
                raise BadInput("mode day cấm quan.stock trong scenario (dùng gather.hold để dựng hàng)")
            if "reputation" in quan:
                raise BadInput("mode day cấm quan.reputation trong scenario (dùng day.reputation)")
        if "quan" in data:
            _check_block(quan, "quan", tuning)
        if "gather" in data:
            ups = day_block.get("upgrades") if isinstance(day_block, dict) else None
            _check_block(data["gather"], "gather", tuning, active_upgrades=ups if isinstance(ups, dict) else None)
        return data
    if not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    return _check_block(data.get(mode, {}), mode, tuning, active_upgrades=active_upgrades)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning, *, active_upgrades=None):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "monsters" in b:
        if "monsters" not in g:
            raise BadInput("gather.monsters cần tuning.monsters của contract v1.1")
        _validate_monsters(b["monsters"], g["monsters"]["species"], bounds)
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    # kind theo dữ liệu (v1.1 thêm ca_keo, keo_neo): nguyên liệu của thực đơn, nút và cá trong tuning
    recipe_kinds = {k for dish in tuning["menu"].values() for k in dish.get("recipe", {})}
    node_kinds = set(NODE_KINDS) | {n["kind"] for n in g["nodes"]}
    fish_kinds = set(FISH_KINDS) | set(g["fish_yield"])
    hold_kinds = set(KINDS_P1) | recipe_kinds | node_kinds | fish_kinds
    if "hold" in b:
        h = b["hold"]
        if "freshness" in tuning:
            validate_items(h, kinds=hold_kinds, contract_version="1.2")
        elif not isinstance(h, list) or any(not isinstance(k, str) or k not in hold_kinds for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax, hp_max = gather_limits(tuning, active_upgrades)
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= hp_max):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        limit = g["choke_interval_ticks"] - 1
        if p["zero_oxy_ticks"] > limit:
            raise BadInput(f"player.zero_oxy_ticks phải trong [0, {limit}]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in node_kinds:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {sorted(node_kinds)}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in fish_kinds:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {sorted(fish_kinds)}")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")


def _validate_monsters(monsters, species, bounds):
    _check_ids("monsters", monsters)
    for monster in monsters:
        name = f"monsters.{monster['id']}"
        extra = set(monster) - MONSTER_KEYS
        if extra:
            raise BadInput(f"{name}: trường lạ {sorted(extra)}")
        kind = monster.get("kind")
        if not isinstance(kind, str) or kind not in species:
            raise BadInput(f"{name}.kind không hợp lệ")
        limits = monster_bounds(bounds, species[kind])
        _pos(f"{name}.pos", monster.get("pos"), limits)
        waypoints = monster.get("waypoints")
        if not isinstance(waypoints, list) or len(waypoints) != 2:
            raise BadInput(f"{name}.waypoints phải có hai tọa độ")
        for idx, pos in enumerate(waypoints):
            _pos(f"{name}.waypoints[{idx}]", pos, limits)
        target = monster.get("target_idx", 1)
        _nonneg_int(f"{name}.target_idx", target)
        if target > 1:
            raise BadInput(f"{name}.target_idx phải là 0 hoặc 1")
        state = monster.get("state", "patrol")
        if not isinstance(state, str) or state not in MONSTER_STATES:
            raise BadInput(f"{name}.state không hợp lệ")
        ticks = monster.get("state_ticks_left", 0)
        _nonneg_int(f"{name}.state_ticks_left", ticks)
        if (ticks > 0) != (state in INACTIVE_STATES):
            raise BadInput(f"{name}.state_ticks_left chỉ dương khi recoil hoặc stunned")
        direction = monster.get("recoil_dir")
        if state == "recoil":
            if not (isinstance(direction, list) and len(direction) == 2
                    and all(_num(c) and -1 <= c <= 1 for c in direction)
                    and math.isclose(math.hypot(*direction), 1.0, rel_tol=1e-6)):
                raise BadInput(f"{name}.recoil_dir phải là vector đơn vị")
        elif direction is not None:
            raise BadInput(f"{name}.recoil_dir phải là null ngoài recoil")


CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                 "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
CUSTOMER_STATES = {"waiting", "eating"}
# PRD-0 mục D: reserved / assigned / unfulfillable / served. Tên cũ của nhóm quy về assigned.
LEGACY_ASSIGNED = {"cooking", "ready", "carried"}
ORDER_STATUSES = {"reserved", "assigned", "unfulfillable", "served"} | LEGACY_ASSIGNED
STOVE_STATES = {"idle", "cooking", "ready"}
STOVE_KEYS = {"id", "pos", "state", "dish", "dish_id", "cook_ticks_left", "ready_ticks", "order_id", "customer_id"}
TABLE_KEYS = {"id", "pos", "customer_id"}
HAND_KEYS = {"dish", "dish_id", "order_id", "customer_id", "base_price"}
PAYLOAD_KEYS = {"order_id", "dish_id", "base_price"}


def _dish_payload(where, obj, menu):
    """Payload món PRD-0 mục D {order_id, dish_id, base_price} -> (order_id, dish_id)."""
    extra = set(obj) - PAYLOAD_KEYS
    if extra:
        raise BadInput(f"{where}: payload món có trường lạ: {sorted(extra)}")
    did = obj.get("dish_id")
    if not isinstance(did, str) or did not in menu:
        raise BadInput(f"{where}: dish_id không có trong menu: {did}")
    oid = obj.get("order_id")
    if not isinstance(oid, str) or not oid:
        raise BadInput(f"{where}: payload món cần order_id")
    if "base_price" in obj:
        bp = obj["base_price"]
        if isinstance(bp, bool) or not isinstance(bp, int) or bp <= 0:
            raise BadInput(f"{where}: base_price phải là số nguyên dương")
    return oid, did


def _linked_dish(where, entity, menu):
    """Check all supported aliases before normalizing an order reference."""
    dish = entity.get("dish")
    order = entity.get("order_id", entity.get("customer_id"))
    if "customer_id" in entity and entity["customer_id"] != order:
        raise BadInput(f"{where}: order_id và customer_id mâu thuẫn")
    if isinstance(dish, dict):
        nested_order, nested_dish = _dish_payload(where, dish, menu)
        if order is not None and nested_order != order:
            raise BadInput(f"{where}: order_id mâu thuẫn với món")
        order, dish = nested_order, nested_dish
    if "dish_id" in entity:
        if dish is not None and dish != entity["dish_id"]:
            raise BadInput(f"{where}: dish_id mâu thuẫn với món")
        dish = entity["dish_id"]
    if dish is not None and (not isinstance(dish, str) or dish not in menu):
        raise BadInput(f"{where}: món không có trong menu: {dish}")
    if dish is not None and (not isinstance(order, str) or not order):
        raise BadInput(f"{where}: món cần order_id")
    return order, dish


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    q_tuning = tuning["quan"]
    menu = tuning["menu"]
    qb = q_tuning["bounds"]
    all_kinds = set(KINDS_P1) | {k for dish in menu.values() for k in dish.get("recipe", {})}

    if "stock" in b:
        validate_items(b["stock"], kinds=all_kinds, contract_version="1.2" if "freshness" in tuning else None)
    # mở rộng `reservations` (lát D): đơn tường minh thay toàn bộ danh sách; random_reservations:false tắt tự sinh
    if "random_reservations" in b and not isinstance(b["random_reservations"], bool):
        raise BadInput("random_reservations phải là boolean")
    if "reservations" in b:
        from .sim.reservations import validate as _validate_reservations
        _validate_reservations(b["reservations"], tuning)
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")

    if "reputation" in b:
        rep = b["reputation"]
        if not _num(rep) or not (q_tuning["reputation_min"] <= rep <= q_tuning["reputation_max"]):
            raise BadInput(f"reputation phải là số trong [{q_tuning['reputation_min']}, {q_tuning['reputation_max']}]")

    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")

    known_tables = {t["id"]: t for t in q_tuning["tables"]}
    for t in b.get("tables", []):
        if not isinstance(t, dict):
            raise BadInput("tables phải là mảng object")
        extra = set(t) - TABLE_KEYS
        if extra:
            raise BadInput(f"tables.{t.get('id', '?')}: trường lạ: {sorted(extra)}")
        if t["id"] not in known_tables:
            raise BadInput(f"id bàn không tồn tại: {t['id']}")
        if "pos" in t:
            _pos(f"tables.{t['id']}.pos", t["pos"], qb, axes=("x", "z"))
        known_tables[t["id"]] = t

    known_stoves = {s["id"]: s for s in q_tuning["stoves"]}
    stove_orders = {}
    stove_dishes = {}
    for s in b.get("stoves", []):
        if not isinstance(s, dict):
            raise BadInput("stoves phải là mảng object")
        extra = set(s) - STOVE_KEYS
        if extra:
            raise BadInput(f"stoves.{s.get('id', '?')}: trường lạ: {sorted(extra)}")
        if s["id"] not in known_stoves:
            raise BadInput(f"id bếp không tồn tại: {s['id']}")
        if "pos" in s:
            _pos(f"stoves.{s['id']}.pos", s["pos"], qb, axes=("x", "z"))
        state = s.get("state", "idle")
        if state not in STOVE_STATES:
            raise BadInput(f"stoves.{s['id']}: state không hợp lệ: {state}")
        oid, dish = _linked_dish(f"stoves.{s['id']}", s, menu)
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in s:
                _nonneg_int(f"stoves.{s['id']}.{key}", s[key])
        if state == "cooking" and s.get("cook_ticks_left", 0) <= 0 and isinstance(s.get("dish"), dict):
            raise BadInput(f"stoves.{s['id']}: bếp cooking phải có cook_ticks_left dương")
        if state == "idle" and (dish is not None or oid is not None):
            raise BadInput(f"stoves.{s['id']}: bếp idle không được giữ món hay đơn")
        if state != "idle" and dish is None:
            raise BadInput(f"stoves.{s['id']}: bếp {state} phải có món")
        if dish is not None:
            stove_dishes[s["id"]] = dish
        if oid is not None:
            if not isinstance(oid, str) or not oid:
                raise BadInput(f"stoves.{s['id']}: order_id phải là chuỗi khác rỗng")
            if oid in stove_orders:
                raise BadInput(f"hai bếp cùng giữ một đơn: {oid}")
            stove_orders[oid] = s["id"]
        known_stoves[s["id"]] = s

    hand = b.get("hand")
    hand_oid = None
    hand_dish = None
    if hand is not None:
        if isinstance(hand, dict):
            extra = set(hand) - HAND_KEYS
            if extra:
                raise BadInput(f"hand có trường lạ: {sorted(extra)}")
            hand_oid, hand_dish = _linked_dish("hand", hand, menu)
            if hand_dish is None:
                raise BadInput("hand cần món và order_id")
            if "base_price" in hand:
                _nonneg_int("hand.base_price", hand["base_price"])
                if hand["base_price"] == 0:
                    raise BadInput("hand.base_price phải dương")
            if hand_oid is not None and (not isinstance(hand_oid, str) or not hand_oid):
                raise BadInput("hand: order_id phải là chuỗi khác rỗng")
        else:
            raise BadInput("hand phải là payload món chứa order_id")

    if hand_oid is not None and hand_oid in stove_orders:
        raise BadInput(f"bếp và tay cùng giữ một đơn: {hand_oid}")

    customers = b.get("customers", [])
    cust_ids = set()
    table_ids = []
    total_reserved = {}
    stock_raw = b.get("stock")
    stock_is_items = isinstance(stock_raw, list)
    stock_item_map = {it["id"]: it for it in stock_raw} if stock_is_items else {}
    seen_reserved_item_ids = set()

    for c in customers:
        if not isinstance(c, dict):
            raise BadInput("customers phải là mảng object")
        cid = c.get("id")
        if not isinstance(cid, str) or not cid:
            raise BadInput("customers: mỗi phần tử cần id (chuỗi khác rỗng)")
        cust_ids.add(cid)
        extra = set(c) - CUSTOMER_KEYS
        if extra:
            raise BadInput(f"customers.{cid}: trường lạ: {sorted(extra)}")

        tid = c.get("table_id")
        if not isinstance(tid, str) or tid not in known_tables:
            raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
        table_ids.append(tid)

        did = c.get("dish_id")
        if not isinstance(did, str) or did not in menu:
            raise BadInput(f"customers.{cid}: dish_id phải là món trong menu")

        state = c.get("state", "waiting")
        if state not in CUSTOMER_STATES:
            raise BadInput(f"customers.{cid}: state không hợp lệ: {state}")

        status = c.get("order_status", "reserved" if state == "waiting" else "served")
        if status not in ORDER_STATUSES:
            raise BadInput(f"customers.{cid}: order_status không hợp lệ: {status}")

        for timer in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
            if timer in c:
                _nonneg_int(f"customers.{cid}.{timer}", c[timer])

        if state == "eating" and status != "served":
            raise BadInput(f"customers.{cid}: khách đang ăn phải có order_status là 'served'")
        if state == "eating" and (c.get("eat_ticks_left", 0) <= 0 or c.get("base_price") is None):
            raise BadInput(f"customers.{cid}: khách đang ăn phải có eat_ticks_left dương và base_price đã chốt")
        if state == "waiting" and status == "served":
            raise BadInput(f"customers.{cid}: đơn served chỉ dành cho khách đang ăn")
        refs = [d for o, d in ([(o, stove_dishes.get(sid)) for o, sid in stove_orders.items()]
                               + [(hand_oid, hand_dish)]) if o == cid]
        if status == "assigned" or status in LEGACY_ASSIGNED:
            if len(refs) != 1:
                raise BadInput(f"customers.{cid}: đơn assigned phải có đúng một món ở bếp hoặc tay")
            if refs[0] is not None and refs[0] != did:
                raise BadInput(f"customers.{cid}: món ở bếp/tay không khớp đơn ({refs[0]} ≠ {did})")
        elif refs:
            raise BadInput(f"customers.{cid}: đơn {status} không được có món ở bếp hoặc tay")

        if "tip" in c:
            tip = c["tip"]
            if isinstance(tip, bool) or not isinstance(tip, (int, float)) or tip < 0:
                raise BadInput(f"customers.{cid}.tip phải là số không âm")

        if "base_price" in c and c["base_price"] is not None:
            bp = c["base_price"]
            if isinstance(bp, bool) or not isinstance(bp, int) or bp <= 0:
                raise BadInput(f"customers.{cid}.base_price phải là số nguyên dương")

        recipe = menu[did]["recipe"]

        if "freshness" in tuning and "reserved" in c and not isinstance(c["reserved"], list):
            raise BadInput(f"customers.{cid}.reserved phải là mảng id")
        if "reserved" in c and c["reserved"] is not None:
            res = c["reserved"]
            if isinstance(res, list):
                if status != "reserved":
                    if res:
                        raise BadInput(f"customers.{cid}: trạng thái đơn hàng {status} mâu thuẫn với nguyên liệu giữ")
                else:
                    for iid in res:
                        if not isinstance(iid, str) or not iid:
                            raise BadInput(f"customers.{cid}.reserved: item_id phải là chuỗi khác rỗng")
                        if stock_is_items and iid not in stock_item_map:
                            raise BadInput(f"customers.{cid}.reserved: item_id {iid} không có trong stock")
                        if iid in seen_reserved_item_ids:
                            raise BadInput(f"customers.{cid}.reserved: cá thể {iid} bị dùng chung giữa nhiều đơn")
                        seen_reserved_item_ids.add(iid)
                        if stock_is_items and stock_item_map[iid]["fresh"] < tuning.get("freshness", {}).get("spoiled_below", 30):
                            raise BadInput(f"customers.{cid}.reserved: cá thể {iid} bị ươn (fresh < 30)")
                    res_counts = {}
                    if stock_is_items:
                        for iid in res:
                            k = stock_item_map[iid]["kind"]
                            res_counts[k] = res_counts.get(k, 0) + 1
                        if res_counts != recipe:
                            raise BadInput(f"customers.{cid}: nguyên liệu giữ không phù hợp công thức món {did}")
            elif isinstance(res, dict):
                for rk, rv in res.items():
                    if rk not in all_kinds:
                        raise BadInput(f"customers.{cid}.reserved: nguyên liệu lạ {rk}")
                    if isinstance(rv, bool) or not isinstance(rv, int) or rv < 0:
                        raise BadInput(f"customers.{cid}.reserved: số lượng cho {rk} phải là số nguyên không âm")

                cleaned_res = {k: v for k, v in res.items() if v > 0}
                if status != "reserved":
                    if cleaned_res:
                        raise BadInput(f"customers.{cid}: trạng thái đơn hàng {status} mâu thuẫn với nguyên liệu giữ")
                else:
                    if cleaned_res != recipe:
                        raise BadInput(f"customers.{cid}: nguyên liệu giữ không phù hợp công thức món {did}")
                if status == "reserved":
                    for rk, rv in cleaned_res.items():
                        total_reserved[rk] = total_reserved.get(rk, 0) + rv
            else:
                raise BadInput(f"customers.{cid}.reserved phải là object hoặc mảng")
        else:
            if status == "reserved" and not stock_is_items:
                for rk, rv in recipe.items():
                    total_reserved[rk] = total_reserved.get(rk, 0) + rv

    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")

    occupying = {c["table_id"]: c["id"] for c in customers}
    for table in b.get("tables", []):
        if "customer_id" in table and table["customer_id"] != occupying.get(table["id"]):
            raise BadInput(f"tables.{table['id']}.customer_id không khớp với khách tại bàn")
    for oid in stove_orders:
        if oid not in cust_ids:
            raise BadInput(f"bếp tham chiếu order/customer không tồn tại: {oid}")
    if hand_oid is not None and hand_oid not in cust_ids:
        raise BadInput(f"tay tham chiếu order/customer không tồn tại: {hand_oid}")

    if "stock" in b and not stock_is_items:
        stock = b["stock"]
        for rk, rv in total_reserved.items():
            if rv > stock.get(rk, 0):
                raise BadInput(f"tổng nguyên liệu giữ vượt quá kho thực tế cho {rk}: giữ {rv}, kho có {stock.get(rk, 0)}")


def validate_quan_against_inventory(scenario_quan: dict, inventory, tuning: dict = None, day_plan: dict = None):
    """Kiểm tra kho thực tế và kế hoạch ngày trước khi mở quán (phục vụ Lát D)."""
    if tuning is None:
        from .contract import load_contract
        tuning = load_contract()["tuning"]

    if isinstance(inventory, dict) and "items" in inventory and isinstance(inventory["items"], list):
        inv_data = inventory["items"]
    elif isinstance(inventory, (dict, list)):
        inv_data = inventory
    else:
        raise BadInput("inventory phải là dict hoặc mảng")

    reservation_type = list if isinstance(inv_data, list) else dict
    for customer in scenario_quan.get("customers", []):
        default_status = "reserved" if customer.get("state", "waiting") == "waiting" else "served"
        reserved = customer.get("reserved")
        if (customer.get("order_status", default_status) == "reserved" and reserved is not None
                and not isinstance(reserved, reservation_type)):
            raise BadInput(f"customers.{customer.get('id')}.reserved: kiểu giữ chỗ phải khớp kiểu kho")

    menu = tuning.get("menu", {})
    all_kinds = set(KINDS_P1) | {k for dish in menu.values() for k in dish.get("recipe", {})}
    cleaned_inv = validate_items(inv_data, kinds=all_kinds, contract_version="1.2" if "freshness" in tuning else None)

    if isinstance(cleaned_inv, list):
        # Resolve explicit item references against the actual file or morning handoff.
        _validate_quan(dict(scenario_quan, stock=cleaned_inv), tuning)
        inv_stock = {}
        for it in cleaned_inv:
            if it["fresh"] >= tuning.get("freshness", {}).get("spoiled_below", 30):
                inv_stock[it["kind"]] = inv_stock.get(it["kind"], 0) + 1
    else:
        inv_stock = cleaned_inv

    plan_dishes = None
    if day_plan is not None:
        if isinstance(day_plan, (list, set)):
            plan_dishes = set(day_plan)
        elif isinstance(day_plan, dict):
            if "dishes" in day_plan:
                plan_dishes = set(day_plan["dishes"].keys())
            elif "menu" in day_plan:
                plan_dishes = set(day_plan["menu"].keys())
            else:
                plan_dishes = {k for k in day_plan if k in menu}

    customers = scenario_quan.get("customers", [])
    total_reserved = {}
    for c in customers:
        did = c.get("dish_id")
        if plan_dishes is not None and did not in plan_dishes:
            raise BadInput(f"khách {c.get('id')} gọi món {did} không thuộc kế hoạch ngày")

        status = c.get("order_status", "reserved" if c.get("state", "waiting") == "waiting" else "served")
        if status == "reserved":
            recipe = menu[did]["recipe"]
            res = recipe if isinstance(cleaned_inv, list) else c.get("reserved", recipe)
            for rk, rv in res.items():
                total_reserved[rk] = total_reserved.get(rk, 0) + rv

    for rk, rv in total_reserved.items():
        if rv > inv_stock.get(rk, 0):
            raise BadInput(f"tổng nguyên liệu giữ cho khách vượt quá kho thực tế cho {rk}: giữ {rv}, kho có {inv_stock.get(rk, 0)}")

    for s in scenario_quan.get("stoves", []):
        dish = s.get("dish") or s.get("dish_id")
        if isinstance(dish, dict):
            dish = dish.get("dish_id")
        if dish and plan_dishes is not None and dish not in plan_dishes:
            raise BadInput(f"bếp {s.get('id')} có món {dish} không thuộc kế hoạch ngày")

    hand = scenario_quan.get("hand")
    if hand:
        dish = hand.get("dish") or hand.get("dish_id") if isinstance(hand, dict) else hand
        if isinstance(dish, dict):
            dish = dish.get("dish_id")
        if dish and plan_dishes is not None and dish not in plan_dishes:
            raise BadInput(f"tay đang cầm món {dish} không thuộc kế hoạch ngày")

