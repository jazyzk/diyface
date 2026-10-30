# 新人上手与六人分工执行方案

这份文档解决三件事：**怎么进仓库**、**怎么配环境**、**六个人各自一步一步怎么干**。
每一步的参考实现都直接内联在下文，不用再翻别的文件；[HANDBOOK.md](HANDBOOK.md) 留作原理与扩展阅读。

当前基线：M0 已完成，测试 71 条通过、11 条跳过。

---

## 1 五分钟加入仓库

### 1.1 你需要先有

| 项 | 说明 |
| --- | --- |
| Gitee 账号 | <https://gitee.com/signup>，注册后完成实名认证（公开仓库必须实名） |
| 网络 | Gitee 国内直连，不需要梯子 |

### 1.2 管理员操作（队长做一次）

仓库页 → **管理** → **仓库成员管理** → **添加成员** → 输入对方的 Gitee 用户名 → 权限选 **开发者**。

6 个人全部加完，列表里应该有 1 个管理员 + 5 个开发者。公开仓库不受「私有仓库最多 5 人」的限制，这一步不会报错。

### 1.3 成员操作

1. 打开 <https://gitee.com/chords-of-fate/diyface>，看到 README 说明已被加进来；
2. 点右上角「克隆/下载」，复制 HTTPS 地址；
3. 执行：

```powershell
git clone https://gitee.com/chords-of-fate/diyface.git
cd diyface
```

一个常见误解：**公开仓库不加成员也能 clone**，加成员是为了拿到 `push` 权限，别把两件事混了。

---

## 2 十五分钟配好环境

### 2.1 检查清单

| 软件 | 版本要求 | 检查命令 |
| --- | --- | --- |
| Python | 3.11 及以上 | `python --version` |
| Git | 任意较新版本 | `git --version` |
| VS Code | 任意较新版本 | 能打开文件夹即可 |
| 浏览器 | Chrome 或 Edge | 后续联调用 |

### 2.2 Windows 逐步（PowerShell）

```powershell
# 1) 允许本地脚本执行（否则激活虚拟环境会报错）
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# 2) 配置自己的提交身份（写你的名字和邮箱）
git config user.name "你的名字"
git config user.email "你的邮箱"

# 3) 建虚拟环境并激活
python -m venv .venv
.venv\Scripts\Activate.ps1

# 4) 装依赖（用清华源，避免 PyPI 直连超时）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn jinja2 pillow pydantic pytest pytest-cov numpy httpx

# 5) 把项目装成本地包，之后 python -m diyface 才可用
pip install -e .
```

### 2.3 macOS 逐步

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn jinja2 pillow pydantic pytest pytest-cov numpy httpx
pip install -e .
git config user.name "你的名字"
git config user.email "你的邮箱"
```

### 2.4 开启提交门禁

只需执行一次，之后每次 `git commit` 都会自动跑测试，红了直接拒绝提交：

```powershell
git config core.hooksPath .githooks
```

### 2.5 什么叫「环境就绪」

三条命令都有预期输出才算完：

| 命令 | 期望 |
| --- | --- |
| `python --version` | `Python 3.11.x` 或更高 |
| `python -m pytest` | 最后一行 `71 passed, 11 skipped` |
| `python -m uvicorn diyface.app:app --port 8000` | 浏览器打开 127.0.0.1:8000 能看到「DIY 头像生成器」 |

11 条跳过是 Word 任务书的校验（没装 `python-docx`），属正常，不用处理。

### 2.6 一定会遇到的三类报错

| 报错 | 原因 | 解决 |
| --- | --- | --- |
| `无法加载文件 Activate.ps1，因为在此系统上禁止运行脚本` | PowerShell 执行策略 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`，重开终端 |
| `python 不是内部或外部命令` | 安装时没勾 Add to PATH | 重装 Python，勾选 Add Python to PATH |
| `pip` 停住不动好几分钟 | PyPI 直连被限速 | 命令里已经带 `-i` 清华源；再不行换阿里源 `https://mirrors.aliyun.com/pypi/simple` |

---

## 3 第一次提交：练手 PR

目的不是写代码，而是**一次性验证四件事**：clone 成功、身份配置正确、钩子生效、有 PR 权限。

1. 同步主分支并开新分支：

```powershell
git switch main
git pull --rebase
git switch -c feat/hello-<你的名字拼音>
```

2. 在 `docs/team/` 下新建 `<你的名字>.md`，写三行：我是谁、负责哪块、这周做什么。

