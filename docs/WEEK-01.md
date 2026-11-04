# 第 1 周任务清单（11-02 周一 ~ 11-08 周日）

给六个人的手把手版：每天做什么、代码贴在哪、怎么验证、提交写什么。
配套阅读：[新人上手](ONBOARDING.md)（原理）与 [交接简报](AGENT-BRIEF.md)（约定）。

本周结束时 `main` 上应该有：**能点的页面 + 30 张合规素材 + 能拦住坏素材的校验工具**，并打 `v0.2`。

---

## 0 一周总览

| 谁 | 周一 | 周二 | 周三 | 周四 | 周五 |
| --- | --- | --- | --- | --- | --- |
| A 渲染 | verify 规则 | verify 测试 | build-thumbs | 性能基线 | 支援 review |
| B 前端 | 三栏骨架 | 类目与素材格 | 预览与取色 | 下载与分享 | 移动端联调 |
| C 接口 | cache | cache 联调 | Docker | 一键门禁 | 演练部署 |
| D 素材 | 3 张试作 | 发型 8 张 | 眼睛 8 张 | 修校验问题 | 交叉验收 |
| E 素材 | 脸型 2 张 | 嘴 7 张 | 眼镜 5 张 | 缩略图 | 交叉验收 |
| F 质量 | 划边界 | 契约测试 | 覆盖率 | README | tag 与报告 |

**每周节奏**：早上 `git pull --rebase` → 做当天任务 → 收工前提交并 push → 群里一句「今天到哪了」。

---

## 1 周一早上：全员 30 分钟

### 1.1 拉代码并确认基线

```powershell
cd D:\头像diy
git switch main
git pull --rebase
python -m pytest
```

必须看到 `... passed, 11 skipped` 且没有 failed（刚拉下来的基线是 178 passed，随着测试增加这个数字会变大）。有 failed 就先别改任何文件，在群里问一句。

### 1.2 建自己的分支

```powershell
git switch -c feat/<你的字母>-w1
```

例如 A 用 `feat/a-w1`，B 用 `feat/b-w1`。本周所有提交都推到这条分支上，周五统一提 PR。

### 1.3 三条铁律（本周会因为违反它们返工）

1. **提交前跑 `python -m pytest`**，红了不提交。
2. **一次提交只做一件事**，提交信息写清做了什么。
3. **不要改别人负责的文件**（分工见 §3 每节标题下的「你的文件」）。

### 1.4 每天同步环境（PowerShell 版）

**每天开工前、每次 `git pull` 之后、每次合完别人的 PR 之后，都按这个顺序做一遍。**
不做同步就去改代码，最常见的后果是：改的是旧版本、提交时冲突一堆、跑出来的测试和队友对不上。

```powershell
cd D:\头像diy

# 1) 先回主分支拿最新代码
git switch main
git fetch gitee
git pull --rebase

# 2) 回到自己的分支，并把 main 的新提交垫到自己下面
git switch feat/<你的字母>-w1
git rebase main

# 3) 激活虚拟环境：提示符前面出现 (.venv) 才算成功
.venv\Scripts\Activate.ps1

# 4) 依赖有变化时才需要（见下面判断方法）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e ".[dev]"

# 5) 别人交了新素材时才需要
python -m diyface build-thumbs

# 6) 跑测试，确认环境是干净的
python -m pytest
```

**怎么判断要不要做第 4 步**：看第 1 步 `git pull` 的输出里有没有出现 `pyproject.toml`。有就装，没有就跳过（装一次要几十秒，没必要天天装）。

**怎么判断要不要做第 5 步**：看 `git pull` 的输出里有没有 `assets/` 下的 `.png`。有就重建，没有就跳过。

**收工前再跑一遍第 3、6 步**，确保你提交的代码在干净环境里也是绿的。

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 提示符前没有 `(.venv)` | 虚拟环境没激活 | 重新跑 `.venv\Scripts\Activate.ps1` |
| `No module named diyface` | 没装成本地包 | `pip install -e ".[dev]"` |
| `No module named pytest` | 装到了别的解释器 | 先激活 `.venv`，再 `pip install pytest` |
| 改了代码页面没变 | uvicorn 没开 `--reload`，或浏览器缓存 | 重启服务，`Ctrl + F5` 硬刷新 |
| 素材图 404 | 缩略图没生成 | `python -m diyface build-thumbs` |
| 测试数量和群里对不上 | 没 `git pull`，或没 rebase main | 回到 §1.4 第 1、2 步重做 |

---

## 2 A：渲染内核 —— 把「能出图」升级成「能自检」

**你的文件**：`src/diyface/validate.py`（新建）、`thumbs.py`（新建）、`__main__.py`、`tests/test_validate.py`（新建）、`tests/test_thumbs.py`（新建）

