# Nguyễn Minh Phương — minhphuong150505

- **Đóng góp.** Tôi làm lịch khách, giữ nguyên liệu và kiên nhẫn ở [Phase 1](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/pull/3), rồi mở rộng vận hành quán và đóng ca ở [Phase 2](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/pull/14). Sang [Phase 3](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/pull/23), tôi chuyển sang kho cá thể, xử lý ươn và chốt giá theo độ tươi.
- **Bàn giao.** Tôi hỗ trợ lát Day của phuthaitran qua `validate_quan_against_inventory`, dùng để đối chiếu khách, phần giữ chỗ và kế hoạch với kho nhận từ Lặn. [PR Phase 4](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/pull/31) bổ sung kiểm tra ID, độ tươi và kiểm thử tương thích.
- **AI sai ở đâu.** Code từng gọi `.items()` trên danh sách ID giữ chỗ. Tôi tái hiện lỗi với fixture kho cá thể và bổ sung [kiểm thử hồi quy](../../tests/test_p3_quan.py).
- **Bài học.** Kiểm tra lại khi hai pha bàn giao kho. Khẳng định cả nguyên liệu tiêu thụ trong sự kiện và trạng thái kho sau tương tác để bắt lỗi lọt qua kiểm tra đầu vào.