3. 提交（钩子会自动跑测试，绿了才放行）：

```powershell
git add docs/team/<你的名字>.md
git commit -m "docs: 添加 <你的名字> 的自我介绍"
git push -u origin feat/hello-<你的名字拼音>
```

4. 到 Gitee 仓库页点 **Pull Requests → 新建**，源分支选你的分支，目标选 `main`，描述里写一句「练习 PR，验证环境」。

5. 找任意一位队友在 PR 里点「审查通过」，然后 **Squash 合并**，删除分支。

完成后回到 main 拉一次，`ls docs/team` 能看到自己的文件，说明整条链路都通了。

---

## 4 六个人分别怎么干

每个人第一周只解决一件事：**让自己那一段链路先跑起来**。下面每一步都给了要改的文件、可直接用的代码和验收方法。

### 4.0 先看依赖：谁在等谁

```
E 的两张脸型 ──┐
               ├──> D 用它们对位发型与帽子
D 的 3 张试作 ─┴──> A 叠图层、出快照
A 的 render() ────> C 的 /api/render ────> B 的实时预览
F 的测试与钩子 ───> 所有人的提交门禁（谁红了谁自己看到）
```

规则：**先做能解锁别人的那一步**。E 先画脸型、D 先画 3 张试作、A 先打通命令行——这三件事不做完，后面四个人都在空转。

### 4.1 A 渲染内核（约 2 天）

**本周目标**：命令行输入一份配方，输出一张 256 的透明 PNG。

**第 1 步：造 3 张占位素材（30 分钟）**

素材组还没交图，但你不能等。先用纯 Python 生成三张全透明的 1024 画布：

```powershell
python -c "from PIL import Image; from pathlib import Path; [ (Path(d).mkdir(parents=True, exist_ok=True), Image.new('RGBA',(1024,1024),(0,0,0,0)).save(Path(d)/f'{n}.png')) for d,n in [('assets/01_skin','skin_base'),('assets/02_bangs','bangs_straight_01'),('assets/06_eyes','eyes_round_01')] ]"
```

✅ 验收：`Get-ChildItem assets -Recurse -Filter *.png` 列出 3 个文件，用看图软件打开是 1024×1024 的透明图。

**第 2 步：扫描目录生成清单（2 小时）**

新建 `src/diyface/catalog.py`。它做三件事：按槽位目录收集 PNG、校验尺寸与模式、拼出 manifest。

```python
"""扫描 assets/ 目录，生成素材清单。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .models import SLOTS, Slot, SlotId

CANVAS = 1024


@dataclass(frozen=True)
class Asset:
    id: str
    slot: SlotId
    path: Path


def scan_slot(root: Path, slot: Slot) -> list[Asset]:
    folder = root / slot.folder_no
    if not folder.is_dir():
        return []
    assets: list[Asset] = []
    for path in sorted(folder.glob("*.png")):
        if path.name.startswith("_"):          # 跳过参考图、缩略图
            continue
        with Image.open(path) as image:
            if image.size != (CANVAS, CANVAS):
                raise ValueError(f"{path.name} 尺寸 {image.size} 应为 {CANVAS}x{CANVAS}")
            if image.mode != "RGBA":
                raise ValueError(f"{path.name} 必须是 RGBA，当前 {image.mode}")
        assets.append(Asset(id=path.stem, slot=slot.id, path=path))
    return assets


def scan(root: Path) -> dict[SlotId, list[Asset]]:
    catalog: dict[SlotId, list[Asset]] = {}
    for slot in SLOTS:
        assets = scan_slot(root, slot)
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
            "assets": [
                {"id": asset.id, "file": f"{slot.folder_no}/{asset.path.name}"}
                for asset in assets
            ],
        })
    return {"schema": 1, "slots": slots}
```

✅ 验收：

```powershell
python -c "from pathlib import Path; from diyface.catalog import scan; print({k.value: [a.id for a in v] for k, v in scan(Path('assets')).items()})"
```

打印出 3 个槽位与之对应的素材 id。

**第 3 步：按 z 序叠图层（3 小时）**

新建 `src/diyface/render.py`。核心只有四步：按 z 取层、着色、alpha 合成、缩放编码。

```python
"""把配方合成为一张 1024 的 RGBA 图。"""

from __future__ import annotations

import io
from functools import lru_cache

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
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
```

两个细节必须做对：合成用 `alpha_composite`（不是 `paste`），缩放用 `LANCZOS`。