**本周交付**：`python -m diyface verify` 能报出体积/tint/命名问题；`python -m diyface build-thumbs` 能生成缩略图。
**验收**：放一张 512 的图与一张缺 `_tint.png` 的图，`verify` 两条都能精确报出文件名。

### 2.1 周一：把校验规则抽出来（约 3 小时）

现在 `catalog.scan()` 里只查了尺寸、模式、文件名。体积、透明区、tint 配对都还没有。

新建 `src/diyface/validate.py`：

```python
"""素材合规校验：一条规则一段逻辑，便于单独测试与复用。"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

CANVAS = 1024
MAX_BYTES = 120 * 1024
_NAME = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*")


def validate_asset(path: Path, *, tintable: bool = True) -> list[str]:
    """返回这张图的所有问题；空列表表示合规。"""
    problems: list[str] = []

    if not _NAME.fullmatch(path.stem):
        problems.append("文件名只允许小写字母、数字与下划线")

    if path.stat().st_size > MAX_BYTES:
        problems.append(f"体积 {path.stat().st_size // 1024}KB 超过 120KB")

    try:
        with Image.open(path) as image:
            if image.size != (CANVAS, CANVAS):
                problems.append(f"尺寸 {image.size} 不是 {CANVAS}x{CANVAS}")
            if image.mode != "RGBA":
                problems.append(f"模式 {image.mode} 不是 RGBA")
            else:
                low, high = image.getchannel("A").getextrema()
                if low != 0:
                    problems.append("没有任何透明像素，叠图时会盖住下层")
                if high != 255:
                    problems.append("没有任何不透明像素，等于一张空图")
    except OSError as exc:
        problems.append(f"打不开图片：{exc}")

    if tintable and not path.with_name(f"{path.stem}_tint.png").exists():
        problems.append("可着色素材缺少同名 _tint.png 蒙版")

    return problems
```

然后在 `__main__.py` 的 `cmd_verify` 里用它：

```python
from .models import SLOTS, AvatarRecipe
from .validate import validate_asset

# cmd_verify 里，把原来的打印改成逐张校验
def cmd_verify(args: argparse.Namespace) -> int:
    catalog = scan(args.root)
    failures = 0
    total = 0
    for slot in SLOTS:
        if args.slot and slot.id.value != args.slot:
            continue
        for asset in catalog.get(slot.id, []):
            total += 1
            for problem in validate_asset(asset.path, tintable=slot.tintable):
                print(f"FAIL {asset.path}  {problem}")
                failures += 1
    print(f"检查 {total} 张，问题 {failures} 个")
    return 1 if failures else 0
```

**完成标志**：

```powershell
python -m diyface verify
```

占位图已经带蒙版，所以应该看到 `问题 0 个`。想确认规则真的会拦人，临时删掉一张蒙版的副本再跑，或直接跑 `pytest tests/test_validate.py`。

**提交**：`feat(verify): 抽出素材校验规则，补体积与 tint 检查`

### 2.2 周二：给规则写测试（约 3 小时）

新建 `tests/test_validate.py`，每条规则一个用例。用 `tests/helpers.write_png` 造图：

```python
"""素材校验规则的测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from diyface.validate import validate_asset
from tests.helpers import write_png


def make(tmp_path: Path, name: str = "bangs_straight_01", **kwargs) -> Path:
    return write_png(tmp_path / "02_bangs" / f"{name}.png", **kwargs)


@pytest.fixture
def workdir_local(tmp_path: Path) -> Path:
    return tmp_path


def test_good_asset_has_no_problem(workdir_local: Path) -> None:
    path = make(workdir_local, bbox=(400, 200, 624, 400))
    path.with_name(f"{path.stem}_tint.png").write_bytes(path.read_bytes())

    assert validate_asset(path) == []


def test_wrong_size_is_reported(workdir_local: Path) -> None:
    path = make(workdir_local, size=(512, 512), bbox=(10, 10, 20, 20))

    assert any("尺寸" in problem for problem in validate_asset(path, tintable=False))


def test_missing_tint_is_reported(workdir_local: Path) -> None:
    path = make(workdir_local, bbox=(400, 200, 624, 400))

    assert any("_tint" in problem for problem in validate_asset(path))


def test_fully_opaque_is_reported(workdir_local: Path) -> None:
    path = make(workdir_local, bbox=None, color=(255, 255, 255, 255))

    assert any("透明" in problem for problem in validate_asset(path, tintable=False))
```

**完成标志**：`python -m pytest tests/test_validate.py -q` 全绿。

**提交**：`test(verify): 覆盖尺寸、体积、tint、透明度四类规则`

### 2.3 周三：缩略图生成（约 3 小时）

前端素材格有几十张图，直接加载 1024 的会卡。新建 `src/diyface/thumbs.py`：

