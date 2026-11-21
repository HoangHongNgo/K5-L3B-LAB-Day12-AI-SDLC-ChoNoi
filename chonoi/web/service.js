// Read-only service tickets for the evening shift. The simulation owns orders and interactions.
(() => {
  "use strict";

  const arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"];
  const metres = new Intl.NumberFormat("vi-VN", {maximumFractionDigits: 1});
  const compare = (a, b) => a < b ? -1 : a > b ? 1 : 0;

  // chonoi.ids.id_key sorts by prefix, numeric suffix and finally the original spelling.
  function compareId(a, b) {
    const left = /^(.*?)(\d+)$/.exec(a);
    const right = /^(.*?)(\d+)$/.exec(b);
    return compare(left?.[1] ?? a, right?.[1] ?? b)
      || compare(left ? BigInt(left[2]) : -1n, right ? BigInt(right[2]) : -1n)
      || compare(a, b);
  }

  function stationsAt(state) {
    const stations = [
      ...(state.stoves || []).map(stove => ({...stove, kind: "bếp", priority: 0})),
      ...(state.tables || []).map(table => ({...table, kind: "bàn", priority: 1})),
    ];
    const [x, z] = state.player.pos;
    for (const station of stations) {
      station.dx = station.pos[0] - x;
      station.dz = station.pos[1] - z;
      station.distance = Math.hypot(station.dx, station.dz);
    }
    stations.sort((a, b) => a.distance - b.distance || a.priority - b.priority || compareId(a.id, b.id));
    // At identical coordinates the simulation always selects the first object.
    return stations.filter((station, i) => !stations.slice(0, i).some(other =>
      other.pos[0] === station.pos[0] && other.pos[1] === station.pos[1]));
  }

  const seconds = ticks => Math.ceil(ticks / 60) + " s";
  function orderTicket(state) {
    const stations = stationsAt(state);
    const customers = state.customers || [];
    const nearest = stations[0]?.distance <= state.meta?.interact_radius ? stations[0] : null;
    const name = dish => window.dishName(dish) || "Món của khách";

    function ticket(stage, label, dish, detail = "", target = null, verb = "") {
      const inRange = !!target && target === nearest;
      if (target) {
        const bearing = (Math.round(Math.atan2(target.dx, target.dz) * 4 / Math.PI) + 8) % 8;
        const location = target.kind + " " + target.id;
        const route = inRange ? "Đã đến " + location
          : arrows[bearing] + " " + metres.format(target.distance) + " m đến " + location;
        detail = [route, detail].filter(Boolean).join(" · ");
      }
      return {stage, label, dish, detail, targetId: target?.id || "", inRange,
        prompt: inRange && verb ? "E · " + verb : ""};
    }

    if (state.hand) {
      const guest = customers.find(c => c.id === state.hand.order_id && c.state === "waiting");
      const table = guest && stations.find(s => s.kind === "bàn" && s.id === guest.table_id);
      return ticket("serve", "Phục vụ" + (guest ? " bàn " + guest.table_id : ""), name(state.hand),
        guest ? "Khách chờ " + seconds(guest.patience_ticks_left) : "", table, "Dọn món cho khách");
    }

    const ready = stations.find(s => s.kind === "bếp" && s.state === "ready");
    if (ready && (state.meta?.carry_limit ?? 1) >= 1) {
      const guest = customers.find(c => c.id === ready.dish?.order_id);
      return ticket("pick", "Bưng món" + (guest ? " cho bàn " + guest.table_id : ""),
        name(ready.dish), "", ready, "Bưng món");
    }

    const order = customers.filter(c => c.state === "waiting" && c.order_status === "reserved")
      .sort((a, b) => a.order_tick - b.order_tick || compareId(a.table_id, b.table_id))[0];
    const idle = stations.find(s => s.kind === "bếp" && s.state === "idle");
    if (order && idle) {
      const duration = state.menu?.[order.dish_id]?.cook_s;
      return ticket("cook", "Nấu cho bàn " + order.table_id, name(order.dish_id),
        duration ? "Nấu " + duration + " s" : "", idle, "Bắt đầu nấu");
    }

    const cooking = stations.filter(s => s.kind === "bếp" && s.state === "cooking")
      .sort((a, b) => a.cook_ticks_left - b.cook_ticks_left || a.distance - b.distance || compareId(a.id, b.id))[0];
    if (cooking) {
      return ticket("cooking", "Chờ món chín", name(cooking.dish),
        "Còn " + seconds(cooking.cook_ticks_left), cooking);
    }

    const eating = customers.filter(c => c.state === "eating")
      .sort((a, b) => a.eat_ticks_left - b.eat_ticks_left || compareId(a.table_id, b.table_id))[0];
    if (eating) {
      return ticket("eating", "Đã phục vụ bàn " + eating.table_id, name(eating.dish_id),
        "Khách tự thanh toán sau " + seconds(eating.eat_ticks_left));
    }
    const blocked = customers.find(c => c.state === "waiting" && c.order_status === "unfulfillable");
    if (blocked) {
      return ticket("unavailable", "Đơn bàn " + blocked.table_id, name(blocked.dish_id),
        "Thiếu nguyên liệu tươi cho món này.");
    }
    const latest = (state.events || []).findLast(e => e.phase === "quan" && e.day === state.day
      && e.tick <= state.tick && ["paid", "no_dish"].includes(e.name));
    if (latest?.name === "paid" && state.tick - latest.tick < 4 * 60) {
      const payment = latest.data;
      return ticket("paid", "Bàn " + payment.table_id + " đã thanh toán",
        "+" + payment.amount + " nghìn", payment.tip ? "Gồm " + payment.tip + " nghìn tiền boa" : "");
    }
    if (latest?.name === "no_dish") {
      return ticket("unavailable", "Chưa có đơn", "Kho thiếu nguyên liệu", "Chuyến sáng sau, hái và bắt theo thực đơn.");
    }
    return ticket("waiting", "Chờ khách gọi món", "", "Khi khách chọn món, phiếu sẽ chỉ đường đến bếp.");
  }

  function render(state, container) {
    if (!container) return "";
    if ((state?.phase || state?.mode) !== "quan" || !state.player?.pos || state.finished) {
      container.hidden = true;
      container.replaceChildren();
      for (const key of ["stage", "targetId", "inRange"]) delete container.dataset[key];
      return "";
    }
    const ticket = orderTicket(state);
    container.hidden = false;
    container.dataset.stage = ticket.stage;
    container.dataset.targetId = ticket.targetId;
    container.dataset.inRange = String(ticket.inRange);
    if (!container.children.length) {
      for (const [tag, className] of [["span", "service-stage"], ["strong", "service-dish"], ["span", "service-detail"]]) {
        const node = document.createElement(tag);
        node.className = className;
        container.append(node);
      }
    }
    [ticket.label, ticket.dish, ticket.detail].forEach((text, i) => {
      const node = container.children[i];
      if (node.textContent !== text) node.textContent = text;
      node.hidden = !text;
    });
    return ticket.prompt;
  }
  window.ServiceGuide = {render};
})();