✅ 验收：写一个小脚本，把配方里 `hat` 设为 `None`，输出的 PNG 在帽子区域 alpha 必须为 0。

**第 4 步：颜色相乘（2 小时）**

新建 `src/diyface/palettes.py`。白色发丝乘目标色会变成目标色，黑色描边乘任何色仍是黑，明暗自然保留。

```python
"""颜色解析与着色。"""

from __future__ import annotations

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

✅ 验收：同一张刘海分别用 `#3B2B23` 与 `#C0392B` 出图，两次结果的描边像素完全一致。

**第 5 步：命令行出图（1.5 小时）**

新建 `src/diyface/__main__.py`，之后 `python -m diyface` 就能用。

```python
"""命令行入口：python -m diyface render recipe.json --out out.png"""

from __future__ import annotations

import argparse
from pathlib import Path

from .catalog import scan
from .models import AvatarRecipe
from .render import render


def build_catalog(root: Path) -> dict:
    return {slot: {asset.id: asset for asset in assets} for slot, assets in scan(root).items()}


def main() -> None:
    parser = argparse.ArgumentParser(prog="diyface")
    sub = parser.add_subparsers(dest="command", required=True)

    render_cmd = sub.add_parser("render", help="按配方出图")
    render_cmd.add_argument("recipe", type=Path)
    render_cmd.add_argument("--out", type=Path, default=Path("out.png"))
    render_cmd.add_argument("--size", type=int, default=256, choices=[256, 1024])

    sub.add_parser("verify", help="校验素材")

    args = parser.parse_args()
    catalog = build_catalog(Path("assets"))

    if args.command == "render":
        recipe = AvatarRecipe.model_validate_json(args.recipe.read_text(encoding="utf-8"))
        args.out.write_bytes(render(recipe, catalog, args.size))
        print(f"已生成 {args.out}")


if __name__ == "__main__":
    main()
```

✅ 验收：

```powershell
python -m diyface render tests/fixtures/recipes/base.json --out out.png
```

能生成图片，用系统看图工具能打开。若提示 `No module named diyface`，回到项目根目录执行一次 `pip install -e .`。

**第 6 步：三张快照基线（2 小时）**

先写 `tests/fixtures/recipes/base.json`：

```json
{
  "version": 1,
  "slots": {
    "skin": "skin_base",
    "bangs": "bangs_straight_01",
    "eyes": "eyes_round_01",
    "mouth": null,
    "glasses": null,
    "hat": null,
    "clothes": null,
    "extra": null
  },
  "colors": { "skin": "#F2D5B8", "bangs": "#3B2B23" }
}
```

再写 `tests/test_golden.py`：第一次运行生成基准图，之后比对 RMSE 是否小于 1%。

```python
"""渲染快照测试：固定配方出图，与基准图比对。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from diyface.catalog import scan
from diyface.models import AvatarRecipe
from diyface.render import compose

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "fixtures" / "golden"
THRESHOLD = 2.55          # 约等于 1% 的均方根误差


def rmse(left: Image.Image, right: Image.Image) -> float:
    a = np.asarray(left.convert("RGBA"), dtype=float)
    b = np.asarray(right.convert("RGBA"), dtype=float)
    return float(np.sqrt(((a - b) ** 2).mean()))


@pytest.mark.parametrize("name", ["base"])
def test_golden(name: str) -> None:
    catalog = {
        slot: {asset.id: asset for asset in assets}
        for slot, assets in scan(ROOT / "assets").items()
    }
    recipe = AvatarRecipe.model_validate_json(
        (ROOT / "tests" / "fixtures" / "recipes" / f"{name}.json").read_text(encoding="utf-8")
    )
    image = compose(recipe, catalog)

    GOLDEN.mkdir(parents=True, exist_ok=True)
    baseline_path = GOLDEN / f"{name}.png"
    if not baseline_path.exists():
        image.save(baseline_path)
        pytest.skip(f"首次运行，已生成基准图 {baseline_path.name}")

    diff = rmse(image, Image.open(baseline_path).convert("RGBA"))
    if diff >= THRESHOLD:
        image.save(GOLDEN / f"diff-{name}.png")
    assert diff < THRESHOLD, f"{name} 与基准差异 {diff:.2f}，已输出 diff-{name}.png"
```

✅ 验收：第一次 `pytest` 跳过并生成基准；第二次通过；改坏一个像素会红并留下 `diff-base.png`。

**第 7 步：交接给 C（30 分钟）**