```python
"""批量生成 256 缩略图，供前端素材格使用。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from .catalog import scan

THUMB = 256


def thumb_path(source: Path) -> Path:
    """缩略图放在同目录的 _thumb/ 下，下划线开头不会被扫描进清单。"""
    return source.parent / "_thumb" / f"{source.stem}_{THUMB}.png"


def build_thumbs(root: Path, slot: str | None = None) -> int:
    count = 0
    for slot_id, assets in scan(root).items():
        if slot and slot_id.value != slot:
            continue
        for asset in assets:
            target = thumb_path(asset.path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(asset.path) as image:
                image.resize((THUMB, THUMB), Image.LANCZOS).save(target, optimize=True)
            count += 1
    return count


def stale_thumbs(root: Path) -> list[Path]:
    """返回缺失或比源文件旧的缩略图。"""
    stale: list[Path] = []
    for assets in scan(root).values():
        for asset in assets:
            target = thumb_path(asset.path)
            if not target.exists() or target.stat().st_mtime < asset.path.stat().st_mtime:
                stale.append(target)
    return stale
```

CLI 里注册子命令：

```python
    thumbs_cmd = sub.add_parser("build-thumbs", help="生成 256 缩略图")
    thumbs_cmd.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    thumbs_cmd.add_argument("--slot", choices=[slot.id.value for slot in SLOTS], default=None)
    thumbs_cmd.add_argument("--check", action="store_true", help="只检查是否过期，不写文件")
```

```python
def cmd_build_thumbs(args: argparse.Namespace) -> int:
    if args.check:
        stale = stale_thumbs(args.root)
        for path in stale:
            print(f"过期 {path}")
        print(f"过期 {len(stale)} 张")
        return 1 if stale else 0
    count = build_thumbs(args.root, args.slot)
    print(f"已生成 {count} 张缩略图")
    return 0
```

**完成标志**：

```powershell
python -m diyface build-thumbs
python -m diyface build-thumbs --check
```

第一次生成 3 张，`--check` 返回 0。

**提交**：`feat(thumbs): 批量生成 256 缩略图并支持过期检查`

### 2.4 周四：性能基线（约 2 小时）

新建 `scripts/bench_render.py`，只为留下一个可比对的数字：

```python
"""渲染耗时基线：python scripts/bench_render.py"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from diyface.catalog import index, scan            # noqa: E402
from diyface.models import AvatarRecipe            # noqa: E402
from diyface.render import render                  # noqa: E402


def main() -> None:
    root = Path("assets")
    catalog = index(scan(root))
    recipe = AvatarRecipe.model_validate_json(
        Path("tests/fixtures/recipes/base.json").read_text(encoding="utf-8")
    )
    for size in (256, 1024):
        samples = []
        for _ in range(10):
            start = time.perf_counter()
            render(recipe, catalog, size)
            samples.append((time.perf_counter() - start) * 1000)
        print(f"{size:4d} 像素  中位 {statistics.median(samples):6.1f} ms  最慢 {max(samples):6.1f} ms")


if __name__ == "__main__":
    main()
```

**完成标志**：跑出两行数字，记进 PR 描述（M5 优化时对比用）。当前基线（3 层占位素材）：256 px 中位约 35 ms，1024 px 约 44 ms；素材到 43 张后会变慢，届时以新数字为准。

**提交**：`chore(bench): 加渲染耗时基线脚本`

### 2.5 周五：支援与 review（约 2 小时）

- 帮 D/E 跑 `verify`，把报错解释给他们听（多半是缺 `_tint.png` 或没留透明区）。
- 看 B 的 PR：重点确认没有在前端重复实现渲染逻辑。
- 把本周 verify 的规则补进 `docs/ONBOARDING.md` §4.4 第 6 步（两边说法要一致）。

---

## 3 B：前端 —— 从静态页到能点

**你的文件**：`src/diyface/templates/index.html`、`src/diyface/static/style.css`、`src/diyface/static/app.js`（新建）

**本周交付**：能选素材、能换色、能随机、能下载 256/1024、能分享链接。
**验收**：375 像素宽不横向滚动；连点 10 次只显示最后一个；下载的 1024 PNG 四角透明。

### 3.1 周一：三栏骨架（约 3 小时）

把 `templates/index.html` 整个换成下面这版（注意 id 要与后面 JS 对上）：

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>DIY 头像生成器</title>
    <link rel="stylesheet" href="/static/style.css">
  </head>
  <body>
    <header class="masthead">
      <h1>DIY 头像生成器</h1>
      <div class="actions">
        <button id="random" type="button">随机</button>
        <button type="button" data-size="256">下载 256</button>
        <button type="button" data-size="1024">下载 1024</button>
        <button id="share" type="button">复制链接</button>
      </div>
    </header>

    <main class="layout">
      <aside class="categories" id="categories" aria-label="类目"></aside>
      <section class="stage">
        <img id="preview" width="256" height="256" alt="头像预览">
      </section>
      <aside class="controls">
        <label for="color">颜色</label>
        <input id="color" type="color" value="#3B2B23">
        <p class="hint" id="hint">先选一个类目</p>
      </aside>
    </main>

    <section class="assets" id="assets" aria-label="素材"></section>
    <div class="toast" id="toast" role="status" aria-live="polite"></div>

    <script type="module" src="/static/app.js"></script>
  </body>
