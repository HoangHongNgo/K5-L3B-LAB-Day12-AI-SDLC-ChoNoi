// The deck is a stage for the live simulation. All interactive objects use their snapshot positions.
export function createCafe(THREE) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x778b9a);
  scene.fog = new THREE.FogExp2(0x9393a0, 0.0065);
  const camera = new THREE.OrthographicCamera(-12, 12, 8, -8, 0.1, 180);
  const center = new THREE.Vector3(0, 0.35, -0.18);
  camera.position.set(3.6, 20.5, 23);
  camera.lookAt(center);
  const hemi = new THREE.HemisphereLight(0xf3e7ed, 0x887263, 1.28);
  const sun = new THREE.DirectionalLight(0xffcf9f, 2.05);
  sun.position.set(-12, 17, 9);
  scene.add(hemi, sun);

  const shapes = {
    box: new THREE.BoxGeometry(1, 1, 1),
    round: new THREE.CylinderGeometry(0.5, 0.5, 1, 12),
    bowl: new THREE.CylinderGeometry(0.5, 0.32, 1, 12),
    cone: new THREE.ConeGeometry(0.5, 1, 12),
    orb: new THREE.SphereGeometry(0.5, 10, 7),
    leaf: new THREE.OctahedronGeometry(0.5),
    disc: new THREE.CircleGeometry(0.5, 32),
    ring: new THREE.RingGeometry(0.46, 0.5, 40),
  };
  const leaves = new THREE.BufferGeometry();
  leaves.setAttribute("position", new THREE.Float32BufferAttribute([
    0,0,0, .38,.58,-.12, 0,.43,1, 0,0,0, 0,.43,1, -.38,.55,-.1,
    0,0,0, -.38,.55,-.1, 0,1,-.18, 0,0,0, 0,1,-.18, .38,.58,-.12,
  ], 3));
  leaves.computeVertexNormals();
  shapes.frond = leaves;
  const materials = new Map();
  function material(color, glow = false) {
    const key = color + (glow ? 'lit' : '');
    if (!materials.has(key)) {
      materials.set(key, glow
        ? new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide })
        : new THREE.MeshStandardMaterial({ color, roughness: .91, flatShading: true, side: THREE.DoubleSide }));
    }
    return materials.get(key);
  }
  const stage = new THREE.Group();
  const scenery = new THREE.Group();
  scene.add(stage, scenery);
  function part(parent, shape, color, x, y, z, w, h, d, rx = 0, ry = 0, rz = 0, glow = false) {
    const m = new THREE.Mesh(shapes[shape], material(color, glow));
    m.position.set(x, y, z);
    m.scale.set(w, h, d);
    m.rotation.set(rx, ry, rz);
    parent.add(m);
    return m;
  }
  const box = (p,c,x,y,z,w,h,d,rx,ry,rz) => part(p,'box',c,x,y,z,w,h,d,rx,ry,rz);
  const tube = (p,c,x,y,z,w,h,d) => part(p,'round',c,x,y,z,w,h,d);
  const orb = (p,c,x,y,z,w,h,d) => part(p,'orb',c,x,y,z,w,h,d);
  function rod(p, c, a, b, width) {
    const v = new THREE.Vector3(...a), t = new THREE.Vector3(...b);
    const p0 = v.clone().lerp(t, .5);
    const r = tube(p, c, p0.x, p0.y, p0.z, width, t.distanceTo(v), width);
    r.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), t.sub(v).normalize());
    return r;
  }
  function group(parent, x=0, y=0, z=0) {
    const g = new THREE.Group();
    g.position.set(x,y,z);
    parent.add(g);
    return g;
  }
  // Batch repeated plank, roof, and foliage primitives into GPU instances.
  function batch(root) {
    root.updateWorldMatrix(true,true);
    const inverse = root.matrixWorld.clone().invert();
    const buckets = new Map();
    root.traverse(m => {
      if (!m.isMesh) return;
      const key = m.geometry.uuid + m.material.uuid;
      if (!buckets.has(key)) buckets.set(key, {geometry:m.geometry, material:m.material, transforms:[]});
      buckets.get(key).transforms.push(new THREE.Matrix4().multiplyMatrices(inverse, m.matrixWorld));
    });
    root.clear();
    for (const {geometry,material,transforms} of buckets.values()) {
      const mesh = new THREE.InstancedMesh(geometry,material,transforms.length);
      transforms.forEach((matrix, i) => mesh.setMatrixAt(i, matrix));
      mesh.instanceMatrix.needsUpdate = true;
      root.add(mesh);
    }
  }

  const timber = '#784735', dark = '#4a3935', bamboo = '#c49058', red = '#ba4940';
  const jade = '#44847a', cream = '#ffdcaa', black = '#353b3c';
  const wood = ['#c28b64','#b87d59','#cc946a','#bf8660','#c08a65'];
  const hash = i => { const t = Math.sin(i * 127.1 + 311.7) * 43758.5453; return t-Math.floor(t); };
  const shadowMat = new THREE.MeshBasicMaterial({color:'#533a39',transparent:true,opacity:.22,depthWrite:false});
  function shadow(parent,x,z,w,d,y=.021) {
    const m = new THREE.Mesh(shapes.disc, shadowMat);
    m.position.set(x,y,z); m.rotation.x=-Math.PI/2; m.scale.set(w,d,1);
    parent.add(m);
  }

  const waterMat = new THREE.ShaderMaterial({
    uniforms:{seconds:{value:0}},
    vertexShader:`varying vec3 world;void main(){vec4 p=modelMatrix*vec4(position,1.);world=p.xyz;gl_Position=projectionMatrix*viewMatrix*p;}`,
    fragmentShader:`varying vec3 world;uniform float seconds;
      void main(){
        vec2 p=world.xz;
        float tide=sin(p.y*2.0+p.x*.18+seconds*.45)*.5+sin(p.x*.71+p.y*.8-seconds*.38)*.5;
        float line=sin(p.y*9.0+sin(p.x*.9+seconds*.8)+seconds*.8);
        vec3 water=mix(vec3(.022,.083,.122),vec3(.044,.191,.205),.5+tide*.35);
        float glint=smoothstep(.89,.99,line)*smoothstep(.45,.95,sin(p.x*1.7+p.y*.59+sin(p.y*.6)));
        water+=vec3(.053,.106,.098)*glint;
        float lamps=exp(-pow(abs(p.x+8.2+.13*tide)*.76,2.)-pow(abs(p.y-5.3)*.32,2.))
          +exp(-pow(abs(p.x-8.2+.13*tide)*.84,2.)-pow(abs(p.y-4.9)*.33,2.))
          +exp(-pow(abs(p.x-3.+.13*tide)*.90,2.)-pow(abs(p.y+7.)*.34,2.));
        water+=vec3(.71,.31,.07)*lamps*(.17+.73*smoothstep(.38,1.,line));
        gl_FragColor=vec4(water,1.);
        #include <colorspace_fragment>
      }`
  });
  const water = new THREE.Mesh(new THREE.PlaneGeometry(220,220),waterMat);
  water.rotation.x=-Math.PI/2; water.position.y=-1.0; scene.add(water);

  // The gondola-like sampan has sheared sides, upturned ends and a small flat bottom.
  const hull = new THREE.BufferGeometry();
  const corners = [];
  for (const [x,rise,half] of [[-0.5,.34,.012],[-.31,.08,.37],[0,0,.5],[.31,.08,.37],[.5,.34,.012]]) {
    corners.push([x,rise+.4,half],[x,rise,half*.52],[x,rise,-half*.52],[x,rise+.4,-half]);
  }
  const faces=[];
  for(let i=0;i<4;i++) for(let j=0;j<4;j++){
    const a=i*4+j,b=i*4+(j+1)%4;
    faces.push(corners[a],corners[b],corners[a+4],corners[a+4],corners[b],corners[b+4]);
  }
  hull.setAttribute('position',new THREE.Float32BufferAttribute(faces.flat(),3));
  hull.computeVertexNormals();
  shapes.hull=hull;
  function sampan(x,z,angle,length,cargo) {
    const g=group(stage,x,-.83,z); g.rotation.y=angle;
    part(g,'hull',timber,0,0,0,length,1,1.55);
    for (const side of [-1,1]) for(let i=0;i<4;i++){
      const a=corners[i*4+(side===1?0:3)],b=corners[(i+1)*4+(side===1?0:3)];
      rod(g,cream,[a[0]*length,a[1],a[2]*1.55],[b[0]*length,b[1],b[2]*1.55],.062);
    }
    for (let i=-1;i<=1;i++) box(g,bamboo,i*length*.22,.48,0,.18,.09,i===0?1.48:1.16);
    if(cargo) for(let i=0;i<5;i++) {
      const bx=(i-2)*length*.127, bz=(i%2-.5)*.4;
      part(g,'bowl','#a66c3a',bx,.61,bz,.67,.32,.63);
      for(let j=0;j<5;j++) orb(g,i%2?'#efad35':'#789550',bx+Math.cos(j*1.26)*.18,.84,bz+Math.sin(j*1.26)*.16,.26,.23,.26);
    }
    rod(g,bamboo,[-1,.52,-.49],[.8,.67,.83],.055);
    part(g,'leaf',timber,.87,.67,.87,.27,.13,.59,0,-.8);
  }
  sampan(-10.1,.8,1.08,6,true);
  sampan(10.7,-1.7,-1.24,5.5,true);
  sampan(2.6,7.7,.01,4.4,false);

  // The pontoon sits above the river on cross-braced timber and bamboo.
  box(stage, dark,0,-.46,0,16.55,.7,10.55);
  for(let iz=0;iz<32;iz++) {
    const z=-5.08+iz*.327;
    const joint=-5.8+(iz%4)*3.4;
    for(const [a,b] of [[-8.3,joint],[joint,8.3]]) {
      box(stage,wood[(iz+Math.floor(b+10))%wood.length],(a+b)*.5,-.075,z,b-a-.022,.15,.315);
    }
  }
  for (const z of [-5.23,5.23]) {
    box(stage,'#8b5541',0,-.24,z,16.75,.48,.18);
    box(stage,bamboo,0,-.12,z+(z>0?.1:-.1),16.7,.07,.08);
    for(let x=-7.9;x<8;x+=2) {
      tube(stage,dark,x,-.48,z,.34,1.12,.34);
      tube(stage,cream,x,-.44,z,.36,.13,.36);
    }
  }
  for (const x of [-8.32,8.32]) {
    box(stage,timber,x,-.20,0,.18,.40,10.60);
    for(const z of [-5,-1.8,1.8,5]) {
      tube(stage,timber,x,.22,z,.24,1.16,.24);
      tube(stage,bamboo,x,.66,z,.28,.12,.28);
    }
  }

  // Back counter and a striped, scalloped canvas canopy over the rear edge.
  const rear = -5.02;
  for(const x of [-7.88,-3.97,.15,4.15,7.88]) {
    tube(stage,timber,x,1.65,rear,.20,3.3,.2);
    tube(stage,bamboo,x,2.94,rear,.25,.13,.25);
  }
  box(stage,timber,0,3.14,rear,16.2,.19,.20);
  box(stage,jade,0,.43,rear,16.22,.83,.19);
  for(let x=-7.9;x<8;x+=.5) box(stage,'#609a8a',x,.46,rear+.12,.047,.82,.04);
  box(stage,bamboo,0,.9,rear,16.24,.12,.30);
  const awningWidth=8.35;
  for(let i=0;i<19;i++) {
    const x=-8.22+(i+.5)*awningWidth/19, color=i%4<2?'#e7b76e':'#ae5647';
    box(stage,color,x,3.28,rear+.28,awningWidth/19+.003,.12,1.67,.16);
    box(stage,color,x,3.07,rear+1.09,awningWidth/19+.003,.24,.08);
    orb(stage,color,x,2.96,rear+1.10,awningWidth/19,.25,.08);
  }
  // Ceramic jars and sauce bottles at the back; spaced far from the interaction lane.
  for(const x of [-6.8,-4.8,-1.8]) {
    box(stage,timber,x,.52,-4.61,1.82,.86,.62);
    box(stage,cream,x,1.01,-4.61,1.9,.15,.76);
    for(let i=0;i<3;i++) {
      const px=x-.54+i*.46,c=['#40847a','#f0c27e','#845248'][i];
      orb(stage,c,px,1.27,-4.58,.30,.42,.30);
      tube(stage,c,px,1.47,-4.58,.13,.16,.13);
      tube(stage,'#563f3b',px,1.56,-4.58,.15,.055,.15);
    }
  }

  function lantern(parent,x,y,z,color,size=1) {
    const g=group(parent,x,y,z); g.scale.setScalar(size);
    part(g,'orb',color,0,-.24,0,.51,.57,.51,0,0,0,true);
    for(const yy of [-.045,-.45]) tube(g,dark,0,yy,0,.25,.07,.25);
    tube(g,'#dca455',0,-.54,0,.055,.17,.055);
    tube(g,red,0,-.68,0,.09,.19,.09);
    for(const angle of [0,Math.PI/2]) {
      box(g,'#e7a059',0,-.24,0,.032,.43,.46,0,angle);
    }
  }
  // Keep the lantern string along the back so customers are visible from above.
  const wire = x => 3.54-.38*(1-Math.pow(x/8,2));
  for(let i=0;i<13;i++) {
    const x=-8+i*2/3;
    rod(stage,dark,[x,wire(x),-4.04],[x+2/3,wire(x+2/3),-4.04],.031);
  }
  for(let i=0;i<6;i++) {
    const x=-7.55+i*1.53;
    lantern(stage,x,wire(x)-.025,-4.04,['#ffd888','#fa906b','#faba70'][i%3],i%2?.91:1.12);
  }

  function plant(parent,x,z,scale=1) {
    const g=group(parent,x,0,z); g.scale.setScalar(scale);
    part(g,'bowl','#a35c49',0,.29,0,.66,.58,.66);
    tube(g,bamboo,0,.56,0,.73,.11,.73);
    for(let i=0;i<8;i++) {
      const angle=i*2.4;
      const f=part(g,'frond',i%2?'#437254':'#69955e',0,.55,0,.62,.83+hash(i)*.48,.72);
      f.rotation.y=angle;
    }
  }
  plant(stage,-7.67,-2.54,1.32); plant(stage,7.65,-4.22,1.3); plant(stage,-7.67,4.65,1.03);
  function palm(parent,x,z,size) {
    const g=group(parent,x,-.95,z); g.scale.setScalar(size);
    const base=[0,0,0], bend=[.22,2.24,0], top=[.65,4.57,.08];
    rod(g,'#665746',base,bend,.33);rod(g,'#807057',bend,top,.27);
    for(let i=0;i<10;i++) {
      const yaw=i*2.4;
      const f=group(g,...top); f.rotation.y=yaw;
      const len=2.35+(i%3)*.27;
      rod(f,'#708458',[0,0,0],[0,.34,len*.55],.065);
      for(let j=1;j<=6;j++) {
        const t=j/7;
        for(const sign of [-1,1]){
          const blade=part(f,'leaf',i%2?'#407363':'#54806b',sign*.23*Math.sin(t*Math.PI),.24*Math.sin(t*Math.PI)-.32*t*t,len*t,.29,.085,1.06*(1-t*.5));
          blade.rotation.y=sign*.62;
          blade.rotation.x=.16+t*.37;
        }
      }
    }
  }
  // Lanterns at the mooring posts mark the playable edge.
  for(const [postX,postZ] of [[-8.15,4.94],[8.15,4.94],[7.9,-4.93]]) {
    const inward=postX>0?-1:1;
    tube(stage,timber,postX,1.47,postZ,.17,2.95,.17);
    box(stage,bamboo,postX+.30*inward,2.90,postZ,.84,.095,.10);
    rod(stage,timber,[postX,2.40,postZ],[postX+.47*inward,2.85,postZ],.065);
    lantern(stage,postX+.62*inward,2.86,postZ,'#ffd37a',1.1);
    const light=new THREE.PointLight(0xffab51,12,7,2);
    light.position.set(postX+.63*inward,2.52,postZ);scene.add(light);
  }
  // The produce cart moors alongside the deck, leaving the walking area clear.
  const cart=group(stage,-8.16,-.02,1.88);
  box(cart,timber,-.12,.11,0,1.52,.21,3.50);
  box(cart,'#517b6b',-.16,.65,0,1.30,.95,3.28);
  for(let i=0;i<12;i++) box(cart,'#678674',.51,.62,i*.27-1.49,.045,.84,.055);
  box(cart,bamboo,-.16,1.18,0,1.52,.15,3.56);
  for(let i=0;i<3;i++) {
    const z=(i-1)*1.08;
    part(cart,'bowl','#9e6949',-.12,1.38,z,.96,.37,.96);
    tube(cart,bamboo,-.12,1.57,z,.99,.065,.99);
    for(let j=0;j<7;j++) {
      const theta=j*2.4, r=j===0?0:.26;
      const a=-.12+Math.cos(theta)*r,b=z+Math.sin(theta)*r;
      const c=['#9da64d','#d99643','#cc6559'][i];
      orb(cart,c,a,1.65+(j===0?.09:0),b,.28,.27,.28);
      part(cart,'leaf','#52764d',a+.046,1.79,b,.15,.06,.07,0,theta);
    }
  }
  // The far bank is a silhouette of stilt houses and coconut palms.
  for(let i=-4;i<=4;i++) {
    const x=i*5.35, z=-15-hash(i+44)*5, ht=1.8+hash(i+55);
    box(scenery,['#777074','#828884','#887975'][Math.abs(i)%3],x,ht*.55,z,3.75,ht,2.65);
    for(const sign of [-1,1]) box(scenery,'#875e51',x,ht+.37,z+sign*.75,4.34,.13,1.82,-sign*.44);
    for(const side of [-1,1]) tube(scenery,dark,x+side*1.55,-.4,z+1.19,.22,1.3,.22);
    for(let j=-1;j<2;j++) {
      box(scenery,'#564e50',x+j,ht*.65,z+1.341,.72,.81,.06);
      if(j!==0) box(scenery,'#ffc589',x+j,ht*.66,z+1.389,.49,.51,.035);
    }
    if(i%2===0) palm(scenery,x+2.6,z-1.55,1+hash(i+21)*.35);
  }
  batch(stage); batch(scenery);
  // Warm, feathered pools on the boards add light under the hanging lanterns.
  const glowMap=ink(128,128,(ctx,w,h)=>{
    const g=ctx.createRadialGradient(w/2,h/2,0,w/2,h/2,w/2);
    g.addColorStop(0,'rgba(255,180,85,.46)');g.addColorStop(.45,'rgba(255,175,75,.15)');
    g.addColorStop(1,'rgba(255,166,65,0)');ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
  });
  const glowMat=new THREE.MeshBasicMaterial({map:glowMap,transparent:true,depthWrite:false,blending:THREE.AdditiveBlending});
  for (const [x,z,w,d] of [[-5.6,-3.2,4.2,3.4],[-2.5,-3.6,4.2,3.4],[-6.73,3.87,2.8,2.25],[6.78,3.92,2.54,2.08],[6.70,-3.86,2.72,2.15]]) {
    const glow=new THREE.Mesh(new THREE.PlaneGeometry(w,d),glowMat);
    glow.rotation.x=-Math.PI/2;glow.position.set(x,.012,z);scene.add(glow);
  }

  function ink(width,height,paint) {
    const canvas=document.createElement('canvas');
    canvas.width=width; canvas.height=height;
    paint(canvas.getContext('2d'),width,height);
    const texture=new THREE.CanvasTexture(canvas);
    texture.colorSpace=THREE.SRGBColorSpace;
    return texture;
  }
  // A faded lotus painted into the floor breaks up the open aisle.
  const lotusMap=ink(384,384,(ctx,w,h)=>{
    ctx.translate(w/2,h*.66);ctx.strokeStyle='rgba(246,215,163,.40)';
    ctx.lineWidth=4;ctx.lineJoin='round';ctx.lineCap='round';
    for(const angle of [-.99,-.52,0,.52,.99]) {
      ctx.save();ctx.rotate(angle);ctx.beginPath();ctx.moveTo(0,0);
      ctx.bezierCurveTo(-35,-32,-32,-82,0,-125);
      ctx.bezierCurveTo(32,-82,35,-32,0,0);ctx.stroke();ctx.restore();
    }
    for(const [width,y] of [[152,20],[101,37],[46,53]]) {
      ctx.beginPath();ctx.moveTo(-width/2,y);ctx.quadraticCurveTo(0,y+7,width/2,y);ctx.stroke();
    }
  });
  const lotus=new THREE.Mesh(new THREE.PlaneGeometry(4.0,4.0),
    new THREE.MeshBasicMaterial({map:lotusMap,transparent:true,depthWrite:false}));
  lotus.rotation.x=-Math.PI/2;lotus.position.set(-3.36,.014,1.70);scene.add(lotus);

  // A hand-lettered board is part of the façade and stays behind all playable stations.
  const sign=group(scene,3.95,2.62,-5.02);
  box(sign,timber,0,0,0,5.5,1.62,.22);
  const board=ink(880,256,(ctx,w,h)=>{
    ctx.fillStyle='#294f4b'; ctx.fillRect(0,0,w,h);
    ctx.strokeStyle='#d0a36b';ctx.lineWidth=4;ctx.strokeRect(12,12,w-24,h-24);
    ctx.strokeStyle='#7c8a75';ctx.lineWidth=2;ctx.strokeRect(20,20,w-40,h-40);
    ctx.textAlign='center';ctx.fillStyle='#efba70';ctx.font='bold 30px Georgia,serif';
    ctx.fillText('•   BẾP MIỀN TÂY   •',w/2,70);
    ctx.fillStyle='#ffe9b3';ctx.font='italic bold 108px Georgia,serif';ctx.fillText('Quán Út Sen',w/2,184);
  });
  const signFace=new THREE.Mesh(new THREE.PlaneGeometry(5.34,1.48),new THREE.MeshBasicMaterial({map:board}));
  signFace.position.z=.121; sign.add(signFace);
  const infoMats=new Map();
  function badge(title,accent) {
    const key=accent+title;
    if(!infoMats.has(key)){
      const map=ink(360,88,(ctx,w,h)=>{
        ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='bold 43px system-ui,sans-serif';
        const len=Math.min(w-8,Math.ceil(ctx.measureText(title).width+53));
        const x=(w-len)/2;
        ctx.fillStyle='#263d39';ctx.beginPath();ctx.roundRect(x,7,len,h-15,29);ctx.fill();
        ctx.strokeStyle=accent;ctx.lineWidth=4;ctx.stroke();
        ctx.fillStyle=accent;ctx.fillText(title,w/2,h/2+1);
      });
      infoMats.set(key,new THREE.SpriteMaterial({map,depthTest:false,depthWrite:false,transparent:true}));
    }
    return infoMats.get(key);
  }
  function label(parent,x,y,z) {
    const s = new THREE.Sprite();
    s.position.set(x,y,z);s.scale.set(2.35,.575,1); s.renderOrder=7;
    parent.add(s);
    return s;
  }
  function dish(parent,x,y,z) {
    const g=group(parent,x,y,z);
    part(g,'bowl','#d9eee0',0,.066,0,.52,.14,.52);
    tube(g,'#df9f41',0,.143,0,.44,.022,.44);
    orb(g,'#61915c',.07,.17,-.04,.17,.075,.15);
    orb(g,'#b94731',-.11,.16,.04,.12,.06,.105);
    return g;
  }
  function character(parent,shirt,hat=false,apron=false) {
    const body=group(parent), torso=group(body);
    const skin='#d99a70', hair='#423a36';
    // The server's checkered scarf and conical hat identify her from above.
    orb(torso,hair,0,1.39,-.035,.49,.57,.45);
    orb(torso,skin,0,1.39,.038,.44,.47,.42);
    orb(torso,hair,0,1.60,-.03,.48,.20,.44);
    for(const side of [-1,1]) {
      orb(torso,hair,side*.092,1.415,.23,.035,.05,.024);
      orb(torso,skin,side*.21,1.40,.04,.09,.13,.09);
      orb(torso,'#e1a17c',side*.13,1.35,.20,.072,.044,.030);
    }
    tube(torso,skin,0,1.155,0,.19,.21,.19);
    part(torso,'bowl',shirt,0,.87,0,.54,.56,.40);
    if(apron) {
      box(torso,'#32685e',0,.83,.181,.35,.47,.055);
      box(torso,'#e7d9ac',0,.72,.211,.22,.08,.025);
      tube(torso,'#e6ba78',0,1.145,.015,.285,.11,.285);
      const scarf=box(torso,'#b9513f',-.16,.981,.19,.105,.34,.082,0,0,-.22);
      for(let n=0;n<3;n++) box(scarf,'#f5ce9b',0,(n-1)*.22,.48,.98,.10,.10);
    }
    if(hat) {
      part(torso,'cone','#dfaa67',0,1.744,0,.94,.34,.94);
      tube(torso,'#ae6c46',0,1.586,0,.94,.037,.94);
      part(torso,'cone','#edd195',0,1.811,0,.55,.20,.55);
    } else {
      orb(torso,hair,0,1.60,-.15,.29,.28,.29);
    }
    const limbs=[];
    for(const side of [-1,1]) {
      const leg=group(body,side*.14,.63,0);
      box(leg,'#42494b',0,-.24,0,.20,.48,.23);
      orb(leg,'#513c36',0,-.52,.052,.235,.16,.34);
      const arm=group(torso,side*.245,1.04,0);
      orb(arm,shirt,side*.038,-.093,0,.20,.26,.25);
      orb(arm,skin,side*.048,-.24,.018,.15,.24,.16);
      limbs.push({leg,arm,side});
    }
    return {body,torso,limbs};
  }
  const stations=new Map(), furniture=new Map();
  const playerRoot=group(scene);
  shadow(playerRoot,0,0,.98,.75);
  const avatar=character(playerRoot,'#cc6548',true,true);
  const orderTray=group(avatar.torso,0,.90,.42);
  tube(orderTray,'#9a6545',0,0,0,.69,.057,.55);
  dish(orderTray,0,.042,0);
  const ring=part(playerRoot,'ring','#fff6ba',0,.034,0,1.05,1.05,1,-Math.PI/2,0,0,true);

  function stove() {
    const root=group(scene), steel='#4d5b5b', brick='#ae6248';
    const fixed=group(root);
    shadow(fixed,.05,.10,2.25,1.75);
    box(fixed,dark,0,.14,0,1.75,.26,1.21);
    box(fixed,brick,0,.56,0,1.67,.70,1.19);
    for(const side of [-1,1]) box(fixed,'#c77c59',side*.56,.53,.604,.36,.095,.025);
    box(fixed,'#e4bf8c',0,.96,0,1.83,.16,1.33);
    box(fixed,steel,-.13,1.055,0,1.10,.06,.92);
    part(fixed,'bowl','#474847',-.13,1.24,0,.77,.35,.77);
    tube(fixed,'#b0ad92',-.13,1.43,0,.81,.063,.81);
    tube(fixed,'#483d35',-.13,1.466,0,.73,.025,.73);
    for(const side of [-1,1]) box(fixed,steel,-.13+side*.46,1.355,0,.25,.08,.14);
    box(fixed,'#4b3834',0,.44,.604,.65,.31,.046);
    for(let i=0;i<3;i++) rod(fixed,'#bc885a',[-.19+i*.16,.37,.68],[-.17+i*.16,.48,.62],.075);
    tube(fixed,jade,.62,1.17,.30,.23,.23,.23);
    rod(fixed,bamboo,[.61,1.2,.3],[.67,1.59,.29],.04);
    batch(fixed);
    const flame=part(root,'orb','#ffb249',0,.46,.64,.54,.18,.04,0,0,0,true);
    const food=dish(root,-.13,1.453,0);food.scale.setScalar(1.23);
    const smoke=group(root,-.13,1.5,0);
    const steam=[];
    for(let i=0;i<4;i++) steam.push(orb(smoke,'#e6d5ae',0,0,0,.1,.1,.1));
    const staff=group(root,.10,0,-.84);
    const cook=character(staff,'#a9c5af',false,true);
    tube(cook.torso,'#f3dfbe',0,1.66,-.01,.50,.16,.48);
    orb(cook.torso,'#f4e2c4',0,1.77,-.04,.58,.20,.54);
    cook.limbs.forEach(({arm})=>{arm.rotation.x=-.75;});
    batch(staff);
    const tag=label(root,.03,1.28,.9);
    return {root,tag,food,steam,smoke,flame,staff};
  }

  function table(index) {
    const root=group(scene), fixed=group(root);
    shadow(fixed,.06,.08,2.33,1.93);
    // A woven chiếu defines the seat and makes the serving location legible.
    box(fixed,'#aa8156',0,.032,0,1.91,.039,2.35);
    for(const x of [-.85,.85]) box(fixed,'#506e61',x,.054,0,.085,.009,2.27);
    for(const z of [-1.08,1.08]) box(fixed,'#506e61',0,.054,z,1.79,.009,.055);
    for(const x of [-.48,.48]) for(const z of [-.34,.34]) {
      box(fixed,timber,x,.46,z,.12,.82,.12,0,0,x*.10);
    }
    tube(fixed,'#9b6045',0,.91,0,1.69,.16,1.50);
    tube(fixed,'#d9a675',0,.998,0,1.63,.05,1.44);
    box(fixed,'#4e8677',0,1.032,0,.37,.019,1.33);
    part(fixed,'bowl','#62897d',.41,1.16,-.24,.21,.25,.21);
    rod(fixed,'#728554',[.42,1.28,-.24],[.44,1.61,-.22],.035);
    for(let i=0;i<5;i++) orb(fixed,'#e7aa7b',.44+Math.cos(i*1.26)*.09,1.61,-.22+Math.sin(i*1.26)*.09,.14,.07,.13);
    tube(fixed,cream,-.48,1.115,.20,.19,.15,.19);
    for (const z of [-.99,.99]) {
      tube(fixed,jade,0,.50,z,.55,.11,.55);
      for(let j=0;j<3;j++) {
        const a=j*2.094;
        rod(fixed,timber,[.28*Math.cos(a),.06,z+.28*Math.sin(a)],[.14*Math.cos(a),.45,z+.14*Math.sin(a)],.08);
      }
    }
    batch(fixed);
    const seat=group(root,0,.05,-.98);
    const guest=character(seat,['#7d8196','#bf775d','#57918d','#c78a59'][index%4]);
    guest.body.scale.setScalar(.94);
    guest.torso.position.y=.02;
    for(const {leg,arm} of guest.limbs) {leg.rotation.x=-.89;arm.rotation.x=-.45;}
    const meal=dish(root,0,1.055,-.2);
    const tag=label(root,0,1.34,.74);
    return {root,seat,guest,meal,tag};
  }
  let lastX,lastZ,prevTime,walk=0,angle=0;
  function position(pos,bounds) {
    const [x0,x1]=bounds.x, [z0,z1]=bounds.z;
    return [(pos[0]-x0)/(x1-x0)*16-8,5-(pos[1]-z0)/(z1-z0)*10];
  }
  function update(state,width,height,seconds=0,screen='',targetId=null) {
    if(!state) return;
    const bounds=state.meta?.bounds;
    if(!bounds?.x || !bounds?.z) return;
    const dt=prevTime===undefined?0:Math.min(.10,Math.max(0,seconds-prevTime));
    prevTime=seconds;
    waterMat.uniforms.seconds.value=seconds;
    const aspect=Math.max(.1,width/Math.max(1,height));
    const span=Math.max(11.8,21.8/aspect);
    camera.top=span*.5; camera.bottom=-span*.5;
    camera.left=-span*aspect*.5; camera.right=span*aspect*.5;
    const offset=screen==='menu' && aspect>1.4?-Math.min(3.4,span*aspect*.10):0;
    camera.position.set(3.6+offset,20.5,23);
    camera.lookAt(center.x+offset,center.y,center.z);
    camera.updateProjectionMatrix();
    playerRoot.visible = Boolean(state.player?.pos);
    if(playerRoot.visible) {
      const [x,z]=position(state.player.pos,bounds);
      if(lastX!==undefined && (x!==lastX || z!==lastZ)) {
        const dx=x-lastX,dz=z-lastZ;
        angle=Math.atan2(dx,dz);
        walk=Math.min(1,Math.hypot(dx,dz)/Math.max(.003,dt)/2);
      } else walk*=Math.exp(-dt*11);
      lastX=x;lastZ=z;
      playerRoot.position.set(x,0,z);
      avatar.body.rotation.y=angle;
      const step=Math.sin(seconds*12)*walk;
      avatar.torso.position.y=Math.abs(step)*.045;
      for(const {leg,arm,side} of avatar.limbs) {
        leg.rotation.x=step*side*.45;
        arm.rotation.x=state.hand?-.84:-step*side*.31;
      }
      orderTray.visible=!!state.hand;
      ring.scale.setScalar(1.03+.045*Math.sin(seconds*3));
    }
    for(const object of stations.values()) object.root.visible=false;
    for(const st of state.stoves||[]) {
      if(!stations.has(st.id)) stations.set(st.id,stove());
      const m=stations.get(st.id), [x,z]=position(st.pos,bounds);
      m.root.visible=true; m.root.position.set(x,0,z);
      const ready=st.state==='ready', cooking=st.state==='cooking';
      m.staff.visible=cooking;
      m.food.visible=ready || cooking; m.flame.visible=cooking; m.smoke.visible=ready || cooking;
      if(m.smoke.visible) m.steam.forEach((p,i)=>{
        const t=(seconds*(cooking?.78:.43)+i*.25)%1;
        p.position.set(.07*Math.sin(t*6+i),t*.72,i%2*.11-.06);
        p.scale.setScalar((.13+Math.sin(t*Math.PI)*.085)*(1-t));
      });
      const text=ready?' · Chín':cooking?' · Nấu':'';
      const next = !screen && st.id === targetId;
      m.tag.material=badge((next ? '▸ ' : '')+st.id+text,next?'#ffc865':ready?'#dbf2a5':cooking?'#ffd48c':'#ffe6b0');
    }
    for(const object of furniture.values()) object.root.visible=false;
    const occupants=new Map((state.customers||[]).map(c=>[c.table_id,c]));
    for(const tb of state.tables||[]) {
      if(!furniture.has(tb.id)) furniture.set(tb.id,table(furniture.size));
      const m=furniture.get(tb.id), [x,z]=position(tb.pos,bounds), c=occupants.get(tb.id);
      m.root.visible=true; m.root.position.set(x,0,z); m.seat.visible=!!c;
      const eating=c?.state==='eating', deliver=!!state.hand && !!c && state.hand.order_id===c.id;
      m.meal.visible=eating;
      m.guest.torso.rotation.x=eating?.075*Math.sin(seconds*2.7):0;
      const text=eating?' · Ăn':deliver?' · Bưng':c?' · Chờ':'';
      const next = !screen && tb.id === targetId;
      m.tag.material=badge((next ? '▸ ' : '')+tb.id+text,next?'#ffc865':deliver?'#c8f9ae':c?'#ffe0ac':'#f5e1bb');
    }
  }
  return {scene,camera,update};
}
