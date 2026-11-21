"""Tuần tra, truy đuổi, va chạm và recoil trong Gather theo tuning v1.1."""

import math

from ..ids import sort_by_id

INACTIVE_STATES = {"recoil", "stunned"}
MONSTER_STATES = {"patrol", "chase"} | INACTIVE_STATES


def monster_bounds(bounds, species):
    """Giao của biên bản đồ và dải độ sâu của loài."""
    map_low, map_high = bounds["d"]
    species_low, species_high = species["depths"]
    return {"x": bounds["x"], "d": (max(map_low, species_low), min(map_high, species_high))}


class MonsterSim:
    def __init__(self, config, bounds, scenario, day, tick_hz):
        self.species = config["species"]
        self.tick_hz = tick_hz
        self.invuln_ticks = config["invuln_ticks"]
        self.loss_ratio = config["loss_ratio"]
        self.bounds = {kind: monster_bounds(bounds, spec) for kind, spec in self.species.items()}
        source = scenario if scenario is not None else [
            monster for monster in config["spawns"] if monster["from_day"] <= day
        ]
        self.monsters = [{
            "id": monster["id"],
            "kind": monster["kind"],
            "pos": list(monster["pos"]),
            "waypoints": [list(pos) for pos in monster["waypoints"]],
            "target_idx": monster.get("target_idx", 1),
            "state": monster.get("state", "patrol"),
            "state_ticks_left": monster.get("state_ticks_left", 0),
            "recoil_dir": (list(monster["recoil_dir"]) if monster.get("recoil_dir") is not None else None),
        } for monster in sort_by_id(source)]

    def snapshot(self):
        return [monster.copy() for monster in self.monsters]

    def step(self, player_pos, *, can_hit):
        """Di chuyển theo id, rồi trả id con gây hit nếu có."""
        closest = None
        closest_dist = math.inf
        for monster in self.monsters:
            spec = self.species[monster["kind"]]
            if monster["state"] in INACTIVE_STATES:
                self._step_inactive(monster, spec)
                continue  # Tick cuối recoil/choáng cũng không được gây hit.

            self._advance(monster, player_pos, spec)
            if can_hit and player_pos[1] >= spec["depths"][0]:
                distance = math.dist(monster["pos"], player_pos)
                if distance <= spec["hit_radius"] and distance < closest_dist:
                    closest, closest_dist = monster, distance

        if closest is None:
            return None
        self._start_recoil(closest, player_pos, closest_dist)
        return closest["id"]

    def _advance(self, monster, player_pos, spec):
        distance = math.dist(monster["pos"], player_pos)
        depth_allowed = player_pos[1] >= spec["depths"][0]
        if monster["state"] == "chase":
            if not depth_allowed or distance > spec["exit_radius"]:
                monster["state"] = "patrol"
        elif depth_allowed and distance <= spec["detect_radius"]:
            monster["state"] = "chase"

        if monster["state"] == "chase":
            self._move_towards(monster, player_pos, spec["chase_speed"] / self.tick_hz)
        else:
            target = monster["waypoints"][monster["target_idx"]]
            if self._move_towards(monster, target, spec["patrol_speed"] / self.tick_hz):
                monster["target_idx"] = 1 - monster["target_idx"]

    def _move_towards(self, monster, target, travel):
        x, depth = monster["pos"]
        dx, dd = target[0] - x, target[1] - depth
        distance = math.hypot(dx, dd)
        # Sau nhiều bước, phép cộng float có thể để lại sai số rất nhỏ tại waypoint.
        if distance <= travel or math.isclose(distance, travel, rel_tol=0.0, abs_tol=1e-10):
            monster["pos"] = self._clamp(monster["kind"], target)
            return True
        monster["pos"] = self._clamp(monster["kind"], (x + travel * dx / distance,
                                                      depth + travel * dd / distance))
        return False

    def _clamp(self, kind, pos):
        bounds = self.bounds[kind]
        return [min(hi, max(lo, value)) for value, (lo, hi) in zip(pos, (bounds["x"], bounds["d"]))]

    def _start_recoil(self, monster, player_pos, distance):
        if distance == 0:
            direction = [1.0, 0.0]
        else:
            direction = [(m - p) / distance for m, p in zip(monster["pos"], player_pos)]
        monster["state"] = "recoil"
        monster["state_ticks_left"] = self.species[monster["kind"]]["recoil_ticks"]
        monster["recoil_dir"] = direction

    def _step_inactive(self, monster, spec):
        if monster["state"] == "recoil":
            travel = spec["recoil_dist"] / spec["recoil_ticks"]
            pos = [p + travel * d for p, d in zip(monster["pos"], monster["recoil_dir"])]
            monster["pos"] = self._clamp(monster["kind"], pos)
        monster["state_ticks_left"] -= 1
        if monster["state_ticks_left"] == 0:
            monster["state"] = "patrol"
            monster["recoil_dir"] = None