</html>
```

`static/style.css` 里把网格加进去（其余样式保留你喜欢的）：

```css
.layout {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) 220px;
  gap: 16px;
  align-items: start;
}

.stage {
  display: grid;
  place-items: center;
  aspect-ratio: 1 / 1;
}

#preview {
  width: min(100%, 320px);
  height: auto;
  image-rendering: auto;
}

.assets button {
  width: 64px;
  height: 64px;
  min-width: 44px;
  min-height: 44px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

@media (max-width: 720px) {
  .layout { grid-template-columns: 1fr; }
  .assets { display: flex; overflow-x: auto; gap: 8px; }
}
```

**完成标志**：桌面三栏；375 像素宽时竖排且无横向滚动条。

**提交**：`feat(ui): 三栏骨架与响应式布局`

### 3.2 周二：用清单点亮界面（约 3 小时）

新建 `static/app.js`（这一版还不接渲染，先让界面能点）：

```javascript
const state = {
  manifest: null,
  recipe: null,
  slot: "bangs",
  seq: 0,
};

const preview = document.getElementById("preview");
const hint = document.getElementById("hint");

async function boot() {
  const shared = new URLSearchParams(location.search).get("r");
  state.manifest = await (await fetch("/api/manifest")).json();
  state.recipe = shared ? decodeRecipe(shared) : state.manifest.default_recipe;

  buildCategories();
  selectSlot(state.manifest.slots[0]?.id ?? "bangs");
  refreshPreview();
}

function buildCategories() {
  const box = document.getElementById("categories");
  box.replaceChildren(
    ...state.manifest.slots.map((slot) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = slot.label.zh;          // 直接用后端给的中文名
      button.dataset.slot = slot.id;
      button.addEventListener("click", () => selectSlot(slot.id));
      return button;
    })
  );
}

function selectSlot(slotId) {
  state.slot = slotId;
  const slot = state.manifest.slots.find((item) => item.id === slotId);
  if (!slot) return;
  hint.textContent = `${slot.label.zh}：${slot.assets.length} 张`;

  const box = document.getElementById("assets");
  const noneButton = document.createElement("button");
  noneButton.type = "button";
  noneButton.textContent = "无";
  noneButton.setAttribute("aria-label", `${slot.label.zh}：不选`);
  noneButton.addEventListener("click", () => setAsset(slotId, null));

  const assetButtons = slot.assets.map((asset) => {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-label", `${slot.label.zh}：${asset.id}`);
    button.style.backgroundImage = `url(/assets/${asset.file})`;
    button.addEventListener("click", () => setAsset(slotId, asset.id));
    return button;
  });

  box.replaceChildren(noneButton, ...assetButtons);

  const colorInput = document.getElementById("color");
  colorInput.disabled = !slot.tintable;
  colorInput.value = state.recipe.colors[slot.id] ?? slot.default_color;
}

function setAsset(slotId, assetId) {
  state.recipe.slots[slotId] = assetId;
  refreshPreview();
}

boot();
```

**完成标志**：三个类目（脸型/发型/眼睛）能点，素材格出现缩略图，点「无」后高亮消失（预览要到下一步才变）。

**提交**：`feat(ui): 用清单渲染类目与素材格`

### 3.3 周三：预览与取色（约 3 小时）

在 `app.js` 末尾加上真正的预览逻辑（**去抖 + 序号**是重点）：

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
      toast("渲染失败，请稍后再试");
      return;
    }
    if (mine !== state.seq) return;                // 丢弃过期响应
    const url = URL.createObjectURL(await response.blob());
    preview.src = url;
    localStorage.setItem("diyface.recipe.v1", JSON.stringify(state.recipe));
  }, 120);
}

document.getElementById("color").addEventListener("input", (event) => {
  const slot = state.manifest.slots.find((item) => item.id === state.slot);
  if (!slot || !slot.tintable) return;
  state.recipe.colors[state.slot] = event.target.value.toUpperCase();
  refreshPreview();
});

function toast(message) {
  const box = document.getElementById("toast");
  box.textContent = message;
  box.classList.add("show");
  setTimeout(() => box.classList.remove("show"), 2000);
}
```

**完成标志**：点素材后预览在 200ms 内变化；连点 10 次最终显示最后一个；换发色只影响头发。

