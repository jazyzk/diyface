# 方脸头像 DIY 生成器 —— 详细实施计划书

| 项 | 内容 |
| --- | --- |
| 项目代号 | `diyface`（工作目录 `D:\头像diy`） |
| 目标产品 | 对标 https://squarefacegenerator.app/ 的可分层拼装头像网页 |
| 文档版本 | v1.0 |
| 撰写日期 | 2026-10-28 |
| 主要实现语言 | Python 3.11+（本机 3.14.0，Pillow 12.3.0 已就绪） |
| 核心约束 | 每次改动建 commit；每次改动补测试且交付前全绿（见 `AGENTS.md`） |

## 0. 摘要（TL;DR）

对标站点本质是「分层贴图 + 实时合成 + 一键导出」的像素/扁平头像生成器：12 个类目、200+ 素材、HTML5 Canvas 实时预览、256×256 PNG 导出、随机按钮、全局免注册。它的技术难点不在算法，而在**素材量、图层秩序、颜色系统、移动端交互**四件事。

本项目按「**Python 为主、前端为壳**」落地：Python 负责素材编目、颜色映射、图层合成、随机约束、导出与质量校验；浏览器只做参数采集与展示。这样既满足“主要用 Python 实现”，又让最容易被写乱的部分（合成顺序、颜色、素材完整性）全部可被 pytest 覆盖。

工期估算：**开发 10 人日 + 素材美术 2～3 人日**（素材精简到 43 张，见 §2.3），分 7 个里程碑（M0–M6），每完成一个里程碑即一个可运行、测试全绿的 commit。

## 1. 对标产品拆解

| 维度 | 对标实现 | 我们的取舍 |
| --- | --- | --- |
| 类目 | Skin、Bangs、Side Hair、Eyes、Nose、Mouth、Eyebrows & Eyelashes、Cheeks & Wrinkles、Glasses、Hats、Clothes、Other，共 12 个 | 只启用 8 个（另 4 个保留枚举），不追求 12 类全覆盖 |
| 素材量 | 200+ 选项，号称百万级组合 | 首发 8 类共 43 个素材，形状组合约 77 万 |
| 渲染 | 浏览器 HTML5 Canvas 实时绘制 | Python/Pillow 服务端合成，客户端去抖请求 |
| 导出 | 256×256 PNG，无水印、免注册 | 256 预览 + 1024 高清导出，均 PNG 透明底 |
| 颜色 | 每个元素独立取色器，无限色彩 | 每槽位独立色板 + 自定义取色，颜色与形状解耦 |
| 随机 | 全局一键随机 | 带兼容规则的加权随机（避免「眼镜套帽子」等穿模） |
| 账号 | 无，全部本地完成，强调隐私 | 无账号；配方存 URL/本地，服务端不落盘用户图像 |
| 其他 | 8 语言、博客、评论区、SEO 落地页 | 首发 zh/en 双语；SEO 页面放 M6 视运营需要 |

关键洞察：**素材是瓶颈，不是代码**。代码骨架 2 天能跑通，成品观感却由分层 PNG 决定。为控制成本，v1 只画 43 张（每类 3～8 张），把「多样感」让给颜色：同一张刘海换 8 种发色，视觉差异不亚于多画 7 张。因此仍把素材规范与自动化校验前移到 M1/M2，先用脚本卡死规格，避免返工。

## 2. 目标与非目标

### 2.1 目标（本次范围）

1. 单页应用：左侧类目 → 中间预览 → 右侧颜色/随机/导出，移动端可用。
2. 分层合成正确：12 个槽位固定 z 序（v1 启用 8 个），素材可叠加、可置空。
3. 颜色系统：每个可着色槽位独立取色，带预设色板。
4. 导出：256×256 与 1024×1024 透明 PNG，文件名带时间戳。
5. 随机：一键生成合法组合，可连续点击。
6. 分享：配方编码进 URL，可复现同一张脸（`?r=<base64url>`）。
7. 质量门禁：素材校验、渲染快照、API 契约、E2E 四类测试全绿才可交付。

### 2.2 非目标（本期不做）

- 用户账号、云端相册、作品广场。
- AI 文生图 / 真人照片换脸（对标站点也没有，成本与合规风险高）。
- 在线素材编辑器（上传自己的素材）。
- 付费/水印/会员体系。
- 原生 App 与小程序。

