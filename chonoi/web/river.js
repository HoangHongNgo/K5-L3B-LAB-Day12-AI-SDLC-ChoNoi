// The river is a longitudinal cutaway. Every interactive object shares the
// plane (simulation x, -depth, 0). Only scenery uses the far-bank axis, z.
export function createRiver(THREE) {
  const T = THREE;
  const scene = new T.Scene();
  const camera = new T.OrthographicCamera(-16, 16, 9, -9, 0.1, 170);
  scene.background = new T.Color(0xffe3b1);
  scene.add(new T.HemisphereLight(0xfff6df, 0x8caaa4, 1.75));
  const sun = new T.DirectionalLight(0xffdfae, 1.85);
  sun.position.set(-18, 28, 20);
  scene.add(sun);

  const material = new T.MeshLambertMaterial({vertexColors: true, side: T.DoubleSide});
  const flat = new T.MeshBasicMaterial({vertexColors: true, side: T.DoubleSide});
  const cube = new T.BoxGeometry(1, 1, 1);
  const gem = new T.IcosahedronGeometry(1, 0);
  const round = new T.SphereGeometry(1, 10, 6);
  const barrel = new T.CylinderGeometry(1, 0.8, 1, 10);
  const cone = new T.ConeGeometry(1, 1, 12);
  const tube = new T.CylinderGeometry(1, 1, 1, 7);
  const matrix = new T.Matrix4();
  const v = new T.Vector3(), point = new T.Vector3(), scale = new T.Vector3();
  const rot = new T.Quaternion(), euler = new T.Euler(), up = new T.Vector3(0, 1, 0);
  const colors = new Map();

  // Bake local models into colored triangle meshes. A whole boat or grove
  // draws in one call and all copies of an entity kind share their geometry.
  class Model {
    constructor() { this.vertices = []; this.colors = []; }
    color(c) {
      if (!colors.has(c)) colors.set(c, new T.Color(c));
      return colors.get(c);
    }
    put(x, y, z, c) {
      this.vertices.push(x, y, z);
      this.colors.push(c.r, c.g, c.b);
    }
    tri(a, b, d, color) {
      const c = this.color(color);
      for (const p of [a, b, d]) this.put(...p, c);
    }
    quad(a, b, c, d, color) {
      this.tri(a, b, c, color); this.tri(a, c, d, color);
    }
    shape(g, color, x, y, z, sx, sy, sz, rx = 0, ry = 0, rz = 0) {
      rot.setFromEuler(euler.set(rx, ry, rz));
      matrix.compose(point.set(x, y, z), rot, scale.set(sx, sy, sz));
      this.transformed(g, color);
    }
    transformed(g, color) {
      const c = this.color(color), pos = g.attributes.position, idx = g.index;
      for (let i = 0, n = idx ? idx.count : pos.count; i < n; i++) {
        v.fromBufferAttribute(pos, idx ? idx.getX(i) : i).applyMatrix4(matrix);
        this.put(v.x, v.y, v.z, c);
      }
    }
    box(color, x, y, z, w, h, d, rz = 0) { this.shape(cube, color, x,y,z,w,h,d,0,0,rz); }
    oval(color, x, y, z, w, h, d) { this.shape(round,color,x,y,z,w,h,d); }
    rod(color, a, b, r) {
      point.set(b[0]-a[0],b[1]-a[1],b[2]-a[2]);
      const length = point.length();
      rot.setFromUnitVectors(up, point.normalize());
      point.multiplyScalar(length / 2).add(v.fromArray(a));
      matrix.compose(point, rot, scale.set(r, length, r));
      this.transformed(tube, color);
    }
    mesh(mat = material) {
      const g = new T.BufferGeometry();
      g.setAttribute("position", new T.Float32BufferAttribute(this.vertices, 3));
      g.setAttribute("color", new T.Float32BufferAttribute(this.colors, 3));
      if (mat === material) g.computeVertexNormals();
      g.computeBoundingSphere();
      return new T.Mesh(g, mat);
    }
  }
  function place(model, x, y, z, size = 1, yaw = 0, mat = material) {
    const mesh = model.mesh(mat);
    mesh.position.set(x,y,z); mesh.scale.setScalar(size); mesh.rotation.y = yaw;
    scene.add(mesh);
    return mesh;
  }
  // Distinct, fixed scenery patterns keep the same path recognizable on return.
  const wave = (i, j) => (Math.sin(i*37.51+j*15.23)*431.17) % 1;
  const frac = (i, j) => Math.abs(wave(i,j));
  const sky = new Model();
  function band(model, y0, y1, c0, c1, z, half = 250) {
    const low = model.color(c0), high = model.color(c1);
    for (const [x, y] of [[-half,y0],[half,y0],[half,y1],[-half,y0],[half,y1],[-half,y1]]) {
      model.put(x,y,z,y === y0 ? low : high);
    }
  }
  band(sky,-25,0,0xffc994,0xffddb0,-50);
  band(sky,0,9,0xffddb0,0xf7ddbf,-50);
  band(sky,9,22,0xf7ddbf,0xaacfcf,-50);
  band(sky,22,120,0xaacfcf,0x8bbec8,-50);
  scene.add(sky.mesh(flat));
  const skyDetails = new Model();
  skyDetails.oval(0xffefbc, 0,2.2,-42,2.55,2.55,.12);
  for (let i=0; i<12; i++) {
    const x = (i-6)*10.3, y = 1.6+frac(i,4)*6;
    skyDetails.oval(0xffecd0,x,y,-43,3.2,.26,.22);
    skyDetails.oval(0xffecd0,x+1.4,y+.25,-43,2,.4,.19);
  }
  const skyObjects = place(skyDetails,0,0,0,1,0,flat);

  const far = new Model();
  for (let i=-10; i<32; i++) {
    const x=i*5.7;
    far.shape(gem, i%2 ? 0x9fb8a1 : 0xb3bfa9,x,-.8,-30,8.5,2+frac(i,2)*2.4,3);
    far.shape(gem, i%2 ? 0x82a691 : 0x94afa0,x+2,-.6,-24,5.3,1.2+frac(i,8)*2.5,1.9);
  }
  far.box(0x729c89,55,-.34,-22,220,.9,2);
  scene.add(far.mesh(flat));

  function palm(m,x,z,h,lean, tint) {
    const top = [x+lean,h,z+.1];
    m.rod(0x886648,[x,-.1,z],[x+lean*.32,h*.55,z],h*.031);
    m.rod(0x9c754b,[x+lean*.32,h*.55,z],top,h*.024);
    for (let i=0; i<9; i++) {
      const angle=i*2.4+x*.17, length=h*(.47 + .11*frac(i,x));
      const dx=Math.cos(angle)*length,dz=Math.sin(angle)*length;
      let prev=top, left=top, right=top;
      for (let k=1; k<=7; k++) {
        const t=k/7, arc=h*(.135*Math.sin(Math.PI*t)-.14*t*t);
        const p=[top[0]+dx*t,top[1]+arc,top[2]+dz*t];
        const s=(k-.52)/7, width=h*.075*Math.sin(s*Math.PI);
        const cx=top[0]+dx*s,cy=top[1]+h*(.135*Math.sin(Math.PI*s)-.14*s*s),cz=top[2]+dz*s;
        for (const sign of [-1,1]) {
          const edge=[cx-sign*Math.sin(angle)*width+dx*.10,cy-width*.60,cz+sign*Math.cos(angle)*width+dz*.10];
          const rib=[cx-sign*Math.sin(angle)*width*.52,cy-width*.18,cz+sign*Math.cos(angle)*width*.52];
          const next=[p[0]-sign*Math.sin(angle)*width*.40,p[1]-width*.2,p[2]+sign*Math.cos(angle)*width*.40];
          const shade=sign===1 ? tint : 0x3e7959;
          m.quad(prev,sign===1 ? left : right,next,p,shade);
          m.tri(rib,next,edge,shade);
          if(sign===1) left=next; else right=next;
        }
        prev=p;
      }
    }
    for (let i=0;i<3;i++) m.shape(gem,0x977348,top[0]+i*.13-.1,h-.14,z+.08,.15,.21,.15);
  }
  function roof(m,x,y,z,w,h,d,c1,c2) {
    for (const side of [-1,1]) {
      const e=z+side*d/2;
      m.quad([x-w/2,y,e],[x+w/2,y,e],[x+w/2,y+h,z],[x-w/2,y+h,z],side>0 ? c1 : c2);
      m.box(0x6c4d3c,x,y-.035,e,w+.06,.10,.09);
    }
    for(const side of [-1,1]) {
      const e=x+side*w/2;
      m.tri([e,y,z-d/2],[e,y+h,z],[e,y,z+d/2],c2);
    }
    m.box(c2,x,y+h,z,w+.12,.10,.12);
  }
  // Stilt houses and rows of split coconut fronds on the opposite bank.
  for(let block=-1;block<6;block++) {
    const bank=new Model(), base=block*25;
    for(let i=0;i<4;i++) {
      const x=i*6.1, z=-16-frac(block,i)*3.5;
      palm(bank,x+2.6,z,3.8+frac(block+i,5)*3.1,wave(i,block)*.75,i%2 ? 0x5d935d : 0x4f9266);
      if((i+block)%3===0) continue;
      const w=2.8+frac(block,i+2)*1.7;
      for(const dx of [-w*.42,w*.42]) bank.rod(0x796e59,[x+dx,-.3,z+.9],[x+dx,1.35,z+.9],.09);
      bank.box(0xa68761,x,1.65,z,w,1.3,1.85);
      bank.box(0x584f43,x+.3,1.59,z+.94,.62,.96,.03);
      bank.box(0x718a7a,x-.76,1.82,z+.95,.47,.48,.03);
      const clay=(i+block)%2;
      roof(bank,x,2.30,z,w+.6,.73,2.65,clay ? 0xb57655 : 0xa49d76,0x906e54);
      for(let k=0;k<11;k++) {
        const a=x+(k/10-.5)*(w+.5);
        bank.rod(clay?0xc18462:0xb0a97d,[a,2.31,z+1.32],[a,3.04,z],.026);
      }
      for(let k=0;k<12;k++) {
        const a=x+(k/11-.5)*w;
        if(Math.abs(a-x-.3)>.38 && Math.abs(a-x+.76)>.29) bank.box(0xb29568,a,1.69,z+.94,.022,1.24,.018);
      }
      bank.box(0x99744e,x,1.03,z+1.00,w+.55,.15,.77);
      for(const sign of [-1,1]) {
        bank.box(0x946e4d,x+sign*(w*.35),1.32,z+1.31,.04,.58,.04);
        bank.box(0xac895e,x+sign*(w*.34),1.61,z+1.31,w*.28,.055,.055);
      }
    }
    for(let k=0;k<18;k++) {
      const x=k*1.5,z=-20+frac(block,k)*.9;
      bank.shape(gem,k%2?0x689875:0x79a37b,x,.5+frac(k,2)*.68,z,1.3,1.15+frac(k,block),.8);
      bank.shape(gem,k%2?0x92a97a:0x75a184,x,-.18,z+1.5,1.5,.52,.8);
    }
    place(bank,base,0,0);
  }

  const water = new Model();
  band(water,-58,-28,0x123d52,0x195466,-10);
  band(water,-28,-12,0x195466,0x267d87,-10);
  band(water,-12,-3,0x267d87,0x379d9c,-10);
  band(water,-3,.07,0x379d9c,0x61b8a2,-10);
  water.quad([-210,0,-20],[250,0,-20],[250,0,.08],[-210,0,.08],0x76c1af);
  scene.add(water.mesh(flat));

  const waterMarks = new Model();
  for(let i=0;i<720;i++) {
    const x=-35+frac(i,2)*176, z=-.15-frac(i,3)*21;
    const len=.21+frac(i,4)*(z < -10 ? 1.85 : .94);
    waterMarks.quad([x-len,.016,z],[x,.016,z+.08],[x+len,.016,z+.015],[x,.016,z-.045],
      [0x92d0b8,0xa5d8be,0x67b4a3,0x87c9ae][i%4]);
  }
  for(let i=-30;i<145;i+=.92) {
    const y=.055+.036*Math.sin(i*.8);
    waterMarks.quad([i,y,.095],[i+.93,.055+.036*Math.sin((i+.92)*.8),.095],
      [i+.93,-.045,.095],[i,-.045,.095],i%4<2?0xc9e7bc:0xabe0c3);
  }
  scene.add(waterMarks.mesh(flat));

  // Layer shafts over the painted water wall so their falloff follows depth.
  const shafts = new Model(), rayTop = new T.Color(0xa8edd2), rayBottom = new T.Color(0x529b9b);
  for(let i=-6;i<35;i++){
    const x=i*4.1+wave(i,11), h=7+frac(i,9)*15, w=.35+frac(i,5)*1.45;
    const drift=-1.5-frac(i,1)*3.8;
    for(const [px,py] of [[x,0],[x+w,0],[x+w*.2+drift,-h],[x,0],[x+w*.2+drift,-h],[x+drift,-h]]) {
      shafts.put(px,py,-9.8,py===0 ? rayTop : rayBottom);
    }
  }
  const rayMat = new T.MeshBasicMaterial({vertexColors:true,transparent:true,opacity:.115,depthWrite:false,side:T.DoubleSide});
  scene.add(shafts.mesh(rayMat));

  const bed = new Model();
  for(let i=-8;i<38;i++) {
    const x=i*4, y=-32+.45*Math.sin(i*.68), next=-32+.45*Math.sin((i+1)*.68);
    bed.quad([x,y,2],[x+4,next,2],[x+4,next-6,2],[x,y-6,2],0x3a655f);
    bed.quad([x,y,2],[x+4,next,2],[x+4,next+.85,-8],[x,y+.85,-8],i%2?0x739286:0x81987c);
    for(let k=0;k<4;k++) {
      const a=x+frac(i,k)*4,h=1+frac(i+2,k)*2;
      bed.shape(gem,k%2?0x608f79:0x668a81,a,y+.45,-2,.85,h*.43,.7);
      for(let j=0;j<4;j++) {
        const b=a+j*.17, v=wave(j,i)*.43;
        bed.tri([b,y,-2.5],[b+.15,y,-2.5],[b+v,y+h*(.7+frac(j,k)*.45),-2.5],j%2?0x33766a:0x408b78);
      }
    }
  }
  scene.add(bed.mesh());
  // Across the channel the bed rises into shallow shelves. Their muted
  // colors and distant z keep their silhouettes distinct from live schools.
  const shelves=new Model();
  const profile=x=>-16+3.5*Math.sin(x*.14)+2.15*Math.cos(x*.38)+.65*Math.sin(x*.97);
  for(let i=-22;i<88;i++) {
    const x=i*1.65, nx=x+1.65, y=profile(x), ny=profile(nx);
    shelves.quad([x,y,-7.7],[nx,ny,-7.7],[nx,ny-.6,-7.1],[x,y-.6,-7.1],0x398383);
    shelves.quad([x,y-.6,-7.1],[nx,ny-.6,-7.1],[nx,ny-2.3,-7.3],[x,y-2.3,-7.3],i%3===0?0x337b80:0x367e80);
    const low=shelves.color(0x205f70),high=shelves.color(0x347a7c);
    for(const [a,b,top] of [[x,y-2.3,1],[nx,ny-2.3,1],[nx,-33,0],[x,y-2.3,1],[nx,-33,0],[x,-33,0]]) {
      shelves.put(a,b,-7.31,top?high:low);
    }
    if(i%3===0) {
      for(let j=0;j<9;j++) {
        const a=x+frac(i,j)*1.5,base=profile(a),h=.7+frac(i+4,j)*1.55, lean=wave(i,j)*.46;
        shelves.quad([a-.09,base-.14,-7.29],[a+.08,base-.14,-7.29],[a+.08+lean*.4,base+h*.61,-7.29],[a-.055+lean*.4,base+h*.61,-7.29],0x438d88);
        shelves.tri([a-.055+lean*.4,base+h*.61,-7.29],[a+.08+lean*.4,base+h*.61,-7.29],[a+lean,base+h,-7.29],0x438d88);
      }
    }
    if(i%4===0) shelves.shape(gem,0x438786,x,y+.01,-7.55,.63,.37,.34);
  }
  scene.add(shelves.mesh(flat));
  const snags=new Model();
  for(let i=0;i<7;i++){
    const x=1+i*17.5,y=-12.5-(i%3)*4;
    snags.rod(0x548a80,[x-.35,y-1,-6.5],[x+.86,y+1.4,-6.65],.14);
    snags.rod(0x578e80,[x+.49,y+.74,-6.65],[x+1.77,y+1.11,-6.7],.08);
    snags.rod(0x568c82,[x+.8,y+1.3,-6.6],[x+.73,y+2.12,-6.63],.056);
    snags.shape(gem,0x578f86,x-.5,y-1,-6.5,.9,.5,.44);
  }
  scene.add(snags.mesh(flat));
  const silt = new Model();
  for(let i=0;i<800;i++) {
    const x=-27+frac(i,7)*154,y=-.7-frac(i,6)*31,z=-8+frac(i,8)*6,r=.018+.045*frac(i,9);
    silt.quad([x-r,y,z],[x,y+r,z],[x+r,y,z],[x,y-r,z],i%3?0x74b3ab:0x9dcabb);
  }
  scene.add(silt.mesh(flat));

  function person(m,x,y,z,shirt) {
    m.oval(shirt,x,y+.52,z,.26,.43,.23);
    m.oval(0xb67e53,x,y+1.05,z,.20,.24,.18);
    m.shape(cone,0xedce8a,x,y+1.33,z,.51,.42,.42);
    m.rod(0xdba779,[x+.10,y+.72,z+.08],[x+.40,y+.50,z+.17],.075);
  }
  function boat(awning,fruitColor,accent) {
    const m=new Model();
    const stations=[[-3.75,.03,1.27],[-3.03,.51,.77],[-2.2,.86,.54],[-.75,1.03,.50],[1.25,.98,.52],[2.62,.72,.68],[3.46,.26,1],[3.8,.035,1.35]];
    for(let k=0;k<stations.length-1;k++) {
      const [a,w,h]=stations[k], [b,v,j]=stations[k+1];
      for(const s of [-1,1]) {
        const A=[a,h,s*w],B=[b,j,s*v],C=[b,j-.16,s*v*.99],D=[a,h-.16,s*w*.99];
        m.quad(A,B,C,D,0xe9b578);
        m.quad(D,C,[b,j-.32,s*v*.92],[a,h-.32,s*w*.92],accent);
        const lowA=Math.max(-.15,h-.74),lowB=Math.max(-.15,j-.74);
        m.quad([a,h-.32,s*w*.92],[b,j-.32,s*v*.92],[b,lowB,s*v*.55],[a,lowA,s*w*.55],k%2 ? 0x794a3c : 0x86533c);
        m.rod(0xbf9164,[a,h-.41,s*w*.87],[b,j-.41,s*v*.87],.018);
      }
      m.quad([a,h-.09,-w*.94],[b,j-.09,-v*.94],[b,j-.09,v*.94],[a,h-.09,w*.94],0xaa784f);
    }
    for(let i=0;i<3;i++) m.box(0xc39363,-1.9+i*.68,.56,.05,.17,.1,1.5);
    if(awning) {
      for(const x of [-1.65,1.35]) for(const z of [-.77,.77]) m.rod(0x8a6746,[x,.42,z],[x,2.08,z],.054);
      for(let i=0;i<8;i++) {
        const a=-1.95+i*.46,b=a+.46;
        for(const s of [-1,1]) {
          const c=i%2 ? 0xf4d793 : awning;
          m.quad([a,2.38,0],[b,2.38,0],[b,2.07,s*1.08],[a,2.07,s*1.08],c);
          m.quad([a,2.07,s*1.08],[b,2.07,s*1.08],[b,1.92,s*1.08],[a,1.89,s*1.08],c);
        }
      }
    }
    for(const [i,x] of [-1.2,-.05,1.1].entries()) {
      m.shape(barrel,0x99714a,x,.66,.44,.49,.34,.36);
      m.shape(barrel,0xbba170,x,.80,.44,.50,.065,.37);
      for(let j=0;j<7;j++) {
        const a=j*2.4,r=j===0?0:.28;
        m.shape(gem,i===1 ? 0xb9be5d : fruitColor,x+Math.cos(a)*r,.89+(j===0?.18:0),.44+Math.sin(a)*r*.65,.17,.19,.15);
      }
    }
    person(m,2.15,.57,-.05,0x416f73);
    if(awning) {
      for(const x of [-1.45,1.12]) {
        m.rod(0x8a6b46,[x,2.06,1.04],[x,1.84,1.04],.019);
        m.oval(0xd26b40,x,1.69,1.04,.13,.17,.12);
        m.box(0xe8b965,x,1.5,1.04,.026,.12,.026);
      }
      m.rod(0x8c663e,[-1.67,.54,.79],[-.75,2.04,.79],.035);
      m.rod(0x8c663e,[1.32,.55,-.77],[.57,2.17,-.77],.035);
    }
    m.rod(0xb98c56,[2.22,1.40,0],[3.31,-.38,1.02],.052);
    m.rod(0x816e47,[-2.15,.4,-.27],[-2.35,3.45,-.27],.052);
    m.tri([-2.34,3.40,-.27],[-2.39,2.84,-.27],[-1.52,3.12,-.27],accent);
    // Painted eyes are a characteristic feature of southern river boats.
    for(const sign of [-1,1]) {
      m.oval(0xf0d6a5,2.92,.60,sign*.60,.15,.072,.035);
      m.oval(0x433e35,2.97,.60,sign*.63,.058,.045,.025);
    }
    return m;
  }
  const foregroundWater = new Model();
  foregroundWater.quad([-210,-.012,0],[250,-.012,0],[250,-.012,60],[-210,-.012,60],0x76c1af);
  for(let i=0;i<500;i++) {
    const x=-32+frac(i,10)*88,z=frac(i,11)*35, w=.25+frac(i,16)*.8;
    foregroundWater.quad([x-w,.012,z],[x,.012,z+.055],[x+w,.012,z],[x,.012,z-.047],i%2?0x9dd3b7:0x68b6a2);
  }
  const foreground=place(foregroundWater,0,0,0,1,0,flat);
  const boats=[];
  const hulls=[
    boat(0xc56040,0xe6a343,0xaf4e3d).mesh(),
    boat(0x55958b,0xdf9450,0x427b77).mesh(),
    boat(null,0xce8a41,0x9c5848).mesh(),
  ];
  for(let i=-1;i<11;i++) {
    const index=(i+3)%3, mesh=hulls[index].clone();
    mesh.position.set(8.7+i*11.7,0,-4.9-(index===1?4:0));
    mesh.rotation.y=(index===1?-1:1)*(.13+.10*frac(i,3));
    mesh.scale.setScalar(index===1?.85:1);
    scene.add(mesh); boats.push(mesh);
  }
  const heroCargo=hulls[2].clone();
  heroCargo.position.set(12.3,0,3.1); heroCargo.rotation.y=-.59; heroCargo.scale.setScalar(1.25);
  scene.add(heroCargo);
  const reflections=new Model();
  for(const boat of boats) {
    for(let i=0;i<24;i++) {
      const x=boat.position.x+wave(i,41)*3,z=boat.position.z+wave(i,43)*.91;
      const w=.32+frac(i,7)*.70;
      reflections.quad([x-w,.032,z],[x,.032,z+.095],[x+w,.032,z],[x,.032,z-.1],i%3===0?0x6ca895:0x579d8f);
    }
  }
  scene.add(reflections.mesh(flat));
  const pier = new Model();
  for(const x of [-3.3,-.8,1.5]) for(const z of [-3.9,-1.25]) {
    pier.rod(0x775a43,[x,-4.1,z],[x,1.21,z],.12);
    pier.shape(barrel,0xa8885d,x,1.18,z,.15,.13,.15);
  }
  for(let i=0;i<14;i++) pier.box(i%3===0?0xb38756:0xc49660,-3.5+i*.39,.64,-2.65,.375,.18,3.4);
  for(const x of [-3.0,-.2]) for(const z of [-3.95,-1.56]) pier.rod(0x977345,[x,.72,z],[x,3.25,z],.09);
  roof(pier,-1.6,3.05,-2.75,4.05,1.22,3.45,0xcb7853,0xa35d43);
  // Sun-faded roof courses and eave lamps.
  for(let i=1;i<6;i++) {
    const f=i/6;
    pier.box(0xd68b60,-1.6,3.06+f*1.22,-1.025-f*1.725,4.09,.06,.11);
  }
  for(const x of [-2.7,-.48]) {
    pier.rod(0x67523d,[x,3,-1.52],[x,2.64,-1.52],.025);
    pier.shape(round,0xda7950,x,2.46,-1.52,.19,.24,.17);
    pier.box(0xad6242,x,2.20,-1.52,.035,.17,.03);
  }
  pier.box(0x996c43,-2.2,1.06,-2.3,1.2,.69,.77);
  pier.shape(barrel,0xb18b57,.27,1.12,-2.1,.36,.71,.35);
  person(pier,-.95,.77,-2.3,0xa04e47);
  const dock=place(pier,0,0,0);

  // Lettered timber boards are meshes fixed to the dock and to the plants' fishing stakes.
  function paintedBoard(words, w, h, background, accent) {
    const canvas=document.createElement("canvas");
    canvas.width=512; canvas.height=140;
    const ctx=canvas.getContext("2d");
    ctx.fillStyle=background; ctx.fillRect(0,0,512,140);
    ctx.lineWidth=4; ctx.strokeStyle=accent; ctx.strokeRect(8,8,496,124);
    ctx.fillStyle=accent;
    for(const pin of [20,492]) for(const y of [20,120]) {
      ctx.beginPath();ctx.arc(pin,y,3,0,Math.PI*2);ctx.fill();
    }
    ctx.textAlign="center";ctx.textBaseline="middle";ctx.font="bold 77px Georgia, serif";
    ctx.fillText(words,256,73,460);
    const map=new T.CanvasTexture(canvas);map.colorSpace=T.SRGBColorSpace;
    return new T.Mesh(new T.PlaneGeometry(w,h),new T.MeshBasicMaterial({map}));
  }
  const gateway=new Model();
  // A short landing with a ladder marks the drop-off at the actual dock coordinate.
  for(const x of [-.55,2.28]) {
    gateway.rod(0x77593c,[x,-2.3,-.86],[x,3.82,-.86],.082);
    for(const y of [.79,2.62,3.65]) gateway.shape(barrel,0xe5b977,x,y,-.86,.092,.14,.092);
    gateway.rod(0x9b784d,[x,2.58,-.86],[x+(x<0?.64:-.64),3.52,-.86],.059);
  }
  gateway.box(0x8d6549,.85,3.56,-.87,3.62,.15,.18);
  gateway.box(0x624c37,.85,3.14,-.83,3.15,.81,.12);
  for(const x of [.22,1.29]) {
    gateway.rod(0xbc9160,[x,-1.42,-.45],[x,.81,-.80],.048);
  }
  for(let i=0;i<5;i++) gateway.box(0xcaac73,.755,.62-i*.42,-.76+i*.068,1.11,.069,.085);
  const lifeRing=new T.Mesh(new T.TorusGeometry(.30,.08,7,24),new T.MeshLambertMaterial({color:0xde6d43}));
  lifeRing.position.set(2.27,1.20,-.75); gateway.box(0xc9ad78,2.25,1.65,-.84,.07,.31,.07);
  const dockName=paintedBoard("Bến Út Sen",3.05,.75,"#29594f","#ffe5ad");
  dockName.position.set(.85,3.14,-.755);
  dock.add(gateway.mesh(),dockName,lifeRing);

  // Mooring line under the landing. Depth knots help locate the way home underwater.
  const sounding=new T.Group(), tether=new Model(), depthKnots=[];
  tether.rod(0x9b9869,[0,0,0],[0,-1,0],.037);
  const rope=tether.mesh(flat);
  sounding.add(rope);
  for(let d=5;d<=30;d+=5){
    const knot=new Model();
    knot.oval(d%10===0?0xf4c46c:0xcab180,0,0,0,.12,.17,.09);
    for(const side of [-1,1]) knot.rod(0xd6bd81,[side*.06,-.04,0],[side*.22,-.19,.04],.03);
    const mesh=knot.mesh(flat);mesh.position.y=-d;
    sounding.add(mesh);depthKnots.push(mesh);
  }
  sounding.position.set(.24,0,-.54);
  dock.add(sounding);
  const anchor=new Model();
  anchor.rod(0x798880,[0,.52,0],[0,-.09,0],.07);
  anchor.rod(0x87978d,[-.42,.24,0],[0,-.09,0],.065);
  anchor.rod(0x87978d,[0,-.09,0],[.42,.24,0],.065);
  const mooringWeight=anchor.mesh();sounding.add(mooringWeight);

  const plantSigns={
    bong_dien_dien:["Điên điển", "#664833", "#ffda74", 0xf2bb48],
    bong_sung:["Bông súng", "#71455a", "#ffe0d9", 0xec93ab],
    keo_neo:["Kèo nèo", "#345e54", "#e5efbb", 0xb1c46d],
  };
  function fishingStake(kind) {
    const [text,bg,ink,flag]=plantSigns[kind] || ["Bãi hái","#335c50","#f5dcab",0xead18a];
    const frame=new Model();
    frame.rod(0x967345,[0,-.75,0],[0,1.69,0],.048);
    frame.shape(barrel,0xe2bb7b,0,.53,0,.075,.20,.075);
    frame.tri([0,1.59,.014],[.50,1.48,.014],[0,1.26,.014],flag);
    frame.box(0x765941,.66,.98,0,2.15,.60,.09);
    const stake=frame.mesh(), board=paintedBoard(text,2.08,.54,bg,ink);
    board.position.set(.66,.98,.051);stake.add(board);
    stake.position.set(1.00,0,-.62);
    return stake;
  }

  function ingredient(kind) {
    const m=new Model(), flowers=new Model();
    for(let i=0;i<8;i++) {
      const a=i*2.4, r=i===0?0:.36+.38*frac(i,2), x=Math.cos(a)*r,z=Math.sin(a)*r*.50;
      if(kind==="bong_sung") {
        m.shape(barrel,i%2?0x538955:0x739c55,x,.035,z,.30,.07,.23);
        if(i%3===0) {
          for(let k=0;k<7;k++) {
            const t=k*.898;
            flowers.oval(k%2?0xeb83a3:0xf3acc1,x+Math.cos(t)*.115,.215,z+Math.sin(t)*.115,.09,.15,.075);
          }
          flowers.oval(0xffd572,x,.27,z,.075,.11,.075);
        }
      } else {
        const h=.35+frac(i,3)*.40;
        m.rod(0x587c4e,[x,0,z],[x+.09,h,z],.028);
        m.shape(gem,0x7aab62,x-.04,h*.55,z,.19,.095,.12,0,0,.38);
        flowers.shape(gem,kind==="keo_neo"?0x83ad63:0xffcc52,x+.12,h,z,.14,.18,.105,0,0,-.25);
        if(kind!=="keo_neo") flowers.oval(0xffdc6c,x+.23,h-.1,z+.02,.09,.11,.08);
      }
    }
    const group=new T.Group();
    group.add(m.mesh(),flowers.mesh(),fishingStake(kind));
    return group;
  }
  function school(kind) {
    const m=new Model();
    const loc=kind==="ca_loc", keo=kind==="ca_keo";
    const count=loc?1:keo?2:3;
    const body=loc?0xb8a05e:keo?0xcc986e:0xbee2ce;
    const back=loc?0x716e45:keo?0x956445:0x72afa4;
    for(let i=0;i<count;i++){
      const x=i===0?0:i===1?-.66:-.52, y=i===0?0:i===1?.33:-.32,z=i===0?.04:-.25;
      const size=loc?1.05:i===0?.75:.53;
      m.oval(body,x,y,z,.85*size,.30*size,.25*size);
      m.tri([x-.60*size,y,z],[x-1.05*size,y+.32*size,z],[x-1.03*size,y-.31*size,z],back);
      m.tri([x-.30*size,y+.21*size,z],[x-.14*size,y+.46*size,z],[x+.28*size,y+.25*size,z],back);
      m.oval(0x293e3f,x+.55*size,y+.06*size,z+.19*size,.064*size,.067*size,.035*size);
      m.tri([x+.16*size,y,z+.20*size],[x-.26*size,y-.20*size,z+.27*size],[x-.08*size,y+.01*size,z+.27*size],back);
    }
    return m.mesh();
  }
  function crocodile() {
    const m=new Model();
    m.oval(0x5e7453,-.23,0,0,1.15,.40,.38);
    m.oval(0x88935e,.96,.07,0,.6,.32,.32);
    m.oval(0xbbac78,1.58,-.025,0,.76,.16,.26);
    m.oval(0x82915e,1.55,.10,0,.77,.17,.26);
    m.tri([-1.05,.13,.08],[-2.55,.34,.05],[-1.07,-.24,.12],0x687a55);
    for(let i=0;i<8;i++) {
      const x=-1.27+i*.26, y=.29+.11*Math.sin(i*.47);
      m.shape(cone,0x52684d,x,y,0,.13,.21,.11);
    }
    for(const x of [-.81,.54]) for(const z of [-.25,.25])
      m.rod(0x7d8857,[x,-.08,z],[x-.25,-.42,z*2.3],.09);
    m.oval(0xe2b76d,1.06,.31,.22,.10,.10,.08);
    m.oval(0x3a4134,1.07,.32,.28,.04,.06,.03);
    return m.mesh();
  }
  function snake() {
    const m=new Model();
    for(let i=0;i<10;i++) {
      const a=i*.27-1.4,b=a+.27;
      m.rod(i%2?0x68785c:0x9f8659,[a,.24*Math.sin(i*.8),0],[b,.24*Math.sin((i+1)*.8),0],.11+i*.007);
    }
    m.oval(0x90824d,1.42,.25,0,.29,.18,.16);
    m.oval(0x252f2b,1.52,.3,.12,.036,.036,.035);
    return m.mesh();
  }
  const diverBody = new Model();
  // Bright headscarf, teal mask, ochre air bottle and vermilion swimming fins.
  diverBody.oval(0xd26b4a,.03,0,0,.37,.52,.24);
  diverBody.oval(0x284e55,-.02,-.38,0,.31,.23,.21);
  diverBody.oval(0xe5b282,.075,.65,0,.30,.34,.27);
  diverBody.oval(0x4c3b35,.015,.84,-.04,.3,.22,.25);
  diverBody.oval(0xd45e40,.04,.84,.08,.312,.101,.235);
  diverBody.shape(cube,0x244b55,.19,.655,.217,.39,.165,.113);
  diverBody.shape(cube,0x94e2db,.205,.667,.282,.29,.095,.023);
  diverBody.rod(0xf0cd72,[.31,.61,.06],[.37,1.02,.06],.04);
  diverBody.oval(0xe3bb64,-.29,.02,-.13,.18,.43,.18);
  diverBody.rod(0xe6b38a,[.20,.25,.13],[.45,-.015,.27],.085);
  diverBody.rod(0xe6b38a,[.45,-.015,.27],[.67,.09,.22],.075);
  const swimmer=new T.Group(), body=diverBody.mesh();
  swimmer.add(body);
  const legModel=new Model();
  legModel.rod(0x365d60,[0,0,0],[-.08,-.39,0],.115);
  legModel.rod(0xc49474,[-.08,-.39,0],[-.17,-.65,.014],.08);
  legModel.oval(0xe3824c,-.24,-.70,.018,.23,.07,.13);
  const leg=legModel.mesh(), otherLeg=leg.clone();
  leg.position.set(-.11,-.45,.13); otherLeg.position.set(.09,-.45,-.13);
  swimmer.add(leg,otherLeg); scene.add(swimmer);

  const bubbles=new Model();
  for(let i=0;i<5;i++){
    const r=.04+(i%3)*.017;
    bubbles.oval(0xb6ead7,Math.sin(i*1.8)*.22,i*.24,0,r,r,.028);
  }
  const breath=place(bubbles,0,0,.4,1,0,flat);
  const ring = new T.Mesh(new T.RingGeometry(.96,1,64),new T.MeshBasicMaterial({
    color:0xffe4a1,transparent:true,opacity:.42,depthWrite:false,side:T.DoubleSide
  }));
  scene.add(ring);
  const targetFlag = new T.Mesh(new T.ConeGeometry(.22, .43, 4), new T.MeshBasicMaterial({color:0xffcd6e}));
  targetFlag.rotation.z = Math.PI;
  scene.add(targetFlag);
  const templates=new Map(), active=new Map(), spare=new Map();
  function visual(type, datum) {
    const key=type+":"+datum.kind;
    let record=active.get(type+":"+datum.id);
    if(record && record.key===key) return record;
    if(record) release(record);
    if(!templates.has(key)) {
      templates.set(key,type==="node" ? ingredient(datum.kind) : type==="fish" ?
        school(datum.kind) : datum.kind==="ran" ? snake() : crocodile());
    }
    const pool=spare.get(key);
    const model=pool?.pop() || templates.get(key).clone(true);
    scene.add(model); model.visible=true; model.rotation.set(0,0,0);
    record={key,model,id:type+":"+datum.id,seen:0,x:null};
    active.set(record.id,record);
    return record;
  }
  function release(record) {
    active.delete(record.id); scene.remove(record.model);
    if(!spare.has(record.key)) spare.set(record.key,[]);
    spare.get(record.key).push(record.model);
  }
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
  let frame=0, facing=1;
  function update(state,width,height,seconds=0,screen="",targetId=null) {
    const meta=state.meta || {}, player=state.player, dp=meta.dock_pos || [2,0];
    const [px,depth]=player?.pos || dp;
    const title=screen==="menu", ratio=width/Math.max(1,height);
    const half=title ? (ratio<1 ? 8.5 : 7.5) : Math.max(9.2,8.5/Math.max(.2,ratio));
    foreground.visible=title; heroCargo.visible=title;
    camera.left=-half*ratio; camera.right=half*ratio; camera.top=half; camera.bottom=-half;
    camera.updateProjectionMatrix();
    const bounds=meta.bounds?.x || [0,100];
    const centerX=clamp(px+Math.min(half*ratio*.17,3.7),bounds[0],bounds[1]);
    const centerY=-depth-.52;
    camera.position.set(centerX,centerY+7.0,39);
    camera.lookAt(centerX,centerY,0);
    if(title) {
      const focusX=ratio<1?8.2:4.3;
      camera.position.set(focusX+10.2,8.45,27.0);
      camera.lookAt(focusX,2.60,-7);
      skyObjects.position.x=4.4;
    } else {
      skyObjects.position.x=centerX*.90+6;
    }
    dock.position.set(dp[0],-dp[1],0);
    const soundDepth=Math.max(0,(meta.bounds?.d?.[1] ?? 30)-dp[1]);
    rope.scale.y=soundDepth; mooringWeight.position.y=-soundDepth;
    for(const knot of depthKnots) knot.visible=-knot.position.y<soundDepth;
    targetFlag.visible = targetId === "@dock" && !screen;
    if (targetFlag.visible) targetFlag.position.set(dp[0], 1.7 - dp[1], .85);
    for(let i=0;i<boats.length;i++) {
      boats[i].position.y=.035*Math.sin(seconds*1.3+i);
      boats[i].rotation.z=.009*Math.sin(seconds+i*2.7);
    }
    swimmer.visible=Boolean(player);
    breath.visible=Boolean(player && !player.at_surface);
    ring.visible=Boolean(player);
    if(player) {
      const angle=(player.heading_deg || 0)*Math.PI/180;
      if(Math.abs(Math.cos(angle))>.1) facing=Math.sign(Math.cos(angle));
      const speed=Math.min(1,Math.hypot(...(player.vel || []))*.3);
      const surf=player.at_surface ?? depth<=.5;
      swimmer.scale.set(facing,1,1);
      // Rest upright at the dock. Tilt toward the actual travel vector below.
      swimmer.rotation.z=surf ? -.13*facing : facing*(-Math.PI/2-Math.atan2(Math.sin(angle),Math.abs(Math.cos(angle))));
      swimmer.position.set(px,-depth+.05*Math.sin(seconds*3),.56);
      leg.rotation.z=.13+Math.sin(seconds*(speed?8:3))*(.15+.32*speed);
      otherLeg.rotation.z=.13-Math.sin(seconds*(speed?8:3))*(.15+.32*speed);
      swimmer.visible=!title && !(player.invuln_ticks>0 && Math.floor(player.invuln_ticks/6)%2);
      breath.position.set(px-.23*facing,-depth+.52+(seconds*.56%1.25),.58);
      const radius=surf ? meta.interact_radius : meta.catch_radius;
      ring.visible=!title && Number.isFinite(radius) && radius>0;
      if(ring.visible) { ring.scale.setScalar(radius); ring.position.set(px,-depth,.32); }
    }
    frame++;
    for(const [type,items] of [["node",state.nodes],["fish",state.fish],["monster",state.monsters]]) {
      for(const item of items || []) {
        const rec=visual(type,item), model=rec.model;
        rec.seen=frame;
        model.position.set(item.pos[0],-item.pos[1],type==="node"?.20:.38);
        if (!screen && item.id === targetId) {
          targetFlag.visible = true;
          targetFlag.position.set(item.pos[0], .9 - item.pos[1] + .08*Math.sin(seconds*3), .85);
        }
        if(type==="node") {
          model.children[1].visible=item.ready!==false;
          model.children[0].scale.setScalar(item.ready===false?.65:1);
          model.children[2].visible=!title;
          model.rotation.z=Math.sin(seconds*1.4+item.pos[0])*.04;
        } else if(type==="fish") {
          const a=(item.heading_deg || 0)*Math.PI/180, sign=Math.cos(a)>=0?1:-1;
          model.scale.x=sign;
          model.rotation.z=-Math.atan2(Math.sin(a),Math.abs(Math.cos(a)))*sign;
          model.rotation.y=.12*Math.sin(seconds*5+item.pos[1]);
        } else {
          if(rec.x!==null && Math.abs(item.pos[0]-rec.x)>.0001) model.scale.x=Math.sign(item.pos[0]-rec.x);
          else if(rec.x===null) model.scale.x=1;
          rec.x=item.pos[0];
        }
      }
    }
    for(const record of active.values()) if(record.seen!==frame) release(record);
  }
  return {scene,camera,update};
}
