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
