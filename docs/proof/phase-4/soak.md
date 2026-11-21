# Soak 10 ngày

Chạy từ gốc repo bằng Python 3.

```sh
python3 -m tools.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json
python3 -m tools.soak --seed 7 --days 10 --out /tmp/chonoi-soak-repeat.json
PYTHONPATH=tests:. python3 -m unittest tests.test_p4_soak -v
```

Bot sử dụng một phiên mô phỏng và một bộ cấp ID trong suốt 10 ngày. Mỗi buổi sáng, bot thu nguyên liệu cho một món trong thực đơn rồi cập bến. Buổi tối, bot nấu và giao món cho khách. Khi đủ tiền, bot mua bình oxy rồi đóng Shop bằng input `shop_done`. Mọi ca chạy theo từng tick của game.

[soak.json](soak.json) ghi kết quả lúc đóng từng Shop. Với seed 7, cả hai lần chạy hoàn tất đủ 10 ngày, không gặp lỗi và cho cùng kết quả gameplay. Có thể kiểm tra lại bằng lệnh sau.

```sh
python3 - <<'PY'
import json
from pathlib import Path

def gameplay(path):
    data = json.loads(Path(path).read_text())
    del data["duration_s"]
    return data

result = gameplay("docs/proof/phase-4/soak.json")
assert result == gameplay("/tmp/chonoi-soak-repeat.json")
assert result["days_completed"] == result["days"] == len(result["results"]) == 10
assert result["crashes"] == 0
PY
```

`test_real_phases_and_ids_across_plan_rollover` kiểm tra từng lần chuyển gather → quan → Shop, vòng lặp thực đơn, ID đàn cá và ID nguyên liệu qua cả ngày thứ sáu. `test_seeded_gameplay_results_repeat` kiểm tra doanh thu tích lũy và tính lặp của bot.
