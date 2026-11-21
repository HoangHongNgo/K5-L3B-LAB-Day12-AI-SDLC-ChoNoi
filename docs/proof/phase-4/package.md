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
