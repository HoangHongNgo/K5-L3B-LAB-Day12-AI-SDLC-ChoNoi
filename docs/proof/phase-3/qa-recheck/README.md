# Kiểm lại contract v1.2

Chạy trên `6ce2505` trong lịch sử `main`, sau khi tích hợp kho cá thể, HUD và đặt trước. GitHub chưa có tag `phase-3`.

- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` chạy 423 test. 422 đạt, 1 bỏ qua dành cho cá đứng yên của v1.0. [Log](regression.log)
- `python3 docs/proof/phase-3/smoke.py` xác nhận `spoiled` đúng tick 1, file kho giữ đúng độ tươi, quán nhận đúng cá thể qua file và qua Day ở `phase_tick:0`, kho đếm trả mã 2. [Kết quả](handoff.json)
- Chạy `python3 -m chonoi.live --mode day --seed 42 --scenario docs/proof/phase-3/qa-recheck/scenario.json` trên Chromium 1280×720. Chơi từ màn hình đầu, vào ca sáng, bấm E cập bến rồi mở quán. HUD hai ca đều hiện bông súng ươn và đơn R1 ở T2. Quán còn đúng cá thể I2 dưới 30 điểm tươi và R1 ở trạng thái giữ bàn. [Ca sáng](p3-gather.png) · [Ca tối](p3-quan.png)
