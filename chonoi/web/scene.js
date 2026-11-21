import * as THREE from "./vendor/three.module.min.js";
import { createRiver } from "./river.js";
import { createCafe } from "./cafe.js";

const canvas = document.getElementById("world3d");
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
const scenes = new Map();
let renderer;
let frameId;
let previousTime;
let sceneTime = 0;

function paint(time) {
    const view = window.gameView;
    const elapsed = previousTime == null ? 0 : Math.min((time - previousTime) / 1000, 0.1);
    previousTime = time;
    if (view?.state) {
        const snapshot = view.state;
        const evening = snapshot.phase === "quan" || snapshot.phase === "shop";
        const key = evening ? "cafe" : "river";
        if (!scenes.has(key)) scenes.set(key, (evening ? createCafe : createRiver)(THREE));
        const world = scenes.get(key);
        const width = canvas.clientWidth;
        const height = canvas.clientHeight;
        if (width && height) {
            const dpr = renderer.getPixelRatio();
            if (canvas.width !== Math.floor(width * dpr) || canvas.height !== Math.floor(height * dpr)) {
                renderer.setSize(width, height, false);
            }
            if (snapshot.state !== "paused" && !reducedMotion.matches) sceneTime += elapsed;
            const room = snapshot.shop_room;
            const state = room ? {meta: {bounds: room.bounds}, tables: room.tables, stoves: room.stoves} : snapshot;
            world.update(state, width, height, sceneTime, view.screen, view.targetId);
            renderer.render(world.scene, world.camera);
            document.body.classList.add("has-3d");
        }
    }
}

function renderFrame(time) {
    try {
        paint(time);
    } catch (error) {
        document.body.classList.remove("has-3d");
        console.warn("Không vẽ được cảnh 3D.", error);
        return;
    }
    frameId = requestAnimationFrame(renderFrame);
}

function start() {
    renderer = new THREE.WebGLRenderer({canvas, antialias: true, powerPreference: "high-performance"});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    frameId = requestAnimationFrame(renderFrame);
}

canvas.addEventListener("webglcontextlost", (event) => {
    event.preventDefault();
    cancelAnimationFrame(frameId);
    document.body.classList.remove("has-3d");
});
canvas.addEventListener("webglcontextrestored", () => {
    previousTime = null;
    frameId = requestAnimationFrame(renderFrame);
});
try {
    start();
} catch (error) {
    console.warn("Trình duyệt dùng giao diện Canvas 2D.", error);
}
