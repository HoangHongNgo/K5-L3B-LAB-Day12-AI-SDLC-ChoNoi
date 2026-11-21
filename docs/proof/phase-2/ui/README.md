# Kiểm chứng Phase 2 — lát U

## Bản chơi 3D

Chạy `python3 -m chonoi.live --mode day --port 8012` với preset v1.1. [Menu chợ nổi](3d-river-menu.jpg) · [Quán buổi tối](3d-cafe.jpg)

Trên Chrome, người chơi di chuyển bằng bàn phím và nút cảm ứng. Thử tắt WebGL vẫn chơi được trên Canvas 2D. Trong ca kiểm tra rút ngắn, giỏ bàn giao 2 bông súng và 1 cá lóc, đồng hồ Shop giữ nguyên trong lúc pause, mua bình oxy trừ 200 nghìn và ngày 2 bắt đầu với 2.700 tick oxy. Bộ unittest đã chạy 371 ca, 370 đạt và 1 ca được bỏ qua.

## Bản UI ban đầu

Giao diện ở `fdb79ba`, kiểm trên Chromium headless 1280×720. Bản ghép thử dùng `main` `c3dcd80`, lát cá `db3c462`, lát Shop/DayState `71f5ada` và các fixture số chuẩn v1.1. Manifest và bộ kiểm tra cấu hình chính thức của lát C vẫn cần được tích hợp.

| Kiểm tra | Kết quả quan sát |
|---|---|
| Menu, DayIntro, EveningIntro | Nút Chơi và Thoát hoạt động. DayIntro chuyển sau khoảng 4 giây hoặc khi nhấn phím. EveningIntro lọc món theo kho và kế hoạch. Đã kiểm thêm ở chiều rộng 320 px. [Menu](menu.png) |
| HUD sáng và tối | Cảnh báo giờ/oxy/kiên nhẫn, giỏ và mục tiêu, 2 bếp/4 bàn, kho trừ phần giữ chỗ, chữ sans-serif 18 px. [HUD sáng](hud-gather.png), [HUD tối](hud-quan.png), [cảnh báo với snapshot giả](gather-warning-mock.png) |
| Pause | Đã kiểm Esc/P, Tiếp tục và màn làm mờ với snapshot `paused` giả. Cần kiểm lại việc dừng tick/timer với lớp bọc lát C, kể cả trong Shop. [Ảnh mock](pause-mock.png) |
| Vòng 5 ngày trên trình duyệt | Ca thử có kho và hai khách dựng sẵn. Ca đầu thu 72 nghìn, trong đó boa 12 nghìn, uy tín +0,2. Mua oxy cấp 1 và thấy 2.700 tick ở ngày sau. M2 có từ ngày 3. Sau khi đóng Shop ngày 5, Summary hiện tổng thu 560 nghìn, số dư 360 nghìn, uy tín 4, điểm 960, cá lóc nướng trui bán 5 suất. Tổng thu gồm 200 nghìn tiền/earned đầu fixture. [Shop](shop.png), [Summary](summary.png) |
| Tốc độ vẽ cục bộ | Đếm lần Canvas vẽ lại cảnh qua `requestAnimationFrame`, chuẩn hóa bằng `performance.now()`. Chromium headless ghi khoảng 240 FPS ở cả HUD sáng (2,5 s) và tối (1,5 s), tại 1280×720. Cần đo lại trên bản tích hợp bàn giao. |
| DaySim qua runner | Seed 42. Một Ngày chạy 22.200 tick trong khoảng 0,63 s. Ba Ngày chạy 66.600 tick, có M2 từ ngày 3. Mỗi cấu hình chạy hai lần cho JSONL giống từng byte. Lệnh CLI v1.1 của lát C cần kiểm riêng. |

Regression chạy bằng `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`. Bản ghép thử đạt 276/276. Fixture số chuẩn v1.1 đạt 134/134 ca regression P1 và live khi cấp cấu hình trực tiếp cho bộ nạp. Nhánh U lấy riêng với main `c3dcd80` còn 6 ca lỗi đã tái hiện trên main trước thay đổi U. Bản ghép thử đã có bản sửa `3a8be98` của nhóm.
