# Kiểm chứng Phase 3 · Mùa Nước Nổi

Mã AC trong bảng do nhóm đặt theo TICKET-03. Đối chiếu qua điểm vào thật của CLI và các test ở mức sim. Có thể chạy lại smoke bằng `python3 docs/proof/phase-3/smoke.py`.

| AC | Hành vi | Bằng chứng |
|---|---|---|
| AC-P3-01 | Kho cá thể, id duy nhất, kiểm kind, miền fresh, từ chối kho đếm | `tests/test_p3_quan.py` và [kết quả CLI, mã 2](../proof/phase-3/handoff.json) |
| AC-P3-02 | Không sửa đích trước gather_end; bàn giao cùng tick, quán chưa hao thêm | [Hai tiến trình và day](../proof/phase-3/handoff.json), `tests/test_p3_day.py` |
| AC-P3-03 | Từ fresh 30 qua ngưỡng tại tick 1, hàng ươn chiếm ô, ngất và LIFO | [Event của runner](../proof/phase-3/handoff.json), `tests/test_p3_gather_lifo.py` |
| AC-P3-04 | Giữ theo id, giữ lại đúng một lần, giá lúc nấu, boa và thanh toán | `tests/test_p3_quan.py`, các lớp ReReservationOnSpoilage và FreshnessPricingAndPayment |
| AC-P3-05 | HUD độ tươi, phân biệt hàng ươn, giỏ/kho và đơn giữ | **Đạt trên `6ce2505`**. HUD hai ca hiện hàng ươn và R1 ở T2. [Ảnh chạy trên v1.2](../proof/phase-3/qa-recheck/README.md) · [Bằng chứng lát U](../proof/phase-3/ui/README.md) |
| AC-P3-06 | Vợt hút cá và khách đặt trước | `tests/test_p2_net.py`, `tests/test_p3_reservations.py` |
| AC-P3-07 | Quyết định migration, hồi quy và tình trạng bàn giao | [Quyết định schema](../clarify.md), [changelog](../../CHANGELOG.md), [log hồi quy v1.2](../proof/phase-3/qa-recheck/regression.log) |

Kiểm lại trên `6ce2505` trong lịch sử main với contract v1.2. Hồi quy đạt 422 ca, bỏ qua 1 ca dành cho v1.0. Smoke bàn giao và lượt chơi kiểm HUD đều đạt. [Lệnh và kết quả](../proof/phase-3/qa-recheck/README.md). Tag `phase-3` trỏ tới `43f2de4` với manifest v1.1. Bằng chứng v1.2 ở đây thuộc `6ce2505`.
