# Smoke tích hợp phút 20 — gather → quan với số chuẩn v1.1 (AC-P2-15)

- Commit đã chạy: `4779862` (nhánh `p2/c-HoangHongNgo`, **chưa gộp lát A/B/Q/S/D/U**), `contract_version: "1.1"`.
- Người chạy: HoangHongNgo. Máy Windows, Python 3.13 (Git Bash; `python3` trỏ tới Python thật).
- Phạm vi: chỉ kiểm **đường kho hai tiến trình** với số chuẩn (2 bếp, 4 bàn, 6 nguyên liệu). Chưa kiểm cá bơi/sinh, Cá Sấu mới, quán 2 bếp (các lát đang làm) — không tính vào AC-P2-15 cho tới khi gộp.

## Lệnh (từ gốc repo, seed 42)

```bash
python3 -m chonoi.headless --mode gather --seed 42 --ticks 1 --scenario docs/proof/phase-2/integration-dock.json --inputs docs/proof/phase-2/integration-dock-inputs.json --inventory-out catch.json --out gather.jsonl
python3 -m chonoi.headless --mode quan --seed 42 --ticks 0 --inventory catch.json --out quan.jsonl
```

## Kết quả

| Kiểm | Kết quả |
|---|---|
| Mã thoát hai lệnh | 0 và 0 |
| File kho [`integration.catch.json`](integration.catch.json) | `{"items":{"bong_sung":2,"ca_loc":1}}` |
| Snapshot quán tick 0 [`integration.quan.jsonl`](integration.quan.jsonl) | `"stock":{"bong_sung":2,"ca_loc":1}` — khớp kho; bếp B1, B2 và bàn T1–T4 đều có trong snapshot |
| Chạy lặp hai lần cùng seed và input | `cmp` giống từng byte với cả ba file (kho, gather, quán) |

## Ca có 6 nguyên liệu (v1.1 thêm `ca_keo`, `keo_neo`)

Scenario [`integration-dock6.json`](integration-dock6.json) dựng giỏ 7 món đủ cả 6 loại, cập bến ở tick 0:

- Kho ghi ra [`integration.catch6.json`](integration.catch6.json): `{"items":{"bong_dien_dien":1,"bong_sung":2,"ca_keo":2,"ca_loc":1,"keo_neo":1}}` (khóa sắp theo id).
- Quán đọc đúng kho đó ở tick 0 ([`integration.quan6.jsonl`](integration.quan6.jsonl)): `"stock"` trùng `items`.

## Chưa làm được ở thời điểm này

- Gather mặc định chưa có đàn cá đầu ca (`fish_initial` = 8 chờ lát A), nên smoke dùng giỏ dựng sẵn thay vì bắt cá thật.
- Cần chạy lại trên `main` sau khi gộp A → B → Q → S → D → U và điền bằng chứng cuối ở 2.3.