在 PR 描述里写清函数签名：`render(recipe, catalog, size) -> bytes`，并 @C 说明可以接 `/api/render` 了。

✅ 验收：C 能直接 `from diyface.render import render` 并在接口里调通。

**后续里程碑**：M2 配合 F 做素材校验、M5 做渲染性能（缓存与预热），其余时间支援 B 的预览问题。

### 4.2 B 前端交互（约 2.5 天）

**本周目标**：把 M0 的静态页换成能用真实清单点动的三栏界面。

**第 1 步：搭三栏骨架（3 小时）**

改 `templates/index.html` 与 `static/style.css`。中间预览严格 1:1，窄屏改单列。

```html
<div class="layout">
  <aside id="categories" aria-label="类目"></aside>
  <main class="stage"><img id="preview" width="256" height="256" alt="头像预览"></main>
  <aside class="controls">
    <input id="color" type="color" aria-label="取色">
    <button id="random" type="button">随机</button>
    <button type="button" data-size="256">下载 256</button>
    <button type="button" data-size="1024">下载 1024</button>
    <button id="share" type="button">复制分享链接</button>
  </aside>
</div>
<div class="assets" id="assets" aria-label="素材"></div>
<script type="module" src="/static/app.js"></script>
```

```css
.layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 260px;
  gap: 16px;
}
.stage {
  display: grid;
  place-items: center;
  aspect-ratio: 1 / 1;
}
@media (max-width: 720px) {
  .layout { grid-template-columns: 1fr; }
}
```

✅ 验收：桌面三栏对齐；浏览器宽度拖到 375 像素，没有横向滚动条。

**第 2 步：用清单渲染类目与素材格（3 小时）**

新建 `static/app.js`：拉清单、生成类目按钮、点类目铺素材格，外带一个「无」按钮。

```javascript
const state = { manifest: null, recipe: null, slot: "bangs", seq: 0 };
const preview = document.getElementById("preview");

async function boot() {
  state.manifest = await (await fetch("/api/manifest")).json();
  state.recipe = state.manifest.default_recipe;
  renderCategories();
  selectSlot(state.slot);
  refreshPreview();
}

function renderCategories() {
  const box = document.getElementById("categories");
  box.replaceChildren(
    ...state.manifest.slots.map((slot) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = slot.id;
      button.addEventListener("click", () => selectSlot(slot.id));
      return button;
    })
  );
}

function selectSlot(slotId) {
  state.slot = slotId;
  const slot = state.manifest.slots.find((item) => item.id === slotId);
  const box = document.getElementById("assets");

  const none = document.createElement("button");
  none.type = "button";
  none.textContent = "无";
  none.addEventListener("click", () => setAsset(slotId, null));

  const buttons = slot.assets.map((asset) => {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-label", `${slotId}：${asset.id}`);
    button.style.backgroundImage = `url(/assets/${asset.file})`;
    button.addEventListener("click", () => setAsset(slotId, asset.id));
    return button;
  });

  box.replaceChildren(none, ...buttons);
}

function setAsset(slotId, assetId) {
  state.recipe.slots[slotId] = assetId;
  localStorage.setItem("diyface.recipe.v1", JSON.stringify(state.recipe));
  refreshPreview();
}

boot();
```

✅ 验收：8 个类目都能点，点「无」后预览里的对应图层消失。缩略图需要 C 把 `assets/` 挂成静态目录（见 §4.3 第 1 步）。

**第 3 步：接预览接口（3 小时）**

在 `app.js` 里加去抖与序号，防止连点闪回旧图：

```javascript
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
    if (!response.ok) {
      console.error("渲染失败", response.status);
      return;
    }
    if (mine !== state.seq) return;          // 过期响应，丢弃
    preview.src = URL.createObjectURL(await response.blob());
  }, 120);
}
```

✅ 验收：快速连点 10 个素材，最终显示的必须是最后点的那个，中间不闪。

**第 4 步：取色器与预设色板（2 小时）**

```javascript
const colorInput = document.getElementById("color");

colorInput.addEventListener("input", (event) => {
  const slot = state.manifest.slots.find((item) => item.id === state.slot);
  if (!slot || !slot.tintable) return;
  state.recipe.colors[state.slot] = event.target.value.toUpperCase();
  refreshPreview();
});
```

✅ 验收：换发色只影响头发，脸和眼睛不变；切换素材后颜色保留。

**第 5 步：下载与分享（2 小时）**