### 2.3 精简素材预算（v1 定稿）

素材从「对标级 200+」压缩到 **共 43 个**，思路是**形状少而精、差异靠颜色**：每槽位 3～8 个选项就足以撑起百万级组合。

| 槽位 | 数量 | 内容 |
| --- | --- | --- |
| skin | 2 | 基础脸 + 窄脸，肤色完全靠取色 |
| bangs | 8 | 直发、卷发、双马尾、齐刘海、碎发、短寸、丸子头、光头 |
| eyes | 8 | 圆眼、细长、笑眼、星星眼、眯眼、惊讶、睡眼、异色瞳 |
| mouth | 7 | 微笑、大笑、小嘴、撇嘴、吐舌、猫嘴、无语 |
| glasses | 5 | 圆框、方框、墨镜、半框、护目镜 |
| hat | 5 | 贝雷帽、鸭舌帽、毛线帽、兔耳、皇冠 |
| clothes | 5 | 圆领、衬衫领、帽衫、背带、围巾 |
| extra | 3 | 耳环、创可贴、星星贴纸 |
| 合计 | 43 | 形状组合 2×8×8×7×6×6×6×4 ≈ 77 万，叠加上色后达亿级 |

四个槽位（`side_hair`、`brows`、`nose`、`cheeks`）**只保留枚举与 z 序，不产出素材**：脸型自带简化鼻与眉，前端按 manifest 自动隐藏空槽位；以后补料即上线，无需改代码。

取舍理由：

- 43 张能把单张的时间投入翻倍，对齐、描边、阴影更容易成套。
- 每张素材都可上色，颜色维度把一个槽位的 8 张扩成数十种观感。
- 素材少，`verify` 与快照基线更好维护，每加一张都能全量回归。

## 3. 技术选型

### 3.1 三个候选方案

| 方案 | 形态 | 优点 | 缺点 | 结论 |
| --- | --- | --- | --- | --- |
| A 服务端渲染 | FastAPI + Pillow 合成，前端薄壳 | Python 承担全部核心逻辑；合成结果可单测/快照；一套代码出多尺寸 | 每次改参数要网络往返，需缓存与去抖 | **推荐** |
| B 纯 Python 前端 | Streamlit 或 NiceGUI | 全 Python，无 JS | 布局与手势受限，难做出对标站点的精细交互；每次交互整页重跑 | 备选，仅用于内部素材预览工具 |
| C 客户端 Canvas | 原生 Canvas + Python 只做编目/构建 | 交互零延迟，与对标一致 | 核心合成逻辑落到 JS，“主要用 Python”不成立；颜色/顺序逻辑双份维护 | 作为 M5 的性能兜底 |

### 3.2 推荐栈

| 层 | 选型 | 理由 |
| --- | --- | --- |
| 运行时 | Python 3.11+ | 3.12 的 `typing` 与性能改进已够用；本机 3.14 可跑 |
| Web 框架 | FastAPI + Uvicorn | 自动 OpenAPI、Pydantic v2 校验、async 静态资源 |
| 图像 | Pillow 12 | 已装；RGBA 合成、`ImageOps.colorize`、PNG 优化齐全 |
| 模板 | Jinja2（服务端首屏） | 首屏直接出 HTML，SEO 与免 JS 降级友好 |
| 前端 | 原生 ES 模块 + CSS（无构建工具） | 单页需求，避免 Node 工具链；后续需要再上 Vite |
| 测试 | pytest + pytest-cov + numpy（像素比对） | 快照 diff 用 numpy 算 RMSE |
| 质量 | ruff + mypy（strict 于 `render/`） | 提交前统一风格与类型 |
| 打包 | Docker + uv（或 pip-tools 锁依赖） | 一键部署到 Fly.io / Render / 自有 VPS |
| CI | GitHub Actions | 三平台跑 lint + test + 素材校验 |

### 3.3 为什么不用前端 Canvas 做首发

对标站用 Canvas 是对的：素材全在前端，交互零延迟。但本项目要求 Python 为主，且**颜色合成规则**（乘色/替换/描边不变色）是最容易出错的部分，放服务端能用参数化测试和快照测试把它钉死。等 M5 若 p95 延迟 > 150ms，再用「Python 预编译图层图集 + OffscreenCanvas」做前端预热，合成规则仍由 Python 单测兜底。

