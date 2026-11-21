"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live --mode gather|quan|day [--seed N] [--port 8000]

Máy chủ HTTP nhỏ (ThreadingHTTPServer) phục vụ `chonoi/web/index.html` và các API:
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input  -> {"move": [a, b], "interact": bool, "catch": bool}   (trạng thái phím đang giữ)
    POST /restart -> chơi lại từ đầu (cùng seed, cùng scenario)
    POST /continue -> vào pha mới, nhận menu_ids tùy chọn khi mở quán
    POST /wait -> chờ lượt khách kế hoặc đóng ca, giữ nguyên thứ tự tick của mô phỏng

Mô phỏng chạy 60 tick/s trong một luồng nền, dùng CÙNG lớp sim như headless (qua `runner.Session`).
Client chỉ ĐỌC snapshot và tự bỏ qua trường chưa có, nên luật do nhóm viết thêm trường nào cũng không vỡ.
Ngẫu nhiên vẫn đi qua `Streams` (seed); chỉ nhịp chạy theo đồng hồ thật, không đi vào luật.
"""

import argparse
import copy
import json
import os
import sys
import threading
import time
import traceback
from collections import Counter, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .contract import load_contract
from .errors import BadInput
from .inputs import LiveInputs
from .inventory import read_inventory
from .runner import Session
from .scenario import load_scenario

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
TICK_S = 1.0 / 60.0
MAX_BODY = 4096
RECENT_EVENTS = 40
DAY_BUTTONS = ("interact", "catch", "pause", "shop_done", "attack", "photo")
PLAY_BUTTONS = ("interact", "catch", "pause")
WEB_ASSETS = {
    "/": ("index.html", "text/html"),
    "/index.html": ("index.html", "text/html"),
    **{"/assets/" + name: (name, "text/css") for name in ("game.css", "forage.css", "flow.css")},
    **{"/assets/" + name: (name, "text/javascript") for name in (
        "scene.js", "river.js", "cafe.js", "forage.js", "service.js", "flow.js",
        "vendor/three.module.min.js", "vendor/three.core.min.js",
    )},
}


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, *, start_in_menu=False):
        self._args = (mode, tuning, scenario, seed, inventory)
        self.mode = mode
        self.tuning = tuning
        self.inventory_out = inventory_out
        self.start_in_menu = start_in_menu
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._run_number = 0
        self._reset()

    def _reset(self):
        self._run_number += 1
        self._arrival_preview = None
        day_mode = self.mode == "day"
        self.session = Session(*self._args, days=5) if day_mode else Session(*self._args)
        self.inputs = LiveInputs(DAY_BUTTONS if day_mode else PLAY_BUTTONS)
        self.menu_pending = self.start_in_menu and not day_mode
        self.events = self.session.initial_rows() if day_mode else []
        self.intro_pending = day_mode
        self._buys = deque()
        self._order_dishes = {}
        self._sold = Counter()
        self._shift = self._empty_shift()
        self._reputation_at_open = None
        self._day_result = None
        self._saved = False
        self.error = None

    @staticmethod
    def _empty_shift():
        return {"served": 0, "left": 0, "shift_earned": 0, "tips": 0, "reputation_delta": 0}

    def _record_day_event(self, row):
        name, data = row["name"], row["data"]
        if name == "phase_start":
            self.intro_pending = True
            self.inputs = LiveInputs(DAY_BUTTONS)
            self._buys.clear()
            if row["phase"] == "quan":
                opening = self.session.snapshot()
                self._reputation_at_open = opening["reputation"]
                self._shift = self._empty_shift()
                self._order_dishes = {c["id"]: c["dish_id"] for c in opening["customers"]}
        elif name == "served":
            self._order_dishes[data["order_id"]] = data["dish_id"]
        elif name == "paid":
            dish = self._order_dishes.pop(data["order_id"], None)
            if dish is not None:
                self._sold[dish] += 1
            self._shift["served"] += 1
            self._shift["tips"] += data["tip"]
            self._shift["shift_earned"] += data["amount"]
        elif name == "customer_left":
            self._order_dishes.pop(data["order_id"], None)
            self._shift["left"] += 1
        elif name == "quan_end":
            self._day_result = {
                **self._shift, "day": row["day"],
                "reputation_delta": round(data["reputation"] - self._reputation_at_open, 2),
            }

    # --- luồng nền ----------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name="chonoi-sim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            nxt += TICK_S
            with self._lock:
                try:
                    self._tick_once()
                except Exception:  # luật của nhóm lỗi: báo ra terminal + client, dừng bước (restart để chơi lại)
                    self.error = traceback.format_exc()
                    sys.stderr.write(self.error)
                    self.session.sim.done = True
                    self.session.sim.reason = "error"
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            elif delay < -0.25:  # chạy chậm quá thì bỏ bù, tránh chạy dồn
                nxt = time.perf_counter()

    def _tick_once(self):
        s = self.session
        if s.done or self.intro_pending or self.menu_pending:
            return
        inp = self.inputs.advance()
        if self._buys:
            inp.buy = self._buys.popleft()
        for row in s.step(inp):
            self.events.append(row)
            if self.mode == "day":
                self._record_day_event(row)
        del self.events[:-RECENT_EVENTS]
        if s.done and not self._saved:
            self._saved = True
            if self.inventory_out:
                try:
                    s.write_inventory_if_done(self.inventory_out)
                except OSError as e:
                    sys.stderr.write(f"lỗi ghi kho: {e}\n")

    # --- API cho handler -----------------------------------------------------------
    def _restaurant(self):
        return self.session.sim.cur if self.mode == "day" else self.session.sim.inner

    def _service_id(self, state):
        return f"{self._run_number}/{state.get('day', 0)}"

    @staticmethod
    def _cookable(room, available):
        allowed = room.menu_ids
        if allowed is None:
            allowed = room.ctx.get("plan_dishes", room.menu)
        return sorted(dish for dish in allowed
                      if all(available.get(kind, 0) >= count
                             for kind, count in room.menu[dish]["recipe"].items()))

    def _can_wait(self, state):
        return (state["phase"] == "quan" and state["state"] == "playing"
                and not self.menu_pending and not self.intro_pending
                and not state["customers"] and not state["hand"]
                and all(stove["state"] == "idle" for stove in state["stoves"]))

    def _wait_to_close(self, room):
        if not room.random_customers or not self._cookable(room, room._available_stock()):
            return True
        first = room.t["first_customer_tick"]
        interval = round(room.t["customer_interval_s"] * room.tick_hz)
        until_arrival = first - room.phase_tick
        if until_arrival <= 0:
            until_arrival = interval - (room.phase_tick - first) % interval
        if until_arrival >= room.time_left_ticks:
            return True
        if not room.is_item_inventory:
            return False

        # Kho từng món có thể ươn trước lúc khách đến. Trong lúc quán trống, chỉ
        # cần xét một lần cho lượt khách kế vì lượng nguyên liệu chỉ giảm theo tick.
        key = (room, room.phase_tick + until_arrival)
        if self._arrival_preview is None or self._arrival_preview[0] != key:
            preview = copy.deepcopy(room)
            for _ in range(until_arrival):
                preview._decay_freshness_and_handle_spoiled()
            closes = not self._cookable(preview, preview._available_stock())
            self._arrival_preview = (key, closes)
        return self._arrival_preview[1]

    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            snap["menu_pending"] = self.menu_pending
            snap["meta"] = self.tuning[snap["phase"]]
            snap["menu"] = self.tuning["menu"]
            if snap["phase"] == "gather" and snap.get("active_upgrades", {}).get("net"):
                active_net = self.session.sim.cur.net
                if active_net is not None:
                    snap["active_net"] = active_net
            if snap["phase"] == "quan":
                room = self._restaurant()
                snap["service_id"] = self._service_id(snap)
                if isinstance(snap.get("stock"), list):
                    snap["available_stock"] = room._available_stock()
                if self.menu_pending or self.intro_pending:
                    available = snap.get("available_stock")
                    if available is None:
                        available = room._available_stock()
                    snap["opening_stock"] = {kind: count for kind, count in available.items() if count > 0}
                    snap["opening_menu"] = self._cookable(room, available)
                snap["can_wait"] = self._can_wait(snap)
                snap["wait_to_close"] = snap["can_wait"] and self._wait_to_close(room)
            if snap["phase"] == "shop":
                room = self.tuning["quan"]
                snap["shop_room"] = {key: room[key] for key in ("bounds", "stoves", "tables")}
            if self.mode == "day":
                best_count = max(self._sold.values(), default=0)
                snap.update(
                    intro_pending=self.intro_pending, day_result=self._day_result,
                    shift_earned=self._shift["shift_earned"],
                    best_sellers={k: v for k, v in sorted(self._sold.items()) if v == best_count},
                )
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        allowed = DAY_BUTTONS if self.mode == "day" else PLAY_BUTTONS
        for b in allowed:
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        buy = body.get("buy")
        if "buy" in body and (self.mode != "day" or not isinstance(buy, str) or not buy):
            raise ValueError("buy phải là chuỗi khác rỗng trong mode day")
        with self._lock:
            if not self.intro_pending and not self.menu_pending:
                self.inputs.set(move, **buttons)
                if buy and self.session.sim.phase == "shop":
                    self._buys.append(buy)

    def continue_intro(self, body):
        with self._lock:
            if not (self.menu_pending or self.intro_pending):
                raise ValueError("màn giới thiệu đã thay đổi")
            state = self.session.snapshot()
            if ("service_id" in body and body["service_id"] != self._service_id(state)
                    or not self._matches(body, state, ("day", "phase", "tick"))):
                raise ValueError("màn giới thiệu đã thay đổi")
            if "menu_ids" in body:
                if state["phase"] != "quan":
                    raise ValueError("chỉ chọn thực đơn lúc mở quán")
                ids = body["menu_ids"]
                if not isinstance(ids, list) or not all(isinstance(dish, str) for dish in ids):
                    raise ValueError("menu_ids phải là danh sách mã món")
                room = self._restaurant()
                feasible = self._cookable(room, room._available_stock())
                if len(set(ids)) != len(ids) or not set(ids).issubset(feasible) or (feasible and not ids):
                    raise ValueError("chọn ít nhất một món nấu được, mỗi món một lần")
                room.menu_ids = list(ids)
            self.intro_pending = False
            self.menu_pending = False

    @staticmethod
    def _matches(body, state, keys):
        return all(type(body.get(k)) is type(state.get(k)) and body.get(k) == state.get(k) for k in keys)

    def wait_for_customer(self, body):
        with self._lock:
            state = self.session.snapshot()
            if (body.get("service_id") != self._service_id(state)
                    or not self._matches(body, state, ("phase", "day"))
                    or not self._can_wait(state)):
                raise ValueError("ca hoặc lượt khách đã thay đổi")
            room = self._restaurant()
            self.inputs = LiveInputs(DAY_BUTTONS if self.mode == "day" else PLAY_BUTTONS)
            for _ in range(room.time_left_ticks):
                self._tick_once()
                if room.customers or room.done:
                    break

    def restart(self):
        with self._lock:
            self._reset()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    game: LiveGame = None  # gán trên lớp con trong make_server

    def log_message(self, fmt, *args):  # yên lặng
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            self._send(200, self.game.state_json())
        elif path in WEB_ASSETS:
            name, content_type = WEB_ASSETS[path]
            try:
                with open(os.path.join(WEB_DIR, name), "rb") as f:
                    self._send(200, f.read(), content_type + "; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu tai nguyen web"}')
        else:
            self._send(404, b'{"error":"khong co"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > MAX_BODY:
            self._send(400, b'{"error":"body sai"}')
            return
        raw = self.rfile.read(n) if n else b""
        try:
            if path in ("/input", "/continue", "/wait"):
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                if path == "/continue":
                    self.game.continue_intro(body)
                elif path == "/wait":
                    self.game.wait_for_customer(body)
                else:
                    self.game.set_input(body)
            elif path == "/restart":
                self.game.restart()
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, b'{"ok":true}')


class LiveServer:
    """Máy chủ + mô phỏng. port=0 -> cổng ngẫu nhiên (đọc `.port`)."""

    def __init__(self, game: LiveGame, host="127.0.0.1", port=8000):
        handler = type("Handler", (_Handler,), {"game": game})
        self.game = game
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True
        self.host = host
        self.port = self.httpd.server_address[1]
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/"

    def start(self):
        self.game.start()
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="chonoi-http", daemon=True)
        self._thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self.game.stop()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi trực tiếp trên trình duyệt (starter).")
    p.add_argument("--mode", required=True, choices=["gather", "quan", "day"])
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--scenario")
    p.add_argument("--inventory", help="chỉ với quan: nạp kho từ file")
    p.add_argument("--inventory-out", dest="inventory_out", help="chỉ với gather: ghi kho khi kết thúc buổi")
    a = p.parse_args(argv)
    try:
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        contract = load_contract()
        if a.mode == "day" and contract["contract_version"] != "1.1":
            raise BadInput("--mode day cần Test Contract v1.1")
        tuning = contract["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning)
        inventory = read_inventory(a.inventory) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out, start_in_menu=True)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    print(f"Mở trình duyệt tại {server.url}  (chế độ {a.mode}, seed {a.seed}). Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