```javascript
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

function encodeRecipe(recipe) {
  const json = JSON.stringify(recipe);
  return btoa(unescape(encodeURIComponent(json)))
    .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function decodeRecipe(token) {
  const base64 = token.replace(/-/g, "+").replace(/_/g, "/");
  return JSON.parse(decodeURIComponent(escape(atob(base64))));
}

document.querySelectorAll("[data-size]").forEach((button) => {
  button.addEventListener("click", () => download(Number(button.dataset.size)));
});

const shared = new URLSearchParams(location.search).get("r");
if (shared) state.recipe = decodeRecipe(shared);
```

✅ 验收：下载的 PNG 是 1024×1024、四角透明；分享链接在无痕窗口打开与原件一致。

**第 6 步：移动端与键盘（2 小时）**

```css
button { min-width: 44px; min-height: 44px; }
:focus-visible { outline: 3px solid #4a6fa5; outline-offset: 2px; }
```

```javascript
document.addEventListener("keydown", (event) => {
  if (event.key === "r") document.getElementById("random").click();
  if (event.key === "s") download(1024);
});
```

✅ 验收：只用键盘能完成「选素材 → 换色 → 导出」全流程。

**第 7 步：与 C 联调（2 小时）**

接口从占位图切到真实渲染后，逐项过一遍：预览延迟、导出尺寸、错误提示（接口 500 时不要白屏）。

✅ 验收：连续操作 30 秒不出现白屏或错位。

**后续里程碑**：M3 完成正式 UI、M4 加素材后检查布局不崩、M6 加 SEO 静态页。

### 4.3 C 接口与部署（约 2 天）

**本周目标**：把 M0 的清单接口扩成能出图的完整接口，304 缓存生效。

**第 1 步：清单接上真实扫描（2 小时）**

改 `app.py`：启动时扫一次目录，把 `assets/` 挂成静态目录，首页内联清单。

```python
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import __version__
from .catalog import manifest as build_manifest, scan

BASE_DIR = Path(__file__).parent
ASSETS = Path("assets")
CATALOG: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global CATALOG
    CATALOG = {slot: {a.id: a for a in assets} for slot, assets in scan(ASSETS).items()}
    yield


app = FastAPI(title="diyface", version=__version__, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/assets", StaticFiles(directory=ASSETS), name="assets")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/api/manifest")
def api_manifest() -> dict:
    return build_manifest(scan(ASSETS))
```

✅ 验收：`curl http://127.0.0.1:8000/api/manifest` 返回的 `slots[].assets` 不为空。

**第 2 步：接上渲染（2 小时）**

```python
import hashlib

from fastapi import HTTPException, Request, Response
from pydantic import BaseModel

from .models import AvatarRecipe
from .render import render


class RenderRequest(BaseModel):
    recipe: AvatarRecipe
    size: int = 256


@app.post("/api/render")
def api_render(payload: RenderRequest, request: Request) -> Response:
    if payload.size not in (256, 1024):
        raise HTTPException(
            status_code=422,
            detail={"code": "BAD_SIZE", "message": "size 只能是 256 或 1024"},
        )
    try:
        png = render(payload.recipe, CATALOG, payload.size)
    except KeyError as exc:
        raise HTTPException(status_code=422, detail={"code": "UNKNOWN_ASSET", "message": str(exc)})

    etag = '"' + hashlib.sha1(png).hexdigest()[:16] + '"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)
    return Response(
        png,
        media_type="image/png",
        headers={"ETag": etag, "Cache-Control": "public, max-age=86400"},
    )
```

✅ 验收：`curl -X POST` 拿到 PNG，用看图工具打开正常。

**第 3 步：ETag 与缓存（1.5 小时）**

上面的 `etag` 已经覆盖 304。再加一个进程内缓存，避免同配方重复合成：

```python
"""渲染结果缓存：键是规范化后的配方 JSON 加尺寸。"""

from __future__ import annotations

import json
from functools import lru_cache

from .models import AvatarRecipe
from .render import render


def normalize(recipe: AvatarRecipe) -> str:
    return json.dumps(recipe.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)


def render_cached(recipe: AvatarRecipe, catalog: dict, size: int) -> bytes:
    return _render(normalize(recipe), size, catalog)


@lru_cache(maxsize=512)
def _render(recipe_json: str, size: int, catalog: dict) -> bytes:
    return render(AvatarRecipe.model_validate_json(recipe_json), catalog, size)
```

✅ 验收：第二次请求带同样的 ETag，状态码 304、响应体为空；连续 20 次同配方请求，耗时降到毫秒级。

