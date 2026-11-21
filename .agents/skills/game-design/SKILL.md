---
name: game-design
description: Thiết kế và cân bằng game cho Quán Ăn Chợ Nổi: vòng chơi lặn - quán - shop, độ khó, độ tươi, cảnh báo và khả năng tiếp cận. Dùng khi thêm cơ chế, chỉnh tuning hoặc thêm giao diện.
---

# game-design — thiết kế game Chợ Nổi

**Vòng chơi lõi:** lặn hái và bắt cá (rủi ro: oxy, Máu, Cá Sấu) → mở quán (nấu, bưng, giữ chỗ, kiên nhẫn khách) → shop (nâng cấp). Mỗi quyết định ở pha trước phải ảnh hưởng pha sau, ví dụ độ tươi của hàng quyết định giá món.

## Nguyên tắc
- **Lựa chọn có đánh đổi:** giỏ đầy nhưng hàng ươn vẫn chiếm chỗ; đi sâu hơn có cá đắt nhưng tốn oxy. Tránh phương án luôn tốt nhất.
- **Số liệu ở một nơi:** mọi hằng số cân bằng nằm trong `game.contract.json` (`tuning`). Đổi số thì đổi ở đó, không hard-code trong luật.
- **Cân bằng bằng đo:** chạy `python3 -m tools.soak --seed 7 --days 10 --out soak.json` và so tiền, uy tín qua các Ngày. Một cơ chế mới không được làm kết quả tất định đổi ngoài phạm vi đã ghi.
- **Phản hồi rõ:** mỗi sự kiện quan trọng có chữ hoặc biểu tượng, không chỉ màu hoặc âm thanh. Thủy quái gần, oxy sắp hết và khách sắp giận phải nhận ra được ở chế độ tương phản cao.
- **Tiếp cận:** có phụ đề SFX, chơi được bằng bàn phím và cảm ứng, không bắt phản xạ dưới ngưỡng hợp lý.
- **Sáng tạo thêm thì tắt được ở headless** và ghi vào mục "Sáng tạo của nhóm" trong `README.md`.

## Trước khi thêm cơ chế
Viết ba dòng: người chơi chọn gì, đánh đổi gì, đo bằng gì. Thiếu một dòng thì chưa nên làm.
