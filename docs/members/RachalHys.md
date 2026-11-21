# RachalHys — phản tư cá nhân

- Tôi hoàn thiện HUD hai buổi, README và test ca biên khi cập bến hoặc chạm giới hạn tick. [HUD sáng](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/0d2a033) · [HUD tối](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/7f887c9) · [README](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/fd042dc) · [Test](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/513b7f6)
- Tôi rà test của bốn lát, chạy lại smoke chuyển kho và ghi kết quả 12 AC theo revision đã kiểm. [Ma trận và bằng chứng](../verification/phase-1.md)
- AI chỉnh HUD sáng lần đầu vẫn để log sự kiện che ô giỏ. Tôi phát hiện ở ảnh Chromium 320 px, dời log và đối chiếu lại với snapshot khi hái, bắt cá và ngất.
- Tôi học được rằng test xanh có thể vẫn bỏ sót schema event. Ca hái đã qua test của repo nhưng JSONL dùng `count`, trong khi Test Contract yêu cầu `amount`.
