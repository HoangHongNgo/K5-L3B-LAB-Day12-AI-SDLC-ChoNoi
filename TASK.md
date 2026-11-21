# TASK — Phase 1 (PRD-0, 0:00–1:00)

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
- [ ] Đọc PRD-0 mục F "Gather" (đoạn 2) và `chonoi/sim/gather.py`.
- [ ] Thống nhất với haiquanng một hàm chung `_add_to_hold(kinds) -> bool` (kiểm trần `hold_capacity`, thêm theo thứ tự nhặt) để hai lát không đụng nhau.
- [ ] Tạo nhánh `p1/lat1-ChuTungDuongg`, dựng hàm trống `_update_oxygen(events, was_surface)`.

### haiquanng — Lát 2
- [x] Đọc PRD-0 mục F "Gather" (đoạn 3–5) và mục G.
- [x] Viết `_add_to_hold` (đã thống nhất với lát 1), commit sớm để lát 1 dùng chung.
- [x] Tạo nhánh `p1/lat2-haiquanng`.

### minhphuong150505 — Lát 3
- [ ] Đọc PRD-0 mục D (khối `quan`), mục F "Quán" (đoạn 4–5).
- [ ] Chốt với phuthaitran cấu trúc khách/đơn: các trường `id, table_id, dish_id, order_tick, state, patience_ticks_left, eat_ticks_left, order_status, reserved, base_price, tip`.
- [ ] Tạo nhánh `p1/lat3-minhphuong150505`.

### phuthaitran — Lát 4
- [ ] Đọc PRD-0 mục F "Quán" (đoạn 1–3), event `cook_started`/`dish_ready`/`dish_picked`/`served`/`paid`/`quan_end`.
- [ ] Viết 1 file scenario mẫu có sẵn khách `waiting` + kho để tự test lát 4 không cần chờ lát 3 (`tests/fixtures/quan_one_customer.json`).
- [ ] Tạo nhánh `p1/lat4-phuthaitran`.

### RachalHys — QA lead + HUD
- [x] Lập khung `docs/verification/phase-1.md` với 12 dòng AC-P1-01..12 (cột cách kiểm chứng).
- [x] Đọc `chonoi/web/index.html` và `chonoi/live.py`, liệt kê trường HUD còn thiếu so với PRD-0 mục 2.
  - Rà bằng fixture trên trình duyệt. HUD sáng đã hiện thời gian, oxy, Máu và giỏ. HUD tối hiện tồn vật lý thay cho kho khả dụng và tên món trên bếp bị hiện thành `[object Object]`.
- [x] Tạo nhánh `p1/hud-RachalHys`.

---

## 1.2 Lõi lát (phút 15–25)

### ChuTungDuongg — Lát 1
- [ ] Oxy theo `d` cuối bước: mặt nước (`d ≤ surface_depth`) +`oxygen_refill_per_tick`, kẹp max, reset `zero_oxy_ticks`; dưới nước −1, kẹp 0.
- [ ] `dive` / `surface` khi đổi phía mặt nước (so đầu/cuối bước, `data.pos`).
- [ ] `oxygen_empty` khi từ dương xuống 0.
- [ ] Commit: `gather: oxy, dive/surface, oxygen_empty`.

### haiquanng — Lát 2
- [x] Hái: chỉ ở mặt nước, ngoài bến; nút `ready` gần nhất trong `interact_radius` (tính cả đúng mép, hòa theo id); đủ chỗ → `gather` + `regrow_ticks = regrow_s × 60`; thiếu chỗ → `hold_full` (`action`, `node_id`, `required`, `free`).
- [ ] Chạy thử `--inventory-out` thật bằng smoke dock.json và đưa file cho lát 3/4 (**mốc phút 25**). — *haiquanng: `--inventory-out` thật đã chạy trong `test_full_run_gather_catch_dock_then_quan` (quán đọc đúng `stock`); chưa tạo `dock.json` và chưa gửi file cho lát 3/4.*
- [x] Commit: `gather: hái nút, hold_full, regrow`.

### minhphuong150505 — Lát 3
- [x] Lịch khách theo `phase_tick`: `first_customer_tick`, rồi mỗi `customer_interval_s × 60`; bàn trống id nhỏ nhất; không có bàn → bỏ lượt.
- [ ] Chọn món đều theo seed (qua `Streams`) trong món đủ kho khả dụng (tồn − giữ), duyệt id món theo Unicode; không đủ → `no_dish`.
- [ ] Giữ đúng công thức vào `reserved`, `customer_arrived`.
- [x] Commit: `quan: lịch khách, chọn món, giữ chỗ`.

### phuthaitran — Lát 4
- [ ] Chọn tối đa một interact theo (khoảng cách, bếp trước bàn, id) trong `interact_radius`; đối tượng không tương tác được → bỏ lượt.
- [ ] Bếp idle lấy đơn `reserved` cũ nhất (order_tick, id bàn), tiêu nguyên liệu giữ, chốt giá → `cook_started` (`items` sắp theo kind, `base_price`); đếm `cook_ticks_left` → `dish_ready`.
- [ ] Commit: `quan: chọn interact, nấu, dish_ready`.

