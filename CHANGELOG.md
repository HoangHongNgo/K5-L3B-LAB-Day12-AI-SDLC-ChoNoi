# Changelog

## Phase 4 · v1.0.0 · contract 1.3

Test Contract v1.3 khai `bench_cmd` để đo cảnh lặn có render và `soak_cmd` để chạy nhiều Ngày. Scenario trả mã 2 khi số lượng nguyên liệu khai trong kế hoạch Ngày sai kiểu hoặc âm. Bản đồ ở màn hình đầu, bản đồ nhỏ trong lúc chơi và Sổ tay hỗ trợ bàn phím lẫn cảm ứng. Ba cảnh báo có chữ, chế độ tương phản cao lưu theo trình duyệt. Gói ZIP chứa mã chạy, Three.js và giấy phép đi kèm.

## Phase 3 · Mùa Nước Nổi · contract 1.2

**Breaking change.** Kho đếm theo loại được thay bằng danh sách cá thể. File kho rỗng là `{"items":[]}`. Mỗi cá thể có id riêng, loại nguyên liệu và độ tươi. Đổi fixture cũ bằng cách tạo một phần tử cho từng đơn vị trong giỏ hoặc kho. Giữ thứ tự nhặt trong giỏ, điền id cá thể vào `customers[].reserved`. File kho đếm trả mã 2.

Giỏ và kho quán hao tươi theo từng bước. Hàng ươn vẫn chiếm chỗ. Bếp giữ từng id, chọn hàng tươi nhất, chốt giá lúc bắt đầu nấu. Quán nhận đúng cá thể vừa cập bến. Bổ sung đơn đặt trước, nhãn độ tươi và danh sách nguyên liệu trong Sổ tay.

Các fixture Phase 1–2 dùng định dạng mới ở những chỗ ticket thay luật kho, giá và payload. Các kiểm tra di chuyển, oxy, tương tác, giới hạn tick và thứ tự event tiếp tục áp dụng.

## Phase 2 · Một ngày ở Chợ Nổi · contract 1.1

Thêm vòng Lặn → Quán → Shop, thực đơn theo Ngày, nâng cấp, cá bơi, thủy quái và vợt hút cá. HUD và menu tạm dừng hiển thị thông tin theo từng ca.

## Phase 1 · Hai ca độc lập

Lặn hái và bắt cá, mở quán, nấu và phục vụ. Hai tiến trình bàn giao kho qua file JSON. Chế độ headless nhận seed, scenario và input để xuất JSONL.
