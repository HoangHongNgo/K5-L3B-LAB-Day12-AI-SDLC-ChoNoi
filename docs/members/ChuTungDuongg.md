# ChuTungDuongg — phản tư cá nhân

- **Phần thực hiện** — Oxy theo độ sâu cuối bước, sự kiện lặn/nổi, ngạt và mất giỏ LIFO khi ngất. Bằng chứng nằm trong các commit [oxy](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/51cde51ad15dcda5076e115623a8bb0ddcce8e48), [ngạt và ngất](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/3b0c59ed557fb44fdba46273e8ba60fe9f4cfcf1) và [test](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/8f2d46224897d1a865521cb0dc06fcd360687834).
- **Phần rà soát** — Phiên Codex đối chiếu AC-P1-02/03 với JSONL và file kho thực tế. Suite chạy trên Windows với Python 3.13.9, đạt 42/42 test. Chưa có review của đồng đội tại thời điểm ghi.
- **Sai khác phát hiện khi dùng AI** — Khi đối chiếu hai tài liệu, Codex thấy giả định `oxygen_empty` trong repo thiếu trường `oxygen_ticks` mà PRD-0 mục E quy định. Ca test kiểm cả payload ở đúng tick chuyển từ oxy dương về 0.
- **Điều rút ra** — Việc đếm cả bước oxy vừa cạn quyết định mốc `t+59`. Fixture nổi lên ở chính bước đó giúp kiểm tra thứ tự di chuyển, hồi oxy và ngạt.
