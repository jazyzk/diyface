/**
 * diyface 前端交互。
 *
 * 设计约束：
 * 1. 首屏素材清单由服务端内联在 #manifest-data；缺失时才回退到 /api/manifest。
 * 2. 预览请求去抖 120ms，并带自增序号；过期响应直接丢弃，新请求会中止旧请求。
 * 3. 任何请求都先校验 response.ok，失败只提示、不白屏。
 * 4. 配方变更立即写入 localStorage，刷新不丢；分享链接把配方编码进 ?r=。
 */

const STORAGE_KEY = "diyface.recipe.v1";
const PREVIEW_DEBOUNCE_MS = 120;
const HEX_COLOR = /^#[0-9A-Fa-f]{6}$/;

const element = (id) => document.getElementById(id);

const elements = {
  categories: element("categories"),
  assets: element("assets"),
  assetsTitle: element("assets-title"),
  assetsCount: element("assets-count"),
  preview: element("preview"),
  previewCard: element("preview-card"),
  previewStatus: element("preview-status"),
  color: element("color"),
  colorValue: element("color-value"),
  colorHint: element("color-hint"),
  swatches: element("swatches"),
  random: element("random"),
  share: element("share"),
  reset: element("reset"),
  toast: element("toast"),
  stickerStatus: element("sticker-status"),
  stickerRemove: element("sticker-remove"),
  stickerLayer: element("sticker-layer"),
  styleTabs: element("style-tabs"),
  stickerScale: element("sticker-scale"),
  stickerScaleValue: element("sticker-scale-value"),
};

const STYLE_FALLBACK = "adventurer";

const STICKER_KEY = "diyface.stickers.v2";
const LEGACY_STICKER_KEY = "diyface.sticker.v1";

const state = {
  manifest: null,
  recipe: null,
  slotId: null,
  seq: 0,
  debounceTimer: 0,
  toastTimer: 0,
  controller: null,
  objectUrl: "",
  randomBusy: false,
  downloading: false,
  previewStatusKind: "",
  stickers: [],
  selectedSticker: 0,
};

/* ------------------------------------------------------------------ */
/* 清单与配方                                                          */
/* ------------------------------------------------------------------ */

function displayLabel(slot) {
  return (slot.label && (slot.label.zh || slot.label.en)) || slot.id;
}

function findSlot(slotId) {
  if (!state.manifest) return null;
  return state.manifest.slots.find((slot) => slot.id === slotId) || null;
}

function readInlineManifest() {
  const node = element("manifest-data");
  if (!node) return null;
  try {
    return JSON.parse(node.textContent || "{}");
  } catch (error) {
    console.warn("内联清单解析失败", error);
    return null;
  }
}

async function fetchManifest() {
  const response = await fetch("/api/manifest", {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`清单加载失败：HTTP ${response.status}`);
  return response.json();
}

/**
 * 用清单校验外来配方（localStorage / 分享链接）：
 * - 槽位必须存在，素材必须属于该槽位；非法值回退到默认配方；
 * - 允许显式的 null（用户主动清空），不能把 null 当成「缺失」；
 * - 颜色必须是 #RRGGBB，缺失时回退默认色；
 * - 只保留清单里认识的槽位，丢掉旧版本残留字段。
 */
function sanitizeRecipe(raw, manifest) {
  const defaults = manifest.default_recipe || {};
  const baseSlots = defaults.slots || {};
  const baseColors = defaults.colors || {};
  const candidate = raw && typeof raw === "object" ? raw : {};
  const candidateSlots =
    candidate.slots && typeof candidate.slots === "object" ? candidate.slots : {};
  const candidateColors =
    candidate.colors && typeof candidate.colors === "object" ? candidate.colors : {};

  const recipe = { version: 1, slots: {}, colors: {} };
  let candidateStyle = null;
  for (const value of Object.values(candidateSlots)) {
    const style = styleOfAsset(value);
    if (style) {
      candidateStyle = style;
      break;
    }
  }

  for (const [slotId, fallback] of Object.entries(baseSlots)) {
    if (!(slotId in candidateSlots)) {
      recipe.slots[slotId] = fallback ?? null;
      continue;
    }
    const value = candidateSlots[slotId];
    if (value === null) {
      recipe.slots[slotId] = null;
      continue;
    }
    const slot = findSlot(slotId);
    const valid =
      slot && typeof value === "string" && slot.assets.some((asset) => asset.id === value);
    if (valid) {
      recipe.slots[slotId] = value;
      continue;
    }
    // 非法素材：回退到「当前这套风格」的第一张，避免回退出另一套风格
    const style = candidateStyle;
    const sameStyle = style
      ? (slot?.assets || []).find((asset) => (asset.style || STYLE_FALLBACK) === style)
      : null;
    recipe.slots[slotId] = sameStyle ? sameStyle.id : (fallback ?? null);
  }

  for (const [slotId, fallback] of Object.entries(baseColors)) {
    const value = candidateColors[slotId];
    recipe.colors[slotId] =
      typeof value === "string" && HEX_COLOR.test(value) ? value.toUpperCase() : fallback;
  }

  if (Number.isInteger(candidate.seed)) recipe.seed = candidate.seed;
  return recipe;
}

function readStoredRecipe() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.warn("读取本地配方失败", error);
    return null;
  }
}

