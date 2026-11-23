# 给 DSH 的项目交接简报

新加入的 DSH（或接手的人）先读这一份。它把「已经定了什么、现在在哪、哪些坑踩过」压成几页，
细节再去读 `docs/PLAN.md`（计划）、`docs/COLLABORATION.md`（协作）、`docs/MIGRATION-v2.md`（契约变更）。

---

## 1 一句话

虚拟头像设计系统：两条输入路径（照片估计 / 手动捏脸）收敛到同一份「配方」JSON，
由确定性的分层渲染引擎合成 256 / 1024 透明 PNG；配方可存库、可分享、可二次编辑。

## 2 硬约定（违反的改动一律打回）

| 约定 | 说明 |
| --- | --- |
| 每改必提 | 每次可交付的改动都要一个 commit，粒度是「一件事」 |
| 每改必测 | 改代码就补/改测试；交付前 `pytest` 全绿（当前基线 391 passed, 11 skipped） |
| 提交信息 | `feat / fix / test / docs / chore(scope): 中文说明` |
| 分支 | 不直推 `main`，一律 PR；一个 PR 一件事，≤ 400 行 |
| 契约 | 槽位 id、目录编号、z 序、接口字段都**不要擅自改**；要改先写迁移说明 |
| 不提交 | `.venv/`、`__pycache__/`、`tests/reports/`、`*.db`、`.kra/.psd` 设计源文件 |

这些规则来自仓库根的 `AGENTS.md`，不是口头约定。

## 3 现状快照（2026-11-15）

- 契约已按《项目说明与分工》v1.0 迁移：**10 槽位 / Flask 3 / 80KB / 新基线**，见 `docs/MIGRATION-v2.md`。
- 测试 **391 passed, 11 skipped**（跳过的是 Word 任务书校验，缺 `python-docx`）。
- 已完成：分层渲染、相乘着色、多尺寸、CLI、素材校验、缩略图、快照基线、清单与渲染接口、随机、前端三栏交互。
- 素材已交付 **54 张**（10 槽位全覆盖），由 `scripts/make_asset_pack.py` 与 `make_face_assets.py` 生成。
- 未开始：`/api/analyze`（照片路径）、`/api/works`（SQLite 作品存储）、6 套预设模板。

## 4 怎么跑

```powershell
cd D:\头像diy
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e ".[dev]"
python -m flask --app diyface.app run --debug --port 8000
```

测试与素材命令：

```powershell
python -m pytest
python -m diyface verify
python -m diyface build-thumbs
python -m diyface render tests/fixtures/recipes/base.json --out out.png
```

## 5 代码地图

| 文件 | 职责 |
| --- | --- |
| `src/diyface/models.py` | 10 个槽位的 z 序、可着色标记、目录编号；`AvatarRecipe` 校验 |
| `src/diyface/catalog.py` | 扫目录编目，跳过 `_` 开头与 `_tint.png` |
| `src/diyface/render.py` | 按 z 序合成、缩放，`compose` / `render` |
| `src/diyface/palettes.py` | 相乘着色（白色底 × 目标色） |
| `src/diyface/randomizer.py` | 随机配方，保证合法 |
| `src/diyface/validate.py` | 素材规格校验（尺寸、模式、命名、80KB、蒙版） |
| `src/diyface/thumbs.py` | 256 缩略图生成与过期检查 |
| `src/diyface/importer.py` | 外部导出图层导入（推断槽位、缩放、补蒙版） |
| `src/diyface/guide.py` | 画素材用的参考线图 |
| `src/diyface/bench.py` | 渲染耗时测量 |
| `src/diyface/pixel.py` | 32×32 拼豆画布：RLE 编解码与 PNG 渲染 |
| `src/diyface/mard.py` | Mard 官方色卡 64 色（色号 + 色值），前端色板的来源 |
| `src/diyface/sticker.py` | 拼豆图裁切缩放，贴到头像右下角 |
| `src/diyface/app.py` | Flask 路由：首页、清单、渲染、随机、拼豆、健康检查 |
| `src/diyface/__main__.py` | CLI：`render` / `verify` / `build-thumbs` |

