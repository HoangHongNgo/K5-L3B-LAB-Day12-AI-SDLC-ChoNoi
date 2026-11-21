# Bằng chứng Phase 2

Sinh lại toàn bộ trên **commit sẽ gắn tag `phase-2`** (từ gốc repo):

```bash
python3 docs/proof/phase-2/run_proof.py
```

[`run_proof.py`](run_proof.py) ghi các file dưới đây, mỗi file có dòng commit và `contract_version` đã chạy. Mục nào chưa chạy được được ghi `CHƯA CHẠY ĐƯỢC` kèm lỗi thật trong `summary.txt`.

| File | Nội dung | Yêu cầu TICKET-02 |
|---|---|---|
| `revision.txt` | commit, `contract_version`, cây sạch hay không | bằng chứng khớp commit gắn tag |
| `tests.log` | toàn bộ unittest | regression P1 + test lát Phase 2 |
| `integration.jsonl`, `integration.json`, `integration.quan.jsonl`, `integration.txt` | smoke `gather --inventory-out` → `quan --inventory` (seed 42, `docs/proof/phase-1/dock.json`) | mục 5, phút 20 |
| `day-1.jsonl`, `day-3.jsonl` | `--mode day --days 1` / `--days 3`, seed 42 | DoD: công bố kế hoạch, chốt Ngày khi Shop đóng, cấp có hiệu lực từ Ngày kế; M2 từ Ngày 3 |
| `cmp.txt` | `day --days 1` chạy hai lần cùng seed, so từng byte | tất định |
| `timing.txt` | thời gian headless 1 Ngày không pause | ≤ 20 s, ≤ 22.200 tick |
| `summary.txt` | PASS / FAIL / CHƯA CHẠY ĐƯỢC từng mục | |
| ảnh HUD/menu/pause, FPS | RachalHys chụp ở 1280×720 và gửi, thêm tay vào thư mục này | ≥ 30 FPS, chữ ≥ 18 px |

Lần chạy thử trên `main` `c3dcd80` (chưa gắn tag): smoke tích hợp PASS; `day` CHƯA CHẠY ĐƯỢC vì contract vẫn v1.0 và chưa có cờ `--days` (lát C); `main` đỏ 6 test do gộp PR #14 (đã sửa ở nhánh `p2/fix-main-haiquanng`). Vì vậy chưa commit file kết quả nào.