function saveRecipe() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.recipe));
  } catch (error) {
    console.warn("保存本地配方失败", error);
  }
  dropShareParam();
}

function loadInitialRecipe(manifest) {
  const shared = new URLSearchParams(location.search).get("r");
  if (shared) {
    const decoded = decodeRecipe(shared);
    if (decoded) return { recipe: sanitizeRecipe(decoded, manifest), source: "share" };
    return { recipe: sanitizeRecipe(manifest.default_recipe, manifest), source: "invalid-share" };
  }

  const stored = readStoredRecipe();
  if (stored) return { recipe: sanitizeRecipe(stored, manifest), source: "storage" };
  return { recipe: sanitizeRecipe(manifest.default_recipe, manifest), source: "default" };
}

function dropShareParam() {
  const url = new URL(location.href);
  if (!url.searchParams.has("r") && !url.searchParams.has("s")) return;
  url.searchParams.delete("r");
  url.searchParams.delete("s");
  history.replaceState(null, "", url.toString());
}

function pickInitialSlot() {
  const slots = state.manifest.slots;
  const preferred = slots.find((slot) => slot.id === "bangs");
  return (preferred || slots[0] || {}).id || null;
}

/* ------------------------------------------------------------------ */
/* 类目与素材                                                          */
/* ------------------------------------------------------------------ */

function styleOfAsset(assetId) {
  if (!assetId || !state.manifest) return null;
  for (const slot of state.manifest.slots) {
    const found = (slot.assets || []).find((asset) => asset.id === assetId);
    if (found) return found.style || STYLE_FALLBACK;
  }
  return null;
}

function currentStyle() {
  if (!state.manifest) return STYLE_FALLBACK;
  for (const slotId of ["skin", "hair", "eyes", "mouth"]) {
    const style = styleOfAsset(state.recipe?.slots?.[slotId]);
    if (style) return style;
  }
  return state.manifest.styles?.[0]?.id || STYLE_FALLBACK;
}

function assetList(slot) {
  const style = state.style || STYLE_FALLBACK;
  return (slot.assets || []).filter((asset) => (asset.style || STYLE_FALLBACK) === style);
}

function buildStyleTabs() {
  const box = elements.styleTabs;
  if (!box || !state.manifest?.styles) return;
  const tabs = state.manifest.styles.map((style) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "style-tab";
    button.dataset.styleId = style.id;
    button.textContent = style.label?.zh || style.id;
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", String(style.id === (state.style || STYLE_FALLBACK)));
    button.addEventListener("click", () => applyStyle(style.id));
    return button;
  });
  box.replaceChildren(...tabs);
}

function applyStyle(styleId) {
  const style = (state.manifest.styles || []).find((item) => item.id === styleId);
  if (!style || !state.recipe) return;
  for (const slot of state.manifest.slots) {
    const next = style.defaults?.[slot.id];
    if (next) state.recipe.slots[slot.id] = next;
    else state.recipe.slots[slot.id] = null;
  }
  state.style = styleId;
  saveRecipe();
  buildStyleTabs();
  renderCategories();
  const slot = findSlot(state.slotId);
  if (slot) {
    renderAssets(slot);
    syncColorControls(slot);
  }
  syncAssetSelection();
  schedulePreview();
  toast(`已切换到「${style.label?.zh || styleId}」`);
}

