"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.

Mode `day` (v1.1, lát D): event của DaySim là (name, data, meta) với meta {"day","phase"} -> vỏ event có `day`;
event đầu Ngày 1 (`initial_events`) ghi ở tick 0 trước snapshot tick 0; `sim_tick`/`phase_tick` lấy từ sim;
dòng `end` có `days_completed`.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "day":
        from .sim.day import DaySim
        return DaySim(tuning, scenario, streams, ids, days=days)
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1, sim=None):
        self.mode = mode
        self.tuning = tuning
        self.sim = sim if sim is not None else build_sim(mode, tuning, scenario, seed, inventory, days)
        self.tick = 0

    def _ticks(self):
        """(sim_tick, phase_tick): mode day đếm theo sim (pha đặt lại phase_tick); mode lẻ = tick."""
        if self.mode == "day":
            return self.sim.sim_tick, self.sim.phase_tick
        return self.tick, self.tick

    def _row(self, tick, ev):
        name, data = ev[0], ev[1]
        row = {"type": "event", "tick": tick}
        if len(ev) > 2:  # thứ tự khóa theo ví dụ TICKET-02 mục 4.4: type, tick, phase, day, name, data
            row["phase"] = ev[2]["phase"]
            row["day"] = ev[2]["day"]
        else:
            row["phase"] = self.sim.phase
        row.update(name=name, data=data)
        return row

    def initial_rows(self) -> list:
        """Event phát lúc dựng sim (mode day: day_start, day_plan, phase_start ở tick 0)."""
        return [self._row(0, ev) for ev in getattr(self.sim, "initial_events", [])]

    @property
    def done(self) -> bool:
        return self.sim.done

    def snapshot(self) -> dict:
        s = _common(self.sim, self.tick, *self._ticks(), self.tuning, "finished" if self.sim.done else "playing")
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        events = self.sim.step(inp)
        self.tick += 1
        return [self._row(self.tick, ev) for ev in events]

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.tick, self.tick, self.tuning, "")["score"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": self._ticks()[0], "mode": sim.mode,
               "state": "finished" if sim.done else "playing",
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1, sim=None):
    sess = Session(mode, tuning, scenario, seed, inventory, days, sim)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_rows():  # mode day: event đầu Ngày 1 ở tick 0
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
