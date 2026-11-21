# Kiểm chứng lại Phase 2

Kiểm trên commit `0fd2d7f` trong lịch sử `main`, contract v1.1, sau khi gộp PR #26. GitHub chưa có tag `phase-2`.

- `PYTHONPATH=tests:. python3 docs/proof/phase-2/run_proof.py` chạy 372 test. 371 đạt, 1 bỏ qua vì chỉ áp dụng cho cá đứng yên v1.0. [Log chi tiết](qa-regression.log)
- Smoke seed 42 cho kho và snapshot Quán tick 0 cùng có 2 bông súng, 1 cá lóc. Chạy lại hai tiến trình hai lần rồi dùng `cmp` trên file kho và hai JSONL. Cả ba file giống từng byte.
- Seed 42, không input, vòng 1 Ngày hoàn tất 22.200 tick trong 1,18 giây. Hai JSONL giống từng byte. Vòng 3 Ngày hoàn tất 66.600 tick trong 3,66 giây. M1 có từ Ngày 1, M2 xuất hiện ở Ngày 3. Ca mua oxy và áp dụng từ Ngày kế nằm trong `test_p2_progress`.