function renderCategories() {
  const visible = state.manifest.slots.filter((slot) => assetList(slot).length > 0);
  const buttons = visible.map((slot) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "category";
    button.dataset.slotId = slot.id;
    button.setAttribute("aria-pressed", String(slot.id === state.slotId));

    const label = document.createElement("span");
    label.textContent = displayLabel(slot);

    const count = document.createElement("span");
    count.className = "category-count";
    count.textContent = String(assetList(slot).length);
    count.setAttribute("aria-hidden", "true");

    button.append(label, count);
    button.addEventListener("click", () => selectSlot(slot.id));
    return button;
  });
  elements.categories.replaceChildren(...buttons);
}

function selectSlot(slotId) {
  const slot = findSlot(slotId);
  if (!slot) return;

  state.slotId = slotId;
  for (const button of elements.categories.querySelectorAll(".category")) {
    button.setAttribute("aria-pressed", String(button.dataset.slotId === slotId));
  }
  renderAssets(slot);
  syncColorControls(slot);
}

function makeAssetButton({ id, file, thumb, selected, label, none = false }) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = none ? "asset asset-none" : "asset";
  button.dataset.assetId = id || "";
  button.setAttribute("aria-label", label);
  button.setAttribute("aria-pressed", String(selected));
  button.title = label;

  if (none) {
    const mark = document.createElement("span");
    mark.textContent = "无";
    mark.setAttribute("aria-hidden", "true");
    button.append(mark);
  } else {
    const image = document.createElement("img");
    image.src = `/assets/${thumb || file}`;
    image.alt = "";
    image.loading = "lazy";
    image.decoding = "async";
    image.draggable = false;
    button.append(image);
  }

  button.addEventListener("click", () => applyAsset(id));
  return button;
}

function renderAssets(slot) {
  const assets = assetList(slot);
  const selected = state.recipe.slots[slot.id];

  const none = makeAssetButton({
    id: null,
    selected: selected === null,
    label: `${displayLabel(slot)}：无`,
    none: true,
  });

  const buttons = assets.map((asset) =>
    makeAssetButton({
      id: asset.id,
      file: asset.file,
      thumb: asset.thumb,
      selected: selected === asset.id,
      label: `${displayLabel(slot)}：${asset.id}`,
    })
  );

  elements.assets.replaceChildren(none, ...buttons);
  elements.assetsTitle.textContent = `${displayLabel(slot)}素材`;
  elements.assetsCount.textContent = `${assets.length} 张`;
}

function applyAsset(assetId) {
  if (!state.slotId) return;
  state.recipe.slots[state.slotId] = assetId;
  saveRecipe();
  syncAssetSelection();
  schedulePreview();
}

function syncAssetSelection() {
  const current = state.recipe.slots[state.slotId] ?? null;
  for (const button of elements.assets.querySelectorAll(".asset")) {
    const assetId = button.dataset.assetId || null;
    button.setAttribute("aria-pressed", String(assetId === current));
  }
}

/* ------------------------------------------------------------------ */
/* 颜色                                                                */
/* ------------------------------------------------------------------ */

function buildSwatches(slot) {
  const colors = [];
  const palette =
    slot && Array.isArray(slot.colors) ? slot.colors : slot ? [slot.default_color] : [];
  for (const raw of palette) {
    const color = String(raw || "").toUpperCase();
    if (slot && slot.tintable && HEX_COLOR.test(color) && !colors.includes(color)) {
      colors.push(color);
    }
  }

  const buttons = colors.slice(0, 12).map((color) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "swatch";
    button.dataset.color = color;
    button.style.backgroundColor = color;
    button.setAttribute("aria-label", `使用颜色 ${color}`);
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => applyColor(color));
    return button;
  });
  elements.swatches.replaceChildren(...buttons);
}

