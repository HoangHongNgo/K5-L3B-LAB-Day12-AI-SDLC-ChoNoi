# TASK

> **Phase 3 (TICKET-03, 1:55–2:30)** ở [cuối file](#phase-3--mùa-nước-nổi-ticket-03-155230). Phase 2 ở [giữa file](#phase-2--một-ngày-ở-chợ-nổi-ticket-02-100155). Phase 1 giữ nguyên bên dưới để tra lại.

# Phase 1 (PRD-0, 0:00–1:00)

> Bảng việc chi tiết theo từng phase nhỏ. Kế hoạch tổng và AC: [`docs/plan/phase-1.md`](docs/plan/phase-1.md). Vai và người dự phòng: [`TEAM.md`](TEAM.md).
> Đánh dấu `[x]` khi xong. Mỗi người **≥ 3 commit có nội dung** trong cả buổi; mỗi phase nhỏ nên có ít nhất 1 commit.

| Phase nhỏ | Phút | Mục tiêu | Điểm chốt |
|---|---|---|---|
| **1.1** Kickoff | 0–15 | Chốt hợp đồng, chia ranh giới file, dựng khung lát | Hợp đồng kho + event trên `main` |
| **1.2** Lõi lát | 15–25 | Luật cốt lõi từng lát chạy được | **Phút 25: xuất file kho thật** từ gather, quán đọc được |
| **1.3** Hoàn thiện lát | 25–45 | Đủ luật mục F, test theo AC | Standup phút 40, mọi PR lát đã mở |
| **1.4** Tích hợp & kiểm chứng | 45–55 | Gộp, smoke hai tiến trình, chơi thử, ma trận truy vết | `main` xanh, `docs/verification/phase-1.md` đủ |
| **1.5** Bàn giao | 55–60 | Ghi chép, gắn tag | Tag `phase-1` trước 1:00 |

Quy ước chung: nhánh `p1/<lát>-<handle>`, chạy test trước khi mở PR, PR nhỏ, review chéo theo cặp (1↔2, 3↔4). Câu hỏi về luật → PO ghi `docs/clarify.md`.

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

---

## 1.1 Kickoff (phút 0–15)

### HoangHongNgo — PO + Integrator + Scrum/Release
- [x] Chốt `docs/contracts/README.md`: schema kho (mục G), danh sách event (tên, `data`, ai phát), giao diện sim↔UI (trường snapshot UI đọc, lệnh `move`/`interact`/`catch`).
- [x] Kiểm `docs/contracts/inventory.sample.json` hợp lệ (chạy `quan --inventory` với file này, mã 0).
- [x] Chốt ranh giới file: lát 1 sửa phần bơi/oxy trong `GatherSim.step`, lát 2 sửa phần interact/catch; lát 3 khách/lịch, lát 4 bếp/bàn trong `QuanSim`.
- [x] Mở `docs/clarify.md`, ghi 2–3 câu hỏi đầu tiên cho Anh Năm (ví dụ: chọn món "đều theo seed" dùng stream nào).
- [x] Commit: `contracts: chốt schema kho, event và giao diện sim-UI`.

### ChuTungDuongg — Lát 1
- [x] Đọc PRD-0 mục F "Gather" (đoạn 2) và `chonoi/sim/gather.py`.
- [x] Thống nhất với haiquanng một hàm chung `_add_to_hold(kinds) -> bool` (kiểm trần `hold_capacity`, thêm theo thứ tự nhặt) để hai lát không đụng nhau.
- [x] Tạo nhánh `p1/lat1-ChuTungDuongg`, dựng hàm trống `_update_oxygen(events, was_surface)`.

### haiquanng — Lát 2
- [x] Đọc PRD-0 mục F "Gather" (đoạn 3–5) và mục G.
- [x] Viết `_add_to_hold` (đã thống nhất với lát 1), commit sớm để lát 1 dùng chung.
- [x] Tạo nhánh `p1/lat2-haiquanng`.

### minhphuong150505 — Lát 3
- [ ] Đọc PRD-0 mục D (khối `quan`), mục F "Quán" (đoạn 4–5).
- [ ] Chốt với phuthaitran cấu trúc khách/đơn: các trường `id, table_id, dish_id, order_tick, state, patience_ticks_left, eat_ticks_left, order_status, reserved, base_price, tip`.
- [ ] Tạo nhánh `p1/lat3-minhphuong150505`.

### phuthaitran — Lát 4
- [x] Đọc PRD-0 mục F "Quán" (đoạn 1–3), event `cook_started`/`dish_ready`/`dish_picked`/`served`/`paid`/`quan_end`.
- [x] Viết 1 file scenario mẫu có sẵn khách `waiting` + kho để tự test lát 4 không cần chờ lát 3 (`tests/fixtures/quan_one_customer.json`).
- [x] Tạo nhánh `p1/lat4-phuthaitran`.

### RachalHys — QA lead + HUD
- [x] Lập khung `docs/verification/phase-1.md` với 12 dòng AC-P1-01..12 (cột cách kiểm chứng).
- [x] Đọc `chonoi/web/index.html` và `chonoi/live.py`, liệt kê trường HUD còn thiếu so với PRD-0 mục 2.
  - Rà bằng fixture trên trình duyệt. HUD sáng đã hiện thời gian, oxy, Máu và giỏ. HUD tối hiện tồn vật lý thay cho kho khả dụng và tên món trên bếp bị hiện thành `[object Object]`.
- [x] Tạo nhánh `p1/hud-RachalHys`.

---

## 1.2 Lõi lát (phút 15–25)

### ChuTungDuongg — Lát 1
- [x] Oxy theo `d` cuối bước: mặt nước (`d ≤ surface_depth`) +`oxygen_refill_per_tick`, kẹp max, reset `zero_oxy_ticks`; dưới nước −1, kẹp 0.
- [x] `dive` / `surface` khi đổi phía mặt nước (so đầu/cuối bước, `data.pos`).
- [x] `oxygen_empty` khi từ dương xuống 0.
- [x] Commit: `gather: oxy, dive/surface, oxygen_empty`.

### haiquanng — Lát 2
- [x] Hái: chỉ ở mặt nước, ngoài bến; nút `ready` gần nhất trong `interact_radius` (tính cả đúng mép, hòa theo id); đủ chỗ → `gather` + `regrow_ticks = regrow_s × 60`; thiếu chỗ → `hold_full` (`action`, `node_id`, `required`, `free`).
- [x] Chạy thử `--inventory-out` thật bằng smoke dock.json và đưa file cho lát 3/4 (**mốc phút 25**). — *haiquanng: trễ mốc; lát 3/4 đã tự dùng fixture. Smoke `dock.json` seed 42 chạy thật trong `docs/proof/phase-1/check_ac.py` (AC-P1-06), file kho ở `docs/proof/phase-1/catch.json`.*
- [x] Commit: `gather: hái nút, hold_full, regrow`.

### minhphuong150505 — Lát 3
- [x] Lịch khách theo `phase_tick`: `first_customer_tick`, rồi mỗi `customer_interval_s × 60`; bàn trống id nhỏ nhất; không có bàn → bỏ lượt.
- [x] Chọn món đều theo seed (qua `Streams`) trong món đủ kho khả dụng (tồn − giữ), duyệt id món theo Unicode; không đủ → `no_dish`.
- [x] Giữ đúng công thức vào `reserved`, `customer_arrived`.
- [x] Commit: `quan: lịch khách, chọn món, giữ chỗ`.

### phuthaitran — Lát 4
- [x] Chọn tối đa một interact theo (khoảng cách, bếp trước bàn, id) trong `interact_radius`; đối tượng không tương tác được → bỏ lượt.
- [x] Bếp idle lấy đơn `reserved` cũ nhất (order_tick, id bàn), tiêu nguyên liệu giữ, chốt giá → `cook_started` (`items` sắp theo kind, `base_price`); đếm `cook_ticks_left` → `dish_ready`.
- [x] Commit: `quan: chọn interact, nấu, dish_ready`.

### RachalHys — HUD
- [x] HUD buổi sáng: thời gian còn lại, thanh oxy, Máu, giỏ (`hold_count/hold_capacity` + danh sách).
  - Đã đối chiếu HUD với snapshot live và chạy lại các ca tương ứng qua headless. Kiểm trên trình duyệt ở chiều rộng 320 và 1024 px.
- [x] Commit: `ui: HUD buổi sáng`.

### HoangHongNgo
- [ ] Standup phút 20: ai vướng → điều người dự phòng vào pair.
- [x] Kiểm dải hợp lệ tuning trong `chonoi/contract.py` (mục A "Dải hợp lệ"), sai → mã 2.
- [x] Commit: `contract: kiểm dải hợp lệ tuning`.

---

## 1.3 Hoàn thiện lát (phút 25–45)

### ChuTungDuongg — Lát 1
- [x] Đếm ngạt: mỗi bước dưới nước kết thúc với oxy 0 tăng `zero_oxy_ticks`; đủ `choke_interval_ticks` → về 0, −1 Máu, `choke` (`hp`). Nổi lên đúng bước đáng lẽ ngạt thì không ngạt.
- [x] Máu 0 → bỏ giỏ LIFO, `faint` (`cause:"choke"`, `lost`, `hp:0`) → `gather_end` `fainted`, kho rỗng, dừng bước.
- [x] Test `tests/test_p1_lat1.py`: choke ở t+59 (AC-P1-02), faint ghi kho `{"items":{}}` (AC-P1-03).
- [x] Mở PR, nhờ haiquanng review.

### haiquanng — Lát 2
- [x] Bắt cá: cạnh `catch`, `catch_cd_ticks == 0`, dưới nước; đàn gần nhất trong `catch_radius` (hòa theo id); đủ chỗ → thêm đủ `fish_yield`, xóa đàn, `fish_caught`, cooldown `catch_cooldown_s × 60`; thiếu chỗ → `hold_full`, giữ đàn, không đặt cooldown.
- [x] Kiểm bước cuối: E đúng mép bến → `docked`; hái/bắt hợp lệ ở bước cuối vẫn vào kho; chạm `--ticks` trước khi xong thì không ghi kho.
- [x] Test `tests/test_p1_lat2.py`: AC-P1-04, AC-P1-05, AC-P1-06.
- [x] Mở PR, nhờ ChuTungDuongg review.

### minhphuong150505 — Lát 3
- [ ] Kiên nhẫn giảm từ bước sau khi đến; còn giờ mà về 0 → `customer_left` `patience`, uy tín + `left_reputation_delta` (kẹp), nhả giữ chỗ, bỏ món của đơn.
- [ ] Khách fixture: suy `reserved` khi thiếu (theo order_tick rồi id bàn); kiểm mâu thuẫn trong `chonoi/scenario.py` (khách trùng bàn, giữ quá tồn/khác công thức, bếp và tay giữ cùng đơn...) → mã 2.
- [ ] Test `tests/test_p1_lat3.py`: AC-P1-07, AC-P1-08.
- [ ] Mở PR, nhờ phuthaitran review.

### phuthaitran — Lát 4
- [x] Bếp ready → tay trống (`carry_limit` 1) → `dish_picked`, bếp về idle; `ready_ticks` chỉ tăng cho món đã ready đầu bước.
- [x] Bàn nhận đúng `order_id` → `served`, ăn `eat_s × 60`; boa `floor(giá × tip_rate)` nếu tỷ lệ kiên nhẫn ≥ `tip_min_patience_ratio`; ăn xong → `paid` (`finished_eating`), boa dương + `tip_reputation`.
- [x] Hết ca: khách đang ăn trả `closing`, khách chờ rời `closing` không trừ uy tín, rồi `quan_end`. Điểm = `earned + 100 × floor(reputation)`.
- [x] Test `tests/test_p1_lat4.py`: AC-P1-09, AC-P1-10.
- [x] Mở PR, nhờ minhphuong150505 review.

### RachalHys — HUD + QA
- [x] HUD buổi tối: kho khả dụng, món gọi + kiên nhẫn từng khách, trạng thái bếp, món trên tay, tiền, uy tín.
- [x] README: chạy từ clone sạch ≤ 3 lệnh (macOS/Linux), điều khiển, cách tính điểm, lệnh test 1 dòng (AC-P1-12).
- [x] Review test của 4 lát, bổ sung ca cập bến đúng mép bán kính ở bước cuối và ca `tick_limit` giữ nguyên file kho có sẵn.
  - Kiểm Chromium 320 và 1024 px với bản ghép thử lát 4. Bộ test pass 110/110 trên nhánh HUD và 136/136 trên bản ghép thử.
- [x] Commit: `ui: HUD buổi tối`, `docs: README cách chạy và điều khiển`.

### HoangHongNgo
- [ ] Standup phút 40; lát nào chậm → người đã xong vào hỗ trợ.
- [ ] Review và gộp PR theo thứ tự: lát 2 (hàm giỏ) → lát 1 → lát 3 → lát 4 → HUD; xử lý xung đột ở `gather.py`/`quan.py`.

---

## 1.4 Tích hợp & kiểm chứng (phút 45–55)

### HoangHongNgo
- [x] Trên `main` sạch: chạy toàn bộ test + smoke hai tiến trình (dock.json, seed 42) → quán tick 0 có `stock:{"bong_sung":2,"ca_loc":1}`.
- [x] Chạy hai lần cùng seed, so `cmp` để kiểm giống từng byte.

### RachalHys
- [x] Lưu log test, `gather.jsonl`, `catch.json`, `quan.jsonl` và ảnh HUD trong `docs/proof/phase-1/`.
- [x] Điền ma trận 12 AC theo lần chạy trên `main` tại `a1c94cb`. Chạy lại khi có commit bàn giao chính thức.

### ChuTungDuongg + haiquanng
- [ ] Chơi thử `gather` trên `main`: lặn tới ngạt, hái, bắt cá, cập bến; ghi lỗi thấy được vào kênh nhóm, sửa nhanh nếu kịp.

### minhphuong150505 + phuthaitran
- [x] Chơi thử `quan` với kho vừa ghi (`--inventory kho.json`): đủ vòng nấu → bưng → phục vụ → trả tiền; để một khách hết kiên nhẫn; sửa nhanh nếu kịp. — bằng chứng: `docs/proof/phase-1/quan-playtest/`

---

## 1.5 Bàn giao (phút 55–60)

### Mọi người
- [ ] Ghi phần của mình vào `docs/ai-usage-log.md` (công cụ, việc dùng AI, token/chi phí nếu đo được). — xong: ChuTungDuongg, haiquanng, phuthaitran
- [ ] Tạo `docs/members/<handle>.md` theo `docs/members/TEMPLATE.md` (có thể hoàn thiện ở phase sau). — xong: ChuTungDuongg, haiquanng, phuthaitran

### HoangHongNgo
- [x] Cập nhật `docs/clarify.md`, `docs/standup.md`, ghi nhanh vào `docs/retro.md`.
- [ ] Gắn và đẩy tag trên commit bàn giao ở `main` **trước 1:00**:

```bash
git tag phase-1 && git push origin phase-1
```

---

## Theo dõi số commit (mục tiêu ≥ 3/người cả buổi)

| Handle | Commit dự kiến ở Phase 1 |
|---|---|
| HoangHongNgo | contracts · kiểm dải tuning · ghi chép + tag |
| ChuTungDuongg | oxy/dive/surface · ngạt/faint · test lát 1 |
| haiquanng | hàm giỏ + hái · bắt cá/cập bến · test lát 2 |
| minhphuong150505 | lịch khách/giữ chỗ · kiên nhẫn/scenario · test lát 3 |
| phuthaitran | interact/nấu · bưng/phục vụ/tiền · test lát 4 |
| RachalHys | HUD sáng · HUD tối · README + verification/proof |

---
---

# Phase 2 — Một ngày ở chợ nổi (TICKET-02, 1:00–1:55)

> Test Contract **v1.1**. Hạn đẩy tag `phase-2`: **1:55**. Nguyên văn ticket nên lưu ở `docs/plan/phase-2.md` (PO làm ở 2.1).
> Đánh dấu `[x]` khi xong. Mỗi người **≥ 1 commit có nội dung mỗi phase nhỏ**.

## Nguyên tắc chia việc: làm song song, không chờ nhau

1. **Mỗi lát sở hữu file riêng** (bảng dưới). File chung (`gather.py`, `quan.py`) chỉ thêm **một dòng gọi hook** vào đúng vị trí trong thứ tự xử lý mục 4.5, nên xung đột còn lại rất nhỏ và Integrator xử lý khi gộp.
2. **Khóa contract v1.1 lấy thẳng từ ticket mục 4.1**, không cần chờ PO commit `game.contract.json`: ai cần số thì đọc qua `tuning[...]` theo đúng tên khóa trong ticket; trong lúc chờ, test tự dựng tuning bằng fixture.
3. **Mỗi lát tự có fixture** trong `tests/fixtures/p2_<lát>_*.json` (scenario có `random_fish:false`, `monsters` cố định, `hold` dựng sẵn…) để test không phụ thuộc lát khác.
4. **Giao diện chốt sẵn (không đổi trong phase nếu chưa báo cả nhóm):**
   - `GatherSim(tuning, scenario, streams, *, day=1, active_upgrades={})`: khi kết thúc phát `gather_end` với `data.inventory` (schema kho v1.0).
   - `QuanSim(tuning, scenario, streams, *, inventory, menu_ids=None, money=0, earned=0, reputation=None)`: `menu_ids=None` là cả 6 món (quán chạy riêng); khác `None` thì lọc theo kế hoạch ngày.
   - Cả hai sim có `step(inputs) -> events`, `snapshot() -> dict`, thuộc tính `done`, `result` (dict trạng thái cuối: tiền, earned, uy tín, kho dư…).
   - `pause` xử lý ở **lớp bọc chung** (`chonoi/sim/pause.py`), không nằm trong từng sim.
   - `ShopSim(tuning, *, money, earned, upgrades, stock)`: cùng giao diện `step/snapshot/done/result`; `result` trả `money`, `upgrades` (cấp đã mua). Lát D gọi Shop như một pha, không tự viết luật mua.
   - `DaySim(tuning, scenario, streams, *, days=1)`: cùng giao diện `step/snapshot/done/result`; `headless.py` chỉ dựng và chạy nó như hai mode kia, nên cờ CLI viết được trước khi `day.py` xong.
   - `DayState` trong `chonoi/sim/progress.py` (hàm thuần, không giữ sim): `money, earned, reputation, upgrades, active_upgrades, day`; `apply_quan_result(result)`, `apply_shop_result(result)`, `start_next_day() -> {"oxygen_max_ticks", "hp_max"}`. Lát D chỉ gọi các hàm này, không tự tính trạng thái xuyên Ngày.

| Lát | Người | File sở hữu | Người review |
|---|---|---|---|
| C — Contract v1.1 + pause + CLI/scenario day + kiểm chứng | HoangHongNgo | `game.contract.json`, `chonoi/contract.py`, `docs/contracts/`, `chonoi/sim/pause.py`, CLI `--mode day/--days` trong `headless.py`, `chonoi/scenario.py` (khối `day`), `docs/verification/phase-2.md` | RachalHys |
| A — Cá bơi/sinh + nút/catch | haiquanng | `chonoi/sim/fish.py` (mới), phần hái/catch trong `gather.py` | ChuTungDuongg |
| S — Shop, nâng cấp, trạng thái xuyên Ngày + proof | haiquanng | `chonoi/sim/shop.py`, `chonoi/sim/progress.py` (mới), `tests/test_p2_shop.py`, `tests/test_p2_progress.py`, `docs/proof/phase-2/` | phuthaitran |
| B — Cá Sấu, Máu, ngất | ChuTungDuongg | `chonoi/sim/monsters.py` (mới), phần oxy/ngạt/faint trong `gather.py` | haiquanng |
| Q — 2 bếp/4 bàn, 6 món, lọc kế hoạch | minhphuong150505 | `chonoi/sim/quan.py`, `chonoi/scenario.py` (phần quan) | phuthaitran |
| D — Vòng ngày | phuthaitran | `chonoi/sim/day.py` (mới), phần gọi `DaySim` trong `headless.py` | minhphuong150505 |
| U — Menu, pause UI, HUD | RachalHys | `chonoi/web/`, `chonoi/live.py`, regression test P1 | HoangHongNgo |

Quy ước: nhánh `p2/<lát>-<handle>`, test xanh trước khi mở PR. Thứ tự gộp: **C → A → B → Q → S → D → U**. Test P1 nào phải đổi vì số chuẩn mới thì ghi lý do trong commit.

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

| Phase nhỏ | Phút | Mục tiêu | Điểm chốt |
|---|---|---|---|
| **2.1** Số chuẩn & lõi lát | 0–20 (1:00–1:20) | Contract v1.1, lõi từng lát chạy được trên fixture riêng | **Phút 20: smoke** `gather --inventory-out → quan --inventory` với số chuẩn, lưu `docs/proof/phase-2/integration.*` |
| **2.2** Hoàn thiện & nối vòng ngày | 20–35 (1:20–1:35) | Đủ luật từng lát, `--mode day` chạy với 2 sim thật | Mọi PR lát đã mở trước phút 35 |
| **2.3** Kiểm chứng & bàn giao | 35–55 (1:35–1:55) | Gộp, smoke day, regression, verification, retro, tag | Tag `phase-2` trước **1:55** |

---

## 2.1 Số chuẩn & lõi lát (phút 0–20)

### HoangHongNgo — Lát C (contract v1.1)
- [x] Phút 0–5: lưu ticket vào `docs/plan/phase-2.md`, báo bảng giao diện chốt sẵn ở trên cho cả nhóm. — xong: `docs/plan/phase-2.md` (ticket nguyên văn + phụ lục AC-P2-01..19 + giao diện chốt sẵn); bảng giao diện chốt sẵn cũng có ở `docs/contracts/README.md` mục 6.4. Chưa báo kênh nhóm.
- [x] `game.contract.json`: `contract_version:"1.1"`, toàn bộ số chuẩn mục 1.1–1.3, 6 nguyên liệu, 6 món, `day_plan` D1–D5, `shop.upgrades.oxygen/hp`, `gather.monsters`, khóa cá mới (mục 4.1). — xong, nhánh `p2/c-HoangHongNgo`.
- [x] `chonoi/contract.py`: kiểm khóa mới và dải hợp lệ; `day_plan.ingredients` phải bằng tổng công thức × số suất, sai thì mã 2. — xong; thêm `resolve_day_plan` dùng chung cho `scenario.py`/lát D. Test: `tests/test_p2_contract.py`.
- [x] Cập nhật `docs/contracts/README.md`: event mới (`monster_hit`, `fish_spawned`, `day_start`, `phase_start`, `day_plan`, `paused`, `resumed`, `bought`, `buy_failed`, `shop_end`), trường snapshot mới, vỏ event có `day`. — xong (mục 6).
- [x] Commit: `contract: v1.1 số chuẩn, day_plan, shop, monsters`.
- [x] Khung `docs/verification/phase-2.md`: liệt kê AC-P2-xx theo `docs/plan/phase-2.md`, cột cách kiểm chứng / bằng chứng / kết quả; ghi sẵn lệnh kiểm cho từng AC để các lát biết test nào cần viết.
- [x] Commit: `docs: khung verification Phase 2`.
- [ ] Rà test P1 nào sẽ vỡ vì số chuẩn mới, gửi danh sách cho các lát (nhận từ RachalHys). — một phần: HoangHongNgo đã tự rà bằng cách chạy toàn bộ test (danh sách ở `docs/contracts/README.md` mục 6.8; test quán/gather còn lại sẽ vỡ khi lát A/Q gộp). Chưa nhận danh sách từ RachalHys, chưa gửi kênh nhóm.
- [x] `headless.py`: thêm cờ `--mode day`, `--days 1..5` (mặc định 1, chỉ hợp lệ với `day`), sai thì mã 2; gọi `DaySim` của lát D (nhận từ phuthaitran). — xong: cờ và kiểm mã 2 chạy được; `DaySim` import trễ từ `chonoi/sim/day.py`, chưa có thì mã 1 "chưa hỗ trợ" (chờ lát D).
- [x] Commit: `headless: cờ --mode day, --days`.

### haiquanng — Lát A (cá & hái)
- [x] `chonoi/sim/fish.py`: đàn cá bơi 1.5 m/s trong `fish_x`, dải độ sâu theo loài; đổi hướng theo seed ở bước bơi thứ 120, 240… (theo `age_ticks`); phản xạ mép (chạm góc đảo cả hai thành phần).
- [x] Đầu ca 8 đàn ở 8 điểm khác nhau (36 cặp loài–vị trí); `fish_yield` linh 3, lóc 1, kèo 2.
- [x] Thêm nút N5/N6 (kèo nèo); catch dùng **vị trí cá trước khi bơi**. — *N5/N6 có trong fixture `p2_fish_tuning.json`, scenario nhận `keo_neo`/`ca_keo`; contract v1.1 (PO) cần thêm N5/N6 vào `gather.nodes`*
- [x] Fixture `tests/fixtures/p2_fish_*.json` (`random_fish:false`).
- [x] Commit: `gather: cá bơi, phản xạ mép, đàn ban đầu`. — *commit 7bbb51f, nhánh `p2/A-haiquanng`*

### haiquanng — Lát S (Shop, khung)
- [x] `chonoi/sim/shop.py` theo giao diện `ShopSim` chốt sẵn: đọc `shop.upgrades.oxygen/hp` và `shop.max_ticks` từ contract (không hard-code giá/cấp); snapshot có `stock` dư và `time_left_ticks`.
- [x] Commit: `shop: khung ShopSim, đọc nâng cấp từ contract`. — *commit 7bdcfeb, nhánh `p2/S-haiquanng`*

### ChuTungDuongg — Lát B (Cá Sấu & Máu)
- [x] Oxy số chuẩn: cơ sở 1.800 tick, +6/tick ở mặt nước; ngạt mất 1 Máu mỗi 60 tick **tính cả bước vừa chạm 0**, reset khi oxy > 0 hoặc lên mặt nước; ngạt xuyên bất tử, không làm rơi hàng.
- [x] Máu cơ sở 3 (lấy `hp_max` theo `active_upgrades` nếu có).
- [x] `chonoi/sim/monsters.py`: M1 (Ngày 1) và M2 (`from_day:3`); trạng thái `patrol` 1.0 m/s ↔ `chase` 3.0 m/s (phát hiện khi người chơi d ≥ 10 và cách ≤ 10 m; rời khi > 16 m hoặc d < 10); chặn theo biên và `depths` của loài.
- [x] Fixture `tests/fixtures/p2_monster_*.json` (`monsters[]` cố định).
- [x] Commit: `gather: oxy/ngạt số chuẩn, Cá Sấu patrol/chase`.

### minhphuong150505 — Lát Q (quán)
- [x] Quán đọc bếp B1/B2, bàn T1–T4, 6 món từ contract (không hard-code); **cả 2 bếp** idle lấy đơn `reserved` cũ nhất (order_tick, id bàn), duyệt bếp theo id.
- [x] Lịch khách `120 + 900·k`, kiên nhẫn 3.600, ăn 600, boa `floor(giá×0.2)` khi còn ≥ 50% kiên nhẫn.
- [x] Thêm tham số `menu_ids` (lọc theo id món kế hoạch **trước** khi lọc nguyên liệu khả dụng); `None` là cả 6 món.
- [x] Fixture `tests/fixtures/p2_quan_*.json` (4 bàn, 2 bếp, kho dựng sẵn).
- [x] Commit: `quan: 2 bếp 4 bàn, 6 món, lọc theo kế hoạch`.

### phuthaitran — Lát D (vòng ngày)
- [x] `chonoi/sim/day.py`: máy pha `gather → quan → shop → (Ngày kế | end)`; event `day_start → day_plan → phase_start(gather)`; sau `gather_end` dựng quán và phát `phase_start(quan)` cùng tick; pha mới chạy gameplay từ bước sau.
- [x] Làm với **sim giả (stub)** cùng giao diện chốt sẵn (`step/snapshot/done/result`) cho gather, quan và shop để không phải chờ lát A/B/Q/S.
- [x] Output day: vỏ event có `day`, dòng `end` có `days_completed`, `reason:"days_complete"` (cờ CLI do HoangHongNgo làm).
- [x] Commit: `day: máy pha gather→quan→shop, --mode day`.

### RachalHys — Lát U (UI)
- [x] Menu chính, DayIntro và EveningIntro. Playwright kiểm trên Chromium với snapshot giả ở 320 px và 1280×720, gồm bỏ qua DayIntro bằng phím, tự chuyển sau 4 giây và lọc món EveningIntro theo kho/kế hoạch.
- [x] Commit: `ui: menu chính, DayIntro, EveningIntro`.

### Phút 20 — Smoke tích hợp (HoangHongNgo dẫn, cả nhóm)
- [x] Trên nhánh tích hợp tạm: `gather --inventory-out kho.json` → `quan --inventory kho.json`, đối chiếu snapshot kho ở tick 0, lưu `docs/proof/phase-2/integration.*`. — chạy trên nhánh C (chưa có lát A/B/Q/S/D): `docs/proof/phase-2/integration.md`; cần chạy lại trên `main` sau khi gộp.
- [ ] Standup 2–3 phút; lát chậm thì người dự phòng (TEAM.md) vào pair.

---

## 2.2 Hoàn thiện & nối vòng ngày (phút 20–35)

### HoangHongNgo — Lát C (pause) + gộp
- [x] `chonoi/sim/pause.py`: bọc sim bất kỳ; xét cạnh `pause` trước; khi đang pause chỉ tăng tick ngoài, phát `paused`, bỏ qua cạnh hành động và `buy`; cạnh kế tiếp phát `resumed` và chạy gameplay ngay bước đó. Snapshot `state:"paused"`. Giữ nút qua đổi pha không tạo cạnh mới.
- [x] Test `tests/test_p2_pause.py` cho cả 3 mode (dùng fixture có sẵn). — mode day kiểm bằng sim giả; thêm ca day thật khi lát D gộp.
- [x] `scenario.py` khối `day` (nhận từ minhphuong150505): cấm `quan.stock`/`quan.reputation` khi chạy day; `day {money,earned,reputation,upgrades,day_plan}` với `0 ≤ money ≤ earned`; `day.day_plan` ghi đè theo Ngày, tính lại `ingredients` và so với giá trị khai nếu có, sai thì mã 2. Test `tests/test_p2_scenario_day.py`. — xong: `tests/test_p2_scenario_day.py`; `load_scenario(.., "day", ..)` trả `{gather, quan, day}` đã điền mặc định.
- [ ] Gộp PR lát A, B khi xanh.
- [x] Commit: `sim: pause cho gather/quan/day`.

### haiquanng — Lát A
- [x] Sinh cá tại `phase_tick = 360·k` **sau khi cá bơi**: dưới trần 12, điểm cách mọi đàn đang sống > 1 m, trọng số 40/30/30 chuẩn hóa theo loài còn điểm, chọn đều một điểm, hướng theo seed; cá mới bơi từ bước sau; phát `fish_spawned`.
- [x] Scenario: `fish[].age_ticks`; `random_fish:false` thì cá fixture đứng yên, không sinh.
- [x] Test `tests/test_p2_fish.py`: phản xạ mép/góc, đổi hướng ở bước 120, sinh đúng tick, bỏ lượt khi hết điểm, catch theo vị trí trước khi bơi.
- [ ] Mở PR lát A, nhờ ChuTungDuongg review.

### haiquanng — Lát S (Shop, luật)
- [x] `buy` (`oxygen`, `hp`) mua cấp kế tiếp, đủ đúng giá vẫn mua, trừ `money` giữ `earned`, phát `bought` (`upgrade,level,price,money`); thiếu tiền/đã tối đa/lệnh lạ thì `buy_failed` (`funds`/`max_level`/`unknown`), tiền và cấp giữ nguyên.
- [x] Đóng bằng `shop_done` → `shop_end(done)`, hoặc sau 600 tick hoạt động → `shop_end(time)`; buy xử lý trước `shop_done` trong cùng bước, kể cả bước cuối.
- [x] Test `tests/test_p2_shop.py`: đúng giá vẫn mua, mua 2 cấp liên tiếp, `max_level`, `funds`, lệnh lạ, buy + shop_done cùng bước, tự đóng ở tick 600.
- [x] `chonoi/sim/progress.py` (`DayState`, nhận từ phuthaitran): tiền/earned/uy tín/cấp giữ qua Ngày; `start_next_day` sao `upgrades → active_upgrades` (chỉ lúc dựng Ngày mới) và trả oxy/Máu tối đa theo cấp có hiệu lực; khởi tạo từ khối `day` của scenario (mặc định tiền/earned 0, uy tín theo tuning, cấp `{}`).
- [x] Test `tests/test_p2_progress.py`: mua oxygen cấp 1 ở Ngày 1 thì Ngày 2 có 2.700 tick, mua hp cấp 2 thì 5 Máu, cấp vừa mua chưa có hiệu lực trong cùng Ngày, uy tín kẹp [0,5].
- [ ] Mở PR lát S, nhờ phuthaitran review (người sẽ nối Shop và `DayState` vào day).

### ChuTungDuongg — Lát B
- [x] Hit sau khi cả hai di chuyển: ≤ 1.5 m, d ≥ 10, hết bất tử thì −1 Máu, bỏ `floor(n/2)` hàng theo LIFO, bất tử 90 tick, `monster_hit`; tối đa 1 hit/bước, chọn con gần nhất, hòa theo id.
- [x] Recoil 60 bước từ bước sau, lùi 2/60 m/bước theo hướng chốt lúc chạm (trùng tâm dùng +x), không gây hit; hết recoil về patrol.
- [x] Máu 0 → `faint` (`cause:"monster"` hoặc `"choke"`, `lost`, `hp:0`) → `gather_end(fainted)` ngay, kho rỗng. Cùng tick: ngạt → hit → hết giờ; cập bến được ưu tiên nếu còn Máu.
- [x] Scenario: `gather.monsters[]` (`target_idx`, `state`, `state_ticks_left`, `recoil_dir`), `player.invuln_ticks`; snapshot thêm `monsters[]`, `player.invuln_ticks`.
- [x] Test `tests/test_p2_monster.py`.
- [x] Mở PR, nhờ haiquanng review.

### minhphuong150505 — Lát Q
- [x] `scenario.py` cho `--mode day`: cấm `quan.stock`/`quan.reputation`; khối `day {money,earned,reputation,upgrades,day_plan}` với `0 ≤ money ≤ earned`; `day.day_plan` ghi đè theo Ngày, tính lại `ingredients` và so với giá trị khai nếu có, sai thì mã 2.
- [x] Hàm `validate_quan_against_inventory` để lát D gọi lúc mở quán: kiểm kho/khách/bếp/món thuộc kế hoạch trên kho thực.
- [x] Đóng ca số chuẩn: khách đang ăn trả ngay, khách chờ rời không trừ uy tín, dọn món và phần giữ.
- [x] Test `tests/test_p2_quan.py`: 2 bếp nấu song song, lọc kế hoạch, `no_dish`, khách vẫn gọi tiếp món đủ hàng khi đã bán đủ suất.
- [ ] Mở PR, nhờ phuthaitran review.

### phuthaitran — Lát D
- [x] Day: giỏ mới, kho dư bỏ sau Shop; Ngày hoàn tất khi Shop đóng (kể cả Ngày cuối). Trạng thái xuyên Ngày lấy từ `DayState` của haiquanng.
- [ ] Thay stub bằng `GatherSim`/`QuanSim`/`ShopSim`/`DayState` thật khi lát A/B/Q/S đã gộp (bàn giao kho trong bộ nhớ; ngất vẫn mở quán với kho rỗng). — GatherSim/QuanSim thật đã nối (mặc định); còn chờ ShopSim/DayState của lát S.
- [x] Snapshot mọi pha có `day`, `day_plan`, `upgrades`, `active_upgrades`.
- [x] Test `tests/test_p2_day.py`: thứ tự event đổi pha, `days_complete`.
- [ ] Mở PR, nhờ minhphuong150505 review.

### RachalHys — Lát U
- [x] HUD sáng và quán theo TICKET-02, gồm cảnh báo, kế hoạch ngày, tiến độ bếp và kiên nhẫn từng bàn. Chromium kiểm font 18 px ở 1280×720, ngưỡng cảnh báo và phép trừ phần giữ chỗ.
- [x] Menu pause, DayResult, Shop UI, Summary. Kiểm giao diện qua snapshot giả, gồm phím Esc/P, mua đủ hoặc thiếu tiền và hiển thị cấp mới. Cần kiểm pause với lớp bọc thật ở lát C.
- [x] Commit: `ui: HUD v1.1, pause, Shop, DayResult, Summary`.

### Phút 35 — Standup
- [ ] Mọi PR lát đã mở; lát nào trễ thì người đã xong vào pair.

---

## 2.3 Kiểm chứng & bàn giao (phút 35–55)

### HoangHongNgo
- [ ] Gộp nốt Q → S → D → U, xử lý xung đột ở `gather.py`/`quan.py`/`headless.py`.
- [ ] Trên `main` sạch: toàn bộ test xanh; chạy `--mode day --days 1` và `--days 3` (cấp nâng cấp có hiệu lực từ Ngày kế, M2 xuất hiện ở Ngày 3); chạy 2 lần cùng seed, `cmp` giống từng byte; đo headless 1 Ngày ≤ 20 s.
- [ ] Điền `docs/verification/phase-2.md`: AC → cách kiểm → bằng chứng → đạt/chưa đạt (ghi trung thực), khớp commit gắn tag.
- [ ] Cập nhật `docs/clarify.md`, `docs/standup.md`; dẫn retro (phút 45–50) vào `docs/retro.md` (điều tốt / điều vướng / 1 hành động có người nhận).
- [ ] Gắn tag trên commit bàn giao ở `main` **trước 1:55**:

```bash
git tag phase-2 && git push origin phase-2
```

### RachalHys
- [x] Chạy regression P1 với fixture số chuẩn v1.1 trên bản ghép thử. Giữ test kiểm đủ bàn theo danh sách thực, tắt cá/khách ngẫu nhiên trong fixture cần vị trí hoặc đơn cố định.
- [x] Chụp HUD/menu/pause và đo FPS ở 1280×720. Ảnh và giới hạn kiểm chứng ở [proof lát U](docs/proof/phase-2/ui/README.md), để haiquanng nối vào proof chung.
- [ ] Kiểm pause thật trong Shop và chạy lại regression trên manifest v1.1 chính thức sau khi lát C được gộp.

### haiquanng — Proof
- [ ] Viết bằng chứng vào `docs/proof/phase-2/`: log test đầy đủ, `integration.*` (từ smoke phút 20), `day.jsonl` (`--days 1` và `--days 3`), kết quả `cmp` hai lần cùng seed, thời gian headless 1 Ngày, ảnh HUD/FPS của RachalHys. Mỗi file ghi commit đã chạy. — *haiquanng: script `docs/proof/phase-2/run_proof.py` đã có (nhánh `p2/proof-haiquanng`); chạy lại trên commit gắn tag khi có contract v1.1 và cờ `--days`*
- [ ] Gửi danh sách file cho HoangHongNgo để nối vào `docs/verification/phase-2.md`.
- [ ] Commit: `docs: proof Phase 2`.

### haiquanng + ChuTungDuongg
- [ ] Chơi thử `gather` số chuẩn: cá bơi/sinh, bị Cá Sấu đuổi và chạm, ngất, cập bến; sửa nhanh lỗi thấy được.
- [ ] (Mở rộng, chỉ khi lõi đã xanh) ChuTungDuongg làm **snake** (dùng lại luật chạm/recoil); haiquanng làm **net** (mở rộng catch, mua trong Shop). Khai `extensions` và ghi README. — *haiquanng: `net` xong ở nhánh `p2/net-haiquanng` (`tests/test_p2_net.py`, README mục "Mở rộng đã làm"); PO cần khai `extensions` + `shop.upgrades.net` trong contract v1.1*

### minhphuong150505 + phuthaitran
- [ ] Chơi thử `day` trọn 1 Ngày: DayIntro → gather → EveningIntro → quan → DayResult → Shop (mua oxygen) → Ngày 2.
- [ ] (Mở rộng, chỉ khi lõi đã xanh) minhphuong150505 làm **burn**; khai `extensions` và ghi README.

> Nhóm 6 người cần **≥ 2 mục mở rộng** trong cả buổi lab. Chỉ làm sau khi lõi Phase 2 đã gộp và xanh.

### Mọi người
- [ ] Ghi phần của mình vào `docs/ai-usage-log.md`; cập nhật `docs/members/<handle>.md`. — xong: ChuTungDuongg

---

## Theo dõi commit Phase 2 (mục tiêu ≥ 1 commit/người mỗi phase nhỏ)

| Handle | 2.1 | 2.2 | 2.3 |
|---|---|---|---|
| HoangHongNgo | contract v1.1 · khung verification · cờ `--mode day` | pause + test · scenario day + test | verification, ghi chép, retro, tag |
| haiquanng | cá bơi, đàn ban đầu · khung Shop | sinh cá + test · luật Shop + `DayState` + test | proof · sửa lỗi chơi thử · mở rộng net |
| ChuTungDuongg | oxy/ngạt số chuẩn, Cá Sấu patrol/chase | hit/recoil/ngất + test | sửa lỗi chơi thử · mở rộng snake |
| minhphuong150505 | 2 bếp 4 bàn, 6 món | kiểm kho lúc mở quán, đóng ca + test | sửa lỗi chơi thử · mở rộng burn |
| phuthaitran | máy pha day + output day | nối sim thật + test day | sửa lỗi chơi thử day |
| RachalHys | menu, intro | HUD v1.1, pause UI, Shop UI | regression P1, ảnh HUD/FPS |

---
---

# Phase 3 — Mùa Nước Nổi (TICKET-03, 1:55–2:30)

> Test Contract **v1.2**. Hạn đẩy tag `phase-3`: **2:30** (35 phút). Nguyên văn ticket: [`TICKET3.md`](TICKET3.md), nên chép sang `docs/plan/phase-3.md`.
> Lõi: **kho đếm → kho cá thể `{id,kind,fresh}`** + độ tươi/ươn/giá theo tươi. Mở rộng: `current`, `reservations`.
> Phase này ngắn, **haiquanng nhận nhiều việc nhất** (đổi schema kho + gather + dòng lũ + proof), người khác nhận lát gọn hơn và hỗ trợ haiquanng khi xong sớm.

## Nguyên tắc: schema trước, làm song song sau

1. **Chốt schema cá thể ở 0–7 phút** (haiquanng + HoangHongNgo): `items:[{id,kind,fresh}]`, id `I1,I2,…` cấp theo thứ tự vào giỏ và tăng xuyên pha/Ngày (dùng `IdAllocator`). Hàm đọc/ghi kho nằm ở `chonoi/inventory.py`; các lát khác chỉ gọi hàm, không tự parse file.
2. **Chuyển đổi an toàn**: adapter hỗ trợ cả v1.1 (đếm) lẫn v1.2 (cá thể) trong lúc chuyển; chỉ bật v1.2 (kho đếm → mã 2) khi gather và quán đều sẵn sàng (bước 3.2).
3. **Độ tươi dùng số nguyên**: 240 đơn vị/điểm tươi, gather −2/tick, quán −1/tick; so ngưỡng 30 trước khi làm tròn. Cả nhóm dùng chung hằng này qua `tuning["freshness"]`, không hard-code.
4. **Fixture riêng** mỗi lát: `tests/fixtures/p3_<lát>_*.json`, kho dựng sẵn dạng cá thể.
5. Thứ tự gộp: **C → A (adapter + gather) → B → Q → D → R → U**. Test P1/P2 nào đổi vì luật mới thì ghi lý do trong commit và `CHANGELOG.md`.

### Bảng ảnh hưởng module

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Contract v1.2, scenario | `game.contract.json`, `chonoi/contract.py`, `chonoi/scenario.py` (`hold`/`stock` mảng, `reserved` là id, `reservations`, `current`), `docs/contracts/` | `test_p2_contract`, `test_p2_scenario_day`, `test_p1_lat3` (scenario) | HoangHongNgo |
| Adapter kho, giỏ, độ tươi gather, dòng lũ | `chonoi/inventory.py`, `chonoi/sim/gather.py`, `chonoi/sim/fish.py` | `test_p1_lat1/2`, `test_p2_fish`, `test_p2_net`, `test_smoke_p1` | **haiquanng** |
| Lặn: LIFO `lost`, ngất, thứ tự tick | `chonoi/sim/monsters.py`, phần oxy/faint trong `gather.py` | `test_p1_lat1`, `test_p2_monster` | ChuTungDuongg |
| Quán: giữ theo id, ươn, giá theo tươi | `chonoi/sim/quan.py`, `chonoi/scenario.py` (phần quan) | `test_p1_lat3/4`, `test_p2_quan`, `test_p3_quan` | minhphuong150505 |
| Day: bàn giao kho cá thể, đặt trước | `chonoi/sim/day.py`, `chonoi/sim/progress.py` | `test_p2_day`, `test_p2_progress` | phuthaitran |
| HUD | `chonoi/web/`, `chonoi/live.py` | `test_live`, regression P1–P2 | RachalHys |

| Lát | Người | File sở hữu | Người review |
|---|---|---|---|
| C — Contract v1.2, scenario, pause freeze, CHANGELOG, verification, tag | HoangHongNgo | `game.contract.json`, `chonoi/contract.py`, `chonoi/scenario.py` (khối `hold`/`stock`/`day`), `chonoi/sim/pause.py`, `docs/contracts/`, `CHANGELOG.md`, `docs/verification/phase-3.md` | RachalHys |
| A — Adapter kho + giỏ + độ tươi gather | haiquanng | `chonoi/inventory.py`, `chonoi/sim/gather.py` (hold/decay/spoiled/xuất kho), `chonoi/runner.py` | ChuTungDuongg |
| X — Dòng nước lũ `current` (mở rộng 1) | haiquanng | `chonoi/sim/gather.py` (hook dòng lũ), `tests/test_p3_current.py` | ChuTungDuongg |
| P — Proof + smoke kho + chơi thử | haiquanng | `docs/proof/phase-3/`, `tests/test_p3_handoff.py` | HoangHongNgo |
| B — Lặn: LIFO cá thể, ngất, thứ tự tick | ChuTungDuongg | `chonoi/sim/monsters.py`, phần oxy/faint trong `gather.py`, `tests/test_p3_gather_lifo.py` | haiquanng |
| Q — Quán: giữ theo id, ươn, giá theo tươi | minhphuong150505 | `chonoi/sim/quan.py`, `tests/test_p3_quan.py` | phuthaitran |
| D — Day: bàn giao + đặt trước (mở rộng 2) | phuthaitran | `chonoi/sim/day.py`, `chonoi/sim/progress.py`, `tests/test_p3_day.py`, `tests/test_p3_reservations.py` | minhphuong150505 |
| U — HUD tươi/ươn, đặt trước, cảnh báo lũ | RachalHys | `chonoi/web/`, `chonoi/live.py`, regression P1–P2 | HoangHongNgo |

Quy ước: nhánh `p3/<lát>-<handle>`, test xanh trước khi mở PR, `Co-authored-by:` khi cùng làm một commit.

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

| Phase nhỏ | Phút | Mục tiêu | Điểm chốt |
|---|---|---|---|
| **3.1** Phân tích & lõi lát | 0–25 (1:55–2:20) | Ghi tác động, chốt schema; schema/adapter, gather, quán, HUD chạy trên fixture riêng | **Phút 20: smoke bàn giao kho** `gather --inventory-out → quan --inventory`, đối chiếu id/kind/fresh |
| **3.2** Bật v1.2 & kiểm chứng | 25–32 (2:20–2:27) | Bật v1.2, smoke hai tiến trình + `day`, regression P1–P2, CHANGELOG, proof | `main` xanh, `verification/phase-3.md` đủ |
| **3.3** Dự phòng & tag | 32–35 (2:27–2:30) | Retro nhanh, sửa lỗi cuối, gắn tag | Tag `phase-3` trước **2:30** |

---

## 3.1 Phân tích & lõi lát (phút 0–25)

### Phút 0–7 — Phân tích tác động (cả nhóm, HoangHongNgo dẫn)
- [ ] Lưu ticket vào `docs/plan/phase-3.md`; điền bảng ảnh hưởng module ở trên vào `docs/clarify.md` (hoặc ADR), kèm quyết định đổi schema kho, cách chuyển (adapter hai phiên bản) và thứ tự gộp.
- [ ] Ghi câu hỏi mơ hồ cho PO vào `docs/clarify.md` (ví dụ: `reserved` của fixture cũ đổi sang id thế nào; tick `spoiled` khi nhiều cá thể cùng vượt ngưỡng).

### HoangHongNgo — Lát C
- [ ] `game.contract.json`: `contract_version:"1.2"`, khối `freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}`; mở rộng: `gather.current {interval_ticks:1800, duration_ticks:480, warning_ticks:120, min_depth:10, speed:1.5}`, `reservations {count:2, table_hold_s:30, price_multiplier:1.5, failed_reputation_delta:-1}`, khai `extensions`.
- [ ] `chonoi/contract.py`: kiểm khóa và dải hợp lệ `freshness`/`current`/`reservations`, sai → mã 2.
- [ ] `chonoi/scenario.py`: `gather.hold`, `quan.stock` là mảng cá thể; `customers[].reserved` là mảng id; id vật lý duy nhất, kind thuộc danh mục, `fresh ∈ [0,100]`; giữ chỗ trỏ tới cá thể chưa ươn, đủ công thức, không dùng chung; bỏ `reserved` thì cấp theo `order_tick`, id bàn, tươi nhất rồi id nhỏ; trong `day`, Ngày kế cấp id mới theo thứ tự mảng. Nhận `random_current`, `current_direction`, `quan.reservations[]`, `random_reservations`. Mâu thuẫn → mã 2.
- [ ] `chonoi/sim/pause.py`: pause dừng hao tươi (kiểm bằng test với hold có `fresh`).
- [ ] Cập nhật `docs/contracts/README.md`: schema kho v1.2, event `spoiled`, `current_*`, `reservation_*`, trường snapshot mới, `lost`/`cook_started.items` là mảng cá thể.
- [ ] Commit: `contract: v1.2 độ tươi, kho cá thể, current, reservations`.

### haiquanng — Lát A (adapter kho + gather tươi) · việc nặng nhất
- [ ] `chonoi/inventory.py`: đọc/ghi kho **cá thể** `{"items":[{id,kind,fresh}]}`; chọn schema theo `contract_version` (v1.2 trả mã 2 cho kho đếm, thiếu `items`, kind lạ, id trùng/rỗng, `fresh` ngoài [0,100]/không hữu hạn); giữ đường đọc v1.1 để chuyển dần.
- [ ] Ghi kho: file tạm cùng thư mục rồi thay thế nguyên tử; xuất theo id, đủ chính xác để giữ giá trị và nhánh ở ngưỡng 30; ngất ghi `{"items":[]}`; chạm `--ticks` trước `gather_end` thì không đụng file đích; `gather_end.data.inventory` theo cùng schema.
- [ ] `gather.py`: giỏ là danh sách cá thể (`IdAllocator` cấp `I1,I2,…` theo thứ tự vào giỏ, tăng xuyên pha/Ngày); hái/bắt cấp cá thể `fresh=100`, hao từ bước sau; `_add_to_hold` giữ kiểm trần `hold_capacity`.
- [ ] Hao tươi gather 0.5/s (2 đơn vị/tick trên thang 240), kẹp 0, ở **đầu bước** theo thứ tự tick của ticket; `spoiled` (`item_id,kind,location:"hold"`) đúng một lần khi đi từ ≥ 30 xuống < 30, nhiều cá thể thì theo id; ươn vẫn chiếm ô.
- [ ] Test `tests/test_p3_gather_fresh.py`: kịch bản ngưỡng của ticket (`fresh:30` → `spoiled` tick 1), hao 60 tick = −0.5, kẹp đáy 0, cấp id xuyên pha, file kho ghi/đọc lại giữ nhánh ngưỡng, kho đếm → mã 2.
- [ ] Mở PR (đầu tiên trong thứ tự gộp sau C), nhờ ChuTungDuongg review. Commit: `inventory: kho cá thể v1.2`, `gather: độ tươi, spoiled, giỏ cá thể`.

### haiquanng — Lát X (Dòng nước lũ `current`, mở rộng 1)
- [ ] Lịch `t = 1800·k` (k ≥ 1): `current_warning` (`starts_at_phase_tick`) ở `t−120`, bắt đầu trước di chuyển ở `t`, kéo dài 480 tick (`t…t+479`); hướng +x/−x chọn đều theo seed qua `Streams` khi bắt đầu.
- [ ] Cộng 1.5 m/s vào người chơi nếu d đầu bước ≥ 10, rồi chặn mép; không tích lũy vào `player.vel`; cá và thủy quái giữ chuyển động riêng.
- [ ] `current_end(elapsed)` ở `t+480` trước di chuyển; ca hết trước thì `current_end(phase_end)` trước `faint` và `gather_end`; bước bắt đầu trùng bước cuối ca vẫn có lực.
- [ ] `gather.random_current:false` tắt lịch, `current_direction:-1/1` khóa hướng; snapshot `current:null` hoặc `{direction,ticks_left}` (đếm cả tick vừa chụp).
- [ ] Test `tests/test_p3_current.py`: cảnh báo ở t−120, lực chỉ khi d ≥ 10, kết thúc `elapsed` và `phase_end`, hướng khóa, tắt lịch → kết quả lõi không đổi.
- [ ] Commit: `gather: dòng nước lũ current`.

### haiquanng — Lát P (smoke + proof, gộp ở 3.2) 
- [ ] Phút 20 dẫn smoke bàn giao: dùng scenario `{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":100}],"random_fish":false,"monsters":[]}}` với `interact:true` ở frame 0 để cập bến, rồi `quan --inventory kho.json --ticks 0`; so chính xác id, kind, fresh với file sau lần hao ở bước gather. Lưu `docs/proof/phase-3/integration.*`.

### ChuTungDuongg — Lát B (Lặn trên kho cá thể)
- [x] `lost` trong `monster_hit`/`faint` là mảng cá thể `{id,kind,fresh}` theo thứ tự bỏ LIFO (thứ tự vào giỏ); `floor(n/2)` vẫn như cũ.
- [x] Ngất: bỏ toàn bộ phần còn lại theo LIFO, `faint` → `gather_end(fainted)`, kho `{"items":[]}`.
- [ ] Đảm bảo thứ tự tick gather theo ticket: đồng hồ/cooldown/hồi nút/**tươi** → (dòng lũ, hook của lát X) → bơi/oxy/ngạt → thủy quái/hit → bến trước hái → bắt cá → hết giờ → cập nhật cá/sinh thêm.
- [x] Test `tests/test_p3_gather_lifo.py`: LIFO với id không liền nhau, faint ghi kho rỗng, ươn vẫn chiếm ô khi rơi hàng.
- [ ] Mở PR sau lát A, nhờ haiquanng review. Commit: `gather: lost/faint theo cá thể LIFO`.
- [ ] Khi xong sớm: vào pair với haiquanng ở lát X (test hướng/biên dòng lũ).

### minhphuong150505 — Lát Q (quán tươi)
- [ ] `quan.py`: `stock` là danh sách cá thể (nhận nguyên số lượng, id, độ tươi, kể cả hàng ươn); hao 0.25/s (1 đơn vị/tick) kể cả hàng đang giữ chỗ; `spoiled` (`location:"stock"`) theo id trước khi xử lý giữ chỗ.
- [ ] Giữ theo id: mỗi loại lấy cá thể khả dụng tươi nhất, hòa theo id; phần giữ có cá thể vừa ươn → nhả toàn bộ và thử giữ lại **đúng một lần**, xử lý theo `order_tick` rồi id bàn; không đủ → `unfulfillable`, khách chờ tới hạn.
- [ ] Nấu: tiêu đúng các id đang giữ, `base_price = floor(giá niêm yết × trung bình fresh / 100)`; boa `floor(tiền món × 0.2)` trên giá đã chốt; `cook_started.data.items` là mảng cá thể sắp theo kind rồi id; điểm vẫn `earned + 100 × floor(reputation)`.
- [ ] Thứ tự tick quán theo ticket (hao tươi → `spoiled` → giữ chỗ → món chín → di chuyển/tương tác → thanh toán/kiên nhẫn/đóng ca → khách).
- [ ] Test `tests/test_p3_quan.py`: qua ngưỡng 30 trong lúc giữ chỗ, giữ lại thành công/thất bại, giá theo tươi (floor), boa trên giá đã chốt, hàng ươn không dùng nấu nhưng chiếm kho.
- [ ] Mở PR sau lát B, nhờ phuthaitran review. Commit: `quan: kho cá thể, giữ theo id, giá theo tươi`.

### phuthaitran — Lát D (day + đặt trước, mở rộng 2)
- [ ] `day.py`: bàn giao kho cá thể **trong cùng tick chuyển pha**, hàng không hao thêm, ca quán chạy từ bước sau; id tiếp tục tăng xuyên pha và Ngày; Ngày kế cấp id mới theo thứ tự mảng với kind/fresh ban đầu của mẫu `gather.hold`.
- [ ] Hàng thô ở Shop/chờ nhập không hao tươi; (nếu nhóm làm Chợ Chú Sáu) hàng mua vào kho quán Ngày kế với `fresh:100`, id mới, tách khỏi `gather_end.inventory`.
- [ ] Đặt trước: mỗi Ngày công bố 2 đơn R1,R2 sau `phase_start(gather)` (`reservation_announced`), bàn khác nhau, món trong kế hoạch, tick đến theo seed trong [1800,10799]; snapshot gather trong `day` và quán có `reservations[]` + `state`, `customers[].reservation_id`, `tables[].reservation_id`.
- [ ] Trạng thái `scheduled → holding → waiting → served | failed`; giữ bàn từ `max(0, arrival_tick − 1800)`; đến giờ: `occupied` / `stock` → fail; thành công → giữ nguyên liệu, `reservation_arrived` rồi `customer_arrived`, kiên nhẫn 60 s, giá `floor(giá đã chốt × 1.5)` rồi mới boa; `served` rồi `reservation_served`.
- [ ] Lỡ đơn (`stock`/`occupied`/`burnt`/`patience`/`closing`): nhả hàng/bàn, hủy món, uy tín −1 đúng một lần, `reservation_failed`; món cháy phát `dish_burnt` (`order_status:"failed"`) trước; đóng ca fail các đơn chưa xong theo id.
- [ ] Test `tests/test_p3_day.py` (bàn giao cùng tick, id xuyên Ngày) và `tests/test_p3_reservations.py` (hai đơn, fail từng lý do, một lần phạt, `random_reservations:false`).
- [ ] Mở PR sau lát Q (đặt trước chạm `quan.py` → phối hợp với minhphuong150505). Commit: `day: bàn giao kho cá thể`, `quan: đặt trước R1/R2`.

### RachalHys — Lát U (HUD) + QA
- [ ] HUD sáng/tối hiện độ tươi hoặc hàng ươn bằng số, thanh, nhãn hoặc biểu tượng, cho giỏ, kho quán và phần giữ; thanh/nhãn không phụ thuộc màu (đọc được ở 320 px và 1280×720).
- [ ] HUD sáng hiện hai đơn đặt trước R1/R2; HUD quán hiện bàn giữ, trạng thái và đồng hồ đến; cảnh báo dòng lũ bằng chữ, biểu tượng, âm thanh.
- [ ] Rà test P1–P2 sẽ vỡ vì kho cá thể, gửi danh sách cho các lát ngay phút 7 (cần cho haiquanng, minhphuong150505).
- [ ] Commit: `ui: HUD độ tươi, đặt trước, cảnh báo lũ`.

### Phút 20 — Smoke tích hợp + standup (haiquanng dẫn, HoangHongNgo hỗ trợ)
- [ ] Chạy smoke bàn giao kho trên bản tích hợp, lưu `docs/proof/phase-3/integration.*`.
- [ ] Standup 2–3 phút: lát nào trễ thì người xong sớm vào pair (ưu tiên giúp haiquanng, người ôm nhiều lát nhất).

---

## 3.2 Bật v1.2 & kiểm chứng (phút 25–32)

### HoangHongNgo
- [ ] Gộp C → A/X → B → Q → D → U; bật v1.2 khi gather và quán cùng sẵn sàng (kho đếm → mã 2); xử lý xung đột `gather.py`/`quan.py`/`scenario.py`.
- [ ] Trên `main` sạch: toàn bộ test xanh, smoke `gather → quan` và `--mode day --days 1/3`, chạy hai lần cùng seed `cmp` giống từng byte.
- [ ] `CHANGELOG.md`: breaking change (kho đếm → mã 2), schema mới, cách cập nhật fixture, test P1/P2 đổi và lý do.
- [ ] `docs/verification/phase-3.md`: AC-P3-xx → cách kiểm → bằng chứng → kết quả (trung thực), khớp commit gắn tag.

### haiquanng — Lát P (proof)
- [ ] `docs/proof/phase-3/`: log test, `integration.*`, `day.jsonl` (`--days 1` và `--days 3`), kết quả `cmp`, ảnh HUD của RachalHys, bằng chứng `current`/`reservations`; mỗi file ghi commit đã chạy. Gửi danh sách file cho HoangHongNgo.
- [ ] Chạy lại regression P1–P2 còn hiệu lực (script `docs/proof/phase-2/run_proof.py` làm mẫu).
- [ ] Commit: `docs: proof Phase 3`.

### ChuTungDuongg + haiquanng
- [ ] Chơi thử `gather`: để hàng ươn trong giỏ, bị Cá Sấu làm rơi (xem `lost`), ngất, cập bến, mở quán với file vừa ghi.

### minhphuong150505 + phuthaitran
- [ ] Chơi thử `day` trọn 1 Ngày: hàng ươn trong kho quán, giữ lại một lần, món giá theo tươi, một khách đặt trước thành công và một fail.

### RachalHys
- [ ] Chạy lại regression P1–P2 và kiểm HUD trên `main`; ảnh HUD bàn giao cho haiquanng.

---

## 3.3 Dự phòng & bàn giao (phút 32–35)

### HoangHongNgo
- [ ] Retro nhanh vào `docs/retro.md`: điều rút ra từ lần đổi schema kho (điều tốt / điều vướng / 1 hành động có người nhận). Cập nhật `docs/clarify.md`, `docs/standup.md`.
- [ ] Gắn và đẩy tag trên commit bàn giao ở `main` **trước 2:30**:

```bash
git tag phase-3 && git push origin phase-3
```

### Mọi người
- [ ] Ghi phần của mình vào `docs/ai-usage-log.md`; cập nhật `docs/members/<handle>.md`; có ≥ 1 commit có nội dung ở Phase 3. — xong: ChuTungDuongg
- [ ] Mở rộng: khai `extensions` trong contract, test + bằng chứng trong README (nhóm 6 người cần **≥ 2 mục** cả buổi lab: `current` — haiquanng, `reservations` — phuthaitran; các mục Phase 2 `net`/`snake`/`burn` tính tiếp nếu đã gộp). Phần "Tự do sáng tạo" ghi ở README, phải tắt được ở headless.

---

## Theo dõi commit Phase 3 (mục tiêu ≥ 1 commit/người mỗi phase nhỏ)

| Handle | 3.1 | 3.2 | 3.3 |
|---|---|---|---|
| HoangHongNgo | contract v1.2 · scenario · pause · ghi tác động | gộp · CHANGELOG · verification | retro · ghi chép · tag |
| haiquanng | inventory cá thể · gather tươi/spoiled · `current` · smoke phút 20 | test `current`/tươi · proof · regression | sửa lỗi chơi thử |
| ChuTungDuongg | lost/faint LIFO cá thể · test thứ tự tick | review lát A · chơi thử gather | sửa lỗi · ai-usage-log |
| minhphuong150505 | quan kho cá thể · giữ theo id | giá theo tươi, boa + test | sửa lỗi chơi thử day |
| phuthaitran | day bàn giao kho cá thể | đặt trước R1/R2 + test | sửa lỗi chơi thử day |
| RachalHys | HUD tươi/ươn · danh sách test vỡ | HUD đặt trước/lũ · regression | ảnh HUD, hỗ trợ lát trễ |