### RachalHys — HUD
- [ ] HUD buổi sáng: thời gian còn lại, thanh oxy, Máu, giỏ (`hold_count/hold_capacity` + danh sách).
- [ ] Commit: `ui: HUD buổi sáng`.

### HoangHongNgo
- [ ] Standup phút 20: ai vướng → điều người dự phòng vào pair.
- [ ] Kiểm dải hợp lệ tuning trong `chonoi/contract.py` (mục A "Dải hợp lệ"), sai → mã 2.
- [ ] Commit: `contract: kiểm dải hợp lệ tuning`.

---

## 1.3 Hoàn thiện lát (phút 25–45)

### ChuTungDuongg — Lát 1
- [ ] Đếm ngạt: mỗi bước dưới nước kết thúc với oxy 0 tăng `zero_oxy_ticks`; đủ `choke_interval_ticks` → về 0, −1 Máu, `choke` (`hp`). Nổi lên đúng bước đáng lẽ ngạt thì không ngạt.
- [ ] Máu 0 → bỏ giỏ LIFO, `faint` (`cause:"choke"`, `lost`, `hp:0`) → `gather_end` `fainted`, kho rỗng, dừng bước.
- [ ] Test `tests/test_p1_lat1.py`: choke ở t+59 (AC-P1-02), faint ghi kho `{"items":{}}` (AC-P1-03).
- [ ] Mở PR, nhờ haiquanng review.

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
- [ ] Bếp ready → tay trống (`carry_limit` 1) → `dish_picked`, bếp về idle; `ready_ticks` chỉ tăng cho món đã ready đầu bước.
- [ ] Bàn nhận đúng `order_id` → `served`, ăn `eat_s × 60`; boa `floor(giá × tip_rate)` nếu tỷ lệ kiên nhẫn ≥ `tip_min_patience_ratio`; ăn xong → `paid` (`finished_eating`), boa dương + `tip_reputation`.
- [ ] Hết ca: khách đang ăn trả `closing`, khách chờ rời `closing` không trừ uy tín, rồi `quan_end`. Điểm = `earned + 100 × floor(reputation)`.
- [ ] Test `tests/test_p1_lat4.py`: AC-P1-09, AC-P1-10.
- [ ] Mở PR, nhờ minhphuong150505 review.

### RachalHys — HUD + QA
- [ ] HUD buổi tối: kho khả dụng, món gọi + kiên nhẫn từng khách, trạng thái bếp, món trên tay, tiền, uy tín.
- [ ] README: chạy từ clone sạch ≤ 3 lệnh (macOS/Linux), điều khiển, cách tính điểm, lệnh test 1 dòng (AC-P1-12).
- [ ] Review test của 4 lát, bổ sung chỗ thiếu ca biên (đúng mép bán kính, đúng tick hết ca).
- [ ] Commit: `ui: HUD buổi tối`, `docs: README cách chạy và điều khiển`.

### HoangHongNgo
- [ ] Standup phút 40; lát nào chậm → người đã xong vào hỗ trợ.
- [ ] Review và gộp PR theo thứ tự: lát 2 (hàm giỏ) → lát 1 → lát 3 → lát 4 → HUD; xử lý xung đột ở `gather.py`/`quan.py`.

---

## 1.4 Tích hợp & kiểm chứng (phút 45–55)

### HoangHongNgo
- [ ] Trên `main` sạch: chạy toàn bộ test + smoke hai tiến trình (dock.json, seed 42) → quán tick 0 có `stock:{"bong_sung":2,"ca_loc":1}`.
- [ ] Chạy hai lần cùng seed, so `cmp` để kiểm giống từng byte.

### RachalHys
- [ ] Lưu output thật vào `docs/proof/phase-1/` (log test, `gather.jsonl`, `catch.json`, `quan.jsonl`, ảnh HUD).
- [ ] Điền `docs/verification/phase-1.md`: AC → cách kiểm → link bằng chứng → đạt/chưa đạt (ghi trung thực).

### ChuTungDuongg + haiquanng
- [ ] Chơi thử `gather` trên `main`: lặn tới ngạt, hái, bắt cá, cập bến; ghi lỗi thấy được vào kênh nhóm, sửa nhanh nếu kịp.

### minhphuong150505 + phuthaitran
- [ ] Chơi thử `quan` với kho vừa ghi (`--inventory kho.json`): đủ vòng nấu → bưng → phục vụ → trả tiền; để một khách hết kiên nhẫn; sửa nhanh nếu kịp.

---

## 1.5 Bàn giao (phút 55–60)

### Mọi người
- [ ] Ghi phần của mình vào `docs/ai-usage-log.md` (công cụ, việc dùng AI, token/chi phí nếu đo được). — xong: ChuTungDuongg, haiquanng
- [ ] Tạo `docs/members/<handle>.md` theo `docs/members/TEMPLATE.md` (có thể hoàn thiện ở phase sau). — xong: ChuTungDuongg, haiquanng

### HoangHongNgo
- [ ] Cập nhật `docs/clarify.md`, `docs/standup.md`, ghi nhanh vào `docs/retro.md`.
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
