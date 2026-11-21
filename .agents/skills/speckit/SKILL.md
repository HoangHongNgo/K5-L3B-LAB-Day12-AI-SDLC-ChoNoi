---
name: speckit
description: Quy trình phát triển theo đặc tả (Spec Kit) cho một lát việc của ChoNoi: hiến pháp, specify, clarify, plan, tasks, implement, kiểm. Dùng khi nhận ticket hoặc PRD mới và trước khi viết mã.
---

# speckit — làm theo đặc tả

Chạy lần lượt, mỗi bước ghi kết quả vào file nêu bên dưới. Không nhảy sang mã khi bước trước chưa xong.

1. **Hiến pháp** — đọc `AGENTS.md` và `docs/contracts/`. Ghi ra những điều không được vi phạm: số liệu chỉ đọc từ `game.contract.json`, ngẫu nhiên qua `Streams`, không đổi contract khi chưa báo nhóm.
2. **Specify** — từ PRD/ticket đúng phase, viết `docs/plan/phase-N.md` mục "Đặc tả" cho lát của bạn: hành vi, đầu vào, đầu ra, event, ca biên. Mỗi dòng phải kiểm được. Gắn mã AC-Pn-xx.
3. **Clarify** — chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO. Không tự bịa yêu cầu.
4. **Plan** — nêu file sẽ sửa, module chịu ảnh hưởng, cách tắt phần sáng tạo ở headless. Một lát một việc, không đụng file của lát khác.
5. **Tasks** — chia thành việc nhỏ, mỗi việc có test đi kèm. Cập nhật `TASK.md`.
6. **Implement** — viết test trước hoặc cùng lúc. Chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` sau mỗi việc.
7. **Kiểm** — điền `docs/verification/phase-N.md` theo mẫu AC → bằng chứng → kết quả; ghi lệnh và kết quả vào mô tả commit. Cập nhật `docs/ai-usage-log.md`.

Kết thúc bằng việc nói rõ phần nào chưa kiểm. Test xanh không thay cho đối chiếu với đặc tả.
