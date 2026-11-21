// Benchmark dùng scene, HUD và luồng 60 tick/s của bản chơi trên trình duyệt.
import { spawn } from "node:child_process";
import { access, mkdtemp, rename, rm, writeFile } from "node:fs/promises";
import { constants } from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

const root = fileURLToPath(new URL("../", import.meta.url));
const children = [];
let profile;
let timer;

async function chromePath() {
  const paths = process.env.CHROME_BIN ? [process.env.CHROME_BIN] : [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ...(process.env.PATH || "").split(delimiter).flatMap(dir =>
      ["google-chrome", "chromium", "chromium-browser", "google-chrome-stable"].map(name => join(dir, name))),
  ];
  for (const path of paths) {
    try { await access(path, constants.X_OK); return path; }
    catch { /* Thử vị trí kế tiếp. */ }
  }
  throw Error("Không tìm thấy Chrome/Chromium. Đặt CHROME_BIN trỏ tới tệp thực thi.");
}

function start(command, args, stdio, aborted) {
  const child = spawn(command, args, { cwd: root, stdio });
  children.push(child);
  let diagnostics = "";
  if (child.stderr) {
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", chunk => { diagnostics = (diagnostics + chunk).slice(-1800); });
  }
  child.once("error", aborted);
  child.once("exit", (code, signal) => aborted(Error(command + " đã dừng: " + (signal || code) + "\n" + diagnostics.trim())));
  return child;
}

// Chromium DevTools pipe dùng thông điệp JSON kết thúc bằng NUL trên fd 3/4.
function devtools(browser, onEvent) {
  let sequence = 0;
  let buffer = "";
  const pending = new Map();
  browser.stdio[4].setEncoding("utf8");
  browser.stdio[4].on("data", chunk => {
    buffer += chunk;
    let boundary;
    while ((boundary = buffer.indexOf("\0")) >= 0) {
      const message = JSON.parse(buffer.slice(0, boundary));
      buffer = buffer.slice(boundary + 1);
      if (!message.id) { onEvent(message); continue; }
      const request = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) request.reject(Error(message.error.message));
      else request.resolve(message.result);
    }
  });
  return (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, {resolve, reject});
    browser.stdio[3].write(JSON.stringify({id, method, params, sessionId}) + "\0");
  });
}

// Chỉ đếm frame khi canvas 3D của cảnh gather thật đã nhận lệnh vẽ.
// document.timeline.currentTime dùng cùng đồng hồ với requestAnimationFrame.
function measureRenderedScene(duration, launched) {
  let warmupStart, previous, startTime, loadMs;
  let pending = false, complete = false;
  const intervals = [];
  const clear = WebGL2RenderingContext.prototype.clear;
  WebGL2RenderingContext.prototype.clear = function (...args) {
    const result = clear.apply(this, args);
    if (complete || pending || this.canvas.id !== "world3d") return result;
    pending = true;
    queueMicrotask(() => {
      pending = false;
      const view = window.gameView;
      if (!document.body.classList.contains("has-3d") || view?.state?.phase !== "gather") return;
      if (view.state.finished) {
        complete = true;
        window.chonoiBench(JSON.stringify({error: "Ca sáng đã hết trước khi đo xong."}));
        return;
      }
      if (view.screen) return;
      const stamp = document.timeline.currentTime;
      if (!Number.isFinite(stamp)) return;
      if (warmupStart === undefined) {
        if (innerWidth !== 1280 || innerHeight !== 720 || this.drawingBufferWidth !== 1280 || this.drawingBufferHeight !== 720) {
          complete = true;
          window.chonoiBench(JSON.stringify({error: "Kích thước canvas không đúng 1280×720."}));
          return;
        }
        warmupStart = stamp;
        loadMs = Math.round(performance.timeOrigin + performance.now() - launched);
        const info = this.getExtension("WEBGL_debug_renderer_info");
        window.chonoiBench(JSON.stringify({renderer: info ? this.getParameter(info.UNMASKED_RENDERER_WEBGL) : "WebGL 2"}));
        return;
      }
      if (stamp - warmupStart < 3000 || stamp === previous) return;
      if (startTime === undefined) {
        startTime = previous = stamp;
        return;
      }
      intervals.push((stamp - previous) / 1000);
      previous = stamp;
      const measured = (stamp - startTime) / 1000;
      if (measured < duration) return;
      complete = true;
      const frames = intervals.length;
      const n = Math.max(1, Math.ceil(.01 * frames));
      const slow = intervals.sort((a, b) => b - a).slice(0, n);
      window.chonoiBench(JSON.stringify({result: {
        avg_fps: frames / measured,
        p1_low_fps: n / slow.reduce((sum, value) => sum + value, 0),
        frames, measured_s: measured, load_ms: loadMs,
      }}));
    });
    return result;
  };
}