## 4. 系统架构

```
浏览器
  │  GET /                        Jinja2 首屏（含 manifest 内联，省一次请求）
  │  POST /api/render  recipe     JSON → PNG（ETag 缓存）
  │  GET  /api/manifest          素材清单（构建期生成，带版本哈希）
  ▼
FastAPI（Python）
  ├─ app.py           路由、静态资源、错误边界
  ├─ models.py        AvatarRecipe / SlotId / ColorSpec（Pydantic v2）
  ├─ catalog.py       扫描 assets/，生成并校验 manifest.json
  ├─ render.py        Pillow 合成管线（纯函数，输入 recipe 输出 Image）
  ├─ palettes.py      颜色解析、乘色/替换、超界裁剪
  ├─ randomizer.py    兼容规则 + 加权随机
  └─ cache.py         LRU（内存）+ 可选磁盘缓存（导出图）
        │
        ▼
assets/  分层素材 1024×1024 RGBA + 每槽位 tint 蒙版
        │
        ▼
scripts/ build_thumbs.py（预生成 256 缩略图）、verify_assets.py（完整性门禁）
```

数据流：浏览器只持有 `recipe`（约 300 字节 JSON），图像永远由服务端按需合成，天然支持多端一致、可分享、可复现。

### 4.1 目录结构

```
头像diy/
├─ AGENTS.md
├─ README.md
├─ docs/PLAN.md                 本计划书
├─ pyproject.toml               ruff/mypy/pytest 配置与依赖
├─ src/diyface/
│  ├─ __init__.py
│  ├─ __main__.py               CLI：render / verify / build-thumbs
│  ├─ app.py                    FastAPI 应用
│  ├─ models.py                 Pydantic 模型
│  ├─ catalog.py                清单生成与校验
│  ├─ render.py                 合成管线
│  ├─ palettes.py               颜色
│  ├─ randomizer.py             随机
│  ├─ templates/index.html      Jinja2
│  └─ static/{app.js, style.css}
├─ assets/
│  ├─ 01_skin/…  02_bangs/…     8 个启用槽位目录（另 4 个预留）
│  └─ manifest.json             构建产物（可提交，便于 review 素材变更）
├─ scripts/{build_thumbs.py, verify_assets.py}
└─ tests/
   ├─ test_models.py
   ├─ test_catalog.py
   ├─ test_render.py
   ├─ test_palettes.py
   ├─ test_randomizer.py
   ├─ test_api.py
   ├─ test_golden.py
   ├─ test_docs.py              本文档的结构校验
   └─ fixtures/{recipes/*.json, golden/*.png}
```

## 5. 数据模型

### 5.1 配方（Recipe）

```python
class SlotId(StrEnum):
    SKIN = "skin"; BANGS = "bangs"; SIDE_HAIR = "side_hair"
    EYES = "eyes"; NOSE = "nose"; MOUTH = "mouth"
    BROWS = "brows"; CHEEKS = "cheeks"; GLASSES = "glasses"
    HAT = "hat"; CLOTHES = "clothes"; EXTRA = "extra"

class AvatarRecipe(BaseModel):
    version: int = 1
    slots: dict[SlotId, str | None]          # 槽位 → 素材 id（None = 不画）
    colors: dict[SlotId, str] = {}           # 槽位 → #RRGGBB
    seed: int | None = None                  # 随机来源，可复现

    model_config = ConfigDict(extra="forbid")  # 未知字段直接 422，防脏数据
```

要点：
- **槽位固定、素材可空**：`slots` 覆盖全部 12 个枚举键，缺键由 `default_recipe()` 补齐；4 个未启用槽位恒为 `None`，渲染层无需判空。
- **颜色与形状解耦**：颜色存槽位而非素材，换素材保留用户挑的颜色。
- **版本号**：`version` 为未来迁移留口；读到高版本降级为默认配方并给提示。
- **配方体积**：序列化后 < 400 字节，可安全放进 URL（base64url，压缩后约 180 字节）。

### 5.2 素材清单（manifest）

