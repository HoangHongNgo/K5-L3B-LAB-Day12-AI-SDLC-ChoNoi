# Bằng chứng mở rộng Phase 4

Chạy trên nhánh `p4/finish-ticket`, Windows 11, Python 3.13.

## `leaderboard`

- Khai `"leaderboard"` trong `extensions` của `game.contract.json`.
- Mã: `chonoi/leaderboard.py`; cờ ở `chonoi/headless.py` và `chonoi/live.py`.
- Test: `tests/test_p4_leaderboard.py` (6 ca): sắp điểm giảm dần, hòa giữ thứ tự ghi sau khi mở lại file, cắt còn 10, tên Unicode, tên rỗng, store hỏng, đúng một mục cho lượt chuẩn 5 Ngày, không ghi khi `--days` khác 5 hoặc có `--scenario`, thiếu một cờ trong cặp hoặc sai mode trả mã 2, xuất qua `run_cmd --export-leaderboard`.

```
python3 -m chonoi.headless --mode day --seed 42 --days 5 --ticks 400000 --out o.jsonl --leaderboard lb.json --player-name "Út Sen"
python3 -m chonoi.live --mode gather --leaderboard lb.json --export-leaderboard ex.json
{"entries":[{"name":"Út Sen","score":0,"days_completed":5,"seed":42}]}
```

Điểm 0 vì lượt này không có input. File xếp hạng không đổi JSONL. Soak không ghi xếp hạng.

## Phụ đề SFX

- Mã: `chonoi/web/sfx.js`, nút ở Sổ tay → Điều khiển (Âm thanh, Phụ đề âm thanh), lưu theo trình duyệt.
- Các hiệu ứng đã triển khai là tiếng tổng hợp bằng WebAudio, gắn với event của sim: nhặt đồ, bắt cá, cá sấu táp, ngạt, hết oxy, ngất, hàng ươn, nấu, món chín, giao món, trả tiền, khách bỏ đi, khách đặt trước đến, mua nâng cấp.
- Mỗi tiếng hiện một dòng phụ đề dạng `[tiếng ...]` trong 2,5 giây, kể cả khi tắt âm thanh. Client chỉ đọc snapshot nên headless và JSONL không đổi.
- Đã chơi thử trên trình duyệt (21/11/2026, ca lặn Ngày 2) với "Âm thanh" tắt: hái bông điên điển làm dòng `[tiếng nhặt đồ]` hiện cạnh thông báo "+1 điên điển" và tự ẩn sau khoảng 2,5 giây. Chưa thử các tiếng khác và nút "Phụ đề âm thanh".

## Hồi quy

`PYTHONPATH="tests;." python -m unittest discover -s tests` → 438 ca, OK (skipped=1).
