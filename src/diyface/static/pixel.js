/* 拼豆画布：32×32，状态全在前端，导出走后端 /api/pixel/render */

const GRID = 32;
const DISPLAY = 512;
const CELL = DISPLAY / GRID;
const STORAGE_KEY = "diyface.pixel.v1";

const PALETTE = [
"#FFFFFF", "#F7D4B8", "#E4B685", "#C79266", "#A17140", "#4B2B1C", "#213244", "#697E80",
"#BB0126", "#EF4D3E", "#F3A014", "#FEC832", "#1D9E54", "#5EE88C", "#26B78E", "#337BAD",
"#54A7E9", "#882893", "#945AB1", "#F1559F", "#98A6A6", "#878787", "#F47E36", "#1E334E",
"#FBFBFB", "#DBD9DA", "#B4B4B4", "#96A09F", "#56534E", "#2C2C2C", "#D8D4D3", "#B0A796",
"#F5C9CA", "#FF9280", "#F73D48", "#D40E1F", "#FFD785", "#FDA42E", "#FB852B", "#F85842",
"#E9EC91", "#DFF139", "#64F343", "#39E158", "#2ADED3", "#3349C3", "#9C34AD", "#EC4072",
"#FCFDFF", "#F2EEE5", "#E0D4BC", "#DCB387", "#B2714B", "#79544E", "#1B1213", "#010101",
"#7DCA9C", "#32C958", "#1A6E3D", "#ABF8FE", "#76CEDE", "#3977CC", "#301A49", "#AB91C0",
"#913635", "#9EB33E", "#E58EAE", "#E987EA", "#627032", "#162C7E", "#E3D2FE", "#343B1A",
"#188690", "#ACE84C", "#B5038F", "#B5026A", "#B2E694", "#ECDB59", "#E0677A", "#4E846D",
"#364A89", "#F2A5E8", "#AE8082", "#0A4241", "#92AD60", "#DA8C42", "#CAEDCF", "#2F1E8E",
"#849DC6", "#BEDDFC", "#9FF685", "#E7B34E", "#44CDFB", "#868DD3", "#3653AF", "#FFFF00",
"#874628", "#C6DF5F", "#907C35", "#64E0A4", "#C76A62", "#FCADB2", "#2A5037", "#C1BD8D",
"#BE454A", "#FCFED6", "#F6BDE8", "#96B69F", "#9D7693", "#8B684C", "#ACB7EF", "#176268",
"#FDA276", "#FEBDA7", "#7EC5F9", "#B37BDC", "#A5452F", "#D33997", "#FBF65E", "#E3FBB1",
"#42ADD1", "#E575C7", "#FDA951", "#D0E0AF", "#D8C2D9", "#F1FA7D", "#911932", "#F13484",
];

const CODES = ["H2", "Y6", "G9", "M13", "R21", "G8", "C18", "M3", "F8", "F3", "G6", "A26", "B8", "Y8", "B19", "P14", "C6", "D14", "R9", "E5", "H15", "H4", "A10", "C12", "H1", "P9", "H3", "H20", "R13", "H6", "R12", "M7", "E15", "F1", "F2", "R1", "A25", "P17", "R3", "A14", "Q2", "B1", "B2", "B5", "C11", "C9", "D20", "E6", "T1", "H19", "M4", "G4", "G13", "G17", "H16", "H7", "R18", "R5", "B12", "C2", "Q5", "C7", "D10", "ZG8", "F6", "B17", "R27", "Y5", "B11", "D4", "D8", "B23", "C19", "B14", "D13", "E13", "B31", "P8", "F9", "B25", "C29", "Q1", "M8", "B22", "B32", "G10", "B20", "D15", "ZG5", "C21", "B3", "G5", "C4", "D2", "D3", "Q3", "F10", "B29", "B26", "B6", "R25", "F14", "B9", "ZG3", "F19", "A2", "E3", "ZG4", "M11", "G14", "D1", "B21", "A12", "P18", "C24", "D6", "G20", "E10", "A15", "B30", "C26", "E9", "A6", "B27", "D19", "Y7", "F7", "R2"];

function colorCode(index) {
  // Mard 官方色号，例如白色 H2、灰色 H3
  return CODES[index] || "—";
}

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

function updateCursorInfo(col, row) {
  const box = document.getElementById("cursor-info");
  if (!box) return;
  box.textContent = col > 0 && row > 0 ? `列 ${col} · 行 ${row}` : "列 — · 行 —";
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
  const index = cellFromEvent(event);
  updateCursorInfo((index % GRID) + 1, Math.floor(index / GRID) + 1);
  applyAt(index);
});

board.addEventListener("pointermove", (event) => {
  if (!drawing) {
    const index = cellFromEvent(event);
    updateCursorInfo((index % GRID) + 1, Math.floor(index / GRID) + 1);
    return;
  }
  if (state.tool === "bucket") return;
  applyAt(cellFromEvent(event));
});

function endDraw() {
  drawing = false;
}

board.addEventListener("pointerup", endDraw);
board.addEventListener("pointercancel", endDraw);
board.addEventListener("pointerleave", endDraw);

/* ---------------------------- 调色板 / 工具 ---------------------------- */

function readableInk(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.62 ? "rgba(15, 15, 16, .75)" : "rgba(255, 255, 255, .9)";
}

function updateColorInfo() {
  const box = document.getElementById("color-info");
  if (!box) return;
  box.textContent = `当前：色号 ${colorCode(state.color)} · ${PALETTE[state.color]}`;
}