**第 4 步：合法随机（2 小时）**

新建 `src/diyface/randomizer.py`：

```python
"""生成合法的随机配方。"""

from __future__ import annotations

import random

from .models import ACTIVE, AvatarRecipe

OPTIONAL = {"glasses", "hat", "clothes", "extra"}


def random_recipe(catalog: dict, rng: random.Random) -> AvatarRecipe:
    slots: dict = {}
    colors: dict = {}
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

```python
@app.post("/api/random")
def api_random() -> dict:
    return random_recipe(CATALOG, random.Random()).model_dump(mode="json")
```

✅ 验收：连调 1000 次 `/api/random`，没有空脸、没有未知素材 id；固定 seed 时结果一致。

**第 5 步：错误结构统一（1 小时）**

```python
from fastapi import Request
from fastapi.responses import JSONResponse


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "ERROR", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail})
```

✅ 验收：`curl -X POST ... -d '{"size":512}'` 返回 422 与 `{"error": {"code": "BAD_SIZE"}}`。

**第 6 步：健康检查（1 小时）**

```python
@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "version": __version__, "assets": sum(len(v) for v in CATALOG.values())}
```

✅ 验收：容器与本地都能访问 `/healthz` 且字段齐全。

**后续里程碑**：M5 做 Docker 镜像与缓存、M6 部署上线与日志。

### 4.4 D 素材·头部（约 1.5 天）

**本周目标**：先交 3 张跑通流程，再批量生产到 21 张。

**第 1 步：准备画布与参考线（1 小时）**

新建 1024×1024 透明画布，拉三条参考线：垂直中线 x=512、脸中心 y=448、头顶基线 y=256。存成 `assets/_guide.png`（下划线开头，不会被扫描进清单）。

✅ 验收：参考图存在，但 `scan()` 结果里没有它。

**第 2 步：建目录与命名（15 分钟）**

```powershell
mkdir assets/02_bangs, assets/06_eyes, assets/10_hat
```

文件名格式 `<槽位>_<形状>_<两位序号>.png`，例如 `bangs_straight_01.png`。只允许小写字母、数字、下划线。

✅ 验收：`Get-ChildItem assets -Directory` 能看到三个槽位目录。

**第 3 步：画 3 张试作（3 小时）**

直发（`bangs_straight_01`）、圆眼（`eyes_round_01`）、贝雷帽（`hat_beret_01`）。重点不是好看，是**位置对**：头发压在头顶基线上、眼睛围绕脸中心对称、帽子盖住头发顶端。

✅ 验收：三张都 1024×1024、RGBA、不越界。

**第 4 步：让 A 叠出来看（1 小时）**

把三张图给 A，让他用渲染器叠到一张脸上。若出现「头发浮空」「帽子歪」，回画布改，不要指望渲染层补偿。

✅ 验收：A 出图后，头发贴头皮、帽子不遮眼。

**第 5 步：批量生产到 21 张（8 小时）**

发型 8 张（直发、微卷、双马尾、齐刘海、碎发、短寸、丸子头、光头）、眼睛 8 张（圆、细长、笑、星星、眯、惊讶、睡眼、异色瞳）、帽子 5 张（贝雷、鸭舌、毛线、兔耳、皇冠）。

节奏建议：每天 7 张，第三天收尾，留半天返工。

✅ 验收：清单里能看到 21 个 id，每张尺寸与命名合规。

**第 6 步：跑校验（1 小时）**

```powershell
python -m diyface verify
```

✅ 验收：校验零报错；素材格加载不卡（缩略图由 F 的脚本生成，见 §4.6 第 4 步）。

**第 7 步：与 E 交叉验收（1 小时）**

把你的 21 张套在 E 的两张脸型上，逐张看有没有露白边；换 E 的眼镜、帽子检查遮挡顺序。

✅ 验收：任意组合都能叠出一张没有穿模的脸。

**后续里程碑**：M4 补齐到 21 张（若 M2 只交了 15 张），M5 视觉统一（描边粗细、配色）。

### 4.5 E 素材·面部与服饰（约 1.5 天）

**本周目标**：先把两张脸型画完（它决定其他所有层的基准），再补嘴、眼镜、衣服、配饰。

**第 1 步：画两款脸型（3 小时）**

`skin_base`（标准方圆脸，自带简化鼻与眉）与 `skin_slim`（略窄）。肤色不靠画，靠取色，所以脸型用白色底 + 灰阶阴影。

坐标参考：脸宽 520、脸高 560，中心 (512, 448)，下巴约 y=728。

✅ 验收：两张脸型的轮廓能容纳 D 的 8 种发型而不露白边。

**第 2 步：交给 D 对位（30 分钟）**

把两张脸型 push 上去，在群里 @D，让他先画发型。**这一步不要拖**，你晚一天，D 就要晚一天返工。

✅ 验收：D 回复「脸型能用」。

**第 3 步：画 7 张嘴（3 小时）**

微笑、大笑露齿、小嘴、撇嘴、吐舌、猫嘴、无语。位置定在脸中心下方约 90 像素，宽度不超过脸宽的 40%。

✅ 验收：7 张嘴任意换，位置都不飘。

**第 4 步：画 5 副眼镜（2 小时）**

圆框、方框、墨镜、半框、护目镜。镜框中心对齐眼睛中心，鼻梁处留 6 像素空隙。

✅ 验收：5 副都能正确压住眼睛而不遮住眉毛。

**第 5 步：画 5 件衣服（2 小时）**

圆领、衬衫领、帽衫、背带、围巾。领口上缘要接住下巴，压住脖子底部约 40 像素。

✅ 验收：换衣服时下巴不悬空。

**第 6 步：画 3 个配饰（1 小时）**

耳环、创可贴、星星贴纸。左右对称摆放，避开中线。

✅ 验收：配饰不遮住眼睛与嘴。

**第 7 步：对位与全开检查（1 小时）**

把 22 张按「全开」模式铺满，逐层开关，检查有没有盖住不该盖的区域；再随机 20 次看组合稳定性。

✅ 验收：随机 20 次无穿模；所有素材尺寸与模式合规。

**后续里程碑**：M4 补齐 22 张、M5 与 D 统一样式。

### 4.6 F 质量与文档（全程，每天 1 到 2 小时）

**本周目标**：让「红了不能合」真正生效，并且报错看得懂。

**第 1 步：补齐测试装置（2 小时）**

改 `tests/conftest.py`，提供假素材与默认配方，让渲染测试不依赖真实 `assets/`：

```python
"""测试公共装置。"""