async function run(options, aborted) {
  const seed = Number(options.seed), duration = Number(options.duration);
  if (!Number.isSafeInteger(seed) || !Number.isFinite(duration) || duration <= 0 || !options.out) {
    throw Error("Dùng --seed <số nguyên> --duration <số giây dương> --out <tệp JSON>.");
  }
  timer = setTimeout(() => aborted(Error("Quá thời gian chờ cảnh 3D hoặc kết quả.")), (duration + 65) * 1000);
  const chrome = await chromePath();
  profile = await mkdtemp(join(tmpdir(), "chonoi-bench-"));
  const server = start(process.env.PYTHON || "python3",
    ["-m", "chonoi.live", "--mode", "gather", "--seed", String(seed), "--port", "0"],
    ["ignore", "pipe", "inherit"], aborted);
  const url = await new Promise(resolve => {
    let log = "";
    server.stdout.on("data", chunk => {
      log += chunk;
      const match = log.match(/http:\/\/127\.0\.0\.1:\d+\//);
      if (match) resolve(match[0]);
    });
  });

  const browser = start(chrome, [
    "--headless=new", "--remote-debugging-pipe", "--no-first-run", "--no-default-browser-check",
    "--disable-background-networking", "--disable-extensions", "--enable-unsafe-swiftshader",
    "--user-data-dir=" + profile, "about:blank",
  ], ["ignore", "ignore", "pipe", "pipe", "pipe"], aborted);
  let finish, fail;
  const measured = new Promise((resolve, reject) => { finish = resolve; fail = reject; });
  const call = devtools(browser, message => {
    if (message.method !== "Runtime.bindingCalled" || message.params.name !== "chonoiBench") return;
    const data = JSON.parse(message.params.payload);
    if (data.error) fail(Error(data.error));
    else if (data.result) finish(data.result);
    else if (data.renderer) console.log(data.renderer);
  });
  console.log((await call("Browser.getVersion")).product);
  const {targetId} = await call("Target.createTarget", {url: "about:blank"});
  const {sessionId} = await call("Target.attachToTarget", {targetId, flatten: true});
  const page = (method, params) => call(method, params, sessionId);
  await page("Runtime.enable");
  await page("Page.enable");
  await page("Emulation.setDeviceMetricsOverride", {width: 1280, height: 720, deviceScaleFactor: 1, mobile: false});
  await page("Runtime.addBinding", {name: "chonoiBench"});
  await page("Page.addScriptToEvaluateOnNewDocument", {
    source: "(" + measureRenderedScene.toString() + ")(" + duration + "," + performance.timeOrigin + ")",
  });
  const state = await (await fetch(url + "state")).json();
  if (state.menu_pending) {
    const response = await fetch(url + "continue", {method: "POST", body: JSON.stringify({phase: state.phase, tick: state.tick})});
    if (!response.ok) throw Error("Chưa vào được ca sáng.");
  }
  await page("Page.navigate", {url});
  const result = await measured;
  const out = resolve(options.out), temporary = out + "." + process.pid + ".tmp";
  try {
    await writeFile(temporary, JSON.stringify(result) + "\n");
    await rename(temporary, out);
  } finally { await rm(temporary, {force: true}); }
  console.log(JSON.stringify(result));
}

try {
  const args = process.argv.slice(2);
  const seedFlag = args.indexOf("--seed");
  if (seedFlag >= 0 && /^-\d+$/.test(args[seedFlag + 1])) {
    args.splice(seedFlag, 2, "--seed=" + args[seedFlag + 1]);
  }
  const {values} = parseArgs({args, options: {
    seed: {type: "string", default: "42"}, duration: {type: "string", default: "30"}, out: {type: "string", default: "bench.json"},
  }});
  let abort;
  const stopped = new Promise((_, reject) => { abort = reject; });
  for (const signal of ["SIGINT", "SIGTERM"]) {
    process.once(signal, () => abort(Error("Đã dừng benchmark.")));
  }
  await Promise.race([run(values, abort), stopped]);
} catch (e) {
  console.error(e.message);
  process.exitCode = 1;
} finally {
  clearTimeout(timer);
  process.removeAllListeners("SIGINT");
  process.removeAllListeners("SIGTERM");
  for (const child of children) {
    for (const stream of child.stdio) stream?.destroy();
  }
  await Promise.all(children.map(child => new Promise(resolve => {
    if (child.exitCode !== null || child.signalCode || !child.pid) return resolve();
    child.once("exit", resolve);
    child.kill();
  })));
  if (profile) await rm(profile, {recursive: true, force: true, maxRetries: 5, retryDelay: 100});
}
