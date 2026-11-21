"use strict";

// An opening menu restricts future orders. The simulation reserves the ingredients.
function openingBoard(state, stock) {
  const content = document.createElement("div");
  content.className = "opening-board";
  const available = new Set(state.opening_menu || []);
  const candidates = Object.keys(state.day_plan?.dishes || state.menu);
  const chosen = new Set(available);
  const openButton = action("Mở quán", () => continueDay([...chosen]));

  const stockText = ingredientLines(stock).join(", ");
  content.append(element("p", stockText ? "Kho khả dụng · " + stockText : "Kho khả dụng đang trống."));
  const choices = document.createElement("fieldset");
  choices.append(element("legend", "Chọn món nhận khách"));
  for (const id of candidates) {
    const dish = state.menu[id];
    if (!dish) continue;
    const row = document.createElement("label");
    const box = document.createElement("input");
    box.type = "checkbox";
    box.value = id;
    box.checked = available.has(id);
    box.disabled = !box.checked;
    box.addEventListener("change", () => {
      if (box.checked) chosen.add(id);
      else chosen.delete(id);
      openButton.disabled = available.size > 0 && chosen.size === 0;
    });
    const body = document.createElement("span");
    const missing = {};
    for (const [kind, need] of Object.entries(dish.recipe)) {
      if (need > (stock[kind] || 0)) missing[kind] = need - (stock[kind] || 0);
    }
    const detail = box.disabled ? "Thiếu " + ingredientLines(missing).join(", ") : ingredientLines(dish.recipe).join(", ");
    body.append(element("strong", dishName(id)), element("small", detail));
    row.append(box, body, element("span", dish.price + " nghìn"));
    choices.append(row);
  }
  content.append(choices);
  if (!available.size) {
    const note = state.customers?.length
      ? "Nguyên liệu đã giữ cho khách vẫn dùng để nấu các đơn hiện có."
      : "Chưa đủ nguyên liệu cho món nào. Vào quán rồi chọn thu dọn để kết thúc ca sớm.";
    content.append(element("p", note));
  }
  return {content, openButton};
}

const waitTurn = document.getElementById("wait-turn");
waitTurn.addEventListener("click", async () => {
  if (!snap?.can_wait || waitTurn.disabled) return;
  waitTurn.disabled = true;
  clearHeld();
  const {day, phase, tick, service_id} = snap;
  try {
    const response = await fetch("/wait", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({day, phase, tick, service_id}),
    });
    if (!response.ok) flashAction("Ca vừa thay đổi. Kiểm tra đơn hiện tại.");
  } catch {
    flashAction("Chưa kết nối được với quán.");
  } finally {
    waitTurn.disabled = false;
  }
});

let lastFeedbackTick = -1;
let lastShift = "";
let feedbackTimer;
function flashAction(message) {
  const output = document.getElementById("event-feedback");
  clearTimeout(feedbackTimer);
  output.hidden = !message;
  output.textContent = message;
  if (message) feedbackTimer = setTimeout(() => { output.hidden = true; }, 3000);
}

function actionReceipt(event) {
  const d = event.data;
  switch (event.name) {
    case "gather": return "+" + d.amount + " " + (KIND_NAME[d.kind] || d.kind);
    case "fish_caught": return "+" + d.yield + " " + (KIND_NAME[d.kind] || d.kind);
    case "hold_full": return "Giỏ còn " + d.free + " chỗ, cần " + d.required + " chỗ. Hãy về bến.";
    case "spoiled": return (KIND_NAME[d.kind] || d.kind) + " " + d.item_id + " đã ươn";
    case "reservation_arrived": return "Khách đặt trước " + d.reservation_id + " đã đến";
    case "reservation_failed": return "Lỡ đơn đặt trước " + d.reservation_id;
    case "monster_hit": return "Cá sấu vừa tấn công · còn " + d.hp + " máu";
    case "cook_started": return d.stove_id + " đang nấu " + dishName(d.dish_id);
    case "dish_ready": return dishName(d.dish_id) + " đã chín ở " + d.stove_id;
    case "served": return "Đã giao " + dishName(d.dish_id) + " cho bàn " + d.table_id;
    case "paid": return "Bàn " + d.table_id + " trả " + d.amount + " nghìn" + (d.tip ? " · gồm " + d.tip + " nghìn tiền boa" : "");
    case "customer_left": return d.reason === "patience" ? "Khách bàn " + d.table_id + " đã hết kiên nhẫn." : "";
    default: return "";
  }
}

function showRecentAction(state) {
  const shift = [state.mode, state.day, state.phase, state.service_id].join("/");
  if (shift !== lastShift || state.tick < lastFeedbackTick) {
    flashAction("");
  } else if (state.tick > lastFeedbackTick) {
    const fresh = (state.events || []).filter(e => e.tick > lastFeedbackTick && e.phase === state.phase);
    const message = fresh.map(actionReceipt).filter(Boolean).at(-1);
    if (message) flashAction(message);
  }
  lastShift = shift;
  lastFeedbackTick = state.tick;
}
