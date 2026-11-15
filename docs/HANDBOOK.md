# 六人分工实施手册

配套文档：[计划书](PLAN.md)、[协作指南](COLLABORATION.md)、[实验任务书](DIY头像生成器-实验任务书.docx)。

这份手册解决一个问题：**每个人拿到自己的角色，第一天就能动手，不必等别人。**

---

## 0 怎么用这份手册

1. 先读 §1（全员通用），15 分钟，装环境、记住契约、学会提交。
2. 再读自己角色的那一章（A 到 F），按步骤做，每步都有「完成标志」。
3. 卡住了看 §9 速查，还不行就在群里问，别自己憋半天。

约定：每章开头的「你要交付什么」就是验收标准；每一步做完就提交一次，别攒着。

---

## 1 全员通用

### 1.1 装环境（约 15 分钟）

| 软件 | 版本 | 备注 |
| --- | --- | --- |
| Python | 3.11 及以上 | 安装时勾选 Add to PATH |
| Git | 最新版 | Windows 用 Git for Windows |
| VS Code | 最新版 | 装 Python 与 Pylance 扩展 |
| 浏览器 | Chrome 或 Edge | 用到 fetch 与 CSS aspect-ratio |

Windows 装依赖：

```powershell
git clone https://gitee.com/chords-of-fate/diyface.git
cd diyface
python -m venv .venv
.venv\Scripts\activate
pip install flask uvicorn jinja2 pillow pydantic pytest pytest-cov numpy
```

macOS 只需把激活那行换成 `source .venv/bin/activate`。

### 1.2 三步跑通仓库

```powershell
python -m flask --app diyface.app run --debug --port 8000
python -m pytest -q
python -m diyface verify --all
```

第一条起服务，第二条跑测试，第三条校验素材。M0 之后这三条都应该成功；哪条失败就是有人合坏了 main，先在群里说。

### 1.3 接口契约（并行开发的前提）

六个人能同时干活，靠的是这份契约先定死。任何一方要改，先在群里说，再同时改 A、B、C 三个人的代码。

**配方（Recipe）**——浏览器与服务端之间唯一的交换格式：

```json
{
  "version": 1,
  "slots": {
    "skin": "skin_base", "bangs": "bangs_straight_01", "eyes": "eyes_round_01",
    "mouth": "mouth_smile_01", "glasses": null, "hat": null,
    "clothes": "clothes_crew_01", "extra": null
  },
  "colors": { "skin": "#F2D5B8", "bangs": "#3B2B23", "clothes": "#4A6FA5" },
  "seed": 20261028
}
```

规则：`slots` 必须包含全部 12 个键（未启用的槽位填 `null`）；素材 id 为 `null` 表示不画；颜色一律 `#RRGGBB`；多余字段直接拒绝。

**槽位与目录**（文件夹编号固定，z 序另算）：

| 目录 | 槽位 id | z | v1 | 负责 |
| --- | --- | --- | --- | --- |
| 01_skin | skin | 10 | 启用 | E |
| 05_cheeks | cheeks | 20 | 预留 | — |
| 02_bangs | bangs | 30 | 启用 | D |
| 03_side_hair | side_hair | 40 | 预留 | — |
| 04_brows | brows | 50 | 预留 | — |
| 06_eyes | eyes | 60 | 启用 | D |
| 08_nose | nose | 70 | 预留 | — |
| 07_mouth | mouth | 80 | 启用 | E |
| 09_glasses | glasses | 90 | 启用 | E |
| 11_clothes | clothes | 100 | 启用 | E |
| 10_hat | hat | 110 | 启用 | D |
| 12_extra | extra | 120 | 启用 | E |

素材总量：D 负责头部 21 张，E 负责面部与服饰 22 张，合计 54 张。

**素材命名**：`<槽位>_<形状>_<两位序号>.png`，例如 `bangs_straight_01.png`，只允许小写字母、数字与下划线。

**接口**：

| 方法 | 路径 | 入参 | 出参 |
| --- | --- | --- | --- |
| GET | / | 无 | HTML |
| GET | /api/manifest | 无 | JSON 清单 |
| POST | /api/render | `{recipe, size}` | image/png |
| POST | /api/random | `{recipe?}` | JSON 配方 |
| GET | /healthz | 无 | `{ok, version, assets}` |

错误响应统一为 `{"error": {"code": "...", "message": "...", "field": "..."}}`。

### 1.4 Git 日常：分支、提交、PR

```powershell
git switch main
git pull --rebase
git switch -c feat/a-render-core
# ... 写代码，每完成一小步就提交 ...
git add -p
git commit -m "feat(render): 按 z 序合成图层"
git push -u origin feat/a-render-core
```

然后到 Gitee 仓库页点「Pull Requests」→ 新建，选你的分支，写清楚改了什么、怎么验证，找一个人 review，Squash 合并。

三条纪律：

1. 不直推 `main`，永远走 PR。
2. 一个提交只做一件事，提交信息用 `feat / fix / test / docs / chore(scope): 说明`。
3. 提交前跑一遍测试，红了就修，别把红的分支推上来。

### 1.5 每日节奏与验收

| 时间 | 动作 |
| --- | --- |
| 早上 | `git pull --rebase`，看一眼 main 有没有新东西 |
| 上午 | 做自己那章的第一个未完成步骤 |
| 收工前 | 提交并 push 功能分支，把 PR 开着（草稿也行） |
| 每周五 | 演示 10 分钟，打 tag，更新进度 |

