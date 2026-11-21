"""Trạng thái xuyên Ngày cho `--mode day` (TICKET-02 mục 2 "Vòng ngày", 4.3, 4.5 "Shop").

DayState là hàm thuần, không giữ sim. Lát D (day.py) chỉ gọi các hàm này:
- DayState(tuning, day_block=None): khởi tạo từ khối `day` của scenario (mặc định tiền/earned 0,
  uy tín theo tuning, cấp `{}`) và ĐÃ dựng Ngày 1: `day = 1`, cấp trong khối `day` có hiệu lực ngay
  (DaySim đọc `state.day` lúc khởi tạo và chỉ gọi start_next_day() sau khi Shop đóng).
  Kiểm hợp lệ khối `day` nằm ở scenario.py.
- start_next_day(): tăng `day`, sao `upgrades -> active_upgrades` (chỉ lúc dựng Ngày mới) và trả
  limits() của Ngày mới.
- limits(): {"oxygen_max_ticks", "hp_max"} theo cấp đang có hiệu lực.
- apply_quan_result(result): tiền, earned, uy tín sau ca quán (giá trị tuyệt đối, uy tín kẹp).
- apply_shop_result(result): tiền và cấp đã mua sau Shop.
- quan_kwargs() / shop_kwargs(stock): tham số dựng QuanSim / ShopSim của Ngày.
"""

from .gather import gather_limits


class DayState:
    def __init__(self, tuning, day_block=None):
        b = day_block or {}
        q = tuning["quan"]
        self.tuning = tuning
        self.money = b.get("money", 0)
        self.earned = b.get("earned", 0)
        self.reputation = b.get("reputation", q["reputation_initial"])
        self.upgrades = dict(b.get("upgrades", {}))
        self.active_upgrades = dict(self.upgrades)
        self.day = 1

    def _clamp_reputation(self, value):
        q = self.tuning["quan"]
        return max(q["reputation_min"], min(q["reputation_max"], value))

    def limits(self) -> dict:
        oxygen_max_ticks, hp_max = gather_limits(self.tuning, self.active_upgrades)
        return {"oxygen_max_ticks": oxygen_max_ticks, "hp_max": hp_max}

    def start_next_day(self) -> dict:
        self.day += 1
        self.active_upgrades = dict(self.upgrades)
        return self.limits()

    def apply_quan_result(self, result):
        self.money = result["money"]
        self.earned = result["earned"]
        self.reputation = self._clamp_reputation(result["reputation"])

    def apply_shop_result(self, result):
        self.money = result["money"]
        self.upgrades = dict(result["upgrades"])

    def quan_kwargs(self) -> dict:
        return {"money": self.money, "earned": self.earned, "reputation": self.reputation}

    def shop_kwargs(self, stock) -> dict:
        return {"money": self.money, "earned": self.earned, "upgrades": dict(self.upgrades), "stock": dict(stock)}
