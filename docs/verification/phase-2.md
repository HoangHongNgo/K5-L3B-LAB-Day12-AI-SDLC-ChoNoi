# Ma trận truy vết Phase 2

Đối chiếu TICKET-02 và Test Contract v1.1 ([`docs/plan/phase-2.md`](../plan/phase-2.md)). Danh sách AC-P2-xx do nhóm suy ra từ ticket (ticket không đánh số), định nghĩa ở phụ lục của file kế hoạch.

> **Trạng thái: KHUNG (phút 2.1).** Cột *Bằng chứng* và *Kết quả* điền ở 2.3 theo lần chạy trên `main` tại commit gắn tag `phase-2`; trước đó mọi dòng là **Chưa kiểm**. Ghi trung thực, không điền "Đạt" khi chưa chạy.

Lệnh test toàn bộ:

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

Quy ước: **Test cần viết** là file test mà lát chịu trách nhiệm; bằng chứng lưu ở `docs/proof/phase-2/` (haiquanng gom), mỗi file ghi commit đã chạy.

| AC | Lát | Cách kiểm chứng (lệnh / test cần có) | Bằng chứng (`docs/proof/phase-2/`) | Kết quả |
|---|---|---|---|---|
| AC-P2-01 | C | `python3 -m unittest tests.test_p2_contract -v` (số chuẩn, 6 nguyên liệu/món, `day_plan.ingredients` = Σ công thức × suất, shop, monsters, sai dải → `BadInput`). Chạy `python3 -m chonoi.headless --mode gather --seed 1 --ticks 0 --out o.jsonl` rồi kiểm mã 0; sửa tay một khóa ngoài dải → mã 2. | _chưa có_ | Chưa kiểm |
| AC-P2-02 | B | `tests/test_p2_monster.py` (oxy 1.800 tick, +6/tick, ngạt tính cả bước chạm 0, ngạt xuyên bất tử, không rơi hàng, Máu cơ sở 3) và regression `tests/test_p1_lat1.py` với số chuẩn. | _chưa có_ | Chưa kiểm |
| AC-P2-03 | A | `tests/test_p2_fish.py` (bơi 1,5 m/s; đổi hướng ở bước 120/240; phản xạ mép và góc; 8 đàn ở 8 điểm khác nhau; catch dùng vị trí trước khi bơi; yield 3/1/2; hái N5/N6 → `keo_neo`). Gỡ skip `test_smoke_p1.test_gather_snapshot_has_gather_fields`. | _chưa có_ | Chưa kiểm |
| AC-P2-04 | A | `tests/test_p2_fish.py` (sinh ở `phase_tick` 360·k sau khi cá bơi; trần 12; clearance > 1 m; trọng số 40/30/30 chuẩn hóa; bỏ lượt khi hết điểm; `fish_spawned`; `random_fish:false` không sinh). | _chưa có_ | Chưa kiểm |
| AC-P2-05 | B | `tests/test_p2_monster.py` (patrol 1,0 m/s đổi waypoint; chase 3,0 m/s khi d ≥ 10 và ≤ 10 m; rời khi > 16 m hoặc d < 10; chặn theo biên và dải độ sâu; M2 chỉ từ Ngày 3). | _chưa có_ | Chưa kiểm |
| AC-P2-06 | B | `tests/test_p2_monster.py` (hit ≤ 1,5 m, bất tử 90 tick, `floor(n/2)` LIFO, 1 hit/bước, recoil 60 bước; Máu 0 → `faint` → `gather_end(fainted)`, kho `{"items":{}}`; thứ tự ngạt → hit → hết giờ; cập bến ưu tiên). | _chưa có_ | Chưa kiểm |
| AC-P2-07 | Q | `tests/test_p2_quan.py` (2 bếp nấu song song, đơn reserved cũ nhất, 4 bàn, lịch `120 + 900·k`, boa/uy tín, đóng ca) + regression `tests/test_p1_lat3.py`, `tests/test_p1_lat4.py`. | _chưa có_ | Chưa kiểm |
| AC-P2-08 | Q | `tests/test_p2_quan.py` (`menu_ids` lọc trước nguyên liệu khả dụng; `no_dish`; khách vẫn gọi món đủ hàng khi đã bán đủ suất; `menu_ids=None` là cả 6 món) và `validate_quan_against_inventory`. | _chưa có_ | Chưa kiểm |
| AC-P2-09 | S | `tests/test_p2_shop.py` (đúng giá vẫn mua; 2 cấp liên tiếp; `max_level`; `funds`; lệnh lạ → `unknown`; buy + `shop_done` cùng bước; tự đóng ở tick 600). | _chưa có_ | Chưa kiểm |
| AC-P2-10 | S | `tests/test_p2_progress.py` (oxygen cấp 1 mua ở Ngày 1 → Ngày 2 có 2.700 tick; hp cấp 2 → 5 Máu; cấp vừa mua chưa hiệu lực trong cùng Ngày; uy tín kẹp [0,5]). | _chưa có_ | Chưa kiểm |
| AC-P2-11 | D, C | `tests/test_p2_day.py` (thứ tự `day_start → day_plan → phase_start(gather) → … → phase_start(quan) → phase_start(shop)`, vỏ event có `day`, `end.days_completed`, `reason:"days_complete"`) và `tests/test_p2_cli_day.py` (`--days 0/6/abc` và `--days` với mode khác → mã 2; mặc định 1). | _chưa có_ | Chưa kiểm |
| AC-P2-12 | C | `python3 -m unittest tests.test_p2_pause -v` (cả 3 mode: `paused`/`resumed`, `sim_tick`/`phase_tick`/timer đứng yên, bỏ qua cạnh hành động và `buy`, giữ nút qua đổi pha không tạo cạnh mới, snapshot `state:"paused"`). | _chưa có_ | Chưa kiểm |
| AC-P2-13 | C | `python3 -m unittest tests.test_p2_scenario_day -v` (cấm `quan.stock`/`quan.reputation` khi chạy `day`; `0 ≤ money ≤ earned`; `day.day_plan` ghi đè, tính lại `ingredients`, sai → mã 2). | _chưa có_ | Chưa kiểm |
| AC-P2-14 | D | `tests/test_p2_day.py` (snapshot mọi pha có `day, day_plan, upgrades, active_upgrades`; Shop có `stock`, `time_left_ticks`). | _chưa có_ | Chưa kiểm |
| AC-P2-15 | C | Smoke phút 20 và lặp ở 2.3: `python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 3000 --inventory-out kho.json --out g.jsonl` rồi `--mode quan --seed 42 --inventory kho.json --ticks 0 --out q.jsonl`; đối chiếu `stock` tick 0 với `items`; chạy lại cùng seed, `cmp` hai bản. | `integration.*` | Chưa kiểm |
| AC-P2-16 | C, S, D | `python3 -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out day1.jsonl` và `--days 3` (cấp nâng cấp có hiệu lực từ Ngày kế, M2 xuất hiện ở Ngày 3); chạy 2 lần cùng seed, `cmp`; đo thời gian 1 Ngày ≤ 20 s (`time python3 -m chonoi.headless …`). | `day.jsonl`, `cmp`, thời gian | Chưa kiểm |
| AC-P2-17 | U | Chơi `python3 -m chonoi.live --mode day` ở 1280×720: menu, DayIntro (4 s hoặc phím), EveningIntro, DayResult, Shop, Summary, pause; HUD chữ ≥ 18 px; đo FPS trung bình ≥ 30. | ảnh HUD/menu/pause, FPS | Chưa kiểm |
| AC-P2-18 | U | Chạy lại toàn bộ `tests/test_p1_*.py` với số chuẩn; test nào đổi phải ghi lý do trong commit (danh sách đã đổi ở [`docs/contracts/README.md` mục 6.8](../contracts/README.md)). | log test | Chưa kiểm |
| AC-P2-19 | mọi người | Nếu làm mở rộng: `extensions` ở gốc `game.contract.json`, mục trong `README.md` kèm test/bằng chứng; nhóm 6 người cần ≥ 2 mục. | _chưa có_ | Chưa kiểm |

## Test P1 đã đổi vì số chuẩn

Xem [`docs/contracts/README.md` mục 6.8](../contracts/README.md#68-test-p1-đã-đổi-vì-số-chuẩn-v11). Ghi thêm tại đây khi RachalHys chạy regression ở 2.3.

## Đánh giá ngắn

_Điền ở 2.3: số AC đạt/chưa đạt, commit gắn tag, lệnh đã chạy._
