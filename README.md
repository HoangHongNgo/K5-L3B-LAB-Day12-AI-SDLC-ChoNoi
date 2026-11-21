# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

Trên macOS hoặc Linux, dùng Git và Python 3 (CI dùng Python 3.12). Game dùng thư viện chuẩn. Chạy ba lệnh sau rồi mở địa chỉ in ra để chơi vòng ngày.

```bash
git clone https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi.git
cd K5-L3B-LAB-Day12-AI-SDLC-ChoNoi
python3 -m chonoi.live --mode day
```

Để chơi hai ca riêng, chạy `python3 -m chonoi.live --mode gather --inventory-out kho.json`. Khi ca sáng kết thúc, dừng bằng `Ctrl+C` rồi chạy `python3 -m chonoi.live --mode quan --inventory kho.json`. Có thể dùng `docs/contracts/inventory.sample.json` để mở quán với kho mẫu.

- **Điều khiển** — `WASD` hoặc phím mũi tên để bơi và đi, `E` để hái, cập bến hoặc tương tác với bếp và bàn, `Space` để bắt cá dưới nước. Trong vòng ngày, dùng `Esc` hoặc `P` để tạm dừng và tiếp tục. Trong ca riêng, dùng `R` để chơi lại.
- **Tính điểm** — `điểm = earned + 100 × floor(uy tín)`, với `earned` là tổng thu trong lượt. Tiền tính bằng nghìn đồng.

Chạy toàn bộ test bằng một lệnh.

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

Chấm tự động qua chế độ **headless** của Test Contract. Chi tiết lệnh và starter xem trong [hướng dẫn kỹ thuật](docs/STARTER.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Mở rộng đã làm

### `net` — Vợt hút cá (haiquanng)

Mua trong Shop (`buy: "net"`), có hiệu lực từ Ngày kế. Cấp 1 giá 250: bán kính 4.0 m, tối đa 2 đàn mỗi lần `catch`. Cấp 2 giá 500: 6.0 m, tối đa 3 đàn. Từ cấp 1, duyệt đàn trong bán kính theo id và bắt tới đủ số đàn; đàn thiếu chỗ phát `hold_full`, được giữ lại và xét đàn kế; chỉ đặt hồi bắt khi có ít nhất một đàn bắt thành công. Cấp 0 dùng luật lõi (đàn gần nhất).

- Luật: `chonoi/sim/gather.py` (`_try_net`), giá và cấp đọc từ `shop.upgrades.net`.
- Bằng chứng: `PYTHONPATH=tests:. python3 -m unittest tests.test_p2_net -v` (9 ca: theo id, đúng mép bán kính, `hold_full` rồi xét đàn kế, không bắt được thì không hồi, cấp 2, cấp 0 giữ luật lõi, mua 2 cấp trong Shop).
- Lõi không đổi: không có `net` trong `active_upgrades` hoặc contract chưa khai `shop.upgrades.net` thì dùng luật lõi; toàn bộ test Phase 1 vẫn xanh.
- Cần thêm vào `game.contract.json` khi lên v1.1 (PO): `"extensions": ["net"]` ở gốc và `shop.upgrades.net` = `[{"level":1,"price":250,"catch_radius":4.0,"max_schools":2},{"level":2,"price":500,"catch_radius":6.0,"max_schools":3}]`.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
