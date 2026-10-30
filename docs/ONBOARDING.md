# 新人上手与六人分工执行方案

这份文档解决三件事：**怎么进仓库**、**怎么配环境**、**六个人各自一步一步怎么干**。
代码层面的完整代码在 [HANDBOOK.md](HANDBOOK.md)，这里给的是顺序、命令、验收标准。

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
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn jinja2 pillow pydantic pytest pytest-cov numpy

# 5) 开启提交门禁：以后每次 commit 自动跑测试
git config core.hooksPath .githooks

# 6) 验证
python -m pytest
```

### 2.3 macOS 逐步

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn jinja2 pillow pydantic pytest pytest-cov numpy
git config user.name "你的名字"
git config user.email "你的邮箱"
git config core.hooksPath .githooks
python -m pytest
```

### 2.4 什么叫「环境就绪」

三条命令都有预期输出才算完：

| 命令 | 期望 |
| --- | --- |
| `python --version` | `Python 3.11.x` 或更高 |
| `python -m pytest` | 最后一行 `71 passed, 11 skipped` |
| `python -m uvicorn diyface.app:app --port 8000` | 浏览器打开 127.0.0.1:8000 能看到「DIY 头像生成器」 |

11 条跳过是 Word 任务书的校验（没装 `python-docx`），属正常，不用处理。

### 2.5 一定会遇到的三类报错

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

每个人第一周只解决一件事：**让自己那一段链路先跑起来**。下面按角色给出逐步操作，每一步都写了「做什么、命令、怎么算完成」。

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

写 `src/diyface/catalog.py`：遍历 `models.SLOTS` 里的目录，收集 `*.png`，跳过下划线开头的文件（参考图、缩略图），校验尺寸 1024 与模式 RGBA，最后拼出 manifest。

✅ 验收：

```powershell
python -c "from pathlib import Path; from diyface.catalog import scan; print({k.value: [a.id for a in v] for k, v in scan(Path('assets')).items()})"
```

打印出 3 个槽位与之对应的素材 id。

**第 3 步：按 z 序叠图层（3 小时）**

写 `render.py` 的 `compose(recipe, catalog)`：从 `SLOTS_BY_Z` 取顺序，`recipe.slots.get(slot.id)` 为空就跳过，否则 `Image.alpha_composite` 叠上去。

两个细节必须做对：合成用 `alpha_composite`（不是 `paste`），缩放用 `LANCZOS`。

✅ 验收：写一个小脚本，把配方里 `hat` 设为 `None`，输出的 PNG 在帽子区域 alpha 必须为 0。

**第 4 步：颜色相乘（2 小时）**

写 `palettes.py` 的 `hex_to_rgb()` 与 `tint()`：把素材与纯色做 `ImageChops.multiply`，再恢复原 alpha。白色发丝会变成目标色，黑色描边仍然是黑。

✅ 验收：同一张刘海分别用 `#3B2B23` 与 `#C0392B` 出图，两次结果的描边像素完全一致。

**第 5 步：命令行出图（1.5 小时）**

写 `__main__.py`，支持 `render <recipe.json> --out <png>`：读配方 → 校验 → 调 `render()` → 写文件。

✅ 验收：`python -m diyface render recipe.json --out out.png` 能生成图片，用系统看图工具能打开。

**第 6 步：三张快照基线（2 小时）**

在 `tests/fixtures/recipes/` 放 3 份固定配方，第一次运行生成基准图存到 `tests/fixtures/golden/`，之后比对 RMSE 小于 1%。

✅ 验收：`python -m pytest tests/test_golden.py` 3 条通过；改坏一个像素会红。

**第 7 步：交接给 C（30 分钟）**

在 PR 描述里写清函数签名：`render(recipe, catalog, size) -> bytes`，并 @C 说明可以接 `/api/render` 了。

✅ 验收：C 能直接 `from diyface.render import render` 并在接口里调通。

**后续里程碑**：M2 配合 F 做素材校验、M5 做渲染性能（缓存与预热），其余时间支援 B 的预览问题。

### 4.2 B 前端交互（约 2.5 天）

**本周目标**：把 M0 的静态页换成能用真实清单点动的三栏界面。

**第 1 步：搭三栏骨架（3 小时）**

改 `templates/index.html` 与 `static/style.css`：`grid-template-columns: 240px 1fr 260px`，中间预览区 `aspect-ratio: 1 / 1`；720 像素以下改单列，类目变底部横滑。

✅ 验收：桌面三栏对齐；浏览器宽度拖到 375 像素，没有横向滚动条。

**第 2 步：用清单渲染类目与素材格（3 小时）**

`static/app.js` 里 `fetch('/api/manifest')`，用返回的 `slots` 生成左侧类目按钮；点某个类目，右侧素材格铺出该槽位的素材缩略图，外加一个「无」按钮表示置空。

