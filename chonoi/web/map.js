// A live river section and café floor plan. World coordinates always come from
// the snapshot. Only the chart's paper, current marks and floorboards are art.
(() => {
  "use strict";
  const C = {
    ink: "#102f36", player: "#fff6d8", dock: "#e8be85", node: "#b7df86",
    fish: "#79dcdb", monster: "#ff8178", stove: "#ffa470", table: "#9bd6fb", route: "#ffd169",
  };
  const names = {
    bong_dien_dien: "Điên điển", bong_sung: "Bông súng", keo_neo: "Kèo nèo",
    ca_linh: "Cá linh", ca_loc: "Cá lóc", ca_keo: "Cá kèo", ca_sau: "Cá sấu", ran: "Rắn",
  };
  const cache = new WeakMap();
  const xy = p => Array.isArray(p) && p.length >= 2 && Number.isFinite(p[0]) && Number.isFinite(p[1]);
  const number = new Intl.NumberFormat("vi-VN", {maximumFractionDigits: 1});
  const format = x => number.format(x);
  const font = (px, bold = false) => (bold ? "650 " : "500 ") + px + "px system-ui, sans-serif";

  function line(g, x0,y0,x1,y1, color, width = 1) {
    g.beginPath(); g.moveTo(x0,y0); g.lineTo(x1,y1);
    g.strokeStyle = color; g.lineWidth = width; g.stroke();
  }
  function path(g, points, fill, stroke, width = 1) {
    g.beginPath(); g.moveTo(...points[0]);
    for (let i=1; i<points.length; i++) g.lineTo(...points[i]);
    g.closePath();
    if(fill) {g.fillStyle=fill; g.fill();}
    if(stroke) {g.strokeStyle=stroke; g.lineWidth=width; g.stroke();}
  }
  function circle(g,x,y,r,fill,stroke,width=1) {
    g.beginPath(); g.arc(x,y,r,0,2*Math.PI);
    if(fill) {g.fillStyle=fill; g.fill();}
    if(stroke) {g.strokeStyle=stroke; g.lineWidth=width; g.stroke();}
  }
  function gridTicks(a,b,target) {
    const exact = (b-a)/target, unit = 10**Math.floor(Math.log10(exact));
    const step = [1,2,2.5,5,10].map(n=>n*unit).find(n=>n>=exact) || unit*10;
    const ticks = [a];
    for(let i=Math.floor(a/step)+1; i*step < b-step*.00001; i++) ticks.push(i*step);
    ticks.push(b);
    return ticks;
  }
  function chartLayout(w,h,bounds,room,large) {
    const tiny = w<190 || h<99;
    const full = large && !tiny;
    const compact = !full || w<360;
    const l=tiny?19:full?40:26, r=tiny?8:full?28:13;
    const top=tiny?11:full?35:17, bottom=tiny?15:full?33:21;
    const [x0,x1]=bounds.x, [y0,y1]=room ? bounds.z : bounds.d;
    const aw=Math.max(1,w-l-r), ah=Math.max(1,h-top-bottom);
    // Preserve the room's floor proportions. A river section has independently
    // marked horizontal distance and depth scales, like a hydrographic profile.
    const scale=Math.min(aw/(x1-x0),ah/(y1-y0));
    const pw=room ? (x1-x0)*scale : aw, ph=room ? (y1-y0)*scale : ah;
    const left=l+(aw-pw)/2, y=top+(ah-ph)/2;
    return {w,h,left,top:y,right:left+pw,bottom:y+ph,pw,ph,x0,x1,y0,y1,room,full,tiny,compact,
      sx:x=>left+(x-x0)/(x1-x0)*pw, sy:v=>y+(room?(y1-v):(v-y0))/(y1-y0)*ph};
  }
  function riverPaper(g,p) {
    const {left:x,top:y,pw:w,ph:h}=p;
    const wash=g.createLinearGradient(0,y,0,y+h);
    wash.addColorStop(0,"#487f78"); wash.addColorStop(.24,"#396e70");
    wash.addColorStop(.65,"#255360"); wash.addColorStop(1,"#173b4b");
    g.fillStyle=wash; g.fillRect(x,y,w,h);
    // Block-printed bands suggest the channel behind the swimmer. They carry
    // no world markers or barriers; the marked scale carries the actual depth.
    for(let n=0;n<5;n++) {
      g.beginPath();
      for(let j=0;j<=80;j++) {
        const t=j/80, yy=y+h*(.19+n*.179+.026*Math.sin(9*t+n*.81)+.016*Math.sin(17*t-n*.65));
        if(j===0) g.moveTo(x,yy); else g.lineTo(x+t*w,yy);
      }
      g.lineTo(x+w,y+h);g.lineTo(x,y+h);g.closePath();
      g.fillStyle=n%2?"#112f3b11":"#112f3b1b";g.fill();
    }
    for(let k=0;k<4;k++) {
      for(let j=0;j<(p.full?12:6);j++) {
        const a=(j+.21+(k%2)*.54)/(p.full?12:6);
        if(a>.97) continue;
        const px=x+a*w, py=y+h*(.16+k*.22+.025*Math.cos(j*1.7));
        const d=p.full?5.4:2.6;
        g.beginPath();g.moveTo(px-d*1.7,py);
        g.bezierCurveTo(px-d*.9,py+d*.54,px-d*.6,py-d*.62,px,py);
        g.bezierCurveTo(px+d*.5,py+d*.40,px+d,py-d*.4,px+d*1.5,py);
        g.strokeStyle="#b1dfce30";g.lineWidth=p.full?.9:.7;g.stroke();
      }
    }
    // Far-bank silhouettes sit above the surface, outside the navigable section.
    g.fillStyle="#294c43";g.fillRect(x,y-(p.full?8:4),w,p.full?8:4);
    const h0=p.full?6.5:3.2;
    for(const t of [.19,.37,.42,.66,.82,.87]) {
      const px=x+w*t, b=y-h0*.7;
      path(g,[[px-2*h0,b],[px-.8*h0,b-h0],[px+.9*h0,b-h0*.98],[px+2*h0,b]],"#74927a");
      g.fillStyle="#567965";g.fillRect(px-h0*1.1,b,h0*2.2,h0*.66);
      line(g,px-h0*.69,b,px-h0*.69,y,"#9aaa86",.7);
      line(g,px+h0*.7,b,px+h0*.7,y,"#9aaa86",.7);
    }
    line(g,x,y,x+w,y,"#a6c9a8",p.full?1.5:1);
  }
  function roomPaper(g,p) {
    const {left:x,top:y,pw:w,ph:h}=p;
    const wash=g.createLinearGradient(x,y,x+w,y+h);
    wash.addColorStop(0,"#546361");wash.addColorStop(.65,"#435758");wash.addColorStop(1,"#354b4d");
    g.fillStyle=wash;g.fillRect(x,y,w,h);
    // Quiet plank joints make the indoor floor legible even at thumbnail size.
    const rows=p.full?14:8;
    for(let n=0;n<rows;n++) {
      const py=y+n*h/rows;
      line(g,x,py,x+w,py,"#bdc7a521",.8);
      for(let j=1;j<=3;j++) {
        const px=x+w*((j-(n%3)*.31)/3.2);
        line(g,px,py,px,py+h/rows,"#c8c7a521",.8);
      }
    }
    g.strokeStyle="#1d3738";g.lineWidth=p.full?5:3;g.strokeRect(x,y,w,h);
    g.strokeStyle="#c1ac7f";g.lineWidth=1;g.strokeRect(x,y,w,h);
    // Paired rails at the room corners are part of the cartographic frame.
    const d=Math.min(13,w*.11,h*.14);
    for(const [a,b] of [[0,0],[1,0],[0,1],[1,1]]) {
      const xx=x+w*a,yy=y+h*b;
      line(g,xx,yy,xx+d*(a?-1:1),yy,"#efe0b0",2);
      line(g,xx,yy,xx,yy+d*(b?-1:1),"#efe0b0",2);
    }
  }
  function background(g,p) {
    const {w,h,left,top,right,bottom,room,full,tiny}=p;
    g.fillStyle=room?"#1e3336":"#19363b";g.fillRect(0,0,w,h);
    if(room) roomPaper(g,p); else riverPaper(g,p);
    const xs=gridTicks(p.x0,p.x1,Math.max(2,Math.min(10,Math.floor(p.pw/(full?65:46)))));
    const ys=gridTicks(p.y0,p.y1,Math.max(2,Math.min(6,Math.floor(p.ph/(full?48:27)))));
    g.font=font(tiny?8:full?11:9);
    g.textBaseline="middle";
    // Keep labels for the endpoints even when a non-round bound lies near a grid tick.
    for(let i=0;i<xs.length;i++) {
      const x=p.sx(xs[i]),end=i===0||i===xs.length-1;
      if(!end && Math.min(x-left,right-x)<(full?28:19)) continue;
      if(!room&&!end) line(g,x,top+1,x,bottom,"#c0ded527",.75);
      line(g,x,bottom,x,bottom+3,"#a2b7ae",.8);
      g.fillStyle="#ced9c6";g.textAlign=i===0?"left":i===xs.length-1?"right":"center";
      g.fillText(format(xs[i])+(i===xs.length-1?" m":""),x,bottom+(full?12:9));
    }
    for(let i=0;i<ys.length;i++) {
      const y=p.sy(ys[i]),end=i===0||i===ys.length-1;
      if(!end && Math.min(y-top,bottom-y)<(full?18:13)) continue;
      if(!room&&!end) {
        g.setLineDash([2,4]);line(g,left,y,right,y,"#d0e5d84d",.8);g.setLineDash([]);
      }
      line(g,left-3,y,left,y,"#a2b7ae",.8);
      g.fillStyle="#ced9c6";g.textAlign="right";
      g.fillText(format(ys[i]),left-5,y);
    }
    if(full) {
      g.font=font(11,true);g.fillStyle="#d7dec5";g.textAlign="left";
      g.fillText(room?"↑ Bắc · z (m)":"↓ Độ sâu (m)",left,Math.max(9,top-21));
      g.font=font(10);g.textAlign="right";
      g.fillText(room?"Đông →":"Dọc sông →",right,bottom+25);
    }
  }

  function marker(g,m,r) {
    const k=m.type, ink=C.ink, color=C[k];
    g.save();g.translate(m.x,m.y);
    g.scale(r,r);g.lineJoin="round";g.lineCap="round";
    if(k==="player") {
      g.rotate(m.angle || 0);
      circle(g,0,0,1.21,"#10333abf","#fff6d8aa",.13);
      path(g,[[1.15,0],[-.80,-.77],[-.50,0],[-.80,.77]],color,ink,.15);
    } else if(k==="dock") {
      line(g,0,0,0,-1.13,"#f1d5a4",.18);
      path(g,[[-.95,-1.25],[0,-2.00],[.95,-1.25]],color,ink,.18);
      path(g,[[-.7,-1.20],[.7,-1.20],[.7,-.48],[-.7,-.48]],ink,color,.14);
      line(g,-.9,-.43,.9,-.43,color,.23);
      circle(g,0,0,.22,color,ink,.1);
    } else if(k==="node") {
      if(m.ready===false) g.globalAlpha=.47;
      path(g,[[0,.82],[-.83,-.1],[-.9,-.64],[-.30,-.58],[0,-.27],[.56,-.83],[.95,-.76],[.77,.04]],color,ink,.18);
      line(g,-.05,.56,.44,-.37,"#457853",.14);
    } else if(k==="fish") {
      if(m.flip) g.scale(-1,1);
      path(g,[[-.47,0],[-1.15,-.60],[-1.12,.59]],color,ink,.17);
      g.beginPath();g.moveTo(-.71,0);g.bezierCurveTo(-.22,-.74,.57,-.65,1.02,0);
      g.bezierCurveTo(.58,.64,-.21,.73,-.71,0);g.closePath();
      g.fillStyle=color;g.fill();g.strokeStyle=ink;g.lineWidth=.16;g.stroke();
      circle(g,.5,-.10,.115,ink);
    } else if(k==="monster") {
      path(g,[[0,-1],[1,.81],[-1,.81]],color,ink,.18);
      line(g,0,-.4,0,.16,ink,.18);circle(g,0,.48,.10,ink);
    } else if(k==="stove") {
      path(g,[[-.87,.52],[-.7,.98],[.7,.98],[.88,.52]],ink,color,.13);
      g.beginPath();g.moveTo(-.63,.37);g.bezierCurveTo(-1.1,-.22,-.04,-.71,-.1,-1.14);
      g.bezierCurveTo(.34,-1.04,.42,-.60,.44,-.40);g.lineTo(.66,-.76);
      g.bezierCurveTo(1.06,-.25,1.01,.19,.67,.38);g.closePath();
      g.fillStyle=color;g.fill();g.strokeStyle=ink;g.lineWidth=.14;g.stroke();
    } else {
      for(const s of [-1,1]) {line(g,-.42,s*.96,.42,s*.96,color,.19);}
      path(g,[[-.8,-.66],[.8,-.66],[.8,.66],[-.8,.66]],color,ink,.18);
      circle(g,.13,-.02,.20,"#497787");
    }
    g.restore();
  }
  function label(g,p,m,word,reserved,marks,important) {
    const fs=p.full?(p.w<400?11:12):9;
    g.font=font(fs,important);
    const w=g.measureText(word).width+8,h=fs+5;
    const gap=m.radius+(important?5:3);
    const offsets=[[gap,-h/2],[-w-gap,-h/2],[-w/2,gap],[-w/2,-h-gap],[gap,gap],[-w-gap,gap]];
    const overlap=(a,b)=>a.x<b.x+b.w && b.x<a.x+a.w && a.y<b.y+b.h && b.y<a.y+a.h;
    for(const [dx,dy] of offsets) {
      const r={x:m.x+dx,y:m.y+dy,w,h};
      if(r.x<p.left || r.x+w>p.right || r.y<p.top+2 || r.y+h>p.bottom-1) continue;
      if(reserved.some(a=>overlap(a,r)) || marks.some(a=>a!==m && Math.abs(a.x-r.x-w/2)<w/2+a.radius*.67
        && Math.abs(a.y-r.y-h/2)<h/2+a.radius*.67)) continue;
      g.fillStyle=important?"#102e35ed":"#16383fd9";g.beginPath();g.roundRect(r.x,r.y,w,h,3);g.fill();
      g.fillStyle=important?C.route:"#e5eed9";g.textBaseline="middle";g.textAlign="left";
      g.fillText(word,r.x+4,r.y+h/2+.2);reserved.push(r);return true;
    }
    return false;
  }
  function marksFor(s,source,p) {
    const result=[];
    function add(type, data, label) {
      if(!xy(data?.pos)) return;
      result.push({id:data.id,type,label,pos:data.pos,ready:data.ready,x:p.sx(data.pos[0]),y:p.sy(data.pos[1]),
        flip:Math.cos((data.heading_deg||0)*Math.PI/180)<0});
    }
    if(p.room) {
      for(const f of s.tables || source.tables || []) add("table",f,"Bàn "+f.id);
      for(const f of s.stoves || source.stoves || []) add("stove",f,"Bếp "+f.id);
    } else {
      add("dock",{id:"@dock",pos:source.dock_pos},"Bến");
      for(const f of s.nodes || []) add("node",f,names[f.kind] || f.kind || f.id);
      for(const f of s.fish || []) add("fish",f,names[f.kind] || f.kind || f.id);
      for(const f of s.monsters || []) add("monster",f,names[f.kind] || "Thủy quái");
    }
    add("player",{id:"@player",pos:s.player?.pos},"Út Sen");
    const player=result.find(m=>m.type==="player");
    if(player) {
      const deg=s.player.heading_deg;
      const vel=s.player.vel || [];
      player.angle=Number.isFinite(deg) ? deg*Math.PI/180 : Math.hypot(...vel)>.01 ? Math.atan2(-vel[1],vel[0]) : -Math.PI/2;
    }
    for(const m of result) {
      const base=p.full ? Math.max(6,Math.min(9,p.w/70)) : Math.max(3.8,Math.min(5.8,p.w/43));
      m.radius=(m.type==="player"?1.19:m.type==="monster"?1.08:1)*base;
    }
    return result;
  }
  function draw(canvas,snap,targetId,opts={}) {
    if(!canvas) return;
    const g=canvas.getContext("2d");
    if(!g) return;
    const w=canvas.clientWidth,h=canvas.clientHeight;
    if(w<=0||h<=0) return;
    const dpr=Math.min(window.devicePixelRatio||1,3);
    const bw=Math.max(1,Math.round(w*dpr)), bh=Math.max(1,Math.round(h*dpr));
    if(canvas.width!==bw || canvas.height!==bh) {
      canvas.width=bw;canvas.height=bh;
      // Default-sized canvases otherwise grow by DPR every time they are drawn.
      if(canvas.clientWidth!==w) canvas.style.width=w+"px";
      if(canvas.clientHeight!==h) canvas.style.height=h+"px";
    }
    g.setTransform(bw/w,0,0,bh/h,0,0);
    const source=snap?.shop_room || snap?.meta;
    const bounds=source?.bounds, room=Boolean(bounds?.z);
    if(!xy(bounds?.x) || !xy(room?bounds.z:bounds?.d) || bounds.x[1]<=bounds.x[0]
      || (room?bounds.z:bounds.d)[1]<=(room?bounds.z:bounds.d)[0]) {
      g.fillStyle="#19363b";g.fillRect(0,0,w,h);g.fillStyle="#e4dfc4";g.font=font(13);g.textAlign="center";
      g.fillText("Đang tải bản đồ…",w/2,h/2);canvas.setAttribute("aria-label","Đang tải bản đồ");return;
    }
    const key=[w,h,dpr,room,opts.large,...bounds.x,...(room?bounds.z:bounds.d)].join("/");
    let page=cache.get(canvas);
    if(!page || page.key!==key) {
      const paper=document.createElement("canvas");paper.width=bw;paper.height=bh;
      const layer=paper.getContext("2d");layer.setTransform(bw/w,0,0,bh/h,0,0);
      const layout=chartLayout(w,h,bounds,room,Boolean(opts.large));background(layer,layout);
      page={key,paper,layout};cache.set(canvas,page);
    }
    const p=page.layout;
    g.drawImage(page.paper,0,0,w,h);
    const marks=marksFor(snap,source,p);
    const player=marks.find(m=>m.type==="player"), target=marks.find(m=>m.id===targetId || (targetId==="dock"&&m.type==="dock"));
    const routeLength=player&&target ? Math.hypot(player.pos[0]-target.pos[0],player.pos[1]-target.pos[1]) : null;
    if(player&&target) {
      const args=[player.x,player.y,target.x,target.y];
      line(g,...args,"#193539bf",p.full?4:3);
      g.setLineDash(p.full?[5,4]:[3,2]);line(g,...args,C.route,p.full?2:1.5);g.setLineDash([]);
    }
    if(target) {
      const r=target.radius*(target.type==="dock"?2:1.59);
      circle(g,target.x,target.y,r,C.route+"1e","#20383a",p.full?3.6:2.8);
      circle(g,target.x,target.y,r,null,C.route,p.full?1.8:1.35);
    }
    // Player stays legible when standing on a station or moored at the dock.
    for(const m of marks) marker(g,m,m.radius);
    const labels=[];
    if(target) label(g,p,target,target.label+(p.full&&routeLength!==null?" · "+format(routeLength)+" m":""),labels,marks,true);
    if(player&&p.full) label(g,p,player,"Út Sen",labels,marks,false);
    const named=new Set(target ? [target.label] : []);
    for(const m of marks) {
      if(m===target || m===player) continue;
      if(p.full || m.type==="dock" || (room&&!p.tiny)) {
        if(!room&&named.has(m.label)) continue;
        if(label(g,p,m,room&&!p.full?m.id:m.label,labels,marks,false)) named.add(m.label);
      }
    }
    const where=player ? " Út Sen ở x "+format(player.pos[0])+" m, "+(room?"z ":"độ sâu ")+format(player.pos[1])+" m." : "";
    const destination=target ? " Mục tiêu "+target.label+(routeLength===null?"":", cách "+format(routeLength)+" m")+"." : "";
    const aria=(room?"Sơ đồ quán, hướng Bắc ở trên.":"Mặt cắt sông, độ sâu tăng xuống dưới.")+where+destination;
    if(canvas.getAttribute("aria-label")!==aria) canvas.setAttribute("aria-label",aria);
  }
  window.RiverAtlas={draw};
})();