每个角色的「完成标志」都写在对应章节末尾，达不到就不算完成，别靠口头「差不多了」。

---

## 2 角色 A：渲染内核

### 2.1 你要交付什么

| 交付物 | 验收 |
| --- | --- |
| `models.py` | 10 个槽位、z 序唯一、配方校验 |
| `catalog.py` | 扫目录生成清单、尺寸与模式校验 |
| `render.py` | 按 z 序合成、空槽位透明、多尺寸导出 |
| `palettes.py` | 颜色相乘、tint 蒙版、非法颜色报错 |
| `__main__.py` | 命令行出图，可脱离 Web 使用 |
| 单测 + 快照 | 至少 25 条，覆盖率不低于 90% |

时间：2 天。你是全队的地基，D、E 的素材要靠 `verify` 校验，B、C 要靠你的接口出图，所以**先把能出图的命令行打通**。

### 2.2 第 1 步：定义槽位与配方（约 2 小时）

先建包：`src/diyface/__init__.py`、`models.py`。

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SlotId(StrEnum):
    SKIN = "skin"
    CHEEKS = "cheeks"
    BANGS = "bangs"
    SIDE_HAIR = "side_hair"
    BROWS = "brows"
    EYES = "eyes"
    NOSE = "nose"
    MOUTH = "mouth"
    GLASSES = "glasses"
    CLOTHES = "clothes"
    HAT = "hat"
    EXTRA = "extra"


@dataclass(frozen=True)
class Slot:
    id: SlotId
    z: int
    tintable: bool
    default_color: str
    folder: str
    folder_no: str


SLOTS = (
    Slot(SlotId.SKIN, 10, True, "#F2D5B8", "skin", "01_skin"),
    Slot(SlotId.CHEEKS, 20, True, "#F2A6A6", "cheeks", "05_cheeks"),
    Slot(SlotId.BANGS, 30, True, "#3B2B23", "bangs", "02_bangs"),
    Slot(SlotId.SIDE_HAIR, 40, True, "#3B2B23", "side_hair", "03_side_hair"),
    Slot(SlotId.BROWS, 50, True, "#3B2B23", "brows", "04_brows"),
    Slot(SlotId.EYES, 60, False, "#2B2B2B", "eyes", "06_eyes"),
    Slot(SlotId.NOSE, 70, True, "#E8B79A", "nose", "08_nose"),
    Slot(SlotId.MOUTH, 80, True, "#C0504D", "mouth", "07_mouth"),
    Slot(SlotId.GLASSES, 90, False, "#2B2B2B", "glasses", "09_glasses"),
    Slot(SlotId.CLOTHES, 100, True, "#4A6FA5", "clothes", "11_clothes"),
    Slot(SlotId.HAT, 110, True, "#8E5A4A", "hat", "10_hat"),
    Slot(SlotId.EXTRA, 120, True, "#D4A017", "extra", "12_extra"),
)

SLOTS_BY_Z = tuple(sorted(SLOTS, key=lambda slot: slot.z))
RESERVED = frozenset({SlotId.CHEEKS, SlotId.SIDE_HAIR, SlotId.BROWS, SlotId.NOSE})
ACTIVE = tuple(slot for slot in SLOTS if slot.id not in RESERVED)


class AvatarRecipe(BaseModel):
    version: int = 1
    slots: dict[SlotId, str | None] = Field(default_factory=dict)
    colors: dict[SlotId, str] = Field(default_factory=dict)
    seed: int | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("colors")
    @classmethod
    def check_hex(cls, value: dict[SlotId, str]) -> dict[SlotId, str]:
        for slot_id, color in value.items():
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                raise ValueError(f"{slot_id} 的颜色必须是 #RRGGBB，收到 {color!r}")
        return value

    @field_validator("slots")
    @classmethod
    def check_asset_id(cls, value: dict[SlotId, str | None]) -> dict[SlotId, str | None]:
        for slot_id, asset_id in value.items():
            if asset_id is not None and not re.fullmatch(r"[a-z0-9_]+", asset_id):
                raise ValueError(f"{slot_id} 的素材 id 非法：{asset_id!r}")
        return value
```

为什么这样拆：槽位与 z 序放在一处常量里，渲染、清单、前端三边都读它，就不会出现「文档说 30、代码写 60」的错。`RESERVED` 只影响是否产出素材，不影响配方结构。

再加一个默认配方函数，供前端首屏与测试使用：

```python
def default_recipe(catalog: dict[SlotId, list[str]]) -> AvatarRecipe:
    return AvatarRecipe(
        slots={slot.id: (catalog[slot.id][0] if catalog.get(slot.id) else None) for slot in SLOTS},
        colors={slot.id: slot.default_color for slot in ACTIVE},
    )
