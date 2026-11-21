# Bằng chứng kiểm chứng Phase 1

Chạy trên checkout sạch của `main` tại `a1c94cb`. [Revision đầy đủ](revision.txt) · [Log 110 test](tests.log) · [Đối chiếu Test Contract](contract.log)

## Kho qua hai tiến trình

Từ gốc repo, chạy với seed 42 và hai fixture dưới đây. Dùng thư mục tạm cho output.

```bash
proof_run=$(mktemp -d)
python3 -m chonoi.headless --mode gather --seed 42 --ticks 1 --scenario docs/proof/phase-1/dock.json --inputs docs/proof/phase-1/dock-inputs.json --inventory-out "$proof_run/catch.json" --out "$proof_run/gather.jsonl"
python3 -m chonoi.headless --mode quan --seed 42 --ticks 0 --inventory "$proof_run/catch.json" --out "$proof_run/quan.jsonl"
```

Kho xuất và snapshot quán đều có 2 bông súng, 1 cá lóc. Lặp hai tiến trình với cùng seed và input, ba file giống từng byte. [Gather JSONL](gather.jsonl) · [File kho](catch.json) · [Quán JSONL](quan.jsonl)

## HUD

Ảnh chụp Chromium ở 320 px, nguồn dữ liệu từ `chonoi.live --scenario`. Fixture quán có 3 bông súng trong kho và khách giữ 2 để đối chiếu lượng khả dụng. [Fixture sáng](hud-gather-fixture.json) · [Ảnh HUD sáng](hud-gather.png) · [Fixture tối](hud-quan-fixture.json) · [Ảnh HUD tối](hud-quan.png)
