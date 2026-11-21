# Ma trận truy vết Phase 2

Đối chiếu TICKET-02 và Test Contract v1.1 ([`docs/plan/phase-2.md`](../plan/phase-2.md)). Danh sách AC-P2-xx do nhóm suy ra từ ticket (ticket không đánh số), định nghĩa ở phụ lục của file kế hoạch.

> **Lát U đã chốt kết quả kiểm AC-P2-17 và AC-P2-18.** Các dòng còn lại giữ trạng thái của ma trận chung. GitHub chưa có tag `phase-2`. Bằng chứng dưới đây ghi commit đã kiểm.

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
| AC-P2-17 | U | Chơi vòng ngày ở 1280×720, kiểm menu, màn chuyển pha, pause, Shop, Summary, HUD và đo FPS. | [Ảnh và kết quả trên `89e2437`](../proof/phase-2/ui/README.md) | **Đạt trên v1.1**. Pause giữ nguyên tick gameplay ở cả 3 pha, HUD 18 px và hai ca đo 60 FPS. |
| AC-P2-18 | U | Chạy các test Phase 1 còn hiệu lực với số chuẩn v1.1. | [Hồi quy P1 trên `89e2437`](../proof/phase-2/ui/regression-v11.log) · [Chạy lại trên `0fd2d7f`](../proof/phase-2/qa-regression.log) | **Đạt trên v1.1**. P1 đạt 119/119 trên `89e2437`. Suite trên `0fd2d7f` đạt 371, bỏ qua 1 ca dành cho v1.0. |
| AC-P2-19 | mọi người | Nếu làm mở rộng: `extensions` ở gốc `game.contract.json`, mục trong `README.md` kèm test/bằng chứng; nhóm 6 người cần ≥ 2 mục. | _chưa có_ | Chưa kiểm |

## Test P1 đã đổi vì số chuẩn

Xem [`docs/contracts/README.md` mục 6.8](../contracts/README.md#68-test-p1-đã-đổi-vì-số-chuẩn-v11).

## Đánh giá ngắn

Lát U đạt 2/2 AC đã kiểm. [Kết quả chạy lại từ `0fd2d7f`](../proof/phase-2/qa-recheck.md) có log kiểm thử, smoke hai tiến trình và thời gian chạy vòng 1/3 Ngày để đối chiếu ma trận chung.
