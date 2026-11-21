// Live-only route guidance. The server chooses all catches and owns the basket.
(() => {
  "use strict";
  const dock = "@dock";
  const views = new WeakMap();
  const directions = [
    ["→", "Sang phải"], ["↘", "Sang phải và lặn xuống"], ["↓", "Lặn xuống"], ["↙", "Sang trái và lặn xuống"],
    ["←", "Sang trái"], ["↖", "Sang trái và bơi lên"], ["↑", "Bơi lên"], ["↗", "Sang phải và bơi lên"],
  ];
  const name = kind => typeof KIND_NAME !== "undefined" && KIND_NAME[kind] || kind.replaceAll("_", " ");
  const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  const meters = n => n.toLocaleString("vi-VN", {minimumFractionDigits: 1, maximumFractionDigits: 1}) + " m";
  const text = (el, value) => { if (el.textContent !== value) el.textContent = value; };

  function make(tag, cls) {
    const el = document.createElement(tag);
    el.className = cls;
    return el;
  }
  function newView(container) {
    const label = make("label", "forage-choose");
    const caption = make("span", "forage-caption");
    const select = make("select", "forage-select");
    label.append(caption, select);
    const route = make("div", "forage-route");
    const arrow = make("span", "forage-arrow");
    arrow.setAttribute("role", "img");
    const detail = make("span", "forage-detail");
    route.append(arrow, detail);
    const advisory = make("span", "forage-advisory");
    const action = make("button", "forage-action");
    action.type = "button";
    container.classList.add("forage-guide");
    container.replaceChildren(label, route, advisory, action);
    const view = {select, caption, arrow, detail, advisory, action, tick: -1, session: "", selected: null,
      extraAt: null, manualDock: false, seen: new Set(), optionKey: "", snapshot: null, command: null};
    select.addEventListener("change", () => {
      const kind = select.value;
      view.selected = kind;
      view.manualDock = kind === dock;
      // An explicit selection of an already collected kind requests one more harvest.
      view.extraAt = kind !== dock && view.complete.has(kind) ? view.counts.get(kind) : null;
      render(view.snapshot, container);
    });
    // A select uses arrows and Space natively. Preserve WASD after selection.
    for (const control of [select, action]) {
      for (const event of ["keydown", "keyup"]) {
        control.addEventListener(event, e => {
          if (e.key.startsWith("Arrow") || e.key === " " || e.key === "Enter") e.stopPropagation();
        });
      }
    }
    action.addEventListener("click", () => {
      if (view.command && typeof press === "function") press(view.command);
    });
    views.set(container, view);
    return view;
  }

  // Snapshot arrays are already sorted by ids.sort_by_id. Keep the first
  // candidate at equal distance, as GatherSim._nearest does.
  function nearest(items, pos, accepts) {
    let item = null, range = Infinity;
    for (const entry of items) {
      if (!accepts(entry)) continue;
      const d = distance(pos, entry.pos);
      if (d < range) { item = entry; range = d; }
    }
    return item ? {item, range} : null;
  }

  function catchable(snap, fish, target, free) {
    const meta = snap.meta, net = snap.active_net;
    if (!net) {
      return nearest(fish, snap.player.pos, () => true)?.item.kind === target;
    }
    // Upgraded nets visit every school in ID order, skipping oversized schools.
    let count = 0;
    for (const f of fish) {
      if (distance(snap.player.pos, f.pos) > net.catch_radius) continue;
      const amount = meta.fish_yield[f.kind];
      if (amount > free) continue;
      if (f.kind === target) return true;
      free -= amount;
      if (++count >= net.max_schools) break;
    }
    return false;
  }

  function track(view, snap) {
    const meta = snap.meta, plan = snap.day_plan?.ingredients;
    const planned = plan !== undefined;
    const counts = new Map();
    for (const item of snap.hold || []) {
      const kind = item.kind || item;
      counts.set(kind, (counts.get(kind) || 0) + 1);
    }
    const nodes = snap.nodes || [], fish = snap.fish || [];
    const nodeKinds = new Set(nodes.map(n => n.kind));
    for (const kind of [...nodeKinds, ...fish.map(f => f.kind), ...counts.keys()]) view.seen.add(kind);
    const kinds = planned ? Object.keys(plan) : [...view.seen];
    const free = snap.hold_capacity - (snap.hold_count ?? snap.hold?.length ?? 0);
    const needed = kind => planned ? plan[kind] : 1;
    const fits = kind => free >= (meta.fish_yield?.[kind] ?? meta.node_yield ?? 1);
    const complete = new Set(kinds.filter(k => (counts.get(k) || 0) >= needed(k)));
    const targets = new Map();
    for (const k of kinds) {
      const isFish = !nodeKinds.has(k) && (Object.hasOwn(meta.fish_yield || {}, k) || fish.some(f => f.kind === k));
      const target = nearest(isFish ? fish : nodes, snap.player.pos, e => e.kind === k && (isFish || e.ready !== false));
      targets.set(k, {isFish, target});
    }
    // Keep tracking a moving school or a regrowing plant until the selected
    // quantity is in the basket. Prefer a reachable source when choosing anew.
    const selected = view.selected;
    const extraPending = view.extraAt !== null && (counts.get(selected) || 0) <= view.extraAt;
    const keep = kinds.includes(selected) && fits(selected) && (!complete.has(selected) || extraPending);
    if (!view.manualDock && !keep) {
      const missing = kinds.filter(k => !complete.has(k) && fits(k));
      let best = null, nearestRange = Infinity;
      for (const kind of missing) {
        const target = targets.get(kind).target;
        if (target && target.range < nearestRange) { best = kind; nearestRange = target.range; }
      }
      view.selected = best || missing[0] || dock;
      view.extraAt = null;
    }
    view.counts = counts;
    view.complete = complete;
    return {meta, planned, plan, counts, kinds, free, targets, nodes, fish, complete, fits};
  }

  function render(snap, container) {
    if (!container) return;
    if (!snap?.player?.pos || !snap.meta || (snap.phase || snap.mode) !== "gather") {
      container.hidden = true;
      views.delete(container);
      return;
    }
    const session = [snap.mode, snap.day ?? "", snap.phase || snap.mode].join("/");
    let view = views.get(container);
    if (!view || view.session !== session || snap.tick < view.tick || (snap.menu_pending && !view.snapshot?.menu_pending)) {
      view = newView(container);
    }
    container.hidden = false;
    view.snapshot = snap;
    view.tick = snap.tick;
    view.session = session;
    const {meta, planned, plan, counts, kinds, free, targets, nodes, fish, complete, fits} = track(view, snap);
    const {player} = snap;
    text(view.caption, planned ? "Theo dõi thực đơn" : "Tìm nguyên liệu");
    const options = kinds.map(k => {
      const count = counts.get(k) || 0;
      const value = planned ? count + "/" + plan[k] : count + " trong giỏ";
      return [k, name(k) + " · " + value];
    });
    options.push([dock, "Trở về bến"]);
    const optionKey = JSON.stringify(options);
    if (optionKey !== view.optionKey) {
      view.select.replaceChildren(...options.map(([value, title]) => new Option(title, value)));
      view.optionKey = optionKey;
    }
    if (view.select.value !== view.selected) view.select.value = view.selected;
    const toDock = view.selected === dock;
    const info = targets.get(view.selected);
    const targetPos = toDock ? meta.dock_pos : info?.target?.item.pos;
    container.dataset.targetId = toDock ? dock : info?.target?.item.id || "";
    const atSurface = player.at_surface ?? player.pos[1] <= meta.surface_depth;
    let advisory = "", command = "", buttonLabel = "";
    if (targetPos) {
      const dx = targetPos[0] - player.pos[0], dd = targetPos[1] - player.pos[1];
      const range = Math.hypot(dx, dd);
      const [arrow, description] = range < .05 ? ["◎", "Tại mục tiêu"]
        : directions[(Math.round(Math.atan2(dd, dx) / (Math.PI / 4)) + 8) % 8];
      text(view.arrow, arrow);
      view.arrow.setAttribute("aria-label", description);
      view.arrow.title = description;
      const depth = targetPos[1] === 0 ? "mặt nước" : "sâu " + meters(targetPos[1]);
      text(view.detail, meters(range) + " · " + depth);
      if (toDock) {
        if (range <= meta.dock_radius) { command = "interact"; buttonLabel = "Cập bến"; }
        if (!view.manualDock) {
          if (kinds.length && complete.size === kinds.length) advisory = planned ? "Đã đủ nguyên liệu hôm nay." : "Đã thu đủ các loại đã gặp.";
          else if (kinds.length && !kinds.some(k => !complete.has(k) && fits(k))) advisory = "Giỏ không đủ chỗ cho mục tiêu tiếp theo.";
        }
      } else if (info.isFish && range <= (snap.active_net?.catch_radius ?? meta.catch_radius)) {
        if (atSurface) advisory = "Lặn xuống để bắt cá.";
        else if (player.catch_cd_ticks > 0) advisory = "Chờ vợt sẵn sàng.";
        else if (!catchable(snap, fish, view.selected, free)) advisory = "Bơi sát đàn cá đã chọn hơn.";
        else { command = "catch"; buttonLabel = "Bắt " + name(view.selected); }
      } else if (!info.isFish && range <= meta.interact_radius) {
        if (!atSurface) advisory = "Bơi lên mặt nước để hái.";
        else if (meta.dock_pos && distance(player.pos, meta.dock_pos) <= meta.dock_radius) advisory = "Ra khỏi vùng bến để hái.";
        else if (nearest(nodes, player.pos, n => n.ready !== false)?.item.kind !== view.selected) advisory = "Bơi sát cây đã chọn hơn.";
        else { command = "interact"; buttonLabel = "Hái " + name(view.selected); }
      }
    } else {
      text(view.arrow, "…");
      view.arrow.setAttribute("aria-label", "Đang tìm");
      view.arrow.title = "";
      text(view.detail, toDock ? "Chưa có vị trí bến." : info?.isFish ? "Chưa thấy đàn cá này." : "Chưa có cây sẵn sàng để hái.");
    }
    text(view.advisory, advisory);
    view.advisory.hidden = !advisory;
    view.command = snap.state === "paused" || snap.finished || snap.menu_pending || snap.intro_pending ? "" : command;
    text(view.action, buttonLabel);
    view.action.hidden = !view.command;
  }

  window.ForageGuide = {render, reset(container) { views.delete(container); }};
})();
