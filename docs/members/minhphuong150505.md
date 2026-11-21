# minhphuong150505 — Báo cáo đóng góp và phản tư cá nhân

## 1. Phase 1 — Lát 3 (Lịch khách, đặt món, giữ chỗ nguyên liệu và kiên nhẫn)
- **Commits Phase 1:**
  + [2c8a197](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/2c8a197): Scenario validation cho customer fixtures, reserved và ràng buộc quán.
  + [fe96d5f](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/fe96d5f): Khởi tạo customer fixture, tính kho khả dụng, suy ra reserved khi thiếu.
  + [e888a95](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/e888a95): Lịch khách đến tất định (phase_tick), chọn bàn trống nhỏ nhất.
  + [78e763f](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/78e763f): Chọn món ngẫu nhiên đều qua Streams, giữ chỗ nguyên liệu, phát customer_arrived và no_dish.
  + [0393768](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/0393768): Đếm ngược kiên nhẫn, xử lý hết kiên nhẫn (customer_left), kẹp uy tín, giải phóng reserved.
  + [ada49d0](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/ada49d0): Bộ unit test và black-box test bao phủ AC-P1-07, AC-P1-08 và ca biên determinism.
  + [63ee371](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/63ee371): docs: record Minh Phuong phase 1 AI usage and contributions.
- **Tình trạng kiểm toán Git Phase 1:**
  + PR #3 đã được merge vào `origin/main` (commit `9512b63`).
  + Nhánh `revert-3-p1/lat3-minhphuong150505` (commit `2c251c7`) được tạo độc lập trên remote nhưng chưa từng được merge vào `main`.
  + Toàn bộ code Phase 1 hợp lệ của Lát 3 đã nằm trong `origin/main` và chạy đạt 100% (36/36 test của `test_p1_lat3.py` pass).

---

## 2. Phase 2 — Lát Q (Hệ thống quán ăn: 2 bếp, 4 bàn, 6 món, kế hoạch ngày, đóng ca và scenario day)
- **Các nhiệm vụ hoàn thành:**
  + **Task Q1:** Hỗ trợ cấu hình động 2 bếp (B1, B2), 4 bàn (T1..T4), 6 món ăn và 6 loại nguyên liệu đọc từ contract/tuning (không hard-code).
  + **Task Q2:** Thêm tham số `menu_ids` lọc món khả dụng theo kế hoạch ngày; sắp xếp Unicode; nếu thiếu nguyên liệu phát `no_dish`; không giới hạn số suất nếu kho còn nguyên liệu.
  + **Task Q3:** Triển khai hai bếp hoạt động song song, lấy đơn reserved cũ nhất (`order_tick`, rồi ID bàn), tiêu thụ nguyên liệu đã giữ, phát `cook_started` và `dish_ready`.
  + **Task Q4 & Q5:** Hoàn thiện vòng đời bưng món (`dish_picked`, tối đa 1 món), phục vụ đúng bàn/đơn (`served`), tính boa `floor(price * 0.2)` khi giao còn ≥ 50% kiên nhẫn, khách ăn 600 tick, thanh toán (`paid`), thu boa dương tăng 0.2 uy tín, hết kiên nhẫn giảm 0.5 uy tín (kẹp [0, 5]).
  + **Task Q6:** Đóng ca (`closing`): khách đang ăn thanh toán ngay, khách chờ rời không bị trừ uy tín, giải phóng reserved, dọn dẹp bàn bếp, phát `quan_end` và tạo dict `self.result` để bàn giao cho Lát D.
  + **Task Q7:** Scenario validation cho mode day trong `chonoi/scenario.py`: hỗ trợ khối `day`, kiểm tra `0 <= money <= earned`, kiểm tra `day_plan` và `ingredients`, cấm `quan.stock`/`reputation` trong mode day; viết hàm `validate_quan_against_inventory`.
  + **Task Q8:** Đảm bảo giao diện tích hợp với DaySim (`step`, `snapshot`, `done`, `result`, tham số khởi tạo) và tương thích hoàn toàn với pause wrapper.
  + **Task Q9:** Xây dựng bộ test `tests/test_p2_quan.py` với 34 ca kiểm thử (Q01-Q34) bao phủ toàn diện và các fixtures `p2_quan_tuning.json`, `p2_quan_scenario.json`.

- **Commits Phase 2:**
  + `242d112`: `p2(quan): support two stoves four tables and six dishes`
  + `0ab973d`: `p2(quan): filter available dishes by day plan`
  + `00dac91`: `p2(quan): implement concurrent stove order processing`
  + `3d8dfd9`: `p2(quan): complete serving payment and tips`
  + `a8924a5`: `p2(quan): finalize shift and produce day handoff result`
  + `20cdb70`: `p2(scenario): validate day inputs and inventory handoff`
  + `1832198`: `test(p2): cover quan gameplay and day compatibility`

- **Kết quả kiểm thử:**
  + Phase 1 regression (`test_p1_lat3.py`): 36/36 tests PASSED.
  + Phase 2 Quan (`test_p2_quan.py`): 34/34 tests PASSED.
  + Toàn bộ test suite: 142/142 tests PASSED.
  + Kiểm tra tính tất định (Determinism): PASS (so sánh `cmp` hai lần chạy độc lập trùng khớp 100% từng byte).

---

## 3. Phản tư cá nhân
- **AI sai ở đâu và tôi phát hiện thế nào:**
  + Trong Phase 2, khi xác thực `day_plan`, logic phân biệt plan theo ngày hay plan đơn trực tiếp bị nhầm key `"menu"` thành tên một ngày, dẫn đến duyệt qua `"ingredients"` và báo lỗi sai; phát hiện ngay khi chạy `test_q29` và đã tinh chỉnh điều kiện nhận diện chính xác.
  + Khi kiểm tra điều kiện boa (≥ 50% kiên nhẫn), phát hiện timer kiên nhẫn giảm 1 tick ở Bước 1 trước khi phục vụ ở Bước 3, do đó fixture ban đầu đặt đúng 1800 tick sẽ bị giảm xuống 1799 tick (< 50%); đã cập nhật test fixture với 1801 tick để kiểm tra đúng biên 50% sau bước giảm timer.
- **Điều học được:**
  + Chiến lược chia nhỏ commit theo từng tính năng và chạy kiểm thử hồi quy liên tục giúp cô lập lỗi ngay lập tức khi phát sinh.
  + Thiết kế giao diện sim độc lập với các fixture giả lập giúp hoàn thành module trước khi các thành viên khác hoàn tất module phụ thuộc mà không bị nghẽn tiến độ.
