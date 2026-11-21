# Kiểm chứng Phase 3 — lát U

Nền kiểm là `main` `43f2de4` cùng thay đổi HUD trong PR #29. Chromium dùng snapshot fixture theo TICKET-03 ở 320×600 và 1280×720. Bản live trên `main` dùng manifest v1.1.

| Kiểm tra | Kết quả |
|---|---|
| Giỏ, kho và phần giữ | Cá thể ở đúng 30 vẫn còn tươi. Cá thể dưới 30 hoặc vừa có event `spoiled` hiện nhãn ươn. Quán hiện phần giữ theo bàn, trong khi kho khả dụng và EveningIntro loại hàng ươn và hàng đang giữ. |
| Đơn đặt trước | Gather hiện R1/R2, bàn, món và giờ đến trong ca tối. Quán hiện trạng thái giữ bàn, thời gian còn lại và trạng thái cuối. Tại 320 px, cuộn bảng HUD để đọc các đơn ở cuối danh sách. |
| Dòng lũ | Fixture báo trước 2 giây bằng chữ và biểu tượng. Playwright quan sát một lần phát âm Web Audio sau khi người chơi tương tác. Khi lũ bắt đầu, HUD hiện hướng và đồng hồ dựa trên `ticks_left`. Cảnh báo biến mất khi dòng kết thúc. |
| Regression và HTTP | Suite chạy 378 test, 377 đạt và 1 skip dành cho v1.0. Trình duyệt mở được vòng ngày v1.1 bình thường. Quán thật qua HTTP trả đúng id, độ tươi và cấu hình ngưỡng ươn khi chạy riêng với fixture cá thể. |
| HUD Phase 2 xuyên Phase 3 | Chromium kiểm mục tiêu đã lấy/cần, cảnh báo giờ còn đúng 30 giây, oxy dưới 25%, hết hơi và viền tím thủy quái. Kiểm gợi ý tại mép vùng bến/hái, tiền ca, 2 bếp, 4 bàn và đổi màu kiên nhẫn dưới 25%. |
| Bản ghép thử lát D | Ghép code UI vào `853ce1b` của lát D. Với cấu hình fixture, trình duyệt đọc được R1/R2 thật từ DaySim, xem R1 giữ bàn rồi lỡ do thiếu kho. Ca quán riêng có R1 giữ đúng cá thể I1, giữ I2 ươn trong kho và hiển thị đúng HUD. 22 test Day, reservations và live đều đạt. [Ảnh quán chạy với lát D](hud-quan-day-candidate.png) |

- HUD sáng có cảnh báo lũ. [1280×720](hud-gather-1280.png) · [320×600](hud-gather-320.png)
- HUD quán với kho cá thể, phần giữ và đơn đặt trước. [1280×720](hud-quan-1280.png) · [320×600](hud-quan-320.png)
- Test và fixture bị ảnh hưởng theo từng lát. [Rà regression](regression.md)

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode day --seed 42
```

Trên bản ghép lát D, chạy `PYTHONPATH=tests:. python3 -m unittest test_p3_day test_p3_reservations test_live -v`.

Kiểm live trọn vòng v1.2, regression trên manifest v1.2 chính thức và ảnh khớp commit bàn giao cần thực hiện sau khi các lát Contract, Gather/current và Day/reservations đã tích hợp.
