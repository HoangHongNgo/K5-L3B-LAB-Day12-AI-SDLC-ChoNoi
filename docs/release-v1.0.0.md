# Quán Ăn Chợ Nổi v1.0.0

Lặn tìm cá linh và rau để kịp bữa tối, chọn thực đơn theo kho rồi nấu và bưng món đến bàn. Bản này có cảnh chợ nổi 3D, bản đồ theo vị trí, khách đặt trước và độ tươi riêng cho từng nguyên liệu. Giỏ đầy cả khi cá đã ươn. Trên bếp, độ tươi quyết định giá chốt của món.

## Chơi từ gói ZIP

Giải nén, mở terminal trong thư mục chứa `game.contract.json`, chạy `python3 -m chonoi.live --mode day` rồi mở địa chỉ được in ra. Game dùng Python 3.12 và trình duyệt hiện đại. Three.js được đóng gói tại chỗ. WASD hoặc phím mũi tên để di chuyển, E tương tác, Space bắt cá. M mở bản đồ. Bấm Sổ tay → Điều khiển để bật tương phản cao.

## Đo và kiểm

```sh
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
node tools/bench.mjs --seed 42 --duration 30 --out bench.json
python3 -m tools.soak --seed 7 --days 10 --out soak.json
```

Benchmark dùng Node.js 22+ và Chrome/Chromium cài trên máy. Số FPS phụ thuộc GPU, trình duyệt và tải hệ thống. Canvas 2D phục vụ máy thiếu WebGL. File kho đếm từ Phase 1–2 cần chuyển sang schema cá thể trước khi mở quán. Hai phần mở rộng được bật là vợt hút cá và khách đặt trước.
