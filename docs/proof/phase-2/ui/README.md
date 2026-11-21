# Kiểm chứng Phase 2 — lát U

Bản kiểm `89e2437` trên `main`, sau khi gộp PR #24, dùng manifest v1.1 chính thức. Seed 42, Chromium headless, viewport 1280×720. Bằng chứng cho AC-P2-17 và AC-P2-18.

```bash
python3 -m chonoi.live --mode day --seed 42 --scenario docs/proof/phase-2/ui/scenario.json
PYTHONPATH=tests:. python3 -m unittest discover -s tests -p 'test_p1_*.py' -v
```

| Kiểm tra | Kết quả quan sát |
|---|---|
| Menu và màn chuyển pha | DayIntro giữ ca ở tick 0 và chuyển sau khoảng 4 giây hoặc khi nhấn phím. EveningIntro nhận 3 nguyên liệu và đợi bấm Mở quán. DayResult ghi 1 khách phục vụ, 1 khách bỏ đi, 72 nghìn tiền ca, boa 12 nghìn và uy tín +0,2. [Menu](menu.png) |
| HUD và tốc độ vẽ | Font HUD sans-serif 18 px. Đếm số lần vẽ Canvas qua `requestAnimationFrame` trong 2,5 s ở gather và 2,4 s ở quán, đo bằng `performance.now()`. Hai ca đạt 60,0 FPS. [HUD sáng](hud-gather.png), [HUD tối](hud-quan.png), [cảnh báo với snapshot giả](gather-warning-mock.png) |
| Pause thật | Esc/P và Tiếp tục hoạt động trong gather, quán và Shop. Khoảng chờ quan sát 400 ms cho mỗi pha. Shop bỏ qua lệnh mua và đóng trong lúc pause, giữ nguyên số dư và cấp. Tiếp tục thì đồng hồ chạy lại. [Ảnh pause Shop](pause-shop.png) |
| Mua nâng cấp và tổng kết | Mua oxy cấp 1 ngày 1, có 2.700 tick oxy từ ngày 2. M2 xuất hiện từ ngày 3. Summary hiện sau khi Shop ngày 5 đóng. Tổng thu 560 nghìn (gồm 200 nghìn đầu fixture), số dư 360 nghìn, uy tín 4, điểm 960, món bán chạy là cá lóc nướng trui với 5 suất. [Shop](shop.png), [Summary](summary.png) |
| Regression | 119/119 ca `test_p1_*.py` đạt. Toàn repo 369 ca đạt, 1 ca bỏ qua vì chỉ áp dụng cho đàn cá đứng yên v1.0. [Log regression](regression-v11.log) |

| Pha lúc pause | Tick ngoài trước → sau | `sim_tick` giữ nguyên | `phase_tick` giữ nguyên | Giờ còn lại (tick) |
|---|---:|---:|---:|---:|
| Gather | 29 → 54 | 24 | 24 | 10.776 |
| Quán | 233 → 257 | 196 | 3 | 297 |
| Shop | 559 → 591 | 495 | 2 | 598 |

Script proof của nhóm chạy trên cùng revision cho smoke chuyển kho đạt, vòng 1 ngày đạt 22.200 tick trong 1,10 s, vòng 3 ngày đạt 66.600 tick. Hai lần chạy một ngày cùng seed cho JSONL giống từng byte.
## Bản chơi 3D

Chạy `python3 -m chonoi.live --mode day --port 8012` với preset v1.1. [Menu chợ nổi](3d-river-menu.jpg) · [Quán buổi tối](3d-cafe.jpg)

Trên Chrome, người chơi di chuyển bằng bàn phím và nút cảm ứng. Thử tắt WebGL vẫn chơi được trên Canvas 2D. Trong ca kiểm tra rút ngắn, giỏ bàn giao 2 bông súng và 1 cá lóc, đồng hồ Shop giữ nguyên trong lúc pause, mua bình oxy trừ 200 nghìn và ngày 2 bắt đầu với 2.700 tick oxy. Bộ unittest đã chạy 371 ca, 370 đạt và 1 ca được bỏ qua.

