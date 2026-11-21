# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | minhphuong150505 | Antigravity / Gemini 3.8 Flash | Triển khai Lát 3: scenario validation, customer model, reservation, arrival schedule, RNG dish selection, patience countdown, unit tests | Không đo được | Lỗi xử lý dict `c.get("reserved", {})` trả về `None` khi key tồn tại với value `None` gây `AttributeError`; phát hiện qua test runner và sửa thành `c.get("reserved") or {}`. |