```json
{
  "schema": 1,
  "generated_from": "a3f9c1e",
  "slots": [
    {
      "id": "bangs",
      "label": {"zh": "刘海", "en": "Bangs"},
      "z": 30,
      "tintable": true,
      "default_color": "#3b2b23",
      "palette": ["#3b2b23", "#8a5a3b", "#e8c39e"],
      "assets": [
        {"id": "bangs_straight_01", "file": "01_bangs/bangs_straight_01.png",
         "thumb": "01_bangs/_thumb/bangs_straight_01_256.png", "tags": ["直发"]}
      ]
    }
  ]
}
```

清单由 `catalog.py` 扫目录自动生成，**不手写**；提交到仓库以便素材变更在 diff 中可见，并做 CI 一致性校验。

### 5.3 z 序（唯一真源）

| z | 槽位 | 说明 | v1 状态 |
| --- | --- | --- | --- |
| 10 | skin | 脸型底 | 启用 |
| 20 | cheeks | 腮红/皱纹，压在皮肤上、五官下 | 预留 |
| 30 | bangs | 刘海 | 启用 |
| 40 | side_hair | 鬓发，压住刘海边缘 | 预留 |
| 50 | brows | 眉/睫毛 | 预留 |
| 60 | eyes | 眼 | 启用 |
| 70 | nose | 鼻 | 预留 |
| 80 | mouth | 嘴 | 启用 |
| 90 | glasses | 眼镜（压五官） | 启用 |
| 100 | clothes | 衣领，压脖底 | 启用 |
| 110 | hat | 帽子，最上层压头发 | 启用 |
| 120 | extra | 耳饰/贴纸等兜底 | 启用 |

z 序只写在 `models.py` 一处常量，渲染、前端预览、文档三处引用同一份，禁止各写一份。

## 6. 素材规范与生产流程

### 6.1 规范（脚本强制校验）

| 项 | 要求 |
| --- | --- |
| 画布 | 1024×1024 PNG，RGBA，透明背景 |
| 对齐 | 所有层共用同一坐标系，脸中心固定在 (512, 448)，头顶基线 y=256 |
| 命名 | `<槽位>_<形状>_<序号>.png`，如 `eyes_round_02.png`；只允许 `[a-z0-9_]` |
| 着色 | 可着色素材另附 `_tint.png`（白=完全上色，黑=不上色）；不可着色素材 `tintable: false` |
| 描边 | 描边画在单独层或直接烘焙，禁止依赖缩放保边 |
| 体积 | 单文件 < 120 KB（1024 层），256 缩略 < 18 KB |
| 版权 | 每个素材目录放 `SOURCE.md` 记录来源与授权（自绘 / CC0 / 采购） |

### 6.2 生产流程

1. 在 1024 画布上按 6.1 画一层，导出 PNG。
2. `python -m diyface verify --slot bangs` 逐项检查尺寸、透明度、命名、体积、tint 蒙版配对。
3. `python -m diyface build-thumbs` 生成 256 缩略图（Lanczos），并刷新 `assets/manifest.json`。
4. 在 `/preview` 页面（内部用，`?all=1` 一次铺满当前槽位）肉眼过一遍，确认没有「浮空」「错位」。

### 6.3 素材来源建议

| 来源 | 成本 | 风险 | 建议 |
| --- | --- | --- | --- |
| 自绘（Aseprite/Krita） | 2～3 人日（43 张） | 无版权风险 | 首选，风格最统一 |
| CC0 素材包（Kenney 等） | 1 人日筛选 | 风格杂、需重绘对齐 | 仅用于早期占位 |
| AI 生成后人工修边 | 2～3 人日 | 一致性差、需要逐张对齐 | 只用于「其他」类目点缀 |
| 采购商用素材 | 视预算 | 授权条款需留存 | 有预算时的加速项 |

### 6.4 加料路径（预留槽位）

manifest 由目录扫描生成，新增 `09_...`、`10_...` 目录并跑 `build-thumbs` 后即自动出现在 UI，渲染代码零改动。因此「先上 8 类、后续补 4 类」是低成本路线，不是技术债。

## 7. 渲染管线

### 7.1 单次渲染步骤

1. **校验**：Pydantic 解析 recipe；未知槽位/未知素材 id → 404/422，前端降级为默认脸。
2. **取层**：按 z 升序取 `(素材图, 颜色, tint 蒙版)`；空槽位跳过。
3. **着色**：在 alpha 内做 `multiply`（或 `colorize` 保留明暗），未着色区域保持原样。
4. **合成**：`Image.alpha_composite` 逐层叠加到 1024 画布，最后 `resize(256, LANCZOS)` 出预览。
5. **编码**：`save(..., optimize=True, compress_level=6)`，ETag = sha1(recipe 规范化 JSON)。
6. **缓存**：进程内 LRU（默认 512 条，按 ETag），命中直接 304/200。

