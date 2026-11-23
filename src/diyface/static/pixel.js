/* 拼豆画布：32×32，状态全在前端，导出走后端 /api/pixel/render */

const GRID = 32;
const DISPLAY = 512;
const CELL = DISPLAY / GRID;
const STORAGE_KEY = "diyface.pixel.v1";

const PALETTE = [
  "#FFFFFF", "#F2D5B8", "#E8B98A", "#C68B59", "#8B5A2B", "#5C3A21",
  "#1F2430", "#6B7280", "#C0392B", "#E74C3C", "#F39C12", "#F1C40F",
  "#27AE60", "#2ECC71", "#16A085", "#2980B9", "#3498DB", "#8E44AD",
  "#9B59B6", "#E84393", "#95A5A6", "#7F8C8D", "#D35400", "#2C3E50",
];

const state = {
  cells: new Array(GRID * GRID).fill(-1),
  color: 0,
  tool: "pen",
  style: "bead",
  history: [],
};

const board = document.getElementById("board");
const paletteBox = document.getElementById("palette");
const statusBox = document.getElementById("status");
const ctx = board.getContext("2d");

function say(text) {
  statusBox.textContent = text || "";
}

function snapshot() {
  return state.cells.slice();
}

function pushHistory() {
  state.history.push(snapshot());
  if (state.history.length > 40) state.history.shift();
}

function paintCell(index, color) {
  if (index < 0 || index >= state.cells.length) return false;
  if (state.cells[index] === color) return false;
  state.cells[index] = color;
  return true;
}

function flush() {
  draw();
  saveLocal();
}

function draw() {
  ctx.clearRect(0, 0, DISPLAY, DISPLAY);
  for (let row = 0; row < GRID; row += 1) {
    for (let col = 0; col < GRID; col += 1) {
      const value = state.cells[row * GRID + col];
      if (value < 0) {
        ctx.fillStyle = (row + col) % 2 === 0 ? "#f6f8fc" : "#eef1f7";
        ctx.fillRect(col * CELL, row * CELL, CELL, CELL);
        continue;
      }
      const color = PALETTE[value];
      if (state.style === "flat") {
        ctx.fillStyle = color;
        ctx.fillRect(col * CELL, row * CELL, CELL, CELL);
      } else {
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(col * CELL + CELL / 2, row * CELL + CELL / 2, CELL / 2 - 1, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "rgba(0, 0, 0, .28)";
        ctx.beginPath();
        ctx.arc(col * CELL + CELL / 2, row * CELL + CELL / 2, CELL * 0.11, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }
}

function cellFromEvent(event) {
  const rect = board.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * DISPLAY;
  const y = ((event.clientY - rect.top) / rect.height) * DISPLAY;
  const col = Math.floor(x / CELL);
  const row = Math.floor(y / CELL);
  if (col < 0 || col >= GRID || row < 0 || row >= GRID) return -1;
  return row * GRID + col;
}

function bucketFill(start, color) {
  const target = state.cells[start];
  if (target === color) return;
  const stack = [start];
  while (stack.length) {
    const index = stack.pop();
    if (state.cells[index] !== target) continue;
    state.cells[index] = color;
    const row = Math.floor(index / GRID);
    const col = index % GRID;
    if (col > 0) stack.push(index - 1);
    if (col < GRID - 1) stack.push(index + 1);
    if (row > 0) stack.push(index - GRID);
    if (row < GRID - 1) stack.push(index + GRID);
  }
}

let drawing = false;

function applyAt(index) {
  if (index < 0) return;
  if (state.tool === "bucket") {
    bucketFill(index, state.color);
  } else {
    paintCell(index, state.tool === "eraser" ? -1 : state.color);
  }
  flush();
}

board.addEventListener("pointerdown", (event) => {
  event.preventDefault();
  pushHistory();
  drawing = true;
  board.setPointerCapture(event.pointerId);
  applyAt(cellFromEvent(event));
});

board.addEventListener("pointermove", (event) => {
  if (!drawing || state.tool === "bucket") return;
  applyAt(cellFromEvent(event));
});

function endDraw() {
  drawing = false;
}

board.addEventListener("pointerup", endDraw);
board.addEventListener("pointercancel", endDraw);
board.addEventListener("pointerleave", endDraw);

/* ---------------------------- 调色板 / 工具 ---------------------------- */

function buildPalette() {
  const buttons = PALETTE.map((color, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "swatch";
    button.style.background = color;
    button.dataset.index = String(index);
    button.setAttribute("aria-label", `颜色 ${color}`);
    button.setAttribute("aria-pressed", String(index === state.color));
    button.addEventListener("click", () => {
      state.color = index;
      if (state.tool === "eraser") setTool("pen");
      syncPalette();
    });
    return button;
  });
  paletteBox.replaceChildren(...buttons);
}

function syncPalette() {
  for (const button of paletteBox.querySelectorAll(".swatch")) {
    button.setAttribute("aria-pressed", String(Number(button.dataset.index) === state.color));
  }
}

function setTool(tool) {
  state.tool = tool;
  for (const button of document.querySelectorAll("[data-tool]")) {
    button.setAttribute("aria-pressed", String(button.dataset.tool === tool));
  }
}

document.querySelectorAll("[data-tool]").forEach((button) => {
  button.addEventListener("click", () => setTool(button.dataset.tool));
});

document.getElementById("undo").addEventListener("click", () => {
  const previous = state.history.pop();
  if (!previous) return say("没有可撤销的操作");
  state.cells = previous;
  flush();
});

document.getElementById("clear").addEventListener("click", () => {
  pushHistory();
  state.cells = new Array(GRID * GRID).fill(-1);
  flush();
});

document.getElementById("style-toggle").addEventListener("click", (event) => {
  state.style = state.style === "bead" ? "flat" : "bead";
  event.currentTarget.textContent = state.style === "bead" ? "换成方块" : "换成珠子";
  event.currentTarget.setAttribute("aria-pressed", String(state.style === "flat"));
  draw();
});

/* ---------------------------- 编码 / 存储 ---------------------------- */

function encode() {
  const parts = [];
  let current = state.cells[0];
  let run = 1;
  for (let index = 1; index < state.cells.length; index += 1) {
    if (state.cells[index] === current) {
      run += 1;
    } else {
      parts.push(`${current}x${run}`);
      current = state.cells[index];
      run = 1;
    }
  }
  parts.push(`${current}x${run}`);
  return parts.join(",");
}

function decode(text) {
  const cells = [];
  for (const chunk of text.split(",")) {
    const match = /^(-?\d+)x(\d+)$/.exec(chunk.trim());
    if (!match) return null;
    const value = Number(match[1]);
    const count = Number(match[2]);
    for (let index = 0; index < count; index += 1) cells.push(value);
  }
  return cells.length === GRID * GRID ? cells : null;
}

function saveLocal() {
  try {
    localStorage.setItem(STORAGE_KEY, encode());
  } catch (error) {
    /* 隐私模式下写不进去，忽略 */
  }
}

function loadLocal() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const cells = raw ? decode(raw) : null;
    if (cells) state.cells = cells;
  } catch (error) {
    /* ignore */
  }
}

function readShareParam() {
  const param = new URLSearchParams(location.search).get("p");
  if (!param) return null;
  return decode(param);
}

/* ---------------------------- 导出 / 分享 ---------------------------- */

async function requestPng(size) {
  const response = await fetch("/api/pixel/render", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      palette: PALETTE,
      pixels: encode(),
      size,
      style: state.style,
    }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload?.error?.message || `导出失败（${response.status}）`);
  }
  return response.blob();
}