**提交**：`feat(ui): 预览去抖与取色`

### 3.4 周四：随机、下载、分享（约 3 小时）

```javascript
document.getElementById("random").addEventListener("click", async () => {
  const response = await fetch("/api/random", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  state.recipe = await response.json();
  selectSlot(state.slot);
  refreshPreview();
});

document.querySelectorAll("[data-size]").forEach((button) => {
  button.addEventListener("click", () => download(Number(button.dataset.size)));
});

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

document.getElementById("share").addEventListener("click", async () => {
  const url = `${location.origin}/?r=${encodeRecipe(state.recipe)}`;
  await navigator.clipboard.writeText(url);
  toast("链接已复制");
});

function encodeRecipe(recipe) {
  const json = JSON.stringify(recipe);
  return btoa(unescape(encodeURIComponent(json)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function decodeRecipe(token) {
  const base64 = token.replace(/-/g, "+").replace(/_/g, "/");
  return JSON.parse(decodeURIComponent(escape(atob(base64))));
}
```

**完成标志**：随机按钮能连续点，每次都换脸；下载的 1024 图四角透明；把分享链接贴到无痕窗口，脸与颜色一致。

**提交**：`feat(ui): 随机、下载与分享链接`

### 3.5 周五：移动端、键盘与联调（约 3 小时）

```javascript
document.addEventListener("keydown", (event) => {
  if (event.key === "r") document.getElementById("random").click();
  if (event.key === "s") download(1024);
});
```

CSS 补两条：触控目标 `min-width/height: 44px`，焦点可见 `:focus-visible { outline: 3px solid #4a6fa5; }`。

联调时重点看三个地方：

1. 渲染慢时有没有白屏（应该保留上一张直到新图到达）；
2. 接口返回 422 时有没有友好提示；
3. 窄屏下素材格能不能横滑。

**完成标志**：只用键盘能完成「选素材 → 换色 → 下载」；375 像素宽无横向滚动。

**提交**：`feat(ui): 移动端与键盘操作`

---

## 4 C：接口与部署 —— 让它能跑在服务器上

**你的文件**：`src/diyface/cache.py`（新建）、`app.py`、`Dockerfile`（新建）、`.dockerignore`（新建）、`scripts/check.ps1`（新建）

**本周交付**：缓存命中、镜像可跑、一键门禁。
**验收**：同配方第二次请求毫秒级；`docker run -p 8000:8000` 后首页与出图正常。

### 4.1 周一：渲染缓存（约 3 小时）

新建 `src/diyface/cache.py`：

```python
"""渲染结果缓存：键是规范化配方 JSON 加尺寸。"""

from __future__ import annotations

from functools import lru_cache

from .models import AvatarRecipe
from .render import render

#: 由 app 在启动时注入，避免 cache 反向依赖 app 造成循环导入。
CATALOG: dict = {}


def set_catalog(catalog: dict) -> None:
    global CATALOG
    CATALOG = catalog
    _render.cache_clear()


@lru_cache(maxsize=512)
def _render(recipe_json: str, size: int) -> bytes:
    recipe = AvatarRecipe.model_validate_json(recipe_json)
    return render(recipe, CATALOG, size)


def render_cached(recipe: AvatarRecipe, size: int) -> bytes:
    return _render(recipe.model_dump_json(), size)


def cache_info():
    return _render.cache_info()
```

改 `app.py` 两处：

```python
from .cache import render_cached, set_catalog


def load_catalog() -> dict:
    global CATALOG
    if not CATALOG:
        CATALOG = build_index(scan(ASSETS_DIR))
        set_catalog(CATALOG)
    return CATALOG
```

```python
    try:
        png = render_cached(payload.recipe, payload.size)   # 原来是 render(...)
```

**完成标志**：

```powershell
python -c "from diyface.app import load_catalog, render_cached; from diyface.models import AvatarRecipe; import pathlib,time; load_catalog(); r=AvatarRecipe.model_validate_json(pathlib.Path('tests/fixtures/recipes/base.json').read_text(encoding='utf-8')); t=time.perf_counter(); render_cached(r,256); print('first', time.perf_counter()-t); t=time.perf_counter(); render_cached(r,256); print('second', time.perf_counter()-t)"
```

第二次应该明显更快。

**提交**：`feat(cache): 按配方缓存渲染结果`

### 4.2 周二：缓存测试（约 2 小时）

新建 `tests/test_cache.py`，用 `monkeypatch` 数调用次数：

