# Kiểm chứng Phase 4 · v1.0.0

Các mã AC dưới đây được đánh số theo TICKET-04 để tra bằng chứng của bản tích hợp.

| AC | Kết quả kiểm | Bằng chứng |
|---|---|---|
| AC-P4-01 | Benchmark mở cảnh lặn thật ở 1280×720, làm nóng 3 giây, đo 30 giây; file có đủ năm trường | [JSON](../proof/phase-4/bench.json) · [cấu hình máy và phương pháp](../proof/phase-4/bench.md) · [lần chạy lại trên Linux](../proof/phase-4/regression.txt) |
| AC-P4-02 | Bật tương phản cao qua Sổ tay; Chrome hiển thị đồng thời thủy quái và oxy ở ca sáng, bàn T1 sắp giận ở ca quán | [Sáng](../proof/phase-4/warning-gather.jpg) · [Tối](../proof/phase-4/warning-quan.jpg) · [fixture sáng](../proof/phase-4/alerts-gather.json) · [fixture tối](../proof/phase-4/alerts-quan.json) |
| AC-P4-03 | Map, hướng dẫn, điều khiển, tạm dừng và tiếp tục bằng phím hay nút | [Trang đầu](../proof/phase-4/lobby.jpg) · [Sổ tay](../proof/phase-4/atlas.jpg) · [điện thoại](../proof/phase-4/mobile.jpg) |
| AC-P4-04 | Soak 10 Ngày, kiểm kết quả chơi hai lượt seed 7, số Ngày và id xuyên suốt | [JSON](../proof/phase-4/soak.json) · [cách kiểm](../proof/phase-4/soak.md) · `tests/test_p4_soak.py` |
| AC-P4-05 | Chrome chạy qua Lặn, Quán và Shop từ clone sạch và ZIP giải nén của cùng commit | [Đóng gói và demo chuyển Ngày](../proof/phase-4/package.md) · [release notes](../release-v1.0.0.md) · [credits](../../CREDITS.md) |
| AC-P4-06 | Regression các phase trước, manifest v1.3 và kiểm đầu vào sai kiểu qua CLI | [Lần chạy tích hợp](../proof/phase-4/regression.txt) · [script smoke kho](../proof/phase-3/smoke.py) |
| AC-P4-07 | Rà hành động retro và tài liệu do thành viên viết | [Retro](../retro.md) · [phản tư](../members/) · [lịch sử sử dụng AI](../ai-usage-log.md) |
| AC-P4-08 | Mốc phát hành và tag được đối chiếu với fork chung. Integrator phụ trách theo TEAM.md | [Phân công](../../TEAM.md) · [lịch sử release của fork](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/releases) |
| AC-P4-09 | Mở rộng `leaderboard`: top 10 bền vững, hòa giữ thứ tự ghi, cặp cờ headless, xuất qua `run_cmd` | [Bằng chứng](../proof/phase-4/extensions.md) · `tests/test_p4_leaderboard.py` |
| AC-P4-10 | Mở rộng phụ đề SFX trong Sổ tay → Điều khiển; đã chơi thử với âm thanh tắt: phụ đề hiện đúng khi hái đồ | [Bằng chứng](../proof/phase-4/extensions.md) |
| AC-P4-11 | Demo sau giờ build: chơi lại một Ngày từ Lặn & Hái qua Mở Quán đến đóng Shop, chạy test, mở ma trận truy vết | Do HoangHongNgo xác nhận đã chơi lại. Chưa lưu video hoặc ảnh; bằng chứng chạy được dùng [gói và demo chuyển Ngày](../proof/phase-4/package.md) |

Để lặp lại hai tình huống cảnh báo, chạy `python3 -m chonoi.live --mode gather --scenario docs/proof/phase-4/alerts-gather.json` hoặc `python3 -m chonoi.live --mode quan --scenario docs/proof/phase-4/alerts-quan.json`. Từ bến, mở bản đồ → Điều khiển → Tương phản cao, quay lại và vào chơi.