```

**完成标志**：`pytest` 里 `default_recipe` 返回 12 个键、颜色 8 个、非法颜色报 `ValidationError`。

### 2.3 第 2 步：扫描素材生成清单（约 3 小时）

素材还没画完，没关系——先自己造 6 张占位图，跑通链路。

```powershell
python -c "from PIL import Image; import os; os.makedirs('assets/02_bangs', exist_ok=True); Image.new('RGBA',(1024,1024),(0,0,0,0)).save('assets/02_bangs/bangs_straight_01.png')"
```

`catalog.py`：

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .models import ACTIVE, SLOTS, SlotId

CANVAS = 1024


@dataclass(frozen=True)
class Asset:
    id: str
    slot: SlotId
    path: Path


def scan_slot(root: Path, folder: str) -> list[Asset]:
    directory = root / folder
    if not directory.is_dir():
        return []
    assets: list[Asset] = []
    for path in sorted(directory.glob("*.png")):
        if path.name.startswith("_"):
            continue
        with Image.open(path) as image:
            if image.size != (CANVAS, CANVAS):
                raise ValueError(f"{path.name} 尺寸 {image.size} 应为 {CANVAS}x{CANVAS}")
            if image.mode != "RGBA":
                raise ValueError(f"{path.name} 必须是 RGBA，当前 {image.mode}")
        assets.append(Asset(id=path.stem, slot=SlotId(folder.split('_', 1)[1]), path=path))
    return assets


def scan(root: Path) -> dict[SlotId, list[Asset]]:
    catalog = {}
    for slot in SLOTS:
        assets = scan_slot(root, slot.folder_no)
        if assets:
            catalog[slot.id] = assets
    return catalog


def manifest(catalog: dict[SlotId, list[Asset]]) -> dict:
    slots = []
    for slot in SLOTS:
        assets = catalog.get(slot.id, [])
        if not assets:
            continue
        slots.append({
            "id": slot.id.value,
            "z": slot.z,
            "tintable": slot.tintable,
            "default_color": slot.default_color,
            "assets": [{"id": a.id, "file": f"{slot.folder_no}/{a.path.name}"} for a in assets],
        })
    return {"schema": 1, "slots": slots}
```

注意两点：`manifest` 只输出有素材的槽位，前端因此不会显示空类目；`scan` 遇到尺寸不对直接抛错，把问题挡在构建期而不是线上。

**完成标志**：`python -c "from diyface.catalog import scan; print(len(scan(Path('assets'))))"` 能打印 1 以上。

### 2.4 第 3 步：把图层叠成一张图（约 4 小时）

`render.py` 只做三件事：取层、着色、合成。全部是纯函数。

```python
from functools import lru_cache
from pathlib import Path

from PIL import Image

from .catalog import Asset
from .models import AvatarRecipe, SLOTS_BY_Z, SlotId
from .palettes import tint

CANVAS = 1024


@lru_cache(maxsize=512)
def load_layer(path: str) -> Image.Image:
    return Image.open(path).convert("RGBA")


def compose(recipe: AvatarRecipe, catalog: dict[SlotId, dict[str, Asset]]) -> Image.Image:
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    for slot in SLOTS_BY_Z:
        asset_id = recipe.slots.get(slot.id)
        if not asset_id:
            continue
        asset = catalog[slot.id][asset_id]
        layer = load_layer(str(asset.path))
        if slot.tintable:
            color = recipe.colors.get(slot.id, slot.default_color)
            layer = tint(layer, color)
        image = Image.alpha_composite(image, layer)
    return image


def render(recipe: AvatarRecipe, catalog: dict[SlotId, dict[str, Asset]], size: int = 256) -> bytes:
    image = compose(recipe, catalog)
    if size != CANVAS:
        image = image.resize((size, size), Image.LANCZOS)
    import io
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
```

要盯住两个细节：合成用 `alpha_composite` 而不是 `paste`，缩放用 `LANCZOS` 而不是默认的双线性。

**完成标志**：用 6 张占位图能输出一张 256 的透明 PNG；把 `hat` 置为 `None` 后，帽子区域 alpha 为 0。

### 2.5 第 4 步：让颜色可换（约 2 小时）

`palettes.py`：

```python
from PIL import Image, ImageChops


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    digits = value.lstrip("#")
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    return tuple(int(digits[i:i + 2], 16) for i in (0, 2, 4))


def tint(layer: Image.Image, color: str, mask: Image.Image | None = None) -> Image.Image:
    red, green, blue = hex_to_rgb(color)
    solid = Image.new("RGB", layer.size, (red, green, blue))
    tinted = ImageChops.multiply(layer.convert("RGB"), solid)
    tinted.putalpha(layer.getchannel("A"))
    if mask is None:
        return tinted
    return Image.composite(tinted, layer, mask.getchannel("A"))
```

原理：白色（255）乘任何色仍是该色，黑色（0）乘任何色仍是黑，所以描边自然保留，明暗也不丢。蒙版用来保护不该变色的部分（比如眼睛高光）。

**完成标志**：同一张刘海传 `#3B2B23` 与 `#C0392B`，输出像素在黑色描边处不变、在发丝处变红。

### 2.6 第 5 步：命令行出图与快照（约 3 小时）

`__main__.py`：

```python
import argparse
import json
from pathlib import Path

from .catalog import scan
from .models import AvatarRecipe
from .render import render


def main() -> None:
    parser = argparse.ArgumentParser(prog="diyface")
    parser.add_argument("command", choices=["render", "verify"])
    parser.add_argument("target", type=Path)
    parser.add_argument("--out", type=Path, default=Path("out.png"))
    args = parser.parse_args()

    root = Path("assets")
    catalog = {slot: {asset.id: asset for asset in assets} for slot, assets in scan(root).items()}

    if args.command == "render":
        recipe = AvatarRecipe.model_validate_json(args.target.read_text(encoding="utf-8"))
        args.out.write_bytes(render(recipe, catalog, size=256))
        print(f"已生成 {args.out}")


if __name__ == "__main__":
    main()
```