function syncColorControls(slot) {
  if (!slot) return;
  const current = state.recipe.colors[slot.id] || slot.default_color || "#000000";
  elements.color.value = (HEX_COLOR.test(current) ? current : "#000000").toLowerCase();
  elements.colorValue.textContent = current.toUpperCase();
  elements.color.disabled = !slot.tintable;
  elements.colorHint.textContent = slot.tintable
    ? `正在调整「${displayLabel(slot)}」的颜色`
    : `「${displayLabel(slot)}」是固定素材，不支持换色`;

  buildSwatches(slot);

  for (const button of elements.swatches.querySelectorAll(".swatch")) {
    button.disabled = !slot.tintable;
    const active = button.dataset.color === current.toUpperCase();
    button.setAttribute("aria-pressed", String(active));
  }
}

function applyColor(color) {
  const slot = findSlot(state.slotId);
  if (!slot || !slot.tintable) {
    toast("这个类目不支持换色");
    return;
  }
  state.recipe.colors[slot.id] = color.toUpperCase();
  saveRecipe();
  syncColorControls(slot);
  schedulePreview();
}

function handleColorInput(event) {
  const slot = findSlot(state.slotId);
  if (!slot || !slot.tintable) return;
  const color = event.target.value.toUpperCase();
  if (!HEX_COLOR.test(color)) return;
  state.recipe.colors[slot.id] = color;
  saveRecipe();
  elements.colorValue.textContent = color;
  syncColorControls(slot);
  schedulePreview();
}

/* ------------------------------------------------------------------ */
/* 预览                                                                */
/* ------------------------------------------------------------------ */

function readStickers() {
  try {
    const raw = localStorage.getItem(STICKER_KEY);
    if (raw) {
      const list = JSON.parse(raw);
      if (Array.isArray(list)) return list;
    }
    const legacy = localStorage.getItem(LEGACY_STICKER_KEY);
    if (legacy) {
      const one = JSON.parse(legacy);
      if (one && one.pixels) return [{ ...one, x: 0.88, y: 0.88, scale: 0.22 }];
    }
  } catch (error) {
    /* ignore */
  }
  return [];
}

function saveStickers() {
  try {
    localStorage.setItem(STICKER_KEY, JSON.stringify(state.stickers));
  } catch (error) {
    /* ignore */
  }
}

function refreshStickerUi() {
  const count = state.stickers.length;
  if (elements.stickerStatus) {
    elements.stickerStatus.textContent = count
      ? `已贴 ${count} 张拼豆贴纸（拖动摆位置）`
      : "还没有拼豆贴纸";
  }
  if (elements.stickerRemove) elements.stickerRemove.hidden = count === 0;
  if (state.selectedSticker >= count) state.selectedSticker = Math.max(0, count - 1);
  syncScaleControl();
  renderStickerLayer();
}

function removeAllStickers() {
  state.stickers = [];
  saveStickers();
  refreshStickerUi();
  schedulePreview();
  toast("已移除全部贴纸");
}

async function stickerThumb(sticker) {
  const response = await fetch("/api/pixel/render", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      palette: sticker.palette,
      pixels: sticker.pixels,
      style: sticker.style || "bead",
      size: 256,
    }),
  });
  if (!response.ok) return null;
  const blob = await response.blob();
  try {
    const bitmap = await createImageBitmap(blob);
    const canvas = document.createElement("canvas");
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(bitmap, 0, 0);
    const { data } = ctx.getImageData(0, 0, canvas.width, canvas.height);
    let minX = canvas.width;
    let minY = canvas.height;
    let maxX = 0;
    let maxY = 0;
    for (let y = 0; y < canvas.height; y += 1) {
      for (let x = 0; x < canvas.width; x += 1) {
        if (data[(y * canvas.width + x) * 4 + 3] > 8) {
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
        }
      }
    }
    sticker.aspect = (maxX - minX + 1) / (maxY - minY + 1);
  } catch (error) {
    sticker.aspect = 1;
  }
  return null;
}

async function ensureThumbs() {
  await Promise.all(
    state.stickers.map(async (sticker) => {
      if (!sticker.aspect) await stickerThumb(sticker);
    })
  );
  renderStickerLayer();
}

