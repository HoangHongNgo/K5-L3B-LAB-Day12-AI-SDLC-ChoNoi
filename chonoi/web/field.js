"use strict";

let atlasTab = "map";
const atlasButtons = {map:"Bản đồ", mission:"Nhiệm vụ", controls:"Điều khiển"};
const reservationsText = {scheduled:"Đã đặt", holding:"Giữ bàn", waiting:"Đang chờ", served:"Đã phục vụ", failed:"Lỡ đơn"};
const byId = id => document.getElementById(id);
try { document.documentElement.classList.toggle("high-contrast", localStorage.getItem("chonoi-contrast")==="on"); } catch {}

function openAtlas(tab) {
  atlasTab = tab;
  if (screenName === "menu") renderAtlas(true);
  else if (screen.hidden && snap) { clearHeld(); press("pause"); }
}
byId("hud-menu").onclick = () => openAtlas("mission");
byId("mini-map").onclick = () => openAtlas("map");
document.querySelector(".lobby-atlas").onclick = () => openAtlas("map");

function mapTarget() {
  const morning = snap.phase === "gather";
  const guide = byId(morning ? "forage-guide" : "service-guide");
  if (dayStarted && guide.dataset.targetId) return guide.dataset.targetId;
  return morning ? snap.nodes?.find(node => node.ready)?.id || "@dock" : null;
}
function paintCharts() {
  if (!snap || !window.RiverAtlas) return;
  const canvas = screenName === "menu" ? byId("lobby-chart")
    : ["atlas-lobby","pause"].includes(screenName) ? byId("large-chart") : !hud.hidden ? byId("mini-chart") : null;
  if (canvas && canvas.clientWidth) RiverAtlas.draw(canvas, snap, mapTarget(), {large:canvas.id !== "mini-chart"});
}
function toggleContrast(button) {
  const enabled = document.documentElement.classList.toggle("high-contrast");
  button.setAttribute("aria-pressed",String(enabled));
  button.textContent = "Tương phản cao · " + (enabled ? "Bật" : "Tắt");
  try { localStorage.setItem("chonoi-contrast",enabled ? "on" : "off"); } catch {}
}
function renderAtlas(lobby) {
  const tabs = element("nav",""); tabs.id = "atlas-tabs"; tabs.setAttribute("aria-label","Mục sổ tay");
  const body = element("div",""); body.id = "atlas-body";
  const pages = Object.entries(atlasButtons).filter(([id])=>id !== "map" || snap.phase !== "shop");
  if (!pages.some(([id])=>id===atlasTab)) atlasTab="mission";
  for (const [id,label] of pages) {
    const button = action(label, () => { atlasTab=id; fillAtlas(); });
    button.dataset.tab=id; tabs.append(button);
  }
  const buttons = lobby ? [action("Về bến",showMenu)] : [action("Tiếp tục",()=>press("pause")),action("Về màn hình chính",returnToMenu,true)];
  showScreen(lobby ? "atlas-lobby" : "pause","Sổ tay Chợ Nổi",[tabs,body],buttons);
  screen.dataset.page="pause";
  byId("panel-kicker").textContent=lobby ? "Trước chuyến đi" : "Đã tạm dừng";
  fillAtlas();
}
function fillAtlas() {
  for(const button of byId("atlas-tabs").children) button.setAttribute("aria-pressed",String(button.dataset.tab===atlasTab));
  const body=byId("atlas-body"); body.replaceChildren();
  const morning=snap.phase==="gather";
  if(atlasTab==="map") {
    const chart=element("canvas",""); chart.id="large-chart";
    const legend=element("div",""); legend.className="map-legend";
    const symbols=morning ? ["⌂ Bến","❧ Cây hái","◁ Cá","⚠ Thủy quái"] : ["♨ Bếp","□ Bàn ăn"];
    for(const label of ["➤ Út Sen","◌ Mục tiêu",...symbols]) legend.append(element("span",label));
    body.append(element("h2",morning ? "Luồng sông · khoảng cách và độ sâu" : "Mặt bằng quán · nhìn từ trên"),chart,legend);
    paintCharts();
  } else if(atlasTab==="controls") {
    const contrast=action("",()=>toggleContrast(contrast),true);
    const enabled=document.documentElement.classList.contains("high-contrast");
    contrast.textContent="Tương phản cao · "+(enabled?"Bật":"Tắt"); contrast.setAttribute("aria-pressed",String(enabled));
    body.append(listSection("Điều khiển",[
      "WASD hoặc mũi tên để di chuyển. Trên điện thoại dùng cụm phím ở góc màn hình.",
      "Buổi sáng dùng E để hái hoặc cập bến, Space để bắt cá. Nổi lên để hồi oxy.",
      "Buổi tối dùng E tại bếp để nấu hoặc lấy món, rồi đến đúng bàn và nhấn E để giao.",
      "M mở bản đồ. Esc hoặc P mở Sổ tay và tạm dừng đồng hồ."
    ],""),contrast);
  } else {
    if(snap.phase==="shop") body.append(element("p","Chọn nâng cấp trong ngân sách rồi đóng tiệm để sang Ngày kế."));
    else if(morning) body.append(listSection("Gom cho bữa chiều",ingredientLines(snap.day_plan?.ingredients),"Hái cây ven sông và bắt đàn cá. Đưa giỏ về bến trước khi hết giờ."));
    else body.append(element("p",byId("service-guide").innerText.trim() || "Đón khách, kiểm nguyên liệu, nấu ở bếp rồi bưng món đến bàn ghi trên phiếu."));
    const bag=morning?snap.hold:snap.stock;
    const items=Array.isArray(bag)?bag.filter(item=>typeof item==="object"):[];
    body.append(listSection("Độ tươi từng nguyên liệu",items.map(item=>item.id+" · "+(KIND_NAME[item.kind]||item.kind)+" · "+freshLabel(item)),"Chưa có nguyên liệu."));
    if(snap.reservations?.length) body.append(listSection("Khách đặt trước",snap.reservations.map(bookingLabel),""));
  }
}
function freshLabel(item) {
  const value = item.fresh.toLocaleString("vi-VN",{maximumFractionDigits:2});
  return (item.fresh < snap.freshness?.spoiled_below ? "Ươn · " : "") + value + "/100";
}
function bookingLabel(r) {
  return r.id+" · "+r.table_id+" · "+dishName(r.dish_id)+" · "+(reservationsText[r.state]||r.state)+" · "+fmtTime(r.arrival_tick);
}
function renderFieldStatus(state, monster) {
  const morning=state.phase==="gather", warnings=[];
  if(monster) warnings.push("⚠ Thủy quái ở gần");
  if(morning && state.player.oxygen_ticks <= state.player.oxygen_max_ticks/4) warnings.push("⬆ Oxy sắp hết · Nổi lên");
  if(!morning) for(const c of state.customers || []) {
    if(c.state==="waiting" && c.patience_ticks_left <= state.meta.patience_s*60/4) warnings.push("⚠ Bàn "+c.table_id+" · Khách sắp giận");
  }
  const warning=byId("field-warning");
  warning.hidden=!warnings.length; setText(warning,warnings.join("  /  "));
  const bag=morning?state.hold:state.stock;
  const items=Array.isArray(bag)?bag.filter(item=>typeof item==="object"):[];
  const least=items.reduce((a,b)=>a && a.fresh<b.fresh?a:b,null);
  const summary=least ? "Độ tươi thấp nhất · "+(KIND_NAME[least.kind]||least.kind)+" · "+freshLabel(least) : "Độ tươi · Giỏ trống";
  setText(byId("fresh-summary"),least || morning ? summary : "Độ tươi · Kho trống");
  const bookings=byId("booking-summary");
  const lines=(state.reservations||[]).map(bookingLabel);
  bookings.hidden=!lines.length;
  setText(bookings,lines.join("  /  "));
}