### Luồng chơi đã kiểm tra trên trình duyệt

- Chọn theo dõi cá lóc trên màn hình 390 × 844, đổi mục tiêu về bến và cập bến khi giỏ trống. Quán hiển thị các món thiếu nguyên liệu. Thu dọn đưa người chơi tới sổ cuối ca, qua tiệm rồi sang ngày 2.
- Dùng kho mẫu, bỏ chọn cá lóc nướng trui và mở quán với gỏi bông súng. Chờ khách, theo phiếu đến bếp B2, nấu, bưng đến T1 rồi phục vụ. Khách trả 48 nghìn. Khi hết nguyên liệu cho món đã chọn, thu dọn kết thúc ca.

## Bản UI ban đầu

Giao diện ở `fdb79ba`, kiểm trên Chromium headless 1280×720. Bản ghép thử dùng `main` `c3dcd80`, lát cá `db3c462`, lát Shop/DayState `71f5ada` và các fixture số chuẩn v1.1. Manifest và bộ kiểm tra cấu hình chính thức của lát C vẫn cần được tích hợp.

| Kiểm tra | Kết quả quan sát |
|---|---|
| Menu, DayIntro, EveningIntro | Nút Chơi và Thoát hoạt động. DayIntro chuyển sau khoảng 4 giây hoặc khi nhấn phím. EveningIntro lọc món theo kho và kế hoạch. Đã kiểm thêm ở chiều rộng 320 px. [Menu](menu.png) |
| HUD sáng và tối | Cảnh báo giờ/oxy/kiên nhẫn, giỏ và mục tiêu, 2 bếp/4 bàn, kho trừ phần giữ chỗ, chữ sans-serif 18 px. [HUD sáng](hud-gather.png), [HUD tối](hud-quan.png), [cảnh báo với snapshot giả](gather-warning-mock.png) |
| Pause | Đã kiểm Esc/P, Tiếp tục và màn làm mờ với snapshot `paused` giả. Cần kiểm lại việc dừng tick/timer với lớp bọc lát C, kể cả trong Shop. [Lần kiểm pause thật](#kiểm-chứng-phase-2--lát-u) |
| Vòng 5 ngày trên trình duyệt | Ca thử có kho và hai khách dựng sẵn. Ca đầu thu 72 nghìn, trong đó boa 12 nghìn, uy tín +0,2. Mua oxy cấp 1 và thấy 2.700 tick ở ngày sau. M2 có từ ngày 3. Sau khi đóng Shop ngày 5, Summary hiện tổng thu 560 nghìn, số dư 360 nghìn, uy tín 4, điểm 960, cá lóc nướng trui bán 5 suất. Tổng thu gồm 200 nghìn tiền/earned đầu fixture. [Shop](shop.png), [Summary](summary.png) |
| Tốc độ vẽ cục bộ | Đếm lần Canvas vẽ lại cảnh qua `requestAnimationFrame`, chuẩn hóa bằng `performance.now()`. Chromium headless ghi khoảng 240 FPS ở cả HUD sáng (2,5 s) và tối (1,5 s), tại 1280×720. Cần đo lại trên bản tích hợp bàn giao. |
| DaySim qua runner | Seed 42. Một Ngày chạy 22.200 tick trong khoảng 0,63 s. Ba Ngày chạy 66.600 tick, có M2 từ ngày 3. Mỗi cấu hình chạy hai lần cho JSONL giống từng byte. Lệnh CLI v1.1 của lát C cần kiểm riêng. |

Regression chạy bằng `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`. Bản ghép thử đạt 276/276. Fixture số chuẩn v1.1 đạt 134/134 ca regression P1 và live khi cấp cấu hình trực tiếp cho bộ nạp. Nhánh U lấy riêng với main `c3dcd80` còn 6 ca lỗi đã tái hiện trên main trước thay đổi U. Bản ghép thử đã có bản sửa `3a8be98` của nhóm.
