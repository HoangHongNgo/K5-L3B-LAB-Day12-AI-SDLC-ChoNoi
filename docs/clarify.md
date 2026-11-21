# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 P1 0:10 | Chọn món "đều theo seed" dùng stream nào của `Streams`, và rút một số mỗi lần khách đến hay chỉ khi có ≥ 2 món đủ kho? | Giả định: stream riêng tên `customers`, rút `randrange(len(ứng viên))` mỗi lần có khách đến và có ≥ 1 món đủ kho (danh sách ứng viên sắp id món theo Unicode). Chờ Anh Năm xác nhận. | PO (tạm) |
| 2 | 2026-11-21 P1 0:10 | `data` của `oxygen_empty`, `gather`, `fish_caught`, `customer_arrived`, `no_dish` gồm những trường nào? PRD-0 mục E chỉ nêu rõ `dive/surface`, `choke`, `faint`, `hold_full`, `cook_started`. | Giả định theo `docs/contracts/README.md` mục 2 (đánh dấu [giả định]). Có câu trả lời thì sửa hợp đồng và báo lát 1–4. **Cập nhật:** PRD-0 mục E có nêu: `gather` {node_id,kind,amount}, `fish_caught` {fish_id,kind,yield}, `oxygen_empty` {oxygen_ticks:0}, `customer_arrived` {order_id,table_id,dish_id}, `no_dish` {}. Lát 2 đã đổi `count` → `amount`/`yield`; lát 1, 3, 4 đã khớp. | PO (tạm) → PRD-0 mục E |
| 3 | 2026-11-21 P1 0:10 | Bước cuối ca quán: xử lý khách mới / interact / kiên nhẫn trước rồi mới trả `closing`, hay `time_left_ticks` về 0 là chốt ca ngay đầu bước? Một khách vừa hết kiên nhẫn đúng tick hết ca thì rời `patience` hay `closing`? | Giả định: chạy đủ bước bình thường, cuối bước mới xử lý `closing` rồi `quan_end`; hết kiên nhẫn cùng tick → `patience` (trừ uy tín). Chờ Anh Năm xác nhận. | PO (tạm) |
| 4 | 2026-11-21 P1 0:55 | Trạng thái câu 1–3 cuối Phase 1? | Chưa có trả lời từ Anh Năm; lát 3 đã dùng giả định câu 1 (chọn món qua `Streams`), lát 4 chưa gộp nên câu 3 vẫn mở. Mang sang Phase 2. | PO |
| 5 | 2026-11-21 P2 0:05 | `fish_initial` v1.1 là số 8: 8 đàn ở "8 điểm khác nhau" chọn thế nào (36 cặp loài–vị trí, 30 vị trí hình học khác nhau)? Chọn theo seed hay cố định? Loài và hướng đầu ca lấy từ stream nào? | Chưa có trả lời. Lát A (haiquanng) tạm chọn theo seed qua `Streams`, mỗi vị trí hình học dùng tối đa một lần; ghi quyết định vào đây khi làm. Trong lúc chờ, gather mặc định chưa có cá đầu ca (TODO(lát A) ở `gather.py`). | PO (tạm) / lát A |
| 6 | 2026-11-21 P2 0:05 | Dạng `day.day_plan` trong scenario: mảng hay map theo Ngày? Ticket chỉ nói "ghi đè theo số Ngày, mỗi mục có `dishes`". | Giả định: mảng `[{"day":N,"dishes":{…},"ingredients":{…}?}]` cùng dạng `tuning.day_plan`; `ingredients` tính lại từ `dishes`, nếu khai thì phải khớp, sai → mã 2. Ngày không khai giữ preset. | PO (tạm) |
| 7 | 2026-11-21 P2 0:05 | `day.upgrades` ở scenario có hiệu lực ngay Ngày 1 không? Ticket: "chỉ khi dựng Ngày mới mới sao cấp đã mua sang `active_upgrades`". | Giả định: dựng Ngày 1 cũng là "dựng Ngày mới" nên `upgrades` khai trong scenario sao sang `active_upgrades` ngay Ngày 1 (cấp đầu kỳ). Lát S/D theo giả định này; `scenario.py` kiểm `gather.player.oxygen_ticks`/`hp` theo `day.upgrades`. | PO (tạm) |
| 8 | 2026-11-21 P2 0:05 | `pause` khi sim đã `done` (cùng bước với `gather_end`)? Và `pause` ở bước đổi pha trong `day`? | Giả định: sim đã `done` thì bỏ qua cạnh `pause` (runner dừng). Pause bọc cả `DaySim` nên đổi pha bên trong day không đổi trạng thái pause; cạnh `pause` vẫn xét trước mọi pha (kể cả Shop). | PO (tạm) |
| 9 | 2026-11-21 P2 0:05 | `buy` hợp lệ ngoài Shop (trong gather/quan) hay đã tính "sai pha, bỏ qua"? Có làm lệnh `buy` rỗng/không phải chuỗi thành mã 2 không? | Giả định theo ticket 4.2: `buy` đúng kiểu (chuỗi khác rỗng) nhưng sai pha thì bỏ qua; rỗng/không phải chuỗi → mã 2 ngay lúc nạp inputs. | PO (tạm) |
| 10 | 2026-11-21 P2 0:05 | Ticket không đánh số AC-P2-xx dù nhắc tới. | Nhóm tự đặt AC-P2-01..19 ở phụ lục `docs/plan/phase-2.md`, dùng làm khóa cho `docs/verification/phase-2.md`. Có bản đánh số chính thức thì đổi theo. | PO (tạm) |