```python
"""缓存行为的测试。"""

from __future__ import annotations

from pathlib import Path

from diyface import cache
from diyface.catalog import index, scan
from diyface.models import AvatarRecipe


def test_second_call_hits_cache(monkeypatch) -> None:
    calls = {"n": 0}
    from diyface import render as render_module

    original = render_module.render

    def counting(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(render_module, "render", counting)
    cache.set_catalog(index(scan(Path("assets"))))
    recipe = AvatarRecipe.model_validate_json(
        Path("tests/fixtures/recipes/base.json").read_text(encoding="utf-8")
    )

    first = cache.render_cached(recipe, 256)
    second = cache.render_cached(recipe, 256)

    assert first == second
    assert calls["n"] == 1, "第二次应该命中缓存"


def test_changing_size_misses_cache() -> None:
    cache.set_catalog(index(scan(Path("assets"))))
    recipe = AvatarRecipe.model_validate_json(
        Path("tests/fixtures/recipes/base.json").read_text(encoding="utf-8")
    )

    assert cache.render_cached(recipe, 256) != cache.render_cached(recipe, 1024)
```

**完成标志**：`pytest tests/test_cache.py -q` 两条通过。

**提交**：`test(cache): 覆盖命中与换尺寸失效`

### 4.3 周三：容器化（约 3 小时）

新建 `Dockerfile`：

```dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir fastapi uvicorn jinja2 pillow pydantic

COPY src ./src
COPY assets ./assets

EXPOSE 8000
CMD ["uvicorn", "diyface.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

`.dockerignore`：

```
.venv
__pycache__
.pytest_cache
tests/reports
docs
tests
.git
```

**完成标志**：

```powershell
docker build -t diyface:dev .
docker run --rm -p 8000:8000 diyface:dev
```

浏览器打开 `127.0.0.1:8000` 能看到页面，`/healthz` 返回 JSON。

**提交**：`chore(docker): 加镜像与忽略文件`

### 4.4 周四：一键门禁（约 2 小时）

新建 `scripts/check.ps1`：

```powershell
# 本地门禁：提交或合并前跑一遍
$ErrorActionPreference = "Stop"

Write-Host "1/3 跑测试……"
python -m pytest
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "2/3 校验素材……"
python -m diyface verify
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "3/3 检查缩略图……"
python -m diyface build-thumbs --check
if ($LASTEXITCODE -ne 0) { Write-Host "提示：跑 python -m diyface build-thumbs 重建"; exit 1 }

Write-Host "全部通过"
```

**完成标志**：`.\scripts\check.ps1` 三步全过；把用法写进 README 的「跑测试」小节。

**提交**：`chore(ci): 加本地一键检查脚本`

### 4.5 周五：演练部署（约 3 小时）

- 把镜像在另一台机器（或清空缓存后）跑一次，确认不依赖本地产物。
- 把部署步骤写进 `docs/COLLABORATION.md`：怎么构建、怎么起、怎么更新。
- 记录一次 `/healthz` 输出作为验收证据。

**完成标志**：别人照着文档能起服务。

---

## 5 D：素材·头部 —— 本周 16 张（发型 8 + 眼睛 8）

**你的文件**：`assets/02_bangs/`、`assets/06_eyes/`

**本周交付**：16 张合规 PNG。
**验收**：`python -m diyface verify --slot bangs` 只剩「缺 tint」这类预期问题，尺寸/命名零错。

### 5.1 周一：参考线与 3 张试作（约 4 小时）

先建目录并生成参考图：

```powershell
mkdir assets/02_bangs, assets/06_eyes
python scripts/make_guide.py
```

`scripts/make_guide.py`（如果 A 还没建，你先建这个脚本，两个人共用）：

```python
"""生成 1024 画布的参考图：中线、脸中心、头顶基线。"""

from pathlib import Path

from PIL import Image, ImageDraw

CANVAS = 1024
GUIDE = Path("assets/_guide.png")


def main() -> None:
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.line([(512, 0), (512, CANVAS)], fill=(0, 160, 255, 120), width=2)      # 垂直中线
    draw.line([(0, 448), (CANVAS, 448)], fill=(255, 120, 0, 120), width=2)      # 脸中心
    draw.line([(0, 256), (CANVAS, 256)], fill=(0, 200, 120, 120), width=2)      # 头顶基线
    GUIDE.parent.mkdir(parents=True, exist_ok=True)
    image.save(GUIDE)
    print(f"已生成 {GUIDE}")


if __name__ == "__main__":
    main()