function renderStickerLayer() {
  const layer = elements.stickerLayer;
  if (!layer) return;
  const pins = state.stickers.map((sticker, index) => {
    const pin = document.createElement("div");
    pin.className = index === state.selectedSticker ? "sticker-pin is-selected" : "sticker-pin";
    pin.style.left = `${(sticker.x ?? 0.88) * 100}%`;
    pin.style.top = `${(sticker.y ?? 0.88) * 100}%`;
    pin.style.width = `${(sticker.scale ?? 0.22) * 100}%`;

    if (sticker.aspect) pin.style.aspectRatio = String(sticker.aspect);

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "sticker-del";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `删除第 ${index + 1} 张贴纸`);
    remove.addEventListener("pointerdown", (event) => event.stopPropagation());
    remove.addEventListener("click", (event) => {
      event.stopPropagation();
      state.stickers.splice(index, 1);
      saveStickers();
      refreshStickerUi();
      schedulePreview();
    });
    pin.append(remove);

    pin.addEventListener("pointerdown", () => {
      // 只切高亮，不能重建 DOM，否则拖拽会立刻失焦
      state.selectedSticker = index;
      for (const item of layer.querySelectorAll(".sticker-pin")) {
        item.classList.toggle("is-selected", item === pin);
      }
      syncScaleControl();
    });

    attachDrag(pin, index);
    return pin;
  });
  layer.replaceChildren(...pins);
}

function syncScaleControl() {
  const sticker = state.stickers[state.selectedSticker];
  const row = elements.stickerScale?.closest(".sticker-scale-row");
  if (!row) return;
  row.hidden = !sticker;
  if (!sticker) return;
  const percent = Math.round((sticker.scale ?? 0.22) * 100);
  if (elements.stickerScale) elements.stickerScale.value = String(percent);
  if (elements.stickerScaleValue) elements.stickerScaleValue.textContent = `${percent}%`;
}

function attachDrag(pin, index) {
  let dragging = false;
  pin.addEventListener("pointerdown", (event) => {
    if (event.target.classList.contains("sticker-del")) return;
    event.preventDefault();
    dragging = true;
    pin.setPointerCapture(event.pointerId);
  });
  pin.addEventListener("pointermove", (event) => {
    if (!dragging) return;
    const canvas = document.getElementById("preview-canvas");
    const rect = canvas.getBoundingClientRect();
    const x = Math.min(0.98, Math.max(0.02, (event.clientX - rect.left) / rect.width));
    const y = Math.min(0.98, Math.max(0.02, (event.clientY - rect.top) / rect.height));
    state.stickers[index].x = x;
    state.stickers[index].y = y;
    pin.style.left = `${x * 100}%`;
    pin.style.top = `${y * 100}%`;
  });
  function end(event) {
    if (!dragging) return;
    dragging = false;
    saveStickers();
    schedulePreview();
  }
  pin.addEventListener("pointerup", end);
  pin.addEventListener("pointercancel", end);
}

function schedulePreview() {
  clearTimeout(state.debounceTimer);
  state.debounceTimer = window.setTimeout(refreshPreview, PREVIEW_DEBOUNCE_MS);
}

async function refreshPreview() {
  clearTimeout(state.debounceTimer);
  if (!state.recipe) return;

  const mine = ++state.seq;
  if (state.controller) state.controller.abort();
  const controller = new AbortController();
  state.controller = controller;
  setPreviewStatus("生成中…", "loading");

  try {
    const response = await fetch("/api/render", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "image/png" },
      body: JSON.stringify({ recipe: state.recipe, size: 256, stickers: state.stickers.length ? state.stickers.map(({ palette, pixels, style, x, y, scale }) => ({ palette, pixels, style, x, y, scale })) : undefined }),
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(await describeError(response));

    const blob = await response.blob();
    if (mine !== state.seq) return;

    const url = URL.createObjectURL(blob);
    await preloadImage(url);
    if (mine !== state.seq) {
      URL.revokeObjectURL(url);
      return;
    }

    elements.preview.src = url;
    if (state.objectUrl) URL.revokeObjectURL(state.objectUrl);
    state.objectUrl = url;
    setPreviewStatus("", "");
  } catch (error) {
    if (error && error.name === "AbortError") return;
    if (mine !== state.seq) return;
    console.error("预览失败", error);
    setPreviewStatus("预览失败，点这里重试", "error");
  }
}