async function download(size) {
  say("正在合成…");
  try {
    const blob = await requestPng(size);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `pixel-${size}.png`;
    link.click();
    URL.revokeObjectURL(url);
    say(`已导出 ${size}×${size}`);
  } catch (error) {
    say(error.message);
  }
}

document.getElementById("download-1024").addEventListener("click", () => download(1024));
document.getElementById("download-256").addEventListener("click", () => download(256));

document.getElementById("share").addEventListener("click", async () => {
  const url = `${location.origin}/pixel?p=${encodeURIComponent(encode())}`;
  try {
    await navigator.clipboard.writeText(url);
    say("分享链接已复制");
  } catch (error) {
    say(url);
  }
});

document.getElementById("to-avatar").addEventListener("click", () => {
  const KEY = "diyface.stickers.v2";
  try {
    let list = [];
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) list = parsed;
    }
    list.push({
      palette: PALETTE,
      pixels: encode(),
      style: state.style,
      x: 0.85,
      y: 0.85,
      scale: 0.22,
    });
    localStorage.setItem(KEY, JSON.stringify(list.slice(-8)));
    location.href = "/?sticker=1";
  } catch (error) {
    say("浏览器存储不可用，无法传给头像页");
  }
});

window.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z") {
    event.preventDefault();
    document.getElementById("undo").click();
    return;
  }
  if (event.key.toLowerCase() === "b") setTool("pen");
  if (event.key.toLowerCase() === "e") setTool("eraser");
  if (event.key.toLowerCase() === "g") setTool("bucket");
});

/* ---------------------------- 启动 ---------------------------- */

loadLocal();
const shared = readShareParam();
if (shared) state.cells = shared;
buildPalette();
draw();
say(shared ? "已载入分享的画布" : "");
