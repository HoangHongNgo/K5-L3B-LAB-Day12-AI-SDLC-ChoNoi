"use strict";
// Âm thanh tổng hợp bằng WebAudio và phụ đề SFX. Phụ đề luôn hiện khi bật, kể cả khi tắt tiếng.
(function () {
  const SFX = {
    gather:            {text: "[tiếng nhặt đồ]", tone: [660, 0.08]},
    fish_caught:       {text: "[tiếng quăng lưới, cá quẫy]", tone: [440, 0.12]},
    monster_hit:       {text: "[tiếng cá sấu táp mạnh]", tone: [110, 0.3]},
    choke:             {text: "[tiếng ho sặc nước, đang ngạt]", tone: [330, 0.2]},
    oxygen_empty:      {text: "[tiếng thở dốc, hết oxy]", tone: [260, 0.25]},
    faint:             {text: "[tiếng ngã xuống nước]", tone: [90, 0.4]},
    bought:            {text: "[tiếng trả tiền mua đồ]", tone: [700, 0.1]},
    spoiled:           {text: "[tiếng nguyên liệu ươn]", tone: [180, 0.15]},
    cook_started:      {text: "[tiếng xèo xèo trên bếp]", tone: [520, 0.1]},
    dish_ready:        {text: "[tiếng chuông món chín]", tone: [880, 0.2]},
    served:            {text: "[tiếng đặt đĩa lên bàn]", tone: [400, 0.08]},
    paid:              {text: "[tiếng tiền leng keng]", tone: [990, 0.15]},
    customer_left:     {text: "[tiếng khách bỏ đi]", tone: [200, 0.2]},
    reservation_arrived: {text: "[tiếng chuông cửa, khách đặt trước đến]", tone: [760, 0.2]},
  };
  const store = (k, v) => { try { v === undefined ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} };
  const load = k => { try { return localStorage.getItem(k); } catch { return null; } };
  let muted = load("chonoi.muted") === "1";
  let captions = load("chonoi.captions") !== "0";
  let ctx = null, timer = null, last = "";

  function beep(freq, dur) {
    if (muted) return;
    try {
      ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.frequency.value = freq; o.type = "triangle";
      g.gain.setValueAtTime(0.06, ctx.currentTime);
      g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + dur);
      o.connect(g); g.connect(ctx.destination);
      o.start(); o.stop(ctx.currentTime + dur);
    } catch {}
  }

  function show(text) {
    const out = document.getElementById("sfx-caption");
    if (!out || !captions) return;
    out.textContent = text; out.hidden = false;
    clearTimeout(timer);
    timer = setTimeout(() => { out.hidden = true; }, 2500);
  }

  // Gọi với các event MỚI của snapshot (đã lọc theo tick và pha).
  function handle(events) {
    const hits = events.map(e => SFX[e.name]).filter(Boolean);
    if (!hits.length) return;
    const s = hits.at(-1);
    show(s.text); beep(...s.tone);
  }

  function toggle(label, get, set) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "secondary";
    const paint = () => { b.textContent = label + " · " + (get() ? "Bật" : "Tắt"); b.setAttribute("aria-pressed", String(get())); };
    b.addEventListener("click", () => { set(!get()); paint(); });
    paint();
    return b;
  }
  // Hai nút cho trang Điều khiển của Sổ tay.
  function buttons() {
    return [
      toggle("Âm thanh", () => !muted, v => { muted = !v; store("chonoi.muted", muted ? "1" : "0"); }),
      toggle("Phụ đề âm thanh", () => captions, v => {
        captions = v; store("chonoi.captions", v ? "1" : "0");
        const out = document.getElementById("sfx-caption"); if (!v && out) out.hidden = true;
      }),
    ];
  }
  window.ChoNoiSfx = {handle, buttons, SFX};
})();