function preloadImage(url) {
  return new Promise((resolve) => {
    const image = new Image();
    image.onload = () => resolve(true);
    image.onerror = () => resolve(false);
    image.src = url;
  });
}

function setPreviewStatus(text, kind) {
  elements.previewStatus.textContent = text;
  elements.previewStatus.dataset.kind = kind || "";
  elements.previewStatus.classList.toggle("is-visible", Boolean(text));
  elements.previewStatus.classList.toggle("is-error", kind === "error");
  elements.previewCard.classList.toggle("is-loading", kind === "loading");
  state.previewStatusKind = kind || "";
}

async function describeError(response) {
  try {
    const data = await response.json();
    if (data && data.error) {
      return `${data.error.code || "ERROR"}：${data.error.message || response.status}`;
    }
  } catch (error) {
    // 响应不是 JSON 时退回状态码。
  }
  return `HTTP ${response.status}`;
}

/* ------------------------------------------------------------------ */
/* 随机、导出、分享                                                    */
/* ------------------------------------------------------------------ */

async function randomize() {
  if (state.randomBusy) return;
  state.randomBusy = true;
  elements.random.disabled = true;

  try {
    const response = await fetch("/api/random", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ style: state.style || STYLE_FALLBACK }),
    });
    if (!response.ok) throw new Error(await describeError(response));

    const raw = await response.json();
    state.recipe = sanitizeRecipe(raw, state.manifest);
    saveRecipe();
    renderAssets(findSlot(state.slotId));
    syncColorControls(findSlot(state.slotId));
    replayPop();
    refreshPreview();
    toast("已随机生成一张脸");
  } catch (error) {
    console.error("随机失败", error);
    toast("随机失败，请稍后重试", "error");
  } finally {
    state.randomBusy = false;
    elements.random.disabled = false;
  }
}

function replayPop() {
  elements.previewCard.classList.remove("is-popping");
  void elements.previewCard.offsetWidth;
  elements.previewCard.classList.add("is-popping");
  window.setTimeout(() => elements.previewCard.classList.remove("is-popping"), 360);
}

function timestamp(date = new Date()) {
  const pad = (value) => String(value).padStart(2, "0");
  const day = `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}`;
  const time = `${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}`;
  return `${day}-${time}`;
}

async function download(size) {
  if (state.downloading) return;
  state.downloading = true;

  try {
    const response = await fetch("/api/render", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "image/png" },
      body: JSON.stringify({ recipe: state.recipe, size, stickers: state.stickers.length ? state.stickers.map(({ palette, pixels, style, x, y, scale }) => ({ palette, pixels, style, x, y, scale })) : undefined }),
    });
    if (!response.ok) throw new Error(await describeError(response));

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `avatar-${timestamp()}.png`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(`已导出 ${size}×${size} PNG`);
  } catch (error) {
    console.error("导出失败", error);
    toast("导出失败，请稍后重试", "error");
  } finally {
    state.downloading = false;
  }
}

const STANDARD_PALETTE = [
  "#FFFFFF", "#F7D4B8", "#E4B685", "#C79266", "#A17140", "#4B2B1C", "#213244", "#697E80",
  "#BB0126", "#EF4D3E", "#F3A014", "#FEC832", "#1D9E54", "#5EE88C", "#26B78E", "#337BAD",
  "#54A7E9", "#882893", "#945AB1", "#F1559F", "#98A6A6", "#878787", "#F47E36", "#1E334E",
  "#FBFBFB", "#DBD9DA", "#B4B4B4", "#96A09F", "#56534E", "#2C2C2C", "#D8D4D3", "#B0A796",
  "#F5C9CA", "#FF9280", "#F73D48", "#D40E1F", "#FFD785", "#FDA42E", "#FB852B", "#F85842",
  "#E9EC91", "#DFF139", "#64F343", "#39E158", "#2ADED3", "#3349C3", "#9C34AD", "#EC4072",
  "#FCFDFF", "#F2EEE5", "#E0D4BC", "#DCB387", "#B2714B", "#79544E", "#1B1213", "#010101",
  "#7DCA9C", "#32C958", "#1A6E3D", "#ABF8FE", "#76CEDE", "#3977CC", "#301A49", "#AB91C0",
];

