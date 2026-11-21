# Gói chơi cục bộ

Lệnh đóng gói nhận một commit hoặc một ref Git có ở máy, giải nó thành mã commit đầy đủ rồi tạo ZIP từ cây Git của commit đó. Lệnh kiểm CRC, mã commit nhúng trong phần chú thích ZIP, hướng dẫn chạy, tệp giấy phép của dự án và Three.js, cùng tài nguyên 3D và giao diện đi kèm. Khi thành công, lệnh in mã nguồn bàn giao và SHA-256 của gói.

```sh
python3 tools/package_release.py HEAD --out ../ChoNoi-v1.0.0.zip
```

Giải nén và chạy trên máy có Python 3.11+ cùng trình duyệt có WebGL 2.

```sh
unzip ../ChoNoi-v1.0.0.zip -d /tmp/chonoi-release
cd /tmp/chonoi-release/cho-noi
python3 -m chonoi.live --mode day --seed 42 --scenario docs/proof/phase-4/demo-day.json
```

Smoke dùng một Ngày có sẵn ba nguyên liệu trong giỏ, bắt đầu ở bến, cho ca tối ngắn và cấp tiền thử nâng cấp. Trong Chrome, nhấn **Bắt đầu chơi**, **Bắt đầu lặn**, **E** tại bến, **Mở quán**, **Ghé tiệm**, mua bình oxy rồi **Đóng tiệm**. Qua Ngày 2, kiểm `active_upgrades.oxygen`, sức chứa oxy, số dư và nguyên liệu đã thực sự bàn giao. Chạy lại cùng kịch bản trên một clone sạch ở đúng commit và thư mục giải nén từ ZIP. Bản đóng gói khởi động trực tiếp bằng Python và sử dụng các tệp JavaScript trong ZIP.

## Kết quả smoke review PR #32

Commit đóng gói và kiểm thử `219647cb85ac5dfa0b51734784339bad227dae3c`. Clone mới bằng `git clone --no-local` có worktree sạch. Gói `ChoNoi-v1.0.0.zip` chứa đúng commit này, CRC đạt và có SHA-256 `e32d0a7deab8b75aa00f078044dfff20d56965a9ba8058e33bf0d3a352973126`.

Trên Linux x86-64, Python 3.12.3 và Chrome 148.0.7778.215, Playwright mở hai máy chủ riêng bằng `python3 -m chonoi.live --mode day --seed 42 --port 0 --scenario docs/proof/phase-4/demo-day.json`. Một máy chủ chạy từ clone sạch. Máy chủ còn lại chạy từ thư mục ZIP đã giải nén.

| Kiểm trên Chrome | Clone sạch | ZIP giải nén |
|---|---|---|
| Mở trang và tải cả hai module Three.js cục bộ | HTTP 200, cảnh 3D | HTTP 200, cảnh 3D |
| Cập bến rồi mở Quán | I1, I2, I3 khớp cả loại và độ tươi với `gather_end` tại tick 0 của Quán | Cùng kết quả |
| Ghé tiệm, mua bình oxy và đóng tiệm | Sang Ngày 2, oxy cấp 1 với 2.700 tick, số dư 100 và tổng thu 300 | Cùng kết quả |
| Lỗi JavaScript trên trang | 0 | 0 |

Kết quả unit test, smoke headless và soak nằm trong [regression.txt](regression.txt).