快照测试放在 `tests/test_golden.py`，用固定配方出图，与 `tests/fixtures/golden/` 下的基准图比对，均方根误差小于 1%。基准图第一次用 `--update-golden` 生成，之后只读。

**完成标志**：`python -m diyface render tests/fixtures/recipes/base.json --out out.png` 出图；快照测试 3 条通过。

### 2.7 自检清单

- [ ] 10 个槽位、z 序与我这份表完全一致（改一处就要同步改文档）。
- [ ] 空槽位不画，且不影响其他层。
- [ ] 未知素材 id 抛 `KeyError`，接口层会转成 422。
- [ ] 尺寸只接受 256 与 1024，其他值报错。
- [ ] 单元测试覆盖 `models`、`palettes`、`catalog`、`render`。
- [ ] 快照基线已提交，并在 PR 里说明「为什么这张图应该变成这样」。

---

## 3 角色 B：前端交互

### 3.1 你要交付什么

| 交付物 | 验收 |
| --- | --- |
| `templates/index.html` | 三栏布局，移动端不横向滚动 |
| `static/app.js` | 类目、素材、取色、随机、下载、分享全通 |
| `static/style.css` | 触控目标不小于 44 像素 |
| 无障碍 | 全部控件可 Tab 到达，素材按钮有 aria-label |

时间：2.5 天。你不需要等后端，A 的 `render` 一旦能出图，你就用真接口联调。

### 3.2 第 1 步：三栏骨架（约 2 小时）

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="/static/style.css">
  <title>DIY 头像生成器</title>
</head>
<body>
  <div class="layout">
    <aside class="categories" id="categories" aria-label="类目"></aside>
    <main class="stage">
      <img id="preview" width="256" height="256" alt="头像预览">
    </main>
    <aside class="controls" id="controls">
      <button id="random" type="button">随机</button>
      <input id="color" type="color" aria-label="取色">
      <div id="palette" class="palette"></div>
      <button type="button" data-size="256">下载 256</button>
      <button type="button" data-size="1024">下载 1024</button>
      <button id="share" type="button">复制分享链接</button>
    </aside>
  </div>
  <script type="module" src="/static/app.js"></script>
</body>
</html>
```

CSS 关键只有三条：`.layout` 用 grid 三列；预览容器 `aspect-ratio: 1 / 1`；窄屏时 `grid-template-columns: 1fr` 并把类目变成底部横滑。

**完成标志**：桌面看到三栏，375 像素宽度下竖向排列且没有横向滚动条。

### 3.3 第 2 步：用清单点亮界面（约 4 小时）

```js
const state = { manifest: null, recipe: null, slot: "bangs", seq: 0 };

async function boot() {
  state.manifest = await (await fetch("/api/manifest")).json();
  state.recipe = state.manifest.default_recipe;
  buildCategories();
  selectSlot(state.slot);
  refreshPreview();
}

function buildCategories() {
  const box = document.getElementById("categories");
  box.replaceChildren(...state.manifest.slots.map((slot) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = slot.label.zh;
    button.addEventListener("click", () => selectSlot(slot.id));
    return button;
  }));
}
```

素材格同理：`slot.assets` 里每一项生成一个按钮，点击把 `state.recipe.slots[slot.id] = asset.id`，另外加一个「无」按钮写 `null`。缩略图用 `loading="lazy"`。

**完成标志**：点「发型」出现 N 个缩略图，点其中一个预览立刻变化（可能 100 毫秒后才变，正常）。

### 3.4 第 3 步：预览请求（约 3 小时）

这一步是前后端体验的分水岭：去抖防抖爆，序号防闪回。

```js
let timer = null;

function refreshPreview() {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    const mine = ++state.seq;
    const response = await fetch("/api/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipe: state.recipe, size: 256 }),
    });
    if (!response.ok) return;
    if (mine !== state.seq) return;
    const url = URL.createObjectURL(await response.blob());
    document.getElementById("preview").src = url;
  }, 120);
}
```

**完成标志**：快速连点 10 个素材，最终显示的一定是最后点的那张；拖动取色器不卡。

### 3.5 第 4 步：取色器（约 2 小时）

```js
const colorInput = document.getElementById("color");

colorInput.addEventListener("input", (event) => {
  const active = state.manifest.slots.find((slot) => slot.id === state.slot);
  if (!active || !active.tintable) return;
  state.recipe.colors[state.slot] = event.target.value.toUpperCase();
  refreshPreview();
});
```

预设色板直接从清单的 `default_color` 与 `palette` 字段渲染，不要在前端硬编码颜色。

**完成标志**：换发色只影响头发，脸与眼睛颜色不变；切换素材后颜色保留。

### 3.6 第 5 步：随机、下载、分享（约 3 小时）

```js
async function download(size) {
  const response = await fetch("/api/render", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recipe: state.recipe, size }),
  });
  const blob = await response.blob();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `avatar-${Date.now()}.png`;
  link.click();
  URL.revokeObjectURL(link.href);
}