### 7.2 性能预算

| 场景 | 目标 p50 | 目标 p95 |
| --- | --- | --- |
| 256 预览（缓存未命中） | < 60 ms | < 150 ms |
| 256 预览（命中） | < 3 ms | < 10 ms |
| 1024 导出 | < 200 ms | < 400 ms |
| 首屏（HTML+清单内联） | < 250 ms | — |

前端交互策略：颜色拖动用 `input` 事件 + 120ms 去抖；点击缩略图立即请求并保留上一张直到新图到达（避免闪烁）。若 M5 实测不达标，启用方案 C 的前端预热。

## 8. API 契约

| 方法 | 路径 | 入参 | 出参 | 备注 |
| --- | --- | --- | --- | --- |
| GET | `/` | — | HTML | 内联 manifest，首屏无额外请求 |
| GET | `/api/manifest` | — | JSON | `Cache-Control: public, max-age=300` |
| POST | `/api/render` | `{recipe, size}` | `image/png` | `size ∈ {256,1024}`；带 `ETag` |
| GET | `/api/render` | `?r=<base64url>` | `image/png` | 分享链接专用，可被 CDN 缓存 |
| POST | `/api/random` | `{constraints?}` | `recipe` | 返回合法配方，不下发图片 |
| GET | `/api/recipe/default` | — | `recipe` | 首次进入的默认脸 |
| GET | `/healthz` | — | `{ok, version, assets}` | 部署探针，含素材哈希 |

约定：错误统一 `{"error": {"code": "...", "message": "...", "field": "..."}}`；`size` 非法一律 422；渲染失败返回 500 并记录 recipe 便于复现。

## 9. 前端方案

### 9.1 布局

- 桌面：三栏（左 280px 类目+素材 / 中自适应预览 / 右 240px 颜色与操作）。
- 移动：预览固定顶部（sticky），类目变底部横向 tab，素材横向滑动，颜色抽屉从底部弹出。
- 预览容器严格 1:1：`aspect-ratio: 1 / 1`，`image-rendering: pixelated` 只用于导出预览放大，不用于素材本身。

### 9.2 交互清单

1. 类目切换 → 该槽位素材九宫格（懒加载缩略图）。
2. 点素材 → 立即应用；点「无」→ 置空该槽位。
3. 颜色：预设色 6～8 个 + 原生 `<input type="color">`；实时预览去抖 120ms。
4. 随机：调用 `/api/random`，300ms 内可连点，带轻微缩放动画。
5. 导出：256/1024 两个按钮，下载名 `avatar-<yyyymmdd-hhmmss>.png`。
6. 分享：复制带 `?r=` 的链接，成功给 toast。
7. 键盘：`R` 随机、`S` 导出、方向键在素材格间移动，全部控件可 Tab 到达。
8. 无障碍：每个素材按钮有 `aria-label`（如「刘海：直发 01」），色板有对比度检查。

### 9.3 状态管理

单一 `state = {recipe, size, dirty}`；渲染请求带序号，只应用最新序号响应（防竞态）。localStorage 持久化 recipe（键 `diyface.recipe.v1`），刷新不丢。

## 10. 测试与质量门禁（对应 AGENTS.md）

### 10.1 测试金字塔

| 层 | 文件 | 覆盖内容 | 数量目标 |
| --- | --- | --- | --- |
| 单元 | `test_models.py` | 配方默认值、未知字段拒绝、版本降级、URL 编解码往返 | 12～15 |
| 单元 | `test_palettes.py` | 颜色解析（#RGB/#RRGGBB/非法）、乘色公式、边界裁剪 | 10 |
| 单元 | `test_catalog.py` | 目录→清单一致性、命名规范、z 序唯一、素材缺失报错 | 10～12 |
| 单元 | `test_randomizer.py` | 兼容规则（帽子与帽子不共存）、加权分布、seed 可复现 | 8 |
| 快照 | `test_golden.py` | 固定配方 → 与 `fixtures/golden/*.png` 比对，RMSE < 1% | 6～10 张 |
| 契约 | `test_api.py` | 各端点状态码、ETag/304、422 分支、健康检查 | 12 |
| 素材 | `test_assets.py` | 全部素材尺寸/模式/透明度/体积/tint 配对 | 动态 |
| E2E | `tests/e2e/` | 选素材→导出→校验 PNG 尺寸；移动视口截图 | 4～5 条 |
| 文档 | `test_docs.py` | 章节齐全、表格列数一致、预算合计正确、12 槽位覆盖 | 10 |
| 性能 | `test_perf.py` | 256 预览 p95 阈值（标记 `slow`，CI 定时跑） | 2 |

