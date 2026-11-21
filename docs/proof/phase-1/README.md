# Bằng chứng kiểm chứng Phase 1

Chạy lại tại `aa18d1b` (nhánh `p1/close-haiquanng`, sau khi gộp lát 4 và sửa payload/fixture theo PRD-0 mục D–E). [Revision đầy đủ](revision.txt) · [Log 153 test](tests.log) · [Log kiểm chứng 12 AC](contract.log)

Tái lập toàn bộ từ gốc repo (ghi lại `contract.log` và ba file smoke bên dưới):

```bash
PYTHONPATH=tests:. python3 docs/proof/phase-1/check_ac.py > docs/proof/phase-1/contract.log
```

[`check_ac.py`](check_ac.py) chạy headless hộp đen cho từng AC, in `PASS`/`FAIL` kèm số liệu thật và trả mã khác 0 nếu có AC trượt. Lần kiểm trước ở `a1c94cb` (5/12 đạt) còn trong lịch sử git.

## Kho qua hai tiến trình

Từ gốc repo, chạy với seed 42 và hai fixture dưới đây. Dùng thư mục tạm cho output.

```bash
proof_run=$(mktemp -d)
python3 -m chonoi.headless --mode gather --seed 42 --ticks 1 --scenario docs/proof/phase-1/dock.json --inputs docs/proof/phase-1/dock-inputs.json --inventory-out "$proof_run/catch.json" --out "$proof_run/gather.jsonl"
python3 -m chonoi.headless --mode quan --seed 42 --ticks 0 --inventory "$proof_run/catch.json" --out "$proof_run/quan.jsonl"
```

Kho xuất và snapshot quán đều có 2 bông súng, 1 cá lóc. Lặp hai tiến trình với cùng seed và input, ba file giống từng byte. [Gather JSONL](gather.jsonl) · [File kho](catch.json) · [Quán JSONL](quan.jsonl)

## HUD

Ảnh chụp Chromium ở 320 px trên bản ghép thử lát 4 (chưa chụp lại sau `aa18d1b`), nguồn dữ liệu từ `chonoi.live --scenario`. Fixture quán có 3 bông súng trong kho và khách giữ 2 để đối chiếu lượng khả dụng. [Fixture sáng](hud-gather-fixture.json) · [Ảnh HUD sáng](hud-gather.png) · [Fixture tối](hud-quan-fixture.json) · [Ảnh HUD tối](hud-quan.png)

## Kiểm lại HUD trên lịch sử main

Chạy hai mode trên `516e868` (PR #15, contract v1.0), seed 42, Chromium 1280×720. Dùng hai fixture HUD ở trên. PR #15 đã gộp bốn lát và các bản sửa được dùng trong ma trận. Tag `phase-1` hiện trỏ tới `9ad3a3e`. Ảnh và log kiểm lại dưới đây thuộc `516e868`.

- Lặn & Hái: bấm E ở N1, hái một bông súng. HUD có giờ, oxy, Máu và giỏ tăng từ 4 lên 5 ô. [Ảnh](qa-recheck/p1-gather.png)
- Mở Quán: T1 gọi gỏi bông súng, kho có 3 bông súng và T1 giữ 2. HUD hiển thị còn 1 bông súng khả dụng cùng tên món và thời gian chờ. Bấm E để nấu ở B1, bưng món đã chín, đi tới T1 rồi giao. Khách trả 48 nghìn gồm 8 nghìn boa, uy tín lên 3,2. [Chờ](qa-recheck/p1-quan-wait.png) · [Nấu](qa-recheck/p1-quan-cook.png) · [Bưng](qa-recheck/p1-quan-carry.png) · [Đã trả](qa-recheck/p1-quan-paid.png)
- `PYTHONPATH=tests:. python3 docs/proof/phase-1/check_ac.py` đạt các ca tự động và chạy 173 test đạt trên clone sạch. [Log](qa-recheck/contract.log)
