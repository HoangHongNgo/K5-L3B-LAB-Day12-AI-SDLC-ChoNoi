# Tác động của kho cá thể đến regression P1–P2

Rà trên `43f2de4`, khi manifest vẫn là v1.1. Danh sách này dùng để chuyển fixture và phép kiểm khi tích hợp v1.2.

| Người nhận | File test cần rà | Thay đổi cần đối chiếu |
|---|---|---|
| HoangHongNgo | `test_p1_contract.py`, `test_p2_contract.py`, `test_p2_scenario_day.py` | Tách test xác thực theo phiên bản. Thêm ca v1.2 từ chối kho đếm và scenario có id trùng, id giữ không tồn tại hoặc hàng giữ đã ươn. |
| haiquanng, ChuTungDuongg | `test_smoke_p1.py`, `test_p1_lat1.py`, `test_p1_lat2.py`, `test_p2_monster.py`, `test_p2_net.py`, `test_p2_fish.py` | Đổi fixture `hold` và kiểm `lost`, `inventory.items` theo id, loại, độ tươi và thứ tự LIFO. Kho rỗng v1.2 là mảng. Giữ các phép kiểm oxy, cooldown, tick cuối và giới hạn tick. |
| minhphuong150505 | `test_p1_lat3.py`, `test_p1_lat4.py`, `test_p1_prd_fixture.py`, `test_p2_quan.py`, `fixtures/quan_one_customer.json` | Đổi `stock` sang cá thể và `reserved` sang danh sách id. Kiểm `cook_started.items` theo kind/id, giá món và boa theo tươi lúc nấu. Giữ phép kiểm khách đến, phục vụ đúng hạn và đóng ca. |
| phuthaitran, haiquanng | `test_p2_cli_day.py`, `test_p2_day.py`, `test_p2_pause.py`, `test_p2_progress.py`, `test_p2_shop.py` | So bàn giao kho bằng id và độ tươi. Kiểm kho dư trong Shop, id xuyên ngày và pause dừng hao tươi. Giữ phép kiểm cấp nâng cấp và thứ tự đổi pha. |
| RachalHys | `test_live.py`, HUD, EveningIntro | UI đọc kho theo schema của bản chạy. Món có thể nấu dựa trên cá thể tươi, còn khả dụng. Test trực quan cả dữ liệu đếm v1.1 và cá thể v1.2. |
