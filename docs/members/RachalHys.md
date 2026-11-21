# RachalHys — phản tư cá nhân

- **Phase 1** — HUD hai buổi, README và test ca biên khi cập bến hoặc chạm giới hạn tick. [HUD sáng](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/0d2a033) · [HUD tối](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/7f887c9) · [Test](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/513b7f6) · [Ma trận 12 AC](../verification/phase-1.md)
- **Phase 2** — Menu, màn giới thiệu, HUD v1.1, pause, Shop, DayResult, Summary. [Menu](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/3b7b625) · [HUD](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/fdb79ba) · [Bằng chứng](../proof/phase-2/ui/README.md). Chạy năm ngày trên bản ghép thử, phát hiện lỗi Ngày 0 và uy tín về 3 trong Shop.
- **Phase 3** — HUD độ tươi, đơn đặt trước, cảnh báo lũ. [Kiểm chứng](../proof/phase-3/ui/README.md)
- **Giúp đồng đội** — Rà test của bốn lát và chạy lại regression Phase 1 sau mỗi lần gộp.
- **AI sai ở đâu** — HUD sáng đầu tiên để log che ô giỏ; ca hái qua test nhưng JSONL dùng `count` thay vì `amount`. Tôi phát hiện qua ảnh Chromium 320 px và đối chiếu Test Contract.
- **Bài học** — Test xanh vẫn có thể sai schema; fixture tách được phần giao diện, nhưng vòng ngày thật phải chạy qua đủ các lần đổi pha.
