# Hợp đồng tích hợp — Phase 1 (v1.0) và Phase 2 (v1.1)

> **Phase 2: mục 1–5 là v1.0, đọc thêm [mục 6 (v1.1)](#6-phase-2--thay-đổi-từ-v10-contract-v11).** Chốt ở kickoff 1.1 bởi PO (HoangHongNgo). Đổi gì ở file này: báo cả nhóm trước, ghi lý do trong commit (hoặc ADR ở `docs/adr/`).
> Nguồn: PRD-0 (mục D, E, F, G), code khung `chonoi/`, `docs/plan/phase-1.md`. Mục nào ghi **[giả định]** là nhóm tự chốt khi PRD chưa nói rõ; câu hỏi tương ứng nằm ở [`docs/clarify.md`](../clarify.md). Có câu trả lời khác thì sửa đúng dòng đó.

Số liệu (bán kính, thời gian, giá…) **không** chép vào đây: luôn đọc `game.contract.json` → `tuning`.

---

## 1. Schema file kho (PRD-0 mục G)

```json
{"items": {"<kind>": <số nguyên ≥ 0>, ...}}
```

| Quy tắc | Chi tiết |
|---|---|
| Khóa gốc | Đúng một khóa `items` (object). Khóa khác → mã 2. |
| `kind` hợp lệ | v1.0: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. **v1.1 thêm `ca_keo`, `keo_neo`** (6 loại, `chonoi/inventory.py:KINDS`). Kind lạ → mã 2. |
| Số lượng | Số nguyên ≥ 0, không phải bool. Âm/thực/bool → mã 2. Mục bằng 0 được đọc nhưng bị bỏ. |
| Ghi (gather) | Ghi **đúng một lần** khi có `gather_end` (`docked`, `time`, `fainted`). Chạm `--ticks` trước khi kết thúc → **không** ghi, file đích giữ nguyên. |
| Định dạng ghi | Khóa sắp theo id nguyên liệu, bỏ mục 0, JSON gọn `(",", ":")`, UTF-8, kết thúc `\n`, ghi nguyên tử (file tạm + `os.replace`). |
| Nội dung | `items` = đếm từ giỏ `hold` lúc kết thúc. `fainted` → `{"items":{}}`. |
| Đọc (quan) | `--inventory kho.json` nạp vào `stock`. Không được vừa có `--inventory` vừa có `quan.stock` trong scenario (mã 2). |

Ví dụ hợp lệ: [`inventory.sample.json`](inventory.sample.json) → `{"items":{"bong_sung":2,"ca_loc":1}}`.
Đã kiểm: `python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory docs/contracts/inventory.sample.json --out q.jsonl` → mã 0, snapshot tick 0 có `"stock":{"bong_sung":2,"ca_loc":1}`.

---

## 2. Dòng JSONL và event (PRD-0 mục E)

Mỗi event là một dòng `{"type":"event","tick":k+1,"phase":"gather|quan","name":...,"data":{...}}` (runner lo vỏ; sim chỉ trả `(name, data)`). Trong một bước, event xếp **theo thứ tự xử lý** trong `step()`; nhiều thực thể cùng loại thì theo `sort_by_id`. Vị trí là mảng 2 số `[x, d]` / `[x, z]`.

### 2.1 Gather — `GatherSim.step` (thứ tự bước)

| # bước | Event | `data` | Ai phát (lát) | Ai nghe |
|---|---|---|---|---|
| 1 | `node_regrown` | `{"node_id"}` | khung (có sẵn) | UI, test |
| 2 | `dive` | `{"pos"}` — pos cuối bước | lát 1 | UI, test |
| 2 | `surface` | `{"pos"}` — pos cuối bước | lát 1 | UI, test |
| 2 | `oxygen_empty` | `{}` **[giả định]** | lát 1 | UI (cảnh báo), test |
| 2 | `choke` | `{"hp"}` — Máu sau khi trừ | lát 1 | UI, test |
| 2 | `faint` | `{"cause":"choke","lost":[kind…],"hp":0}` — `lost` theo LIFO (mới nhất trước) | lát 1 | UI, test |
| 3 | `gather` | `{"node_id","kind","count"}` **[giả định `kind`,`count`]**; `count` = `node_yield` | lát 2 | UI, test |
| 3/4 | `hold_full` | `{"action":"gather"\|"catch","node_id"\|"fish_id","required","free"}` | lát 2 | UI, test |
| 4 | `fish_caught` | `{"fish_id","kind","count"}` **[giả định]**; `count` = `fish_yield[kind]` | lát 2 | UI, test |
| 3/5, hoặc 2 khi ngất | `gather_end` | `{"reason":"docked"\|"time"\|"fainted","inventory":{"items":{…}}}` | khung + lát 1 (`fainted`) | runner (ghi kho), UI |

Thứ tự trong một bước (khung đã đặt sẵn trong `step()`): 1 đồng hồ/hồi chiêu/mọc lại → 2 bơi + chặn mép → dive/surface → oxy/ngạt/ngất → 3 `interact` (bến **trước**, rồi hái) → 4 `catch` → 5 hết giờ.

### 2.2 Quán — `QuanSim.step`

`order_id` **= id khách** (mỗi khách đúng một đơn ở P1) **[giả định]**.

| Event | `data` | Ai phát (lát) |
|---|---|---|
| `customer_arrived` | `{"customer_id","table_id","dish_id","reserved":{kind:n}}` **[giả định]** | lát 3 |
| `no_dish` | `{"table_id"}` **[giả định]** — có bàn trống nhưng không món nào đủ kho khả dụng | lát 3 |
| `customer_left` | `{"customer_id","table_id","reason":"patience"\|"closing"}` | lát 3 (patience), lát 4 (closing) |
| `cook_started` | `{"stove_id","order_id","dish_id","items":{kind:n} (sắp theo kind),"base_price"}` | lát 4 |
| `dish_ready` | `{"stove_id","order_id","dish_id"}` | lát 4 |
| `dish_picked` | `{"stove_id","order_id","dish_id"}` | lát 4 |
| `served` | `{"table_id","customer_id","order_id","dish_id","tip"}` | lát 4 |
| `paid` | `{"customer_id","order_id","amount","tip","reason":"finished_eating"\|"closing"}` — `amount` = `base_price + tip` | lát 4 |
| `quan_end` | `{"reason":"time","money","earned","shift_earned","reputation"}` | khung + lát 4 |

Cuối ca (lát 4): khách đang ăn → `paid` `closing`; khách đang chờ → `customer_left` `closing` (không trừ uy tín); rồi `quan_end`. Điểm = `earned + reputation_multiplier × floor(reputation)` (runner đã tính).

---

## 3. Cấu trúc khách / đơn (chốt giữa lát 3 ↔ lát 4)

Mỗi phần tử `QuanSim.customers` (snapshot in ra nguyên, sắp theo id):

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | str | id khách = `order_id` (cấp qua `IdAllocator`) |
| `table_id` | str | bàn đang ngồi |
| `dish_id` | str | khóa trong `tuning.menu` |
| `order_tick` | int | `phase_tick` lúc đến (để lấy đơn cũ nhất) |
| `state` | `"waiting"` \| `"eating"` | |
| `patience_ticks_left` | int | `patience_s × 60` lúc đến; giảm từ bước sau khi đến |
| `eat_ticks_left` | int | 0 khi chờ; `eat_s × 60` khi `served` |
| `order_status` | `"reserved"` \| `"cooking"` \| `"ready"` \| `"carried"` \| `"served"` | |
| `reserved` | `{kind:n}` | nguyên liệu đang giữ; rỗng sau `cook_started` |
| `base_price` | int \| null | chốt ở `cook_started` |
| `tip` | int | 0 cho tới `served` |

Kho khả dụng = `stock[kind] − Σ reserved[kind]`. `hand` = `null` hoặc `{"order_id","dish_id"}`. Bếp: `state` `"idle"|"cooking"|"ready"`, `dish` = `null` hoặc `{"order_id","dish_id"}`.

---

## 4. Giao diện sim ↔ UI (`chonoi/live.py`, `chonoi/web/index.html`)

UI **chỉ đọc** snapshot, **chỉ gửi** input. Không gọi hàm luật, không sửa state.

**Lệnh UI gửi** — `POST /input`: `{"move":[a,b], "interact":bool, "catch":bool}` (trạng thái phím đang giữ; `LiveInputs` tự lấy cạnh lên). `move` mỗi thành phần ∈ [−1, 1], chuẩn hóa nếu dài > 1. Gather: `[x, d]` (d dương = lặn xuống); quán: `[x, z]`.

**UI đọc** — `GET /state` = snapshot (cùng trường headless) + `meta` + `events`.

| Phần | Trường UI dùng cho HUD |
|---|---|
| Chung | `mode`, `state`, `time_left_ticks`, `money`, `earned`, `reputation`, `score` |
| Gather | `player.{pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, catch_cd_ticks, at_surface}`, `hold` (thứ tự nhặt), `hold_count`, `hold_capacity`, `nodes[].{id,pos,kind,ready,regrow_ticks}`, `fish[].{id,pos,kind,heading_deg}` |
| Quán | `player.pos`, `stock` (tồn, >0), `hand`, `stoves[].{id,pos,state,dish,cook_ticks_left,ready_ticks}`, `tables[].{id,pos,customer_id}`, `customers[]` (mục 3) |

UI tự tính "kho khả dụng" từ `stock` − `customers[].reserved`, không cần trường riêng. Sim thêm trường mới không làm vỡ UI (UI bỏ qua trường chưa biết).

---

## 5. Ranh giới file (ai sửa đâu)

| Lát | Người | Được sửa |
|---|---|---|
| 1 | ChuTungDuongg | `GatherSim.step` bước 2 (dive/surface, oxy, ngạt, ngất) + `_update_oxygen`; `tests/test_p1_lat1.py` |
| 2 | haiquanng | `GatherSim.step` bước 3–4 (hái, bắt cá) + `_add_to_hold`; `tests/test_p1_lat2.py` |
| 3 | minhphuong150505 | `QuanSim`: dựng khách, lịch khách, chọn món, giữ chỗ, kiên nhẫn; `_validate_quan` trong `chonoi/scenario.py`; `tests/test_p1_lat3.py` |
| 4 | phuthaitran | `QuanSim`: chọn interact, bếp, bưng, phục vụ, ăn/trả tiền, cuối ca; `tests/test_p1_lat4.py`, `tests/fixtures/quan_*.json` |
| HUD | RachalHys | `chonoi/web/`, `README.md`, `docs/verification/` |
| PO | HoangHongNgo | `docs/contracts/`, `game.contract.json`, `chonoi/contract.py`, `docs/clarify.md` |

Hàm dùng chung giỏ (lát 2 viết, lát 1 dùng): `_add_to_hold(kinds: list[str]) -> bool` — thêm đủ cả `kinds` theo thứ tự nếu `len(hold) + len(kinds) ≤ hold_capacity`, ngược lại không thêm gì và trả `False`. Ngất bỏ giỏ theo LIFO: `lost = list(reversed(hold))`.

---

## 6. Phase 2 — thay đổi từ v1.0 (contract v1.1)

> Nguồn: `TICKET2.md` (nguyên văn ở [`docs/plan/phase-2.md`](../plan/phase-2.md)) mục 1–4. Số liệu vẫn **chỉ** đọc từ `game.contract.json` → `tuning`; mục này chỉ ghi tên khóa, event và giao diện. Kiểm bằng `chonoi/contract.py` (sai → mã 2).

### 6.1 Khóa mới trong `game.contract.json`

| Phạm vi | Khóa |
|---|---|
| Gốc | `contract_version:"1.1"`, `extensions:[]` (khai mã mở rộng đã làm: `weapon`, `net`, `snake`, `burn`, `vendor`, `ca_ho`). |
| `gather` | `fish_initial` là **số** đàn đầu ca (8, không còn là mảng). Thêm `fish_speed, fish_turn_ticks, fish_max, fish_spawn_ticks, fish_spawn_clearance, fish_x` (miền x `[lo,hi]`), `fish_depths`, `fish_spawn_x` (danh sách x), `fish_spawn_depths`, `fish_weights` (map theo loài). `fish_yield` đủ 3 loài (`ca_linh`, `ca_loc`, `ca_keo`); nút `N5`/`N6` là `keo_neo`. |
| `gather.monsters` | `species.ca_sau {patrol_speed, chase_speed, detect_radius, exit_radius, depths, hit_radius, recoil_ticks, recoil_dist}`, `spawns[] {id, kind, pos, waypoints, from_day}`, `invuln_ticks`, `loss_ratio`. `pos` = waypoint đầu. |
| `quan`, `menu` | Bếp B1–B2, bàn T1–T4, 6 món; `burn_s` vẫn `null` (số dương chỉ khi bật mở rộng `burn`). |
| `day_plan` | Mảng đúng 5 object `{day, dishes, ingredients}` (`dishes`/`ingredients` là map id → số nguyên dương). `ingredients` **phải bằng** Σ công thức × số suất (`contract.plan_ingredients`). |
| `shop` | `{max_ticks, upgrades}`; `upgrades.oxygen[] {level, price, oxygen_max_s}`, `upgrades.hp[] {level, price, hp_max}`, mảng theo cấp (level 1, 2, …; giá trị tăng dần). |

Hàm dùng chung cho các lát: `chonoi.contract.plan_ingredients(dishes, menu)` và `check_dishes(name, dishes, menu)` (kiểm `day.day_plan` trong scenario).

### 6.2 Event mới và đổi

Vỏ event: `{"type":"event","tick","phase":"gather|quan|shop","day":N,"name","data"}` — **`day` chỉ có khi chạy `--mode day`**. Event kết thúc một pha mang pha cũ.

| Event | `data` | Ai phát |
|---|---|---|
| `monster_hit` | `{"monster_id","hp","lost":[kind…] (LIFO),"pos"}` — `pos` là vị trí người chơi | lát B |
| `fish_spawned` | `{"id","kind","pos"}` — chỉ khi sinh theo lịch (không phát cho đàn đầu ca) | lát A |
| `faint` | `{"cause":"choke"\|"monster","lost","hp":0}` | lát B |
| `day_start`, `phase_start` | `{}` | lát D |
| `day_plan` | `{"dishes","ingredients"}` của Ngày đó | lát D |
| `paused`, `resumed` | `{}` | `chonoi/sim/pause.py` (lát C) |
| `bought` | `{"upgrade","level","price","money"}` | lát S |
| `buy_failed` | `{"action","reason":"funds"\|"max_level"\|"out_of_stock"\|"unknown"}` | lát S |
| `shop_end` | `{"reason":"done"\|"time"}` | lát S |

Thứ tự đổi pha (cùng một tick): `day_start → day_plan → phase_start(gather)` · sau `gather_end` (kể cả `fainted`) dựng quán và `phase_start(quan)` · sau `quan_end` dựng Shop và `phase_start(shop)` · đóng Shop thì tăng `days_completed`, kết thúc hoặc dựng Ngày kế ngay tick đó. Pha mới chỉ chạy gameplay từ bước sau.

Dòng `end` của `day`: thêm `days_completed` (số Shop đã đóng); đủ Ngày thì `reason:"days_complete"`.

### 6.3 Inputs và pause

- Nút boolean mới: `pause` (cả 3 mode), `shop_done` (Shop). `attack`, `photo` chỉ khi bật mở rộng. Chỉ tác động ở **cạnh lên**; giữ nút qua đổi pha không tạo cạnh mới.
- `buy` là chuỗi khác rỗng, chạy **chỉ tại frame khai báo**: `oxygen`, `hp` (mở rộng: `weapon`, `net`, `buy:<kind>`/`sell:<kind>`). Lệnh không hỗ trợ → `buy_failed(unknown)`. Sai pha → bỏ qua.
- Xét cạnh `pause` **trước**. Bước vào pause chỉ tăng `tick` ngoài, phát `paused`; khi còn pause bỏ qua cạnh hành động và `buy`; `sim_tick`, `phase_tick`, lịch, timer đứng yên. Cạnh `pause` kế phát `resumed` và chạy gameplay ngay trong bước đó. Snapshot `state:"paused"`.
- `pause` xử lý ở lớp bọc `chonoi/sim/pause.py` (bọc bất kỳ sim nào), không nằm trong từng sim.

### 6.4 Giao diện sim chốt sẵn (không đổi trong phase nếu chưa báo cả nhóm)

| Lớp | Chữ ký |
|---|---|
| `GatherSim` | `(tuning, scenario, streams, *, day=1, active_upgrades={})`; `gather_end.data.inventory` theo schema kho |
| `QuanSim` | `(tuning, scenario, streams, *, inventory, menu_ids=None, money=0, earned=0, reputation=None)`; `menu_ids=None` là cả 6 món |
| `ShopSim` | `(tuning, *, money, earned, upgrades, stock)`; `result` trả `money`, `upgrades` |
| `DaySim` | `(tuning, scenario, streams, *, days=1)` |
| mọi sim | `step(inputs) -> events`, `snapshot() -> dict`, `done`, `result` (dict trạng thái cuối: tiền, earned, uy tín, kho dư…) |
| `DayState` (`chonoi/sim/progress.py`) | hàm thuần: `money, earned, reputation, upgrades, active_upgrades, day`; `apply_quan_result`, `apply_shop_result`, `start_next_day() -> {"oxygen_max_ticks","hp_max"}` |

### 6.5 Snapshot mới

| Phạm vi | Trường |
|---|---|
| Chung | `state:"paused"` khi đang pause |
| Gather | `monsters[] {id,kind,pos,waypoints,target_idx,state,state_ticks_left,recoil_dir}`, `player.invuln_ticks`; cá thêm `age_ticks` khi lát A xong |
| `day` (mọi pha) | `day`, `day_plan`, `upgrades` (cấp đã mua), `active_upgrades` (cấp đang áp dụng), `phase` ∈ `gather\|quan\|shop` |
| Shop | `stock` (kho dư từ ca quán), `time_left_ticks` tới lúc đóng |

Snapshot lúc đổi pha ghi pha mới với `phase_tick:0`.

### 6.6 Scenario v1.1

- `gather.fish[]` thêm `age_ticks` (mặc định 0). `random_fish:false` tắt cá mặc định, bơi và sinh (cá fixture đứng yên). Khai `fish` khi cờ bật thì thay đàn ban đầu, vẫn bơi/sinh.
- `gather.monsters[]` thay danh sách mặc định (`{id,kind,pos,waypoints,target_idx,state,state_ticks_left,recoil_dir}`); `gather.player.invuln_ticks`.
- Khối `day {money,earned,reputation,upgrades,day_plan}` (lát C, `chonoi/scenario.py`): chạy `--mode day` nhận `gather` và `quan` làm mẫu khởi tạo mỗi Ngày; **cấm** `quan.stock`, `quan.reputation`. `0 ≤ money ≤ earned`; mặc định tiền/earned 0, uy tín theo tuning, `upgrades {}`. `day.day_plan` ghi đè theo số Ngày (**[giả định]** dạng `{"<ngày>": {"dishes":{…}, "ingredients":{…}?}}`, xem `docs/clarify.md`), `ingredients` tính lại và so với giá trị khai nếu có, sai → mã 2.

### 6.7 Ranh giới file Phase 2

| Lát | Người | File sở hữu |
|---|---|---|
| C | HoangHongNgo | `game.contract.json`, `chonoi/contract.py`, `docs/contracts/`, `chonoi/sim/pause.py`, cờ `--mode day/--days` trong `headless.py`, `chonoi/scenario.py` (khối `day`), `docs/verification/phase-2.md` |
| A | haiquanng | `chonoi/sim/fish.py`, phần hái/catch trong `gather.py` |
| S | haiquanng | `chonoi/sim/shop.py`, `chonoi/sim/progress.py`, `tests/test_p2_shop.py`, `tests/test_p2_progress.py`, `docs/proof/phase-2/` |
| B | ChuTungDuongg | `chonoi/sim/monsters.py`, phần oxy/ngạt/faint trong `gather.py` |
| Q | minhphuong150505 | `chonoi/sim/quan.py`, `chonoi/scenario.py` (phần quán) |
| D | phuthaitran | `chonoi/sim/day.py`, phần gọi `DaySim` trong `headless.py` |
| U | RachalHys | `chonoi/web/`, `chonoi/live.py`, regression test P1 |

File chung (`gather.py`, `quan.py`) chỉ thêm **một dòng gọi hook** đúng vị trí theo thứ tự xử lý (ticket mục 4.5); xung đột còn lại Integrator xử lý khi gộp. Thứ tự gộp: **C → A → B → Q → S → D → U**.

### 6.8 Test P1 đã đổi vì số chuẩn v1.1

| Test | Lý do |
|---|---|
| `test_p1_lat3` `test_t05_no_table_skips_turn` | 4 bàn: hết bàn chỉ khi cả T1–T4 có khách |
| `fixtures/quan_one_customer.json` (dùng ở `test_p1_lat4` `TestFullLoopFixture`) | fixture là đúng một khách; thêm `random_customers:false` vì có bàn trống từ tick 120 |
| `test_smoke_p1` `test_gather_snapshot_has_gather_fields` | 6 đàn → `fish_initial` (8); **đang skip** tới khi lát A đặt đàn đầu ca theo seed (gỡ skip khi gộp lát A) |
