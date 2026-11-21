# RachalHys — phản tư cá nhân

- Tôi hoàn thiện HUD hai buổi, README và test ca biên khi cập bến hoặc chạm giới hạn tick. [HUD sáng](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/0d2a033) · [HUD tối](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/7f887c9) · [README](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/fd042dc) · [Test](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/513b7f6)
- Tôi rà test của bốn lát, chạy lại smoke chuyển kho và ghi kết quả 12 AC theo revision đã kiểm. [Ma trận và bằng chứng](../verification/phase-1.md)
- AI chỉnh HUD sáng lần đầu vẫn để log sự kiện che ô giỏ. Tôi phát hiện ở ảnh Chromium 320 px, dời log và đối chiếu lại với snapshot khi hái, bắt cá và ngất.
- Tôi học được rằng test xanh có thể vẫn bỏ sót schema event. Ca hái đã qua test của repo nhưng JSONL dùng `count`, trong khi Test Contract yêu cầu `amount`.

## Phase 2

- Tôi làm menu và hai màn giới thiệu, HUD v1.1, pause UI, Shop, DayResult và Summary. [Menu và intro](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/3b7b625) · [HUD và vòng ngày](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/fdb79ba)
- Tôi rà regression Phase 1 với số chuẩn mới và chạy năm ngày trên bản ghép thử. Đợt ghép đầu lộ lỗi Ngày 0 và uy tín về 3 trong Shop. Bản ghép lại với commit sửa của lát S chạy đến tổng kết và giữ đúng uy tín xuyên ngày. [Bằng chứng UI](../proof/phase-2/ui/README.md)
- Sau khi gộp lát C, tôi kiểm Esc/P trên trình duyệt ở cả ba pha, kể cả lúc mua nâng cấp trong Shop. Tôi thay ảnh pause mô phỏng bằng ảnh từ bản chạy v1.1 và chạy lại 119 ca regression Phase 1.
- Qua lần này, tôi thấy fixture giúp tách phần giao diện để làm sớm, còn vòng ngày thật cần chạy qua đủ các lần đổi pha để phát hiện lỗi bàn giao.