function buildRulers() {
  const x = document.getElementById("ruler-x");
  const y = document.getElementById("ruler-y");
  if (!x || !y) return;
  const make = (count) =>
    Array.from({ length: count }, (_, index) => {
      const span = document.createElement("span");
      span.textContent = String(index + 1);
      if ((index + 1) % 4 === 0 || index === 0) span.classList.add("is-major");
      return span;
    });
  x.replaceChildren(...make(GRID));
  y.replaceChildren(...make(GRID));
}

function buildPalette() {
  const buttons = PALETTE.map((color, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "swatch";
    button.style.background = color;
    button.dataset.index = String(index);
    button.setAttribute("aria-label", `颜色 ${color}`);
    button.setAttribute("aria-pressed", String(index === state.color));
    button.title = `色号 ${colorCode(index)} · ${color}`;

    const code = document.createElement("span");
    code.className = "swatch-code";
    code.textContent = colorCode(index);
    code.style.color = readableInk(color);
    button.append(code);

    button.addEventListener("click", () => {
      state.color = index;
      if (state.tool === "eraser") setTool("pen");
      syncPalette();
      updateColorInfo();
    });
    return button;
  });
  paletteBox.replaceChildren(...buttons);
}

function syncPalette() {
  updateColorInfo();
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

document.getElementById("import-image").addEventListener("click", () => {
  document.getElementById("import-file").click();
});

document.getElementById("import-file").addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  say("正在识别图片…");
  try {
    const form = new FormData();
    form.append("image", file);
    const response = await fetch("/api/pixel/import", { method: "POST", body: form });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload?.error?.message || `导入失败（${response.status}）`);
    }
    const data = await response.json();
    const cells = decode(data.pixels);
    if (!cells) throw new Error("服务端返回的画布无法解析");
    pushHistory();
    state.cells = cells;
    flush();
    say(`已导入：${data.colors} 种颜色，${cells.filter((v) => v >= 0).length} 颗珠子`);
  } catch (error) {
    say(error.message);
  } finally {
    event.target.value = "";
  }
});

document.getElementById("toggle-codes").addEventListener("click", () => {
  const box = document.getElementById("codes-box");
  box.hidden = !box.hidden;
  if (!box.hidden) document.getElementById("codes-text").focus();
});

document.getElementById("codes-apply").addEventListener("click", async () => {
  const text = document.getElementById("codes-text").value;
  if (!text.trim()) return say("先把色号粘进来");
  try {
    const response = await fetch("/api/pixel/codes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data?.error?.message || "解析失败");
    const cells = decode(data.pixels);
    if (!cells) throw new Error("返回的画布无法解析");
    pushHistory();
    state.cells = cells;
    flush();
    const unknown = data.unknown?.length ? `，未识别：${data.unknown.join(" ")}` : "";
    say(`已生成：${data.colors} 种颜色${unknown}`);
  } catch (error) {
    say(error.message);
  }
});

let chartState = null;

document.getElementById("import-chart").addEventListener("click", () => {
  document.getElementById("chart-file").click();
});

document.getElementById("chart-file").addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  say("正在找网格…");
  try {
    const form = new FormData();
    form.append("image", file);
    const response = await fetch("/api/pixel/chart", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data?.error?.message || "识别失败");

    chartState = data;
    renderChartClusters(data);
    document.getElementById("chart-box").hidden = false;
    say(`识别到 ${data.rows}×${data.cols} 网格，${data.clusters.length} 种图案`);
  } catch (error) {
    say(error.message);
  } finally {
    event.target.value = "";
  }
});

function renderChartClusters(data) {
  const box = document.getElementById("chart-clusters");
  document.getElementById("chart-size").textContent = `${data.rows} 行 × ${data.cols} 列`;
  const rows = data.clusters.map((cluster, index) => {
    const row = document.createElement("div");
    row.className = "chart-cluster";

    const img = document.createElement("img");
    img.src = `data:image/png;base64,${cluster.preview}`;
    img.alt = `图案 ${index + 1}`;

    const select = document.createElement("select");
    select.dataset.clusterId = String(cluster.id);
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = `空（${cluster.count} 格）`;
    select.append(empty);
    for (const code of data.codes || []) {
      const option = document.createElement("option");
      option.value = code;
      option.textContent = code;
      select.append(option);
    }
    // 数量最多的那一类默认当空格
    if (index === 0) select.value = "";

    row.append(img, select);
    return row;
  });
  box.replaceChildren(...rows);
}

document.getElementById("chart-apply").addEventListener("click", async () => {
  if (!chartState) return;
  const mapping = new Map();
  for (const select of document.querySelectorAll("#chart-clusters select")) {
    mapping.set(Number(select.dataset.clusterId), select.value);
  }

  const grid = Array.from({ length: chartState.rows }, () =>
    Array.from({ length: chartState.cols }, () => "-")
  );
  for (const cluster of chartState.clusters) {
    const code = mapping.get(cluster.id);
    if (!code) continue;
    for (const [row, col] of cluster.cells) {
      if (row < chartState.rows && col < chartState.cols) grid[row][col] = code;
    }
  }

  const text = grid.map((line) => line.join(" ")).join("\n");
  try {
    const response = await fetch("/api/pixel/codes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data?.error?.message || "生成失败");
    const cells = decode(data.pixels);
    pushHistory();
    state.cells = cells;
    flush();
    say(`图纸已生成：${data.colors} 种颜色`);
  } catch (error) {
    say(error.message);
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
buildRulers();
buildPalette();
draw();
updateColorInfo();
say(shared ? "已载入分享的画布" : "");