function toBase64Url(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromBase64Url(token) {
  const base64 = token.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
  const binary = atob(padded);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

function encodeStickers() {
  if (!state.stickers.length) return "";
  const same = (list) =>
    Array.isArray(list) && list.length === STANDARD_PALETTE.length &&
    list.every((color, index) => color.toUpperCase() === STANDARD_PALETTE[index]);

  const payload = state.stickers.map((sticker) => {
    const item = {
      p: sticker.pixels,
      st: sticker.style || "bead",
      x: Number((sticker.x ?? 0.88).toFixed(3)),
      y: Number((sticker.y ?? 0.88).toFixed(3)),
      sc: Number((sticker.scale ?? 0.22).toFixed(3)),
    };
    if (!same(sticker.palette)) item.pal = sticker.palette;
    return item;
  });
  return toBase64Url(JSON.stringify(payload));
}

function decodeStickers(token) {
  try {
    const list = JSON.parse(fromBase64Url(token));
    if (!Array.isArray(list)) return [];
    return list
      .filter((item) => item && typeof item.p === "string")
      .map((item) => ({
        pixels: item.p,
        style: item.st === "flat" ? "flat" : "bead",
        palette: Array.isArray(item.pal) ? item.pal : STANDARD_PALETTE,
        x: Number(item.x ?? 0.88),
        y: Number(item.y ?? 0.88),
        scale: Number(item.sc ?? 0.22),
      }))
      .slice(0, 8);
  } catch (error) {
    return [];
  }
}

function encodeRecipe(recipe) {
  const json = JSON.stringify(recipe);
  const bytes = new TextEncoder().encode(json);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function decodeRecipe(token) {
  try {
    const base64 = token.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    const binary = atob(padded);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch (error) {
    console.warn("分享链接解析失败", error);
    return null;
  }
}

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.top = "0";
  area.style.opacity = "0";
  document.body.append(area);
  area.select();
  const copied = document.execCommand("copy");
  area.remove();
  if (!copied) throw new Error("copy command failed");
}

async function shareLink() {
  const url = new URL(location.href);
  url.searchParams.set("r", encodeRecipe(state.recipe));
  const stickers = encodeStickers();
  if (stickers) url.searchParams.set("s", stickers);
  else url.searchParams.delete("s");
  url.hash = "";
  history.replaceState(null, "", url.toString());

  try {
    await copyText(url.toString());
    toast("分享链接已复制，打开即可复现这张脸");
  } catch (error) {
    console.warn("复制失败", error);
    window.prompt("复制这条分享链接：", url.toString());
  }
}

function resetRecipe() {
  state.recipe = sanitizeRecipe(state.manifest.default_recipe, state.manifest);
  saveRecipe();
  selectSlot(state.slotId);
  refreshPreview();
  toast("已恢复默认配方");
}

/* ------------------------------------------------------------------ */
/* 键盘与提示                                                          */
/* ------------------------------------------------------------------ */

function handleGlobalKeydown(event) {
  if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return;

  const target = event.target;
  if (
    target instanceof HTMLElement &&
    (target.matches("input, textarea, select") || target.isContentEditable)
  ) {
    return;
  }

  const key = event.key.toLowerCase();
  if (key === "r") {
    event.preventDefault();
    randomize();
  } else if (key === "s") {
    event.preventDefault();
    download(1024);
  }
}

function handleAssetKeydown(event) {
  if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;

  const buttons = Array.from(elements.assets.querySelectorAll("button.asset"));
  const current = document.activeElement;
  const index = buttons.indexOf(current);
  if (index < 0) return;

  event.preventDefault();
  const rect = current.getBoundingClientRect();
  if (!rect.width || !rect.height) return;

  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  const horizontal = event.key === "ArrowLeft" || event.key === "ArrowRight";
  let best = null;
  let bestScore = Infinity;

  for (const button of buttons) {
    if (button === current) continue;
    const other = button.getBoundingClientRect();
    if (!other.width || !other.height) continue;

    const ox = other.left + other.width / 2;
    const oy = other.top + other.height / 2;
    let primary = 0;
    let secondary = 0;

    if (horizontal) {
      if (event.key === "ArrowLeft" && ox >= cx - 1) continue;
      if (event.key === "ArrowRight" && ox <= cx + 1) continue;
      primary = Math.abs(ox - cx);
      secondary = Math.abs(oy - cy);
    } else {
      if (event.key === "ArrowUp" && oy >= cy - 1) continue;
      if (event.key === "ArrowDown" && oy <= cy + 1) continue;
      primary = Math.abs(oy - cy);
      secondary = Math.abs(ox - cx);
    }

    const score = primary + secondary * 0.6;
    if (score < bestScore) {
      bestScore = score;
      best = button;
    }
  }

  if (best) best.focus();
}

function toast(message, kind = "info") {
  clearTimeout(state.toastTimer);
  elements.toast.textContent = message;
  elements.toast.dataset.kind = kind;
  elements.toast.hidden = false;
  state.toastTimer = window.setTimeout(() => {
    elements.toast.hidden = true;
  }, 2400);
}

function fatal(error) {
  console.error("初始化失败", error);
  elements.categories.replaceChildren();
  elements.assetsTitle.textContent = "加载失败";
  elements.assetsCount.textContent = "";
  const message = document.createElement("p");
  message.className = "fatal";
  message.textContent = "素材清单加载失败，请刷新页面重试。";
  elements.assets.replaceChildren(message);
  setPreviewStatus("无法加载素材清单", "error");
  for (const control of document.querySelectorAll(".action, input[type=color]")) {
    control.disabled = true;
  }
}

/* ------------------------------------------------------------------ */
/* 启动                                                                */
/* ------------------------------------------------------------------ */

function wireEvents() {
  elements.color.addEventListener("input", handleColorInput);
  elements.random.addEventListener("click", randomize);
  elements.share.addEventListener("click", shareLink);
  elements.reset.addEventListener("click", resetRecipe);
  elements.assets.addEventListener("keydown", handleAssetKeydown);
  elements.previewStatus.addEventListener("click", () => {
    if (state.previewStatusKind === "error") refreshPreview();
  });
  document.addEventListener("keydown", handleGlobalKeydown);

  for (const button of document.querySelectorAll("[data-size]")) {
    button.addEventListener("click", () => download(Number(button.dataset.size)));
  }
}

async function boot() {
  state.stickers = readStickers();
  const sharedStickers = new URLSearchParams(location.search).get("s");
  if (sharedStickers) {
    const decoded = decodeStickers(sharedStickers);
    if (decoded.length) {
      state.stickers = decoded;
      saveStickers();
    }
  }
  if (elements.stickerRemove) elements.stickerRemove.addEventListener("click", removeAllStickers);
  refreshStickerUi();
  ensureThumbs();
  if (elements.stickerScale) {
    elements.stickerScale.addEventListener("input", (event) => {
      const sticker = state.stickers[state.selectedSticker];
      if (!sticker) return;
      sticker.scale = Number(event.target.value) / 100;
      if (elements.stickerScaleValue) {
        elements.stickerScaleValue.textContent = `${event.target.value}%`;
      }
      renderStickerLayer();
      saveStickers();
      schedulePreview();
    });
  }
  try {
    state.manifest = readInlineManifest() || (await fetchManifest());
    if (!state.manifest || !Array.isArray(state.manifest.slots) || !state.manifest.slots.length) {
      throw new Error("素材清单为空");
    }

    state.style = currentStyle();
    buildStyleTabs();

    const initial = loadInitialRecipe(state.manifest);
    state.recipe = initial.recipe;
    state.style = currentStyle();
    buildStyleTabs();
    state.slotId = pickInitialSlot();
    if (!state.slotId) throw new Error("没有可用槽位");

    buildSwatches(findSlot(state.slotId));
    renderCategories();
    selectSlot(state.slotId);
    wireEvents();
    await refreshPreview();

    if (initial.source === "share") {
      toast("已载入分享的配方");
    } else if (initial.source === "storage") {
      toast("已恢复上次的配方");
    } else if (initial.source === "invalid-share") {
      toast("分享链接无效，已使用默认配方", "error");
    }
  } catch (error) {
    fatal(error);
  }
}

boot();
