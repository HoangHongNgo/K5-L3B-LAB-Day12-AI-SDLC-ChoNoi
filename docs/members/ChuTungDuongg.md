# ChuTungDuongg — phản tư cá nhân

- **Phần thực hiện** — Oxy theo độ sâu cuối bước, sự kiện lặn/nổi, ngạt và mất giỏ LIFO khi ngất. Bằng chứng nằm trong các commit [oxy](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/51cde51ad15dcda5076e115623a8bb0ddcce8e48), [ngạt và ngất](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/3b0c59ed557fb44fdba46273e8ba60fe9f4cfcf1) và [test](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/8f2d46224897d1a865521cb0dc06fcd360687834).
- **Phần rà soát** — Phiên Codex đối chiếu AC-P1-02/03 với JSONL và file kho thực tế. Suite chạy trên Windows với Python 3.13.9, đạt 44/44 test. Chưa có review của đồng đội tại thời điểm ghi.
- **Sai khác phát hiện khi dùng AI** — Ca nổi ban đầu đi qua ngưỡng, bỏ sót việc chạm đúng `0.5 m`. Rà soát tái hiện ngạt nhầm ở điểm này, dẫn đến sửa phép cộng độ sâu và thêm hai ca sát ngưỡng.
- **Điều rút ra** — Việc đếm cả bước oxy vừa cạn quyết định mốc `t+59`. Kiểm cả tọa độ chạm ngưỡng và tọa độ vừa sâu hơn giúp phát hiện sai phân loại mà snapshot làm tròn có thể che khuất.

## Phase 2 — Lát B

- **Phần thực hiện** — Cá Sấu tuần tra và truy đuổi theo tuning, xuất hiện theo Ngày. Va chạm làm mất Máu, rơi hàng LIFO, kích hoạt bất tử và recoil. Gather áp dụng cấp oxy/Máu đang có hiệu lực khi dựng ca.
- **Kiểm chứng** — Smoke hai tiến trình xác nhận `choke → monster_hit → faint → gather_end` trong cùng tick và quán nhận kho rỗng. Hai lượt cùng seed cho JSONL và file kho giống từng byte. Test bổ sung kiểm sát các ngưỡng phát hiện, rời truy đuổi và va chạm bằng tọa độ thập phân.
- **Điều rút ra** — Fixture chỉ còn một tick recoil giúp xác nhận rằng Cá Sấu chưa được gây hit ở bước chuyển về patrol. Fixture cuối ca có cả ngạt và va chạm giúp kiểm tra thứ tự xử lý trước khi xuất kho.

## Phase 3 — Lát B

- **Phần thực hiện** — Dùng thứ tự vào giỏ để chọn cá thể bị mất khi va chạm hoặc ngất. Dùng cùng biểu diễn `id`, `kind`, `fresh` với kho bàn giao. Đặt `faint` sau việc dọn dòng lũ và ngay trước `gather_end`.
- **Kiểm chứng** — Fixture giỏ cá thể kiểm ID không liền nhau, hàng ươn vẫn chiếm ô, ngất do ngạt hoặc do chạm, và runner xuất `{"items":[]}`. Ca va chạm ở bước cuối xác nhận không bắt cá tiếp.
- **Điều rút ra** — Thứ tự giỏ quyết định món nào rơi. Thứ tự id của kho bàn giao chỉ dùng khi xuất.
