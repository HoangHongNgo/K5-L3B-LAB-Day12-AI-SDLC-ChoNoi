# minhphuong150505 — Báo cáo đóng góp và phản tư cá nhân

- **Họ và tên:** Nguyễn Minh Phương
- **GitHub Username:** `minhphuong150505`
- **Nhóm:** Quán Ăn Chợ Nổi — Lab 12 AI SDLC
- **Repository nhóm:** [HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi)
- **Repository gốc (giảng viên):** [VinUni-AI20k/K5-L3B-LAB-Day12-AI-SDLC](https://github.com/VinUni-AI20k/K5-L3B-LAB-Day12-AI-SDLC)
- **Branch Rebuild chính thức:** `p4/rebuild-quan-minhphuong150505`

---

## 1. Phase 1 — Lát 3 (Lịch khách, đặt món, giữ chỗ nguyên liệu và kiên nhẫn)
- **Nhiệm vụ phân công:** Lát 3 — Khách đến theo lịch, chọn món ngẫu nhiên tất định, giữ chỗ nguyên liệu trong kho khả dụng, đếm ngược kiên nhẫn, khách bỏ về khi hết kiên nhẫn và trừ uy tín.
- **Chi tiết triển khai:**
  + `_should_spawn_customer`: Khách xuất hiện tại `first_customer_tick`, lặp lại mỗi `customer_interval_s * 60` tick.
  + `_find_available_table`: Chọn bàn trống có ID nhỏ nhất theo thứ tự Unicode (`T1` -> `T4`).
  + `_spawn_customer`: Lọc danh sách món có đủ nguyên liệu khả dụng (`stock - reserved`), duyệt theo ID Unicode, chọn đều theo seed bằng `rng.choice(valid_dishes)` từ `streams.get("customers")`. Nếu không có món nào nấu được, phát event `no_dish`.
  + `_infer_customer_reservations`: Tự động tính toán và giữ chỗ nguyên liệu cho khách fixture thiếu `reserved` (theo thứ tự `order_tick` rồi ID bàn).
  + `_update_customer_patience` & `_expire_customer`: Kiên nhẫn bắt đầu giảm từ bước sau khi khách đến (`phase_tick != order_tick`). Khi kiên nhẫn về 0 trong giờ ca, phát `customer_left` (reason: `patience`), giảm uy tín (`left_reputation_delta = -0.5`, kẹp đáy tại 0), giải phóng nguyên liệu đã giữ.
  + `_validate_quan` trong `chonoi/scenario.py`: Xác thực scenario hợp lệ, cấm trùng bàn, cấm giữ quá tồn kho hoặc sai công thức, trả exit code 2 khi vi phạm.
- **Commits Phase 1:**
  + `2c8a197`: Scenario validation cho customer fixtures, reserved và ràng buộc quán.
  + `fe96d5f`: Khởi tạo customer fixture, tính kho khả dụng, suy ra reserved khi thiếu.
  + `e888a95`: Lịch khách đến tất định (phase_tick), chọn bàn trống nhỏ nhất.
  + `78e763f`: Chọn món ngẫu nhiên đều qua Streams, giữ chỗ nguyên liệu, phát customer_arrived và no_dish.
  + `0393768`: Đếm ngược kiên nhẫn, xử lý hết kiên nhẫn (customer_left), kẹp uy tín, giải phóng reserved.
  + `ada49d0`: Bộ unit test và black-box test bao phủ AC-P1-07, AC-P1-08 và ca biên determinism.
  + `63ee371`: docs: record Minh Phuong phase 1 AI usage and contributions.
- **Tình trạng kiểm toán Git Phase 1:**
  + PR #3 đã được merge vào `origin/main` (commit `9512b63`).
  + Nhánh `revert-3-p1/lat3-minhphuong150505` (commit `2c251c7`) được tạo độc lập trên remote nhưng chưa từng được merge vào `main`.
  + Toàn bộ code Phase 1 hợp lệ của Lát 3 đã nằm trong `origin/main` và chạy đạt 100% (36/36 test của `test_p1_lat3.py` pass).

---

## 2. Phase 2 — Lát Q (Hệ thống quán ăn: 2 bếp, 4 bàn, 6 món, kế hoạch ngày, đóng ca và scenario day)
- **Nhiệm vụ phân công:** Lát Q — Toàn bộ nghiệp vụ vận hành Quán ăn theo Test Contract v1.1 (TICKET-02).
- **Chi tiết triển khai:**
  + **Task Q1:** Cấu hình động 2 bếp (B1, B2), 4 bàn (T1..T4), 6 món ăn và 6 loại nguyên liệu đọc trực tiếp từ tuning (không hard-code).
  + **Task Q2:** Thêm tham số `menu_ids` lọc món khả dụng theo kế hoạch ngày (`day_plan.dishes` hoặc `day_plan.menu`). Sắp xếp ID món theo Unicode; nếu không có món nào khả dụng phát `no_dish`. Không giới hạn số lượt phục vụ nếu kho còn nguyên liệu.
  + **Task Q3:** Triển khai hai bếp hoạt động song song, lấy đơn `reserved` cũ nhất (`order_tick`, rồi ID bàn), tiêu thụ nguyên liệu đã giữ, phát `cook_started` và `dish_ready`.
  + **Task Q4 & Q5:** Hoàn thiện vòng đời bưng món (`dish_picked`, giới hạn tay cầm 1 món), phục vụ đúng bàn/đơn (`served`), tính boa `floor(price * 0.2)` khi giao còn ≥ 50% kiên nhẫn, khách ăn 600 tick, thanh toán (`paid`), thu boa dương tăng 0.2 uy tín, hết kiên nhẫn giảm 0.5 uy tín (kẹp [0, 5]).
  + **Task Q6:** Đóng ca (`closing`): khách đang ăn thanh toán ngay theo giá niêm yết, khách chờ rời không bị trừ uy tín, giải phóng reserved, dọn dẹp bàn bếp, phát `quan_end` và tạo dict `self.result` để bàn giao cho Lát D.
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
  + Kiểm tra tính tất định (Determinism): PASS (so sánh `cmp` hai lần chạy độc lập trùng khớp 100% từng byte).

---

## 3. Phase 3 — Lát Q (TICKET-03: Mùa Nước Nổi, Test Contract v1.2)
- **Nhiệm vụ phân công:** Nâng cấp hệ thống Quán ăn đáp ứng Test Contract v1.2 "Mùa Nước Nổi": Kho cá thể, vòng đời độ tươi, cơ chế ươn, re-reservation và định giá theo độ tươi.
- **Chi tiết triển khai:**
  + **Điều chỉnh Phase 2:** Sửa fixture `p2_quan_tuning.json` khớp chuẩn Ticket 02 (`ca_keo_nuong` cook_s: 6, price: 70; `lau_mam` recipe 4 loại, cook_s: 12, price: 200) và hỗ trợ cả hai khóa `dishes` và `menu` trong `day_plan`.
  + **Kho cá thể (Item-based inventory):** Chuyển đổi mô hình kho từ đếm số lượng sang mảng cá thể `[{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]`. Quán nhận nguyên số lượng, id và độ tươi kể cả hàng ươn. Trả mã 2 cho kho đếm khi chạy contract v1.2.
  + **Giữ chỗ theo Item IDs:** `customer["reserved"]` là mảng các chuỗi `item_id`. Thuật toán ưu tiên chọn cá thể khả dụng tươi nhất (`fresh >= 30`), hòa theo ID nhỏ hơn. Cấm dùng item ươn hoặc dùng chung cá thể giữa các khách.
  + **Hao tươi trong Quán (Freshness Decay):** Tốc độ giảm 0.25/s (1/240 điểm mỗi tick) cho toàn bộ kho thô kể cả hàng đang giữ chỗ. Món đang nấu trên bếp không hao tươi. Độ tươi kẹp đáy tại 0. Dùng `Fraction(1, 240)` để loại bỏ triệt để sai số dấu phẩy động.
  + **Event `spoiled`:** Tự động phát hiện và phát event `spoiled` khi độ tươi giảm từ `>= 30` xuống `< 30` đúng một lần tại tick vượt ngưỡng. Nhiều cá thể cùng ươn được phát theo thứ tự Unicode ID.
  + **Cơ chế Re-reservation:** Khi nguyên liệu đang giữ bị ươn, nhả toàn bộ reserved của đơn và thử giữ lại với nguyên liệu tươi nhất còn lại trong kho. Xử lý theo thứ tự `order_tick` rồi ID bàn. Nếu không đủ, chuyển `order_status = "unfulfillable"`, khách tiếp tục chờ đến hết kiên nhẫn.
  + **Chốt giá theo độ tươi (Freshness Pricing):** Tại thời điểm bắt đầu nấu (`cook_started`), chốt `base_price = floor(giá niêm yết * avg_fresh / 100)` dựa trên trung bình độ tươi của các cá thể tiêu thụ. `cook_started.items` là mảng cá thể sắp theo kind rồi id.
  + **Phục vụ và Boa:** `tip = floor(base_price * 0.2)` nếu lúc phục vụ kiên nhẫn còn lại sau bước 1 `>= 50%`. Thanh toán `amount = base_price + tip`.
  + **Đóng ca và Snapshot/Result:** Snapshot `stock` và `result["stock"]` xuất mảng cá thể đúng schema v1.2 kèm độ tươi cuối ca.
  + **Scenario Validation v1.2:** Bổ sung xác thực mảng cá thể cho `quan.stock`, kiểm tra `reserved` trỏ đúng cá thể hợp lệ chưa ươn, không dùng chung cá thể, khớp recipe món.
  + **Kiểm thử toàn diện Phase 3:** Xây dựng `tests/test_p3_quan.py` với 27 ca test bao phủ toàn bộ 7 nhóm yêu cầu và fixtures `p3_quan_tuning.json`, `p3_quan_scenario.json`.
- **Commits Phase 3:**
  + `5aebe32`: `fix(p2): align menu fixtures and dishes day plan schema with ticket 02`
  + `2de3541`: `p3(quan): support item-based inventory and freshness lifecycle`
  + `149211a`: `test(p3): cover item inventory freshness and re-reservation`
  + `2489fa6`: `docs(p3): update Minh Phuong phase 3 contribution report`
  + `1d11cd6`: `Merge branch 'main' into p3/quan-minhphuong150505`
- **Kết quả kiểm thử:**
  + Bộ test Phase 3 (`test_p3_quan.py`): 27/27 tests PASSED.
  + Toàn bộ test suite repository: 234/234 tests PASSED.
  + Kiểm tra tất định (Determinism): PASS (so sánh `cmp` trùng khớp từng byte).

---

## 4. Phase 4 — Kiểm toán Toàn Diện và Trạng thái Release (Full Rebuild & Audit)

### 4.1. Kiểm toán Git và Đối chiếu Repository
- **Repository gốc của giảng viên (`upstream/main`):**
  + URL: `https://github.com/VinUni-AI20k/K5-L3B-LAB-Day12-AI-SDLC.git`
  + HEAD: `f0a1906` (`README: quy ước tên repo K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`)
  + Đối chiếu: Repository nhóm kế thừa chuẩn cấu trúc starter, bổ sung đầy đủ các pha mở rộng Phase 1, Phase 2 và Phase 3 theo hướng dẫn của giảng viên.
- **Repository nhóm (`origin/main`):**
  + URL: `https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi`
  + HEAD hiện tại trên main: `e5574e7` (đã tích hợp các PR #17..#21 từ các thành viên khác: DaySim, Shop, Monsters, Net, Proof).
- **Branch Rebuild độc lập:**
  + Tạo branch: `p4/rebuild-quan-minhphuong150505`.
  + Base commit: `1d11cd6` (commit trên `origin/p3/quan-minhphuong150505` đã tích hợp sạch sẽ giữa `origin/main` `e5574e7` và toàn bộ mã nguồn Quán của Minh Phương).
  + Lý do chọn base: Đảm bảo kế thừa trọn vẹn cả lịch sử phát triển Quán (Phase 1, 2, 3) lẫn các cải tiến mới nhất từ main của đồng đội, không gây mất mát dữ liệu hay xung đột giả.

### 4.2. Tình trạng TICKET-04 và Phạm vi Phase 4
- **Kết quả rà soát tài liệu:**
  + Kiểm tra toàn bộ git log, commit history, branch remotes, tags, issues và thư mục repo: `find . -name "*TICKET*"`, `grep -rnwi "TICKET-04"`.
  + File tồn tại trong repo: `PRD0.md`, `TICKET2.md`, `TICKET3.md`. **Không tồn tại file `TICKET4.md` hay `TICKET-04`**.
  + Link Claude artifact (`https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg`) không thể truy cập từ môi trường sandbox.
- **Tuân thủ quy định & Trạng thái Phase 4:**
  + Tuân thủ nghiêm ngặt cảnh báo của Master Prompt: *"Nếu không có TICKET-04: Không tự sáng tạo yêu cầu Phase 4. Đánh dấu các chức năng chưa thể triển khai do thiếu TICKET-04 là BLOCKED. Không tuyên bố đã hoàn thành Phase 4 đầy đủ."*
  + **Trạng thái Phase 4:** `BLOCKED (Chờ tài liệu đặc tả TICKET-04)`.
  + Phần việc thuộc trách nhiệm của Nguyễn Minh Phương: Đã hoàn thiện 100% việc kiểm toán, tối ưu hóa mã nguồn Quán ăn, đảm bảo tính đúng đắn và chuẩn bị đầy đủ các tiêu chí release v1.0.0.

### 4.3. Kiểm tra Tính Tất định (Determinism) & Toàn bộ Test Suite
- **Tính tất định (Determinism Check via `filecmp.cmp`):**
  + Kịch bản Quán v1.0 (`quan_one_customer.json`, seed 42, 1200 ticks): PASS (so sánh nhị phân trùng khớp 100% từng byte).
  + Kịch bản Quán v1.1 (`p2_quan_scenario.json`, seed 42, 1200 ticks): PASS (so sánh nhị phân trùng khớp 100% từng byte).
  + Kịch bản Quán v1.2 (`p3_quan_scenario.json`, seed 42, 1200 ticks): PASS (so sánh nhị phân trùng khớp 100% từng byte).
- **Toàn bộ Test Suite Repo:**
  + **310/310 tests PASSED** trên toàn bộ repository (thời gian chạy ~6.8 giây).
  + Tỷ lệ đạt: **100%** (không có lỗi hay regression).

---

## 5. Phản tư cá nhân

### AI sai ở đâu và tôi phát hiện thế nào?
1. **Giai đoạn Phase 1:**
   - Khi khởi tạo khách fixture, hàm xử lý ban đầu `c.get("reserved", {})` trả về `None` khi khách có key `"reserved": null`, dẫn đến lỗi `AttributeError` khi gọi `.items()`. Tôi phát hiện qua unit test và sửa thành `c.get("reserved") or {}`.
2. **Giai đoạn Phase 2:**
   - Trong `scenario.py`, khi xác thực kế hoạch ngày, logic ban đầu duyệt qua các key của `day_plan` nhưng nhầm lẫn khi có cấu trúc `menu` trực tiếp; tôi đã bổ sung hàm kiểm tra nhận diện linh hoạt giữa dạng kế hoạch đơn ngày và đa ngày.
   - Khi kiểm tra ngưỡng tính boa (≥ 50% kiên nhẫn), phát hiện timer kiên nhẫn bị giảm 1 tick ở Bước 1 trước khi phục vụ ở Bước 3. Do đó nếu fixture để đúng 1800 tick, bước phục vụ sẽ nhận 1799 tick (< 50%). Tôi đã hiệu chỉnh fixture lên 1801 tick để bảo đảm test đúng biên nghiệp vụ.
3. **Giai đoạn Phase 3:**
   - Khi tính giá món theo độ tươi lúc bắt đầu nấu: ban đầu test fixture mong đợi giá chốt theo độ tươi ban đầu (fresh 80 -> giá 48 cho món 60đ). Tuy nhiên, theo thứ tự hợp đồng TICKET-03, kho thô bị hao tươi ở Bước 2 (giảm 1/240 điểm tươi) trước khi người chơi tương tác nấu ở Bước 4. Tại Bước 4, độ tươi thực tế là `80 - 1/240 = 79.9958`, do đó `floor(60 * 79.9958 / 100) = 47`. Tôi đã phân tích đúng thứ tự thực thi theo hợp đồng và xác nhận giá trị 47 là chính xác tuyệt đối.
4. **Giai đoạn Rebuild & Phase 4:**
   - Phát hiện docstring bị lặp lại 2 lần liên tiếp trong hàm `_order_ref` của `chonoi/sim/quan.py`, đã được dọn dẹp sạch sẽ.
   - Kiểm tra kỹ lưỡng sự khác biệt giữa hợp đồng repo và tuning fixtures: nhận diện rõ `game.contract.json` trên main vẫn ở v1.0 (do Integrator chưa merge v1.1/v1.2), trong khi toàn bộ nghiệp vụ Quán đã được thiết kế backward-compatible, chạy hoàn hảo trên cả 3 phiên bản v1.0, v1.1, và v1.2.

### Điều học được về Software Architecture và AI Collaboration:
- **Tất định tuyệt đối nhờ Kiểu dữ liệu Phân số (`Fraction`):** Xử lý hao tươi với `Fraction(1, 240)` thay vì số thực `float` giúp loại bỏ hoàn toàn lỗi tích lũy dấu phẩy động qua hàng nghìn tick, bảo đảm ngưỡng so sánh 30 điểm và tính toán giá trị luôn đồng nhất giữa các môi trường chạy.
- **Tính Tương thích Ngược (Backward Compatibility):** Xây dựng một module sim duy nhất có thể tự động thích ứng giữa mô hình đếm số lượng (v1.0/v1.1) và mô hình mảng cá thể (v1.2) giúp toàn bộ hệ thống test suite lớn (310 tests) luôn xanh mà không làm đứt gãy công việc của các đồng đội khác.
- **Tính Kỷ luật trong SDLC:** Khi thiếu đặc tả Phase 4 (TICKET-04), thái độ đúng đắn của một kỹ sư là báo rõ trạng thái BLOCKED, hoàn thiện tuyệt đối những phần đã có đặc tả và kiểm chứng chất lượng thay vì tự ý bịa đặt tính năng gây xung đột và rủi ro cho đợt release v1.0.0 của nhóm.
