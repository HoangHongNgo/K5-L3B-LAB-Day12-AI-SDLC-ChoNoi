# Nguyễn Đức Khương Lam — RachalHys

- **Đóng góp.** Phase 1, tôi làm HUD hai ca, lập ma trận 12 AC và chơi thử quán từ lúc nấu đến khi nhận tiền. Phase 2, tôi làm menu, pause, Shop và HUD vòng ngày. Phase 3, tôi thêm hiển thị độ tươi, đơn đặt trước và kiểm khi chuyển từ Lặn sang Quán. [Phase 1](../verification/phase-1.md) · [Phase 2](../verification/phase-2.md) · [Phase 3](../proof/phase-3/qa-recheck/README.md)
- **Hỗ trợ.** Tôi tổng hợp ảnh HUD, smoke bàn giao kho và log hồi quy để HoangHongNgo đối chiếu bản tích hợp. [Kết quả v1.1](../proof/phase-2/qa-recheck.md)
- **Lỗi AI.** Bản HUD đầu để log sự kiện che giỏ. Tôi thấy lỗi khi chụp Chromium ở chiều rộng 320 px, dời log rồi thử lại ở cả hai kích thước màn hình.
- **Bài học.** Tôi kiểm cùng dữ liệu trên headless và trong trình duyệt để đối chiếu từ snapshot đến HUD, nhất là khi chuyển pha.
