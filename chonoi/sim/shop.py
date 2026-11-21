"""Shop cuối Ngày (TICKET-02 mục 2 "Shop và nâng cấp", 4.2, 4.4, 4.5 "Shop").

Giao diện chốt sẵn (TASK.md Phase 2): ShopSim(tuning, *, money, earned, upgrades, stock) với
step(inputs) -> events, snapshot() -> dict, done, result.

Một bước: giảm thời gian còn lại -> xử lý một `buy` (nếu frame có) -> cạnh `shop_done` -> hết giờ.
- `buy` mua cấp kế tiếp của nâng cấp có trong `shop.upgrades` (giá, cấp đọc từ contract).
  Đủ đúng giá vẫn mua; trừ `money`, giữ `earned`. Phát `bought {upgrade, level, price, money}`.
- Thiếu tiền / đã tối đa / lệnh lạ -> `buy_failed {action, reason}` (funds/max_level/unknown), tiền và cấp giữ nguyên.
- Lệnh của mở rộng chưa bật (weapon, net, buy:<kind>, sell:<kind>) bị bỏ qua (mục 4.2).
- Đóng bằng cạnh `shop_done` -> `shop_end {reason:"done"}`; hết `max_ticks` -> `shop_end {reason:"time"}`.
  Nút ở bước cuối được ưu tiên là `done`.
"""

EXTENSION_UPGRADES = ("weapon", "net")
VENDOR_PREFIXES = ("buy:", "sell:")


class ShopSim:
    mode = "shop"
    phase = "shop"

    def __init__(self, tuning, *, money, earned, upgrades, stock, reputation=None):
        self.t = tuning["shop"]
        self.upgrade_table = self.t["upgrades"]
        self.money = money
        self.earned = earned
        self.reputation = tuning["quan"]["reputation_initial"] if reputation is None else reputation
        self.upgrades = dict(upgrades)
        self.stock = {k: v for k, v in sorted(stock.items()) if v > 0}
        self.time_left_ticks = int(self.t["max_ticks"])
        self.done = False
        self.reason = None

    @property
    def result(self) -> dict:
        return {"money": self.money, "earned": self.earned, "upgrades": dict(self.upgrades),
                "stock": dict(self.stock)}

    def snapshot(self) -> dict:
        return {"stock": dict(self.stock), "upgrades": dict(self.upgrades)}

    def step(self, inp) -> list:
        if self.done:
            return []
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        cmd = getattr(inp, "buy", None)
        if cmd:
            events.extend(self._buy(cmd))
        if inp.pressed("shop_done"):
            self._close("done", events)
        elif self.time_left_ticks <= 0:
            self._close("time", events)
        return events

    def _buy(self, cmd) -> list:
        if cmd not in self.upgrade_table:
            if cmd in EXTENSION_UPGRADES or cmd.startswith(VENDOR_PREFIXES):
                return []  # mở rộng chưa bật: bỏ qua
            return [("buy_failed", {"action": cmd, "reason": "unknown"})]
        level = self.upgrades.get(cmd, 0) + 1
        entry = next((e for e in self.upgrade_table[cmd] if e["level"] == level), None)
        if entry is None:
            return [("buy_failed", {"action": cmd, "reason": "max_level"})]
        if entry["price"] > self.money:
            return [("buy_failed", {"action": cmd, "reason": "funds"})]
        self.money -= entry["price"]
        self.upgrades[cmd] = level
        return [("bought", {"upgrade": cmd, "level": level, "price": entry["price"], "money": self.money})]

    def _close(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))
