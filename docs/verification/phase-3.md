# Kiểm chứng Phase 3 · Mùa Nước Nổi

Mã AC trong bảng do nhóm đặt theo TICKET-03. Đối chiếu qua điểm vào thật của CLI và các test ở mức sim. Có thể chạy lại smoke bằng `python3 docs/proof/phase-3/smoke.py`.

| AC | Hành vi | Bằng chứng |
|---|---|---|
| AC-P3-01 | Kho cá thể, id duy nhất, kiểm kind, miền fresh, từ chối kho đếm | `tests/test_p3_quan.py` và [kết quả CLI, mã 2](../proof/phase-3/handoff.json) |
| AC-P3-02 | Không sửa đích trước gather_end; bàn giao cùng tick, quán chưa hao thêm | [Hai tiến trình và day](../proof/phase-3/handoff.json), `tests/test_p3_day.py` |
| AC-P3-03 | Từ fresh 30 qua ngưỡng tại tick 1, hàng ươn chiếm ô, ngất và LIFO | [Event của runner](../proof/phase-3/handoff.json), `tests/test_p3_gather_lifo.py` |
| AC-P3-04 | Giữ theo id, giữ lại đúng một lần, giá lúc nấu, boa và thanh toán | `tests/test_p3_quan.py`, các lớp ReReservationOnSpoilage và FreshnessPricingAndPayment |
| AC-P3-05 | HUD độ tươi, phân biệt hàng ươn, giỏ/kho và đơn giữ | [Ảnh và fixture của Rachal](../proof/phase-3/ui/README.md); Sổ tay → Nhiệm vụ cho biết độ tươi từng id |
| AC-P3-06 | Vợt hút cá và khách đặt trước | `tests/test_p2_net.py`, `tests/test_p3_reservations.py` |
| AC-P3-07 | Quyết định migration, hồi quy và tình trạng bàn giao | [Quyết định schema](../clarify.md), [changelog](../../CHANGELOG.md), [regression](../proof/phase-3/regression.txt) |

Thư mục bằng chứng chứa kết quả trên bản tích hợp. Việc chấm mốc giờ và đối chiếu tag trên main căn cứ vào lịch sử của fork.