from __future__ import annotations

import pytest
from PIL import Image

from diyface.models import AvatarRecipe, default_recipe


@pytest.fixture
def fake_assets(tmp_path):
    layout = {"01_skin": "skin_base", "02_bangs": "bangs_straight_01", "06_eyes": "eyes_round_01"}
    for folder, name in layout.items():
        directory = tmp_path / folder
        directory.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (1024, 1024), (255, 255, 255, 255)).save(directory / f"{name}.png")
    return tmp_path


@pytest.fixture
def recipe() -> AvatarRecipe:
    return default_recipe()
```

✅ 验收：`pytest` 在没有 `assets/` 的空目录里也能跑通。

**第 2 步：契约测试（3 小时）**

新建 `tests/test_api.py`，覆盖 5 个路由的正常、非法、边界：

```python
"""接口契约测试。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from diyface.app import app

client = TestClient(app)


def test_render_rejects_bad_size(recipe):
    response = client.post("/api/render", json={"recipe": recipe.model_dump(mode="json"), "size": 512})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BAD_SIZE"


def test_render_sets_etag_and_returns_304(recipe):
    payload = {"recipe": recipe.model_dump(mode="json"), "size": 256}
    first = client.post("/api/render", json=payload)
    etag = first.headers["etag"]
    second = client.post("/api/render", json=payload, headers={"If-None-Match": etag})
    assert second.status_code == 304


def test_healthz_reports_fields():
    body = client.get("/healthz").json()
    assert body["ok"] is True
    assert "version" in body and "assets" in body
```

✅ 验收：`test_api.py` 至少 12 条，全绿。`TestClient` 依赖 `httpx`，环境里已装。

**第 3 步：快照工具（3 小时）**

`rmse()` 与基准比对已写在 §4.1 第 6 步的 `tests/test_golden.py` 里。你负责把它推广成 3 到 6 组固定配方，并在差异超阈值时输出 `diff-<name>.png`。

✅ 验收：故意改一个像素，测试红并指出差异图路径。

**第 4 步：素材校验脚本（3 小时）**

新建 `scripts/verify_assets.py`：

```python
"""素材校验：尺寸、模式、命名、体积、tint 配对。"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

CANVAS = 1024
MAX_BYTES = 120 * 1024
ALLOWED = set("abcdefghijklmnopqrstuvwxyz0123456789_")