✅ 验收：8 个类目都能点，点「无」后预览里的对应图层消失。

**第 3 步：接预览接口（3 小时）**

写 `refreshPreview()`：`setTimeout` 去抖 120 毫秒，请求带自增序号，响应回来时序号不是最新的就丢弃（防止连点闪回旧图）。

```javascript
let timer = null;
function refreshPreview() {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    const mine = ++state.seq;
    const res = await fetch("/api/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipe: state.recipe, size: 256 }),
    });
    if (mine !== state.seq) return;
    preview.src = URL.createObjectURL(await res.blob());
  }, 120);
}
```

✅ 验收：快速连点 10 个素材，最终显示的必须是最后点的那个，中间不闪。

**第 4 步：取色器与预设色板（2 小时）**

`<input type="color">` 的 `input` 事件里改 `recipe.colors[当前槽位]`，再调 `refreshPreview()`。预设色从 manifest 的 `default_color` 生成，不要在前端写死颜色。

✅ 验收：换发色只影响头发，脸和眼睛不变；切换素材后颜色保留。

**第 5 步：下载与分享（2 小时）**

下载：请求 `size: 1024`，把返回的 blob 挂到隐藏 `<a download>` 上点一下。
分享：把配方 JSON 转 base64url 拼到 `?r=`，页面加载时若存在就解码复现。

✅ 验收：下载的 PNG 是 1024×1024、四角透明；分享链接在无痕窗口打开与原件一致。

**第 6 步：移动端与键盘（2 小时）**

触控目标不小于 44 像素；所有素材按钮加 `aria-label`；`R` 随机、`S` 导出、方向键在素材格间移动。

✅ 验收：只用键盘能完成「选素材 → 换色 → 导出」全流程。

**第 7 步：与 C 联调（2 小时）**

接口从占位图切到真实渲染后，逐项过一遍：预览延迟、导出尺寸、错误提示（接口 500 时不要白屏，给一句「服务暂时不可用」）。

✅ 验收：连续操作 30 秒不出现白屏或错位。

**后续里程碑**：M3 完成正式 UI、M4 加素材后检查布局不崩、M6 加 SEO 静态页。

### 4.3 C 接口与部署（约 2 天）

**本周目标**：把 M0 的清单接口扩成能出图的完整接口，304 缓存生效。

**第 1 步：清单接上真实扫描（2 小时）**

`app.py` 里把 `build_manifest()` 换成调用 `catalog.scan()` 的结果，缓存到模块级变量（启动时算一次，别每个请求都扫盘）。

✅ 验收：`curl http://127.0.0.1:8000/api/manifest` 返回的 `slots[].assets` 不为空。

**第 2 步：接上渲染（2 小时）**

新增 `POST /api/render`：Pydantic 校验 `{recipe, size}`，`size` 只允许 256 或 1024，调用 A 的 `render()`，`Response(content, media_type="image/png")`。

✅ 验收：`curl -X POST` 拿到 PNG，用看图工具打开正常。

**第 3 步：ETag 与 304（1.5 小时）**

对 PNG 内容算 sha1，放进 `ETag` 头；请求带 `If-None-Match` 且相等时返回 304；成功的响应加 `Cache-Control: public, max-age=86400`。

✅ 验收：第二次请求带同样的 ETag，HTTP 状态码是 304，响应体为空。

**第 4 步：合法随机（2 小时）**

写 `randomizer.py`：必填槽位（脸、发型、眼、嘴）必选，可选槽位（眼镜、帽子、衣服、配饰）各有 35% 概率为空；颜色取各槽位默认值；最后写入 `seed` 保证可复现。

✅ 验收：连调 1000 次 `/api/random`，没有空脸、没有未知素材 id；同一 seed 两次结果一致。

**第 5 步：错误结构统一（1 小时）**

加一个异常处理器，把所有错误整理成 `{"error": {"code": ..., "message": ..., "field": ...}}`。非法 size 返回 422 且带 `code: BAD_SIZE`。

✅ 验收：`curl -X POST ... -d '{"size":512}'` 返回 422 与上面结构。

**第 6 步：健康检查（1 小时）**

`/healthz` 返回 `{ok, version, assets, commit}`，`commit` 可取环境变量，部署时注入。

✅ 验收：容器与本地都能访问 `/healthz` 且字段齐全。

**后续里程碑**：M5 做 Docker 镜像与缓存、M6 部署上线与日志。

### 4.4 D 素材·头部（约 1.5 天）

**本周目标**：先交 3 张跑通流程，再批量生产到 21 张。

**第 1 步：准备画布与参考线（1 小时）**

新建 1024×1024 透明画布，拉三条参考线：垂直中线 x=512、脸中心 y=448、头顶基线 y=256。存成 `assets/_guide.png`（下划线开头，不会被扫描进清单）。