```

然后画 3 张：`bangs_straight_01`、`eyes_round_01`、`hat_beret_01`（帽子本周先不交，但画一张用来对位置）。

规则只有三条：

1. 画布 1024×1024、透明背景；
2. 头发压在 y=256 那条线上，眼睛围绕 (512, 448) 对称；
3. 可着色区域**用白色画**（换色时才不会发灰）。

**完成标志**：三张图交给 A，叠到脸型上不浮空。

**提交**：`feat(assets): 加 3 张试作与参考线脚本`

### 5.2 周二：发型补到 8 张（约 4 小时）

按清单画：直发、微卷、双马尾、齐刘海、碎发、短寸、丸子头、光头。

每画完 3 张就跑一次：

```powershell
python -m diyface verify --slot bangs
```

**完成标志**：8 张齐全，尺寸与命名零错。

**提交**：`feat(assets): 发型补齐 8 张`

### 5.3 周三：眼睛补到 8 张（约 4 小时）

圆、细长、笑、星星、眯、惊讶、睡眼、异色瞳。眼睛是**不可着色**槽位，颜色直接画死。

**完成标志**：8 张齐全；换发色时眼睛颜色不变。

**提交**：`feat(assets): 眼睛补齐 8 张`

### 5.4 周四：跑校验修问题（约 3 小时）

```powershell
python -m diyface verify
python -m diyface build-thumbs --slot eyes
```

把 `verify` 报的每一条都修掉；缺 `_tint.png` 的先补一张全白的蒙版（表示整层都可着色）：

```powershell
python -c "from PIL import Image; Image.new('RGBA',(1024,1024),(255,255,255,255)).save('assets/02_bangs/bangs_straight_01_tint.png')"
```

**完成标志**：`verify` 零报错（或只剩你能解释的项）。

**提交**：`fix(assets): 修素材校验问题并补 tint 蒙版`

### 5.5 周五：与 E 交叉验收（约 2 小时）

把 16 张套在 E 的两张脸型上逐张看，记录问题到群里。

**完成标志**：任意组合无露白、无穿模。

---

## 6 E：素材·面部 —— 本周 14 张（脸型 2 + 嘴 7 + 眼镜 5）

**你的文件**：`assets/01_skin/`、`assets/07_mouth/`、`assets/09_glasses/`

**本周交付**：14 张。
**验收**：两张脸型能托住 D 的 8 种发型。

### 6.1 周一：只做两张脸型（约 4 小时）

**这是全队的关键路径**：你不交脸型，D 的 8 张发型没法对位。

参考尺寸：脸宽约 520、高约 560，中心 (512, 448)，下巴 y≈728。

- `skin_base`：标准方圆脸，自带简化眉与鼻；
- `skin_slim`：略窄的瓜子脸。

画完立刻 push 并 @D：

```powershell
git add assets/01_skin
git commit -m "feat(assets): 两款脸型"
git push
```

**完成标志**：D 回复「脸型能用」。

### 6.2 周二：嘴 7 张（约 4 小时）

微笑、大笑露齿、小嘴、撇嘴、吐舌、猫嘴、无语。位置在脸中心下方约 90 像素，宽度不超过脸宽 40%。

**完成标志**：7 张嘴任意换，位置不飘。

**提交**：`feat(assets): 嘴部 7 张`

### 6.3 周三：眼镜 5 张（约 3 小时）

圆框、方框、墨镜、半框、护目镜。镜框中心对齐眼睛，鼻梁留 6 像素空隙。

**完成标志**：5 副都能压住眼睛、不遮眉。

**提交**：`feat(assets): 眼镜 5 张`

### 6.4 周四：缩略图与校验（约 2 小时）

```powershell
python -m diyface verify
python -m diyface build-thumbs
```

**完成标志**：`assets/*/_thumb/` 里出现 256 缩略图，`verify` 零报错。

### 6.5 周五：全开检查（约 2 小时）

把 14 张按「全开」模式铺满（每层都开），逐层开关，确认遮挡顺序正确：眼镜压眼睛、衣服接下巴。

**完成标志**：与 D 的素材任意组合无悬空。

---

## 7 F：质量与文档 —— 让门禁真的生效

**你的文件**：`pyproject.toml`、`tests/`、`CHANGELOG.md`（新建）、`README.md`

**本周交付**：覆盖率门槛、契约测试补齐、CHANGELOG、`v0.2` tag。
**验收**：写坏一个断言会被钩子拦住；覆盖率低于门槛时失败。

### 7.1 周一：和 A 划清边界（约 1 小时）

约定：**A 负责 `validate.py` 的规则与 `verify` 命令，你负责把它接进门禁、统计与文档**。
两个人不要同时改 `__main__.py`，要改先在群里说一句。

**完成标志**：群里有一条明确的约定消息。

### 7.2 周二：补契约测试（约 3 小时）

现有 `tests/test_api.py` 已覆盖渲染、304、随机。补这四类边界：

```python
def test_manifest_slots_are_z_sorted() -> None:
    data = http_client.call(app, "GET", "/api/manifest").json
    z_values = [slot["z"] for slot in data["slots"]]
    assert z_values == sorted(z_values)


def test_render_rejects_empty_body() -> None:
    response = http_client.call(app, "POST", "/api/render", json_body={})
    assert response.status == 422
    assert response.json["error"]["code"] == "INVALID_REQUEST"


def test_random_seed_can_be_replayed() -> None:
    first = http_client.call(app, "POST", "/api/random", json_body={"seed": 99}).json
    second = http_client.call(app, "POST", "/api/random", json_body={"seed": 99}).json
    assert first["slots"] == second["slots"]


def test_healthz_assets_count_matches_directory() -> None:
    from pathlib import Path

    count = len(list(Path("assets").rglob("*.png"))) - len(list(Path("assets").rglob("_*.png")))
    body = http_client.call(app, "GET", "/healthz").json
    assert body["assets"] == count
```

**完成标志**：`pytest tests/test_api.py -q` 全绿，条数 ≥ 15。

### 7.3 周三：开覆盖率门槛（约 3 小时）

先看当前基线：

```powershell
python -m pytest --cov=src/diyface --cov-report=term-missing
```

把结果记下来，再改 `pyproject.toml`：

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
addopts = "-q"
```

**先不要**把 `--cov-fail-under` 直接写进 `addopts`——那会让所有人的日常测试变慢。改成单独一条命令并写进文档与钩子：

```powershell
python -m pytest --cov=src/diyface --cov-report=term-missing --cov-fail-under=85
```

覆盖率不够就补测试，**不要删断言来凑数**。

**完成标志**：这条命令能跑过 85%；不足时明确列出缺覆盖的文件。

### 7.4 周四：README 与 CHANGELOG（约 2 小时）

新建 `CHANGELOG.md`：

```markdown
# 变更记录

## v0.2（2026-11-08）

- 新增：三栏界面、素材格、取色、随机、下载与分享
- 新增：`verify` 素材校验与 `build-thumbs` 缩略图
- 新增：渲染缓存与 Docker 镜像
- 素材：首批 30 张（脸型 2、发型 8、眼睛 8、嘴 7、眼镜 5）
```

README 补三段：截图、`python -m diyface verify`、`scripts/check.ps1`。

**完成标志**：新人照 README 从零跑通。

### 7.5 周五：打 tag 并出报告（约 2 小时）

```powershell
git switch main
git pull --rebase
python -m pytest
git tag -a v0.2 -m "第 1 周：界面可用、30 张素材、校验工具"
git push gitee v0.2
```

本周质量报告（发群里）：

```markdown
# 第 1 周质量报告

- 测试：N passed
- 覆盖率：N%
- 素材：30 张，verify 零报错
- 合并 PR：N 个
- 遗留问题：无
```

**完成标志**：tag 已推、报告已发。

---

## 8 周五验收（全员 30 分钟）

- [ ] `git switch main && git pull --rebase && python -m pytest` 全绿。
- [ ] 打开 `127.0.0.1:8000`：能选素材、换色、随机、下载 1024。
- [ ] `assets/` 里 30 张素材，`python -m diyface verify` 零报错。
- [ ] `python -m diyface build-thumbs` 能生成缩略图。
- [ ] `v0.2` tag 已推。
- [ ] 每人本周至少 3 个提交，且都在 `main` 上。

## 9 卡住了怎么办

| 现象 | 先做什么 | 还不行 |
| --- | --- | --- |
| `pytest` 红了但不是自己改的 | `git stash` 后重跑，确认是不是环境问题 | 群里 @ 对应模块负责人 |
| 改了代码但页面没变 | 确认 uvicorn 是 `--reload` 启动的 | 重启服务并硬刷新浏览器 |
| 素材 `verify` 报错看不懂 | 把整行报错贴到群里 | 拉 A 一起看 |
| 提交被钩子拦住 | 先看它打印的失败断言 | 修到绿，别用 `--no-verify` 绕过 |
| push 报 `non-fast-forward` | `git pull --rebase` 再推 | 冲突文件找原作者确认 |
| 接口 500 | 看 uvicorn 终端的堆栈 | 把堆栈贴给 C |

**每天收工前必做**：提交、push、群里报一句「今天完成了 X，卡在 Y」。

---

## 10 收工前 5 分钟（每天一次）

```powershell
cd D:\头像diy
git status                        # 1) 有没有漏提交的文件
git add -p                        # 2) 挑要提交的改动
git commit -m "feat(ui): 预览去抖与取色"
git push                          # 3) 推到自己的分支
```

然后做一遍环境同步（§1.4），最后确认这四件事：

- [ ] `git status` 里没有意外文件（`.venv`、`tests/reports/`、别人交的素材）。
- [ ] 激活 `.venv` 后 `python -m pytest` 全绿。
- [ ] `git push` 成功，分支在 Gitee 上能看到今天的新提交。
- [ ] 群里报了一句：今天完成什么、卡在哪、明天先做什么。

周五收工时多一步：把本周的提交整理成一条 PR（`feat/<你的字母>-w1` → `main`），
按 §8 的清单自检，然后 @ 一个人来审。