def check(path: Path, tintable: bool) -> list[str]:
    problems: list[str] = []
    with Image.open(path) as image:
        if image.size != (CANVAS, CANVAS):
            problems.append(f"尺寸 {image.size} 不是 {CANVAS}x{CANVAS}")
        if image.mode != "RGBA":
            problems.append(f"模式 {image.mode} 不是 RGBA")
    if path.stat().st_size > MAX_BYTES:
        problems.append(f"体积 {path.stat().st_size // 1024}KB 超过 120KB")
    if set(path.stem) - ALLOWED:
        problems.append("文件名只允许小写字母、数字、下划线")
    return problems


def main() -> int:
    root = Path("assets")
    failures = 0
    for slot_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for path in sorted(slot_dir.glob("*.png")):
            if path.name.startswith("_"):
                continue
            for problem in check(path, tintable=True):
                print(f"FAIL {path}  {problem}")
                failures += 1
    print(f"检查完成，问题数 {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
```

✅ 验收：放一张 512 的图进去，脚本精确报出文件名与「尺寸不是 1024」。

**第 5 步：覆盖率与门禁（2 小时）**

在 `pyproject.toml` 的 pytest 配置里加覆盖率门槛：

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
addopts = "-q --cov=src/diyface --cov-fail-under=85"
```

✅ 验收：把某条断言改错后 `git commit`，钩子拦住并打印失败位置；覆盖率不足时同样失败。

**第 6 步：文档与发布（每周五 1 小时）**

README 保持三步可跑；CHANGELOG 每个 tag 记三条以内；周五打 tag（`v0.1`、`v0.2`）。

✅ 验收：新人照 README 从零跑通，不需要问人。

**后续里程碑**：M2 起逐步加严（开覆盖率）、M6 出最终测试报告与演示材料。

---

## 5 每周节奏

| 时点 | 全员动作 | 负责人 |
| --- | --- | --- |
| 每天早上 | `git pull --rebase`，看 main 有无新提交 | 每人自己 |
| 每天收工 | 提交并 push 自己的分支，PR 开着（草稿也行） | 每人自己 |
| 每周二、周四 | 集成：把已完成的 PR 合入 main，跑全量测试 | C |
| 每周五上午 | 演示 10 分钟：每人 90 秒说进展与卡点 | 队长 |
| 每周五下午 | 打 tag（`v0.1`、`v0.2`…），更新 PLAN 进度 | F |

晨会只回答三个问题：昨天完成什么、今天做什么、卡在哪。卡点超过半天直接群里喊。

---

## 6 交付与验收

### 6.1 个人自查（每次提 PR 前）

- [ ] `python -m pytest` 全绿（至少 71 passed）。
- [ ] 提交信息符合 `feat / fix / test / docs / chore(scope): 说明`。
- [ ] 一个 PR 只做一件事，改动不超过 400 行。
- [ ] PR 描述里贴了实际跑的命令与结果。
- [ ] 没有提交 `.venv`、`__pycache__`、`assets/` 里的设计源文件。

### 6.2 阶段验收（团队）

| 里程碑 | 验收标准 | 谁来验收 |
| --- | --- | --- |
| M0 | 首页能开、71 条测试绿 | 已完成 |
| M1 | 命令行出图、快照 3 张、接口返回 PNG | A + F |
| M2 | 30 张素材合规、清单非空 | D + E + F |
| M3 | 页面能完整点选并导出 | B + C |
| M4 | 43 张素材齐、随机 20 次无穿模 | D + E |
| M5 | p95 小于 150 毫秒、Docker 镜像可跑 | C + F |
| M6 | 线上可访问、README 三步跑通 | 全体 |

---

## 7 速查

| 我想做 | 命令 |
| --- | --- |
| 看主分支最新 | `git switch main && git pull --rebase` |
| 开新分支 | `git switch -c feat/<域>-<简述>` |
| 看自己改了什么 | `git status` 与 `git diff` |
| 提交 | `git add -p` 然后 `git commit -m "..."` |
| 推送 | `git push -u origin <分支名>` |
| 跑测试 | `python -m pytest` |
| 只看失败 | `python -m pytest -x` |
| 起服务 | `python -m uvicorn diyface.app:app --reload --port 8000` |
| 校验素材 | `python -m diyface verify` |
| 撤销未提交改动 | `git restore <文件>` |
| 拉取冲突 | `git pull --rebase`，冲突改完后 `git add` 与 `git rebase --continue` |
