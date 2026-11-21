# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | ChuTungDuongg | Codex | Đối chiếu PRD-0 và mã starter, triển khai oxy/ngạt/ngất, viết 12 ca headless và chạy toàn bộ suite. | Chưa đo token và chi phí. | Ca nổi lên đầu tiên bỏ sót tình huống chạm đúng ngưỡng. Rà soát phát hiện sai số tích lũy độ sâu có thể gây ngạt nhầm. Sau khi sửa và thêm hai ca sát ngưỡng, 44/44 test đạt. |
| Phase 1 | minhphuong150505 | Antigravity / Gemini 3.8 Flash | Triển khai Lát 3: scenario validation, customer model, reservation, arrival schedule, RNG dish selection, patience countdown, unit tests | Không đo được | Lỗi xử lý dict `c.get("reserved", {})` trả về `None` khi key tồn tại với value `None` gây `AttributeError`; phát hiện qua test runner và sửa thành `c.get("reserved") or {}`. |