## 6 接口契约

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 三栏首页，内联清单 |
| GET | `/api/manifest` | 清单 + 默认配方 |
| GET | `/api/recipe/default` | 默认配方 |
| POST | `/api/render` | 按配方返回 PNG，带 ETag / 304 |
| POST | `/api/random` | 合法随机配方，可带 seed |
| GET | `/pixel` | 拼豆画布页面（32×32 自由填色） |
| POST | `/api/pixel/render` | 拼豆画布渲染成 PNG |
| GET | `/healthz` | ok、version、slots、assets |
| GET | `/assets/<path:filename>` | 素材与缩略图 |

错误统一 `{"error": {"code", "message", "field"}}`；已实现错误码 `BAD_SIZE`、`UNKNOWN_ASSET`、`INVALID_REQUEST`。
规划中：`/api/analyze`（照片）、`/api/works`（作品 CRUD），错误码 `NO_FACE`、`MULTI_FACE`、`FACE_TOO_SMALL`、`BLURRY`。

## 7 数据模型要点

- 槽位 id 与 z 序只写在 `models.py`，渲染、清单、前端都从这里读。
- Recipe：`{"version", "slots": {10 个键}, "colors": {"#RRGGBB"}, "seed"}`，`extra="forbid"`。
- 可着色槽位必须白底 + 灰度明暗 + 黑描边；眼睛的 tint 蒙版只覆盖虹膜。
- 素材文件名 `<槽位>_<形状>_<两位序号>.png`，蒙版 `<stem>_tint.png`，缩略图 `_thumb/<stem>_256.png`。

## 8 已经踩过的坑

| 坑 | 症状 | 结论 |
| --- | --- | --- |
| FastAPI 换 Flask | 路由/测试全变 | 契约不变，测试改用 Flask `test_client` |
| `index` 名字冲突 | 无限递归 | `from .catalog import index as build_index` |
| 静态文件空响应 | 200 但 0 字节 | 旧 ASGI 客户端过早断开；换 Flask 后消失 |
| tint 蒙版取错通道 | 整层被染色 | 用 `mask.convert("L")`，不是 alpha 通道 |
| 测试写死素材张数 | 加图就红一片 | 改成扫目录动态计算 |
| pytest 临时目录 | `WinError 5` | 用仓库内 `tests/reports/tmp` 夹具 |
| Figma 导出裁边 | 素材全挤中间 | 用 1024 画板导出，或让 importer 按槽位锚点摆放 |

## 9 下一步

1. P1 按新目录补齐 54 张（当前 16 张）。
2. P4 实现 `/api/works` + SQLite（表结构见 PLAN §5.2）。
3. P5 跑通 `/api/analyze` 与分类器训练。
4. P3 补 6 套预设模板与移动端细节。

## 10 PR 前的自检

```powershell
python -m pytest
python -m diyface verify
git status
```

- [ ] 测试全绿，没有跳过新加的用例。
- [ ] 改了契约就同步 `PLAN.md` / `MIGRATION-v2.md`。
- [ ] 没有临时文件、密钥、`tests/reports/` 进入提交。
- [ ] 提交信息符合 `类型(范围): 说明`。

## 11 对 DSH 的行为要求

- 先读代码再改；不确定的契约先问，不要猜。
- 一次只做一件事，改动尽量小，改动后立即跑测试。
- 不擅自升级依赖、不引入构建链、不改 `main` 历史。
- 不要用 `--no-verify` 绕过提交钩子；测试红了就修，不许跳过。
- 报告进度时给出「改了什么、怎么验证的、还有什么没做」三段。

## 12 30 秒版（可直接粘贴给 DSH）

> 仓库 `D:\头像diy`，虚拟头像设计系统（Flask 3 + Pillow，10 槽位）。
> 先读 `AGENTS.md` 与 `docs/AGENT-BRIEF.md`；改完必须 `python -m pytest` 全绿（基线 391 passed, 11 skipped），
> 素材改动还要跑 `python -m diyface verify`。接口契约见 `/api/render`、`/api/manifest`，不要擅自改槽位与字段。
> 一次只做一件事，提交信息用 `类型(范围): 中文说明`，不要用 `--no-verify` 跳过测试。