✅ 验收：参考图存在但 `scan()` 结果里没有它。

**第 2 步：建目录与命名（15 分钟）**

```powershell
mkdir assets/02_bangs, assets/06_eyes, assets/10_hat
```

文件名格式 `<槽位>_<形状>_<两位序号>.png`，例如 `bangs_straight_01.png`。只允许小写字母、数字、下划线。

✅ 验收：`Get-ChildItem assets -Directory` 能看到三个槽位目录。

**第 3 步：画 3 张试作（3 小时）**

直发（`bangs_straight_01`）、圆眼（`eyes_round_01`）、贝雷帽（`hat_beret_01`）。重点不是好看，是**位置对**：头发压在头顶基线上、眼睛围绕脸中心对称、帽子盖住头发顶端。

✅ 验收：三张都 1024×1024、RGBA、1024 宽内不越界。

**第 4 步：让 A 叠出来看（1 小时）**

把三张图给 A，让他用渲染器叠到一张脸上。若出现「头发浮空」「帽子歪」，回画布改，不要指望渲染层补偿。

✅ 验收：A 出图后，头发贴头皮、帽子不遮眼。

**第 5 步：批量生产到 21 张（8 小时）**

发型 8 张（直发、微卷、双马尾、齐刘海、碎发、短寸、丸子头、光头）、眼睛 8 张（圆、细长、笑、星星、眯、惊讶、睡眼、异色瞳）、帽子 5 张（贝雷、鸭舌、毛线、兔耳、皇冠）。

节奏建议：每天 7 张，第三天收尾，留半天返工。

✅ 验收：`verify --all` 零报错；清单里能看到 21 个 id。

**第 6 步：跑校验与缩略图（1 小时）**

```powershell
python -m diyface verify --slot bangs
python -m diyface build-thumbs --slot bangs
```

✅ 验收：缩略图生成到 `_thumb/` 目录，前端素材格加载不卡。

**第 7 步：与 E 交叉验收（1 小时）**

把你的 21 张套在 E 的两张脸型上，逐张看有没有露白边；换 E 的眼镜、帽子检查遮挡顺序。

✅ 验收：任意组合都能叠出一张没有穿模的脸。

**后续里程碑**：M4 补齐到 21 张（若 M2 只交了 15 张），M5 视觉统一（描边粗细、配色）。

### 4.5 E 素材·面部与服饰（约 1.5 天）

**本周目标**：先把两张脸型画完（它决定其他所有层的基准），再补嘴、眼镜、衣服、配饰。

**第 1 步：画两款脸型（3 小时）**

`skin_base`（标准方圆脸，自带简化鼻与眉）与 `skin_slim`（略窄）。肤色不靠画，靠取色，所以脸型用白色底 + 灰阶阴影。

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

✅ 验收：随机 20 次无穿模；`verify --all` 零报错。

**后续里程碑**：M4 补齐 22 张、M5 与 D 统一样式。

### 4.6 F 质量与文档（全程，每天 1 到 2 小时）

**本周目标**：让「红了不能合」真正生效，并且报错看得懂。

**第 1 步：补齐测试装置（2 小时）**

`tests/conftest.py` 提供 `fake_assets`（临时目录 + 占位 PNG）与 `recipe`（默认配方）。所有渲染测试从这里取素材，不依赖真实 `assets/`。

✅ 验收：`pytest` 在没有 `assets/` 的空仓库里也能跑通。

**第 2 步：契约测试（3 小时）**

`tests/test_api.py` 覆盖 5 个路由：正常、参数非法、边界各一条。断言状态码、`ETag`、304、错误结构。

✅ 验收：`test_api.py` 至少 12 条，全绿。

**第 3 步：快照工具（3 小时）**

写 `rmse()` 与 `assert_snapshot()`：固定配方出图，与基准图比较，超过 1% 输出差异图到 `tests/reports/`。

✅ 验收：故意改一个像素，测试红并指出差异图路径。

**第 4 步：素材校验脚本（3 小时）**

`scripts/verify_assets.py` 检查六条：存在、1024 见方、RGBA、命名合规、体积小于 120KB、可着色素材有 `_tint.png`。输出必须能定位到具体文件与规则。

✅ 验收：放一张 512 的图进去，脚本精确报出文件名与「尺寸不是 1024」。

**第 5 步：覆盖率与门禁（2 小时）**

`pyproject.toml` 里配 `--cov-fail-under=85`；确认 `.githooks/pre-commit` 跑的是快测（单元 + 契约 + 文档），慢测留给合并前。

✅ 验收：把某条断言改错后 `git commit`，钩子拦住并打印失败位置。

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
| 撤销未提交改动 | `git restore <文件>` |
| 拉取冲突 | `git pull --rebase`，冲突改完后 `git add` 与 `git rebase --continue` |