### 10.2 快照测试做法

- 固定 `seed` 与 `Pillow` 版本；`pytest --snapshot-update` 才允许写新基准，其余情况只读。
- 比对用 numpy：`rmse = sqrt(mean((a-b)^2))`，阈值 1%（约 2.55/255），超阈值输出 diff 图到 `tests/reports/`。
- 形状类改动必然改快照，PR 必须同时说明「为什么这张图应该变」。

### 10.3 门禁顺序（每次提交前）

```
ruff check . && ruff format --check .
mypy src
python -m pytest -q --cov=src/diyface --cov-fail-under=85
python -m diyface verify --all        # 素材完整性
python -m diyface build-thumbs --check # 缩略图与清单是否过期
```

CI 在 push 与 PR 上跑同一组命令；任一失败即阻断合并。快慢分层：快测（单元+契约）< 15s，慢测（快照+E2E+性能）在 PR 上跑。

### 10.4 与 AGENTS.md 的对应

| 约定 | 落地方式 |
| --- | --- |
| 每次改动建 commit | 里程碑内按「一个可验证单元」提交；`pre-commit` 钩子跑快测，失败即拒绝提交 |
| 每次改动补测试 | 功能 PR 必须带测试用例；纯文档改动由 `test_docs.py` 校验文档结构；纯素材改动由 `verify --all` 校验 |
| 交付前测试全绿 | 交付清单见 §14，命令必须原样可复现 |

## 11. 里程碑排期

| 里程碑 | 内容 | 交付物 | 验收标准 | 工时 |
| --- | --- | --- | --- | --- |
| M0 骨架 | 仓库结构、pyproject、FastAPI hello、Jinja2 空页、CI、pre-commit | 能 `uvicorn` 起首页 | `pytest` 有 3 条冒烟测试且绿；CI 通过 | 0.5 天 |
| M1 渲染内核 | models/render/palettes/catalog + CLI | `python -m diyface render r.json out.png` 出图 | 单元测试 + 3 张快照绿；未知素材降级正确 | 2 天 |
| M2 素材管线 | 素材规范、`verify`、`build-thumbs`、首批 5 类共 30 张 | 30 个合规素材 + 清单 | `verify --all` 全绿；缩略图与清单不漂移 | 1.5 天 + 美术 |
| M3 Web UI | 三栏布局、素材格、颜色、随机、下载、分享、移动端 | 可用的单页产品 | E2E 5 条通过；Lighthouse 性能 ≥ 90 | 2.5 天 |
| M4 补齐素材 | 加 hat/clothes/extra 共 13 张、z 序终稿、兼容规则 | 8 类共 43 张 | 形状组合 ≥ 70 万；随机无穿模 | 1 天 + 美术 |
| M5 打磨与性能 | 缓存、压缩、OG 分享图、i18n(zh/en)、错误边界、Docker | 可部署镜像 | p95 < 150ms；断网/超时有友好降级 | 1.5 天 |
| M6 上线 | 部署、日志指标、SEO 静态页、隐私说明、README | 线上可用 | 探针、错误率、真实设备抽查通过 | 1 天 |

合计约 **10 人日**（不含美术 2～3 天），建议按 2.5 周排：第 1 周 M0–M2，第 2 周 M3–M4，第 3 周前半 M5–M6 与缓冲。

```
周1  ██ M0 ██ M1 ████ M2 规范+30 张 ██
周2  ████ M3 ████ M4 补 13 张 ████
周3  ██ M5 ██ M6 ██ 缓冲/回归 ██
```

## 12. 仓库结构与工程约定

