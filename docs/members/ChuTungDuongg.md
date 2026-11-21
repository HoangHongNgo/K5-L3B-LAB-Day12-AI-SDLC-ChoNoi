# ChuTungDuongg — phản tư cá nhân

- **Phase 1, Lát B** — Oxy theo độ sâu, sự kiện lặn/nổi, ngạt và mất giỏ LIFO khi ngất. Commit: [oxy](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/51cde51ad15dcda5076e115623a8bb0ddcce8e48), [ngạt và ngất](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/3b0c59ed557fb44fdba46273e8ba60fe9f4cfcf1), [test](https://github.com/HoangHongNgo/K5-L3B-LAB-Day12-AI-SDLC-ChoNoi/commit/8f2d46224897d1a865521cb0dc06fcd360687834).
- **Phase 2** — Cá Sấu tuần tra, truy đuổi, va chạm làm mất Máu và rơi hàng, bất tử, recoil. Smoke hai tiến trình xác nhận `choke → monster_hit → faint → gather_end` cùng tick, và hai lượt cùng seed giống từng byte.
- **Phase 3** — Thứ tự vào giỏ quyết định cá thể rơi; hàng ươn vẫn chiếm ô; `faint` đặt ngay trước `gather_end`. Fixture giỏ cá thể kiểm các ca này và kho rỗng `{"items":[]}`.
- **AI sai ở đâu** — Ca nổi ban đầu bỏ sót việc chạm đúng `0.5 m`, gây ngạt nhầm. Tôi tái hiện bằng test, sửa phép cộng độ sâu và thêm hai ca sát ngưỡng.
- **Bài học** — Luôn kiểm cả tọa độ chạm ngưỡng lẫn tọa độ vừa vượt ngưỡng, vì snapshot làm tròn có thể che sai phân loại.