function shareLink() {
  const json = JSON.stringify(state.recipe);
  const payload = btoa(unescape(encodeURIComponent(json)))
    .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  return `${location.origin}/?r=${payload}`;
}
```

页面加载时若 URL 带 `?r=`，解码后用 `/api/render` 出图，实现「打开链接即复现」。

**完成标志**：下载的 PNG 四角透明；分享链接在无痕窗口打开与原件完全一致。

### 3.7 第 6 步：移动端与可访问性（约 2 小时）

- 断点在 720 像素：类目改底部横滑，颜色收进抽屉。
- 每个素材按钮加 `aria-label`，例如「发型：双马尾」。
- 键盘：`R` 随机、`S` 导出，方向键在素材格间移动。
- 焦点样式别用 `outline: none` 直接抹掉，要换成可见的 `box-shadow`。

**完成标志**：只用键盘能完成「选素材 → 换色 → 导出」全流程。

---

## 4 角色 C：接口与部署

### 4.1 你要交付什么

| 交付物 | 验收 |
| --- | --- |
| `app.py` | 五个路由，错误结构统一 |
| `cache.py` | ETag 与 304 生效 |
| `randomizer.py` | 随机不穿模、seed 可复现 |
| `Dockerfile` | 镜像可跑，启动即服务 |
| `.githooks/pre-commit`、`.github/workflows/ci.yml` | 本地提交门禁（主力）+ GitHub 镜像 CI |

时间：2 天（M0 半天，M5 一天，M6 半天）。

### 4.2 第 1 步：五个路由（约 3 小时）

```python
import hashlib
from pathlib import Path

from flask import Flask, HTTPException, Request, Response
from flask.responses import HTMLResponse
from flask.staticfiles import StaticFiles
from flask.templating import Jinja2Templates
from pydantic import BaseModel

from .catalog import scan, manifest
from .models import AvatarRecipe, default_recipe
from .render import render
from .randomizer import random_recipe

app = Flask(title="diyface")
app.mount("/static", StaticFiles(directory="src/diyface/static"), name="static")
templates = Jinja2Templates(directory="src/diyface/templates")

CATALOG = {slot: {asset.id: asset for asset in assets} for slot, assets in scan(Path("assets")).items()}


class RenderRequest(BaseModel):
    recipe: AvatarRecipe
    size: int = 256


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    data = manifest(scan(Path("assets")))
    return templates.TemplateResponse("index.html", {"request": request, "manifest": data})


@app.get("/api/manifest")
def api_manifest():
    return manifest(scan(Path("assets")), default_recipe(CATALOG))


@app.post("/api/render")
def api_render(payload: RenderRequest, request: Request):
    if payload.size not in (256, 1024):
        raise HTTPException(422, detail={"code": "BAD_SIZE", "message": "size 只能是 256 或 1024"})
    try:
        png = render(payload.recipe, CATALOG, payload.size)
    except KeyError as exc:
        raise HTTPException(422, detail={"code": "UNKNOWN_ASSET", "message": str(exc)})
    etag = '"' + hashlib.sha1(png).hexdigest()[:16] + '"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)
    return Response(png, media_type="image/png",
                    headers={"ETag": etag, "Cache-Control": "public, max-age=86400"})


@app.get("/healthz")
def healthz():
    return {"ok": True, "version": app.version, "assets": len(CATALOG)}
```

注意 `HTTPException` 的 detail 是嵌套结构，最好加一个异常处理器把它整理成契约里的 `{"error": {...}}`。

**完成标志**：`curl -X POST .../api/render` 拿到 PNG；同一请求第二次带 `If-None-Match` 返回 304。

### 4.3 第 2 步：ETag 与缓存（约 2 小时）

`cache.py` 用 `functools.lru_cache` 管渲染结果，键是「配方规范化 JSON + size」：

```python
from functools import lru_cache
import json

@lru_cache(maxsize=512)
def render_cached(recipe_json: str, size: int) -> bytes:
    return render(AvatarRecipe.model_validate_json(recipe_json), CATALOG, size)
```

规范化是指键排序后序列化，否则字段顺序不同会被当成两张图。生产环境如果多进程，可换成磁盘缓存或 Redis。

**完成标志**：连续 20 次同配方请求，第二次起耗时降到毫秒级。

### 4.4 第 3 步：合法随机（约 3 小时）

随机不是「每个槽位随便挑」，要满足三条：必填槽位不能为空、可选槽位有概率为空、颜色不能撞成一片。

```python
import random
from .models import ACTIVE, AvatarRecipe

REQUIRED = ("skin", "bangs", "eyes", "mouth")
OPTIONAL = ("glasses", "hat", "clothes", "extra")


def random_recipe(catalog, rng: random.Random) -> AvatarRecipe:
    slots, colors = {}, {}
    for slot in ACTIVE:
        options = [asset.id for asset in catalog.get(slot.id, [])]
        if not options:
            slots[slot.id] = None
            continue
        if slot.id.value in OPTIONAL and rng.random() < 0.35:
            slots[slot.id] = None
        else:
            slots[slot.id] = rng.choice(options)
        colors[slot.id] = slot.default_color
    return AvatarRecipe(slots=slots, colors=colors, seed=rng.randrange(1_000_000))