| 约定 | 规则 |
| --- | --- |
| 分支 | `main` 保护；功能用 `feat/<scope>`，改完 squash 合入 |
| 提交 | Conventional Commits：`feat / fix / test / docs / chore(scope): 说明`；一个提交一件事 |
| 版本 | `pyproject.toml` 语义化版本；`/healthz` 暴露版本与素材哈希 |
| 依赖 | `uv.lock`（或 requirements 锁定）提交；Pillow 版本写死，避免快照漂移 |
| 素材 | 单文件 < 120KB 走普通 Git；总量超 100MB 再迁移 Git LFS（提前在 M2 评估） |
| 跨平台 | `.gitattributes` 统一 LF、`*.png` 标为 binary；文件名一律小写 |
| 协作 | 6 人分工、GitHub 建仓与 PR 流程见 `docs/COLLABORATION.md` |
| 代码风格 | ruff（line-length 100）+ mypy strict 于 `src/diyface/render.py`、`palettes.py` |
| 日志 | 结构化 JSON；不记录用户 IP 与图像内容 |

## 13. 风险登记表

| 风险 | 影响 | 概率 | 对策 |
| --- | --- | --- | --- |
| 素材工作量被低估 | 交付延期 | 中 | 已压到 43 张；M2 先做 30 张跑通全链路，余 13 张 M4 补 |
| 素材偏少导致撞脸 | 缺少差异化 | 中 | 颜色维度放大差异；按 §6.4 随时加料，代码零改动 |
| Pillow 缩放导致边缘锯齿 | 观感劣化 | 中 | 高分辨率源 + LANCZOS 缩到 256；描边单独层 |
| 快照测试过脆 | 频繁误报 | 中 | 阈值 1% RMSE；只在 Pillow 升级时整体重刷 |
| 颜色乘色发灰 | 颜色不正 | 中 | 提供 `multiply`/`colorize` 两种模式，按素材实测选 |
| 服务端渲染延迟高 | 拖动卡顿 | 中 | LRU + ETag + 前端去抖；兜底方案 C |
| 版权争议 | 下架风险 | 低 | 只自绘或 CC0；每个目录留 `SOURCE.md` |
| URL 配方过长 | 分享失败/截断 | 低 | 短键名 + zlib + base64url；超长降级为「仅本地」 |
| SEO 无落地页 | 无自然流量 | 中 | M6 用 Jinja2 生成类目静态页、sitemap、结构化数据 |

## 14. 验收清单（Definition of Done）

- [ ] 8 个启用槽位可切换，4 个预留槽位不出现在 UI，素材空态正确，z 序与 §5.3 一致。
- [ ] 素材总数与 §2.3 预算一致（43 张），且每类数量与预算表对得上。
- [ ] 每个可着色槽位独立取色，颜色随素材切换保留。
- [ ] 256 与 1024 导出均为透明 PNG，尺寸与命名符合规范。
- [ ] 随机 20 次无穿模、无空脸、无重复到单调。
- [ ] `?r=` 分享链接可复现同一张脸（含颜色）。
- [ ] 移动端 375×667 无横向滚动，触摸目标 ≥ 44px。
- [ ] `ruff`、`mypy`、`pytest --cov ≥ 85%`、`verify --all` 全绿。
- [ ] 快照基准已提交且 diff 可解释。
- [ ] 首页 Lighthouse 性能 ≥ 90、可访问性 ≥ 90。
- [ ] README 含一键启动、测试、部署三节，命令实测可跑。
- [ ] `/healthz` 返回版本与素材哈希，部署探针接入。

## 15. 待确认决策

以下三项会改变实施细节，建议动工前定：

1. **素材来源**：43 张自绘（2～3 天），还是先用 AI 生成占位把链路跑通、上线前再重绘？决定 M2 的实际日历长度。
2. **是否要账号/云端保存**：若要，M4 需插入用户表、会话与存储，工期 +3 天，且需隐私合规说明。
3. **部署环境**：自有 VPS / Fly.io / 内网演示机？决定 M5 的容器与缓存方案（CDN 与否）。

## 16. 参考

- 对标站点：https://squarefacegenerator.app/ （12 类目、200+ 素材、256px PNG、Canvas 实时渲染）
- Pillow 文档：`Image.alpha_composite`、`ImageOps.colorize`、`resize(LANCZOS)`
- FastAPI + Pydantic v2 校验与 OpenAPI 生成
- 快照测试思路：golden image + RMSE 阈值（numpy 实现，无需额外依赖）
