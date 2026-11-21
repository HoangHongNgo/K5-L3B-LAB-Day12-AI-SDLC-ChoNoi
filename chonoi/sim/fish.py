"""Đàn cá bơi và sinh (TICKET-02 mục 1.1 "Đàn cá bơi", "Điểm sinh", "Sinh cá"; 4.3; 4.5 "Gather").

Chỉ bật khi tuning gather có khóa v1.1 (`fish_speed`); contract v1.0 giữ 6 đàn đứng yên như Phase 1.

- Đầu ca: `fish_initial` (số) đàn ở các điểm sinh khác nhau, chọn như luật sinh cá.
- Mỗi bước (sau bắt cá và xét hết giờ, chỉ khi còn giờ): mỗi đàn theo id tăng `age_ticks`; nếu
  `age_ticks` chia hết `fish_turn_ticks` (bước bơi thứ 120, 240…) thì đổi hướng theo seed TRƯỚC khi
  di chuyển; đi `fish_speed / tick_hz` m theo hướng; tới mép `fish_x` hoặc dải độ sâu của loài thì
  phản xạ phần quãng đường còn lại và đảo thành phần hướng vuông góc với mép (góc: đảo cả hai).
- Tại `phase_tick = fish_spawn_ticks·k` (k ≥ 1), sau khi bơi: nếu dưới `fish_max`, sinh tối đa một
  đàn ở điểm cách mọi đàn đang sống > `fish_spawn_clearance`. Loài chọn theo `fish_weights` chuẩn hóa
  lại trên các loài còn điểm, rồi chọn đều một điểm, hướng theo seed. Cá mới bơi từ bước sau.
- `random_fish: false`: cá fixture đứng yên, không sinh.

Luồng RNG riêng: "fish_turn" (đổi hướng), "fish_spawn" (đàn đầu ca và sinh thêm).
"""

import math

from ..ids import sort_by_id


class FishSchools:
    def __init__(self, gather_tuning, scenario, streams, ids, tick_hz):
        g = gather_tuning
        self.g = g
        self.rng = streams
        self.ids = ids
        self.enabled = "fish_speed" in g
        random_fish = scenario.get("random_fish", True)
        self.moving = self.enabled and random_fish
        self.step_dist = g["fish_speed"] / tick_hz if self.enabled else 0.0
        if "fish" in scenario:
            src = scenario["fish"]
        elif random_fish and not isinstance(g["fish_initial"], list):
            src = None
        elif random_fish:
            src = g["fish_initial"]
        else:
            src = []
        self.fish = []
        if src is not None:
            for f in src:
                fish = {"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                        "heading_deg": f.get("heading_deg", 0)}
                if self.enabled:
                    fish["age_ticks"] = f.get("age_ticks", 0)
                self.fish.append(fish)
                ids.reserve(f["id"])
        else:
            for _ in range(int(g["fish_initial"])):
                self._spawn()

    # --- mỗi bước ------------------------------------------------------------------
    def step(self, phase_tick) -> list:
        if not self.moving:
            return []
        for f in sort_by_id(self.fish):
            self._swim(f)
        events = []
        every = int(self.g["fish_spawn_ticks"])
        if phase_tick > 0 and phase_tick % every == 0:
            f = self._spawn()
            if f is not None:
                events.append(("fish_spawned", {"id": f["id"], "kind": f["kind"], "pos": list(f["pos"])}))
        return events

    def _swim(self, f):
        f["age_ticks"] += 1
        if f["age_ticks"] % int(self.g["fish_turn_ticks"]) == 0:
            f["heading_deg"] = self.rng.get("fish_turn").random() * 360.0
        h = math.radians(f["heading_deg"])
        vx, vd = math.cos(h), math.sin(h)
        x = f["pos"][0] + vx * self.step_dist
        d = f["pos"][1] + vd * self.step_dist
        x, fx = _reflect(x, self.g["fish_x"])
        d, fd = _reflect(d, self.g["fish_depths"][f["kind"]])
        f["pos"] = [x, d]
        if fx or fd:
            f["heading_deg"] = math.degrees(math.atan2(-vd if fd else vd, -vx if fx else vx)) % 360.0

    # --- sinh cá -------------------------------------------------------------------
    def _free_points(self):
        clear = self.g["fish_spawn_clearance"]
        free = {}
        for kind in sorted(self.g["fish_spawn_depths"]):
            pts = [[float(x), float(d)] for x in self.g["fish_spawn_x"] for d in self.g["fish_spawn_depths"][kind]]
            pts = [p for p in pts if all(math.dist(p, f["pos"]) > clear for f in self.fish)]
            if pts:
                free[kind] = pts
        return free

    def _spawn(self):
        if len(self.fish) >= int(self.g["fish_max"]):
            return None
        free = self._free_points()
        if not free:
            return None
        rng = self.rng.get("fish_spawn")
        kinds = sorted(free)
        weights = [self.g["fish_weights"][k] for k in kinds]
        r = rng.random() * sum(weights)
        kind = kinds[-1]
        for k, w in zip(kinds, weights):
            if r < w:
                kind = k
                break
            r -= w
        pos = free[kind][rng.randrange(len(free[kind]))]
        f = {"id": self.ids.new("F"), "kind": kind, "pos": list(pos),
             "heading_deg": rng.random() * 360.0, "age_ticks": 0}
        self.fish.append(f)
        return f


def _reflect(v, bounds):
    """Phản xạ tọa độ `v` vào [lo, hi]; trả (v, có đảo hướng không) theo số lần chạm mép lẻ."""
    lo, hi = bounds
    flipped = False
    while v < lo or v > hi:
        v = 2 * lo - v if v < lo else 2 * hi - v
        flipped = not flipped
    return v, flipped
