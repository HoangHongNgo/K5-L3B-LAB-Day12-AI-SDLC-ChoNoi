# Benchmark có render · Cảnh lặn

Ngày 21/11/2026, bản chơi sáng chạy trên macOS 15.5 (24F74), Apple M4, RAM 16 GiB. Chrome 157.0.8103.80 chạy ở chế độ headless mới, dùng WebGL 2 qua ANGLE Metal trên GPU Apple M4. Node 22.17.1 và Python 3.12.10 chạy runner và máy chủ cục bộ.

| Chỉ số | Kết quả | Mốc TICKET-04 |
|---|---:|---:|
| FPS trung bình | 60,002 | ≥ 60 |
| 1% low | 59,524 FPS | ≥ 30 |
| Tải cảnh lần đầu | 575 ms | ≤ 10.000 ms |
| Thời gian đo thực | 30,0155 s | 30 s |
| Khung trong khoảng đo | 1.801 | |

Từ thư mục gốc của repo, cần Node 22+, Python 3 và Chrome/Chromium có WebGL 2. Có thể đặt `CHROME_BIN` thành đường dẫn tuyệt đối đến trình duyệt, hoặc `PYTHON` thành đường dẫn đến Python. Các tài nguyên của game và Three.js đều đi qua máy chủ loopback.

```sh
node tools/bench.mjs --seed 42 --duration 30 --out bench.json
```

Runner mở một hồ sơ Chrome tạm, đặt canvas đúng 1280×720 với tỉ lệ điểm ảnh 1 và vào ca sáng bằng API của game. Út Sen đứng ở bến. Cá, cá sấu, độ tươi, HUD, bản đồ và hiệu ứng chạy theo dữ liệu và mô phỏng của game.

Mỗi lần cảnh 3D thật gửi lệnh vẽ, runner lấy dấu thời gian của khung hình từ đồng hồ hoạt ảnh của trang. `load_ms` tính từ lúc tiến trình Node khởi động đến khi trình duyệt hoàn thành callback vẽ cảnh đầu tiên. Sau 3 giây làm nóng, runner tính FPS trung bình bằng số khoảng khung chia thời gian thực. Với 1% low, runner lấy `ceil(frames × 0.01)` khoảng dài nhất và tính nghịch đảo của thời gian trung bình. Số gốc giữ nguyên trong [bench.json](bench.json).

Phép đo phản ánh tốc độ trình duyệt gửi khung vẽ trong một phiên Chrome cục bộ. Độ trễ màn hình vật lý, tốc độ trên điện thoại và tốc độ dùng bộ dựng phần mềm cần được đo riêng. Chrome cài trên Linux có thể chọn SwiftShader khi thiếu GPU. Thời lượng yêu cầu phải nằm trong ca sáng.
