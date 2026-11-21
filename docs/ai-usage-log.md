# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | ChuTungDuongg | Codex | Đối chiếu PRD-0 và mã starter, triển khai oxy/ngạt/ngất, viết 10 ca headless và chạy toàn bộ suite. | Chưa đo token và chi phí. | Các ca mới về oxy và ngạt thất bại trước khi có logic tương ứng. Sau triển khai, 42/42 test đạt. Payload `oxygen_empty` dùng `{"oxygen_ticks":0}` theo PRD-0 mục E để xử lý khác biệt với giả định trong tài liệu repo. |
