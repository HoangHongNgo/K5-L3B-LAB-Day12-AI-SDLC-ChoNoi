"""Lớp bọc pause dùng chung cho gather, quan và day (Test Contract v1.1, mục 4.2).

`PauseSim(sim)` bọc MỘT sim bất kỳ có giao diện `step(inp) -> events`, `snapshot()`, `done`:

* Cạnh lên của `pause` được xét TRƯỚC mọi thứ khác trong bước.
* Chưa pause + cạnh `pause`: vào pause, phát `paused`, KHÔNG chạy sim (đồng hồ, lịch và mọi timer đứng yên).
* Đang pause: bỏ qua mọi cạnh hành động và `buy`; không phát gì; sim không chạy.
* Đang pause + cạnh `pause`: ra pause, phát `resumed`, rồi chạy gameplay NGAY trong bước đó với input của bước.
* `sim_tick` chỉ tăng ở các bước sim thật sự chạy (tick ngoài do runner đếm). `phase_tick` lấy của sim nếu
  sim có (QuanSim, DaySim), không thì bằng `sim_tick`.
* Giữ nút qua đổi pha không tạo cạnh mới: cạnh do `InputPlayer`/`LiveInputs` sinh ra ngoài sim, nên đổi pha
  bên trong `DaySim` không thể làm một nút đang giữ thành cạnh lên.

Mọi thuộc tính khác (mode, phase, money, earned, reputation, time_left_ticks, done, reason, result,
inventory_items...) được chuyển thẳng cho sim bên trong.
"""


class PauseSim:
    def __init__(self, inner):
        self._inner = inner
        self.paused = False
        self._steps = 0

    # --- chuyển tiếp -----------------------------------------------------------------
    def __getattr__(self, name):
        # Chỉ chạy khi thuộc tính không có trên wrapper; tránh đệ quy khi _inner chưa có.
        if name == "_inner":
            raise AttributeError(name)
        return getattr(self._inner, name)

    @property
    def inner(self):
        return self._inner

    @property
    def sim_tick(self) -> int:
        return getattr(self._inner, "sim_tick", self._steps)

    @property
    def phase_tick(self) -> int:
        return getattr(self._inner, "phase_tick", self.sim_tick)

    def snapshot(self) -> dict:
        return self._inner.snapshot()

    # --- một bước ---------------------------------------------------------------------
    def step(self, inp):
        events = []
        if inp.pressed("pause") and not self._inner.done:
            if not self.paused:
                self.paused = True
                events.append(("paused", {}))
                return events
            self.paused = False
            events.append(("resumed", {}))
            events.extend(self._run(inp))
            return events
        if self.paused:
            return events
        return self._run(inp)

    def _run(self, inp):
        self._steps += 1
        return self._inner.step(inp)
