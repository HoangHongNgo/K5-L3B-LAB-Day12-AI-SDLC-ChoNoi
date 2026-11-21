# Nguyễn Đức Khương Lam (RachalHys) — phản tư cá nhân

- **Đóng góp.** Phase 1, tôi làm HUD hai ca, lập ma trận 12 AC và chơi thử quán từ lúc nấu đến khi nhận tiền. Phase 2, tôi làm giao diện menu, pause, Shop và HUD vòng ngày. Phase 3, tôi thêm độ tươi và đơn đặt trước vào HUD rồi kiểm khi chuyển từ Lặn sang Quán. [Ma trận Phase 1](../verification/phase-1.md) · [HUD v1.1](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/fdb79ba0deeedfae3f836eb64fffa032b18ce13d) · [Kiểm HUD v1.2](../proof/phase-3/qa-recheck/README.md)
- **Hỗ trợ.** Tôi tổng hợp ảnh HUD, smoke bàn giao kho và log hồi quy để HoangHongNgo đối chiếu bản tích hợp. [Kết quả v1.1](../proof/phase-2/qa-recheck.md)
- **Lỗi AI.** Trong bản HUD do AI đề xuất, log sự kiện che giỏ. Tôi phát hiện qua ảnh Chromium ở 320 px, dời log lên trên rồi kiểm lại ở 320 và 1024 px. [Bản sửa HUD](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/0d2a0339bc065c0828704c6739862fe65ddd4965)
- **Bài học.** Tôi học được cách đối chiếu snapshot với những gì người chơi thấy trên HUD, nhất là khi chuyển pha và khi màn hình hẹp.
