# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | ChuTungDuongg | Codex | Đối chiếu PRD-0 và mã starter, triển khai oxy/ngạt/ngất, viết 12 ca headless và chạy toàn bộ suite. | Chưa đo token và chi phí. | Ca nổi lên đầu tiên bỏ sót tình huống chạm đúng ngưỡng. Rà soát phát hiện sai số tích lũy độ sâu có thể gây ngạt nhầm. Sau khi sửa và thêm hai ca sát ngưỡng, 44/44 test đạt. |
| 1 | haiquanng | Claude Code (Claude Opus) | Đọc repo/TASK.md để tách việc độc lập; lập plan lát 2; viết test hộp đen trước (18 ca, quan sát RED), rồi viết `_add_to_hold`, hái, bắt cá; một reviewer AI riêng rà toàn nhánh. | Chưa đo token và chi phí. | Test chạy toàn trình đầu tiên đặt người chơi trong bán kính bến nên bấm E sẽ cập bến thay vì hái — phát hiện khi đối chiếu `dock_radius` trước khi chạy, đã dời điểm xuất phát. Reviewer chỉ ra test hòa id chưa có ca `F10` vs `F2` (để sau). 50/50 test đạt trên nhánh, 62/62 sau khi gộp với lát 1. |