## Quyết định tích hợp TICKET-03 và TICKET-04

Từ v1.2, mọi file kho công khai dùng mảng cá thể; một file đếm cũ cần chuyển từng đơn vị thành một id duy nhất. V1.3 giữ nguyên luật và định dạng này. Giỏ dùng thứ tự nhặt để bỏ LIFO; lúc xuất file mới sắp theo id. Adapter tách hiển thị số thập phân khỏi so sánh chính xác ở ngưỡng 30.

| Lát | Tác động | Bằng chứng / người phụ trách theo TEAM.md |
|---|---|---|
| Adapter và Lặn | inventory, runner, gather, JSONL và fixture cũ | haiquanng, ChuTungDuongg; smoke hai tiến trình, test LIFO |
| Quán và vòng ngày | scenario, quan, reservations, day và shop | minhphuong150505, phuthaitran; test giữ chỗ, thanh toán, bàn giao |
| HUD và QA | live, web; dữ liệu từng id, cảnh báo, khả năng đọc trên điện thoại | RachalHys; ảnh và kết quả trong docs/proof |
| Tích hợp / phát hành | manifest, regression, tag, gói chạy | HoangHongNgo theo TEAM.md; đối chiếu ma trận Phase 3–4 |

Tích hợp từ main, lấy các commit Quán/vòng ngày/HUD của từng lát, bổ sung adapter và luồng Lặn, rồi chạy smoke cả file lẫn day trước khi nâng lệnh công cụ sang v1.3. Phạm vi mở rộng bàn giao gồm vợt hút cá và khách đặt trước. Điểm bắt đầu và kết thúc phép đo của benchmark ghi tại docs/proof/phase-4/bench.md.

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 11 | 2026-11-21 P4 | `leaderboard`: "lượt chuẩn đủ 5 Ngày" gồm trường hợp nào, và live có ghi bảng không? | Giả định: chỉ `--days 5`, không scenario, `reason:"days_complete"`. Headless ghi qua cặp cờ; live mode `day` cũng ghi khi hết 5 Ngày. Soak không ghi. Hòa điểm giữ thứ tự ghi nhờ sắp ổn định trên file đã sắp. | HoangHongNgo, chưa có xác nhận của giảng viên |
| 12 | 2026-11-21 P4 | Phụ đề SFX khi repo chưa có âm thanh nào? | Giả định: thêm tiếng tổng hợp WebAudio cho các event chính và phụ đề `[tiếng ...]` cho từng tiếng; phụ đề hiện kể cả khi tắt âm thanh. Chỉ client, headless không đổi. | HoangHongNgo |
| 13 | 2026-11-21 P4 | Gắn tag `phase-1..3` sau giờ build vào commit nào? | Giả định: `phase-1` = commit "done phase 1" (`1f0946a`); `phase-2` = merge trước khi giao việc Phase 3 (`526d067`); `phase-3` = merge gồm bàn giao kho cá thể (`e6ed470`). Gắn muộn, ghi rõ trong thông điệp tag. | HoangHongNgo |