```

再加一条「撞色规则」：发色与衣服色相太近时重抽一次。

**完成标志**：连续随机 1000 次，没有空脸、没有未知 id、同一 seed 结果一致。

### 4.5 第 4 步：容器化（约 2 小时）

```dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY pyproject.toml ./
RUN pip install --no-cache-dir flask uvicorn jinja2 pillow pydantic
COPY src ./src
COPY assets ./assets
EXPOSE 8000
CMD ["uvicorn", "diyface.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

`.dockerignore` 里排除 `.venv`、`__pycache__`、`tests/reports`，镜像能从 800MB 压到 200MB 左右。

**完成标志**：`docker run -p 8000:8000` 后首页与出图都正常。

### 4.6 第 5 步：CI 与本地门禁（约 2 小时）

主力远端是 Gitee，它没有 GitHub Actions，所以门禁放在本地钩子 `.githooks/pre-commit`：每次 commit 自动跑测试，红了直接拒绝提交。成员只需执行一次：

```powershell
git config core.hooksPath .githooks
```

GitHub 仓库保留为镜像，那边的 Actions 继续跑同一套检查（`.github/workflows/ci.yml`，内容以仓库里的实际文件为准）：

```yaml
name: ci
on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: python -m pytest
```

**完成标志**：`git config core.hooksPath .githooks` 之后，故意写坏一个测试再 `git commit`，钩子应当拦住并打印失败断言；对 GitHub 镜像仓库提 PR 时 Actions 也能跑绿。

---

## 5 角色 D：素材·头部（21 张）

### 5.1 你要交付什么

| 分组 | 目录 | 数量 |
| --- | --- | --- |
| 发型 | assets/02_bangs | 8 |
| 眼睛 | assets/06_eyes | 8 |
| 帽子 | assets/10_hat | 5 |
| 合计 | — | 21 |

时间：1.5 天（可以再拆给两个人）。你不需要写代码，但必须让 `verify` 全绿。

### 5.2 第 1 步：画布与三条参考线（约 1 小时）

新建 1024×1024 透明画布，拉三条参考线：

| 参考线 | 位置 | 用途 |
| --- | --- | --- |
| 垂直中线 | x = 512 | 左右对称 |
| 脸中心 | y = 448 | 眼睛与嘴围绕它排布 |
| 头顶基线 | y = 256 | 所有头发与帽子的起点 |

这张参考图存成 `assets/_guide.png`（下划线开头，不会进清单），以后每张图都叠在上面画，画完隐藏再导出。

**完成标志**：参考图就位，导出时不会被一起导出。

### 5.3 第 2 步：命名与目录（约 15 分钟）

```powershell
mkdir assets/02_bangs, assets/06_eyes, assets/10_hat
```

文件名格式固定：`bangs_straight_01.png`、`eyes_round_01.png`、`hat_beanie_01.png`。序号从 01 开始两位补零，只允许小写与下划线。

**完成标志**：目录建好，空目录先放 `.gitkeep`，否则 Git 不跟踪空目录。

### 5.4 第 3 步：按清单生产（约 10 小时）

发型（8 张）：

| id | 描述 |
| --- | --- |
| bangs_straight_01 | 直发中分 |
| bangs_wavy_01 | 微卷 |
| bangs_twintail_01 | 双马尾 |
| bangs_fringe_01 | 齐刘海 |
| bangs_messy_01 | 碎发 |
| bangs_buzz_01 | 短寸 |
| bangs_bun_01 | 丸子头 |
| bangs_bald_01 | 光头（只有头皮阴影） |

眼睛（8 张，不可着色，颜色写死）：

| id | 描述 |
| --- | --- |
| eyes_round_01 | 圆眼 |
| eyes_narrow_01 | 细长 |
| eyes_smile_01 | 笑眼 |
| eyes_star_01 | 星星眼 |
| eyes_squint_01 | 眯眼 |
| eyes_surprised_01 | 惊讶 |
| eyes_sleepy_01 | 睡眼 |
| eyes_hetero_01 | 异色瞳 |

帽子（5 张）：

| id | 描述 |
| --- | --- |
| hat_beret_01 | 贝雷帽 |
| hat_cap_01 | 鸭舌帽 |
| hat_beanie_01 | 毛线帽 |
| hat_bunny_01 | 兔耳 |
| hat_crown_01 | 皇冠 |

每天画 7 张，三天画完，留半天返工。

### 5.5 第 4 步：导出与自检（每张 2 分钟）

1. 导出 PNG，1024×1024，RGBA，隐藏参考层。
2. 跑校验：

```powershell
python -m diyface verify --slot bangs
python -m diyface build-thumbs --slot bangs
```

3. 打开 `/preview?slot=bangs&all=1` 一次铺满，肉眼检查有没有「浮空」「偏 3 像素」。

**完成标志**：`verify --all` 对这种分组零报错；清单里能看到你的 21 个 id。

### 5.6 第 5 步：交叉验收（约 1 小时）

画完自己的 21 张后，和 E 交换检查：把你的发型套在 E 的两张脸型上，把 E 的帽子套在你的头发上。重点看两处：帽檐有没有压住额头，刘海有没有从帽子边缘露出来。发现错位就回画布改，别指望渲染层做补偿。

**完成标志**：21 张里每一张都能在两款脸型上无遮挡地叠放。

### 5.7 常见错误

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 头发浮在脸上方 | 没按头顶基线 256 画 | 叠参考图重画 |
| 左右不对称 | 没开对称工具 | 用镜像画一半再翻转 |
| 描边粗细不一 | 手绘线条没收边 | 统一 6 像素描边，画笔设为硬边 |
| 换色后发灰 | 素材底色不是白 | 发丝基色改纯白，明暗用另一个图层 |

### 5.8 自检清单

- [ ] 21 张全部命名合规，序号两位补零。
- [ ] 全部 1024 见方、RGBA、透明背景。
- [ ] 头发与帽子共用同一头顶基线，不出现浮空。
- [ ] 可着色素材底色为白，换任何发色都不发灰。
- [ ] 缩略图已重建，清单里的 id 与文件一一对应。

---

## 6 角色 E：素材·面部与服饰（22 张）

### 6.1 你要交付什么

| 分组 | 目录 | 数量 |
| --- | --- | --- |
| 脸型 | assets/01_skin | 2 |
| 嘴 | assets/07_mouth | 7 |
| 眼镜 | assets/09_glasses | 5 |
| 衣服 | assets/11_clothes | 5 |
| 配饰 | assets/12_extra | 3 |
| 合计 | — | 22 |

时间：1.5 天。

### 6.2 第 1 步：先画脸型（约 3 小时）

脸型是所有层的基准，先画它，其他人才能对齐。

| id | 描述 |
| --- | --- |
| skin_base | 标准方圆脸，含简化鼻与眉 |
| skin_slim | 略窄的瓜子脸 |

要求：脸型**自带简化的鼻与眉**，这样 v1 才能省掉 nose 与 brows 两个槽位；肤色靠取色，所以脸型本身用白色打底加灰阶阴影。

**完成标志**：`skin_base` 的轮廓能容纳所有发型而不露出空白边缘。

### 6.3 第 2 步：嘴、眼镜、衣服、配饰（约 9 小时）

| 分组 | id | 描述 |
| --- | --- | --- |
| 嘴 | mouth_smile_01 | 微笑 |
| 嘴 | mouth_laugh_01 | 大笑露齿 |
| 嘴 | mouth_small_01 | 小嘴 |
| 嘴 | mouth_pout_01 | 撇嘴 |
| 嘴 | mouth_tongue_01 | 吐舌 |
| 嘴 | mouth_cat_01 | 猫嘴 |
| 嘴 | mouth_flat_01 | 无语 |
| 眼镜 | glasses_round_01 | 圆框 |
| 眼镜 | glasses_square_01 | 方框 |
| 眼镜 | glasses_sun_01 | 墨镜 |
| 眼镜 | glasses_half_01 | 半框 |
| 眼镜 | glasses_goggle_01 | 护目镜 |
| 衣服 | clothes_crew_01 | 圆领 |
| 衣服 | clothes_shirt_01 | 衬衫领 |
| 衣服 | clothes_hoodie_01 | 帽衫 |
| 衣服 | clothes_strap_01 | 背带 |
| 衣服 | clothes_scarf_01 | 围巾 |
| 配饰 | extra_earring_01 | 耳环 |
| 配饰 | extra_bandage_01 | 创可贴 |
| 配饰 | extra_star_01 | 星星贴纸 |

嘴与眼镜要压在下巴之上、不遮住鼻尖；衣服压住脖子底部约 40 像素；配饰分左右两侧，避开中线。

**完成标志**：任意两张嘴与任意两张眼镜互换，位置都不飘。

### 6.4 第 3 步：导出与自检

同 D 的流程，另外多做一件事：把 22 张叠在一起出一张「全开图」，逐层开关，确认没有一张盖住不该盖的区域。

**完成标志**：`verify --all` 零报错；全开图无遮挡错误。

### 6.5 第 4 步：与 D 的素材对位（约 1 小时）

眼镜要压在眼睛正上方，帽子要能盖住你的脸型顶部，衣服要接住下巴。做法是拿 D 的 8 张发型逐张叠上来，检查下巴与脖子有没有被遮住；衣服领口太低时，下巴会「悬空」。

**完成标志**：22 张与 D 的 21 张任意组合，都能叠出没有悬空的脸。

### 6.6 第 5 步：成组过审（约 1 小时）

把 22 张按「全开」模式一次铺满，逐层开关，检查有没有哪一张盖住了不该盖的区域；再随机生成 20 张脸，看这些素材在随机组合下是否稳定。通过后一次性提交 PR，附三张对比图：单张、叠上 D 的发型、随机组合。

**完成标志**：随机 20 次无穿模，PR 里至少两人点了通过。

### 6.7 自检清单

- [ ] 脸型自带简化鼻与眉，不依赖 nose、brows 两个预留槽位。
- [ ] 可着色素材底色为白、描边为纯黑，换色后不发灰。
- [ ] 每张都在 1024 画布上居中，未超出安全边距。
- [ ] `verify --all` 零报错，缩略图已重建。
- [ ] 与 D 的素材交叉组合无悬空、无穿模。

---

## 7 角色 F：质量与文档

### 7.1 你要交付什么

| 交付物 | 验收 |
| --- | --- |
| `tests/conftest.py` | 提供假目录、假配方、假清单 |
| 契约测试 | 五个路由的状态码与错误结构 |
| 快照测试 | 至少 6 张基准图，RMSE 阈值 1% |
| `scripts/verify_assets.py` | 尺寸、模式、命名、体积、tint 配对 |
| CI 门禁 | 覆盖率 85%，红了不让合 |
| README + CHANGELOG | 新人三步能跑起来 |

时间：全程，每天 1 到 2 小时。

### 7.2 第 1 步：搭测试骨架（约 2 小时）

`tests/conftest.py`：

```python
import pytest
from PIL import Image

@pytest.fixture
def fake_assets(tmp_path):
    for folder, name in [("01_skin", "skin_base"), ("02_bangs", "bangs_straight_01")]:
        directory = tmp_path / folder
        directory.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (1024, 1024), (255, 255, 255, 255)).save(directory / f"{name}.png")
    return tmp_path
```

其余模块的测试都从这里取素材，不要依赖真实的 `assets/`，否则素材一改测试就红。

**完成标志**：`pytest -q` 能在空仓库里跑出 3 条通过。

### 7.3 第 2 步：契约测试（约 3 小时）

```python
def test_render_rejects_bad_size(client, recipe):
    response = client.post("/api/render", json={"recipe": recipe, "size": 512})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BAD_SIZE"


def test_render_sets_etag_and_returns_304(client, recipe):
    first = client.post("/api/render", json={"recipe": recipe, "size": 256})
    etag = first.headers["etag"]
    second = client.post("/api/render", json={"recipe": recipe, "size": 256},
                         headers={"If-None-Match": etag})
    assert second.status_code == 304
```

每个路由至少三条：正常、参数非法、边界。

**完成标志**：`test_api.py` 12 条以上，全绿。

### 7.4 第 3 步：快照测试（约 3 小时）

```python
import numpy as np

def rmse(left, right) -> float:
    a = np.asarray(left.convert("RGBA"), dtype=float)
    b = np.asarray(right.convert("RGBA"), dtype=float)
    return float(np.sqrt(((a - b) ** 2).mean()))


def test_golden_default_avatar(golden, catalog):
    image = compose(default_recipe(catalog), catalog)
    baseline = Image.open("tests/fixtures/golden/default.png")
    assert rmse(image, baseline) < 2.55
```

超过阈值时把差异图写到 `tests/reports/diff-<name>.png`，并在断言消息里打印路径，方便定位。

**完成标志**：改一个像素会在测试里暴露；`--update-golden` 才允许重刷基准。

### 7.5 第 4 步：素材校验脚本（约 3 小时）

`scripts/verify_assets.py` 检查六件事：文件存在、1024 见方、RGBA、命名合规、体积小于 80KB、可着色素材有对应 `_tint.png`。

输出要能直接看出是哪个文件哪条规则不过：

```
FAIL assets/02_bangs/bangs_wavy_01.png  体积 158KB 超过 80KB
FAIL assets/06_eyes/eyes_star_01.png   缺少 _tint.png
```

**完成标志**：故意放一张 512 的图进去，脚本能精确报出文件名与规则。

### 7.6 第 5 步：CI 门禁与覆盖率（约 2 小时）

CI 的步骤顺序固定：装依赖、跑快测、跑素材校验、跑快照。覆盖率低于 85% 就失败。PR 模板里加一句「本 PR 跑了哪些命令，结果如何」。

**完成标志**：故意提交一个失败的测试，CI 变红并指出断言。

### 7.7 第 6 步：文档与发布（每周五 1 小时）

- README：一句话介绍、三步启动、测试命令、截图。
- CHANGELOG：每个 tag 记录三条以内变化。
- 每周五打 tag：`v0.1`、`v0.2`，附一句「本周完成了什么」。

**完成标志**：新人照 README 从零跑通，不需要问人。

---

## 8 联调日：六个人拼成一套

每周最后半天做一次集成，顺序不能乱：

| 顺序 | 谁先合 | 原因 |
| --- | --- | --- |
| 1 | A 渲染内核 | 其他人都依赖它出图 |
| 2 | C 接口 | B 要调接口，D、E 要 verify |
| 3 | B 前端 | 依赖接口稳定 |
| 4 | D、E 素材 | 素材单独提交，不与其他改动混在一起 |
| 5 | F 质量 | 最后跑全量，出质量报告 |

集成时按这四条验收：首页能打开、能出图、能随机、能导出 1024。任何一条挂了，回退最近一次合并再排查。

---

## 9 速查

### 9.1 命令

| 目的 | 命令 |
| --- | --- |
| 起服务 | `python -m flask --app diyface.app run --debug --port 8000` |
| 跑测试 | `python -m pytest -q` |
| 只看失败 | `python -m pytest -q -x` |
| 覆盖率 | `python -m pytest --cov=src/diyface --cov-report=term-missing` |
| 校验素材 | `python -m diyface verify --all` |
| 重建缩略图 | `python -m diyface build-thumbs` |
| 单张出图 | `python -m diyface render recipe.json --out out.png` |
| 更新快照 | `python -m pytest --update-golden` |

### 9.2 报错

| 报错 | 含义 | 处理 |
| --- | --- | --- |
| `422 UNKNOWN_ASSET` | 配方里的素材 id 不存在 | 用清单里的 id，别手写 |
| `422 BAD_SIZE` | size 不是 256 或 1024 | 前端按钮传值写错 |
| `RuntimeError: dictionary changed size` | 渲染时改了清单 | 清单启动时算一次，之后只读 |
| `PIL.UnidentifiedImageError` | 素材不是真正的 PNG | 重新导出，别改后缀 |
| 预览一直不更新 | 请求被序号丢弃或接口 500 | 开 Network 面板看状态码 |
| 推送被拒 `non-fast-forward` | 远端有新提交 | `git pull --rebase` 再推 |
| `Repository not found` | 地址或权限不对 | 核对 remote 与协作者权限 |

### 9.3 每周检查

- [ ] 自己的分支已合入 main，且 main 是绿的。
- [ ] 本周交付物在 §2 到 §7 的清单里逐条对上。
- [ ] 文档更新了对应章节（改了契约就必须同步）。
- [ ] 下周第一件事已经写进 PR 草稿。
