# 给 DSH 的项目交接简报

新加入的 DSH（或接手的人）先读这一份。它把「已经定了什么、现在在哪、哪些坑踩过」压成一页，
细节再去读 `docs/ONBOARDING.md`（分角色逐步教程）与 `docs/PLAN.md`（设计）。

---

## 1 一句话

分层 DIY 头像生成器：浏览器点选，Python 把分层 PNG 按固定 z 序合成头像，输出 256 / 1024 透明 PNG；
用户只持有一份「配方」JSON，配方可编码进链接复现同一张脸。

## 2 硬约定（违反的改动一律打回）

| 约定 | 说明 |
| --- | --- |
| 每改必提 | 每次可交付的改动都要一个 commit，粒度是「一件事」 |
| 每改必测 | 改代码就补/改测试；交付前 `pytest` 全绿（当前基线 152 passed, 11 skipped） |
| 提交信息 | `feat / fix / test / docs / chore(scope): 中文说明` |
| 分支 | 不直推 `main`，一律 PR；一个 PR 一件事，≤ 400 行 |
| 契约 | 槽位 id、目录编号、z 序、接口字段都**不要擅自改**；要改先在本文件里讨论 |
| 不提交 | `.venv/`、`__pycache__/`、`tests/reports/`、`.kra/.psd` 设计源文件 |

这些规则来自仓库根的 `AGENTS.md`，不是口头约定。

## 3 现状快照（2026-11-02）

- 20 个提交，测试 **152 passed, 11 skipped**（跳过的是 Word 任务书校验，缺 `python-docx`）。
- 已完成：M0 骨架、A 的 M1（占位素材 / 编目 / 渲染 / 着色 / CLI / 快照基线）、C 的接口（manifest / render / ETag 304 / random / 中文标签）。
- 未开始：B 的前端交互、D/E 的正式素材、F 的契约与覆盖率、M5 部署、M6 上线。
- 素材只有 3 张占位图（`skin_base`、`bangs_straight_01`、`eyes_round_01`），所以清单里只有 3 个槽位。

## 4 怎么跑

```powershell
cd D:\头像diy
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn jinja2 pillow pydantic pytest pytest-cov numpy httpx
pip install -e .
git config core.hooksPath .githooks     # 提交前自动跑测试
python -m pytest                        # 期望 152 passed, 11 skipped
python -m uvicorn diyface.app:app --reload --port 8000
```

要点：

- `pyproject.toml` 里配了 `pythonpath = ["src"]`，所以**不安装也能跑测试**；但 `python -m diyface` 需要 `pip install -e .`。
- PyPI 直连经常超时，一律加清华源（或阿里源 `https://mirrors.aliyun.com/pypi/simple`）。
- 远端是 Gitee（公开库）：`https://gitee.com/chords-of-fate/diyface.git`。GitHub 只作备份镜像，网络不稳。

## 5 代码地图

| 文件 | 职责 | 状态 |
| --- | --- | --- |
| `src/diyface/models.py` | 12 槽位、z 序、配方模型与校验 | 稳定，别动常量 |
| `src/diyface/catalog.py` | 扫 `assets/` 生成清单、校验素材规格 | 稳定 |
| `src/diyface/palettes.py` | 颜色解析、相乘着色、tint 蒙版 | 稳定 |
| `src/diyface/render.py` | 按 z 序合成、多尺寸 PNG | 稳定 |
| `src/diyface/randomizer.py` | 合法随机配方 | 稳定 |
| `src/diyface/app.py` | 路由与错误结构 | 稳定 |
| `src/diyface/__main__.py` | 命令行 `render` / `verify` | 稳定 |
| `src/diyface/templates/`、`static/` | 页面骨架 | **待 B 重做** |
| `assets/` | 分层素材 | 3 张占位，待 D/E 交 43 张 |
| `tests/` | 152 条测试 | 持续补充 |

## 6 接口契约（以此文件为准）

| 方法 | 路径 | 入参 | 出参 |
| --- | --- | --- | --- |
| GET | `/` | — | HTML 首页 |
| GET | `/api/manifest` | — | `{schema, slots[], default_recipe}` |
| GET | `/api/recipe/default` | — | 配方 |
| POST | `/api/render` | `{recipe, size}` | `image/png` + `ETag` + `Cache-Control`，命中返回 304 |
| POST | `/api/random` | `{seed?}` | 配方（12 个槽位键） |
| GET | `/healthz` | — | `{ok, version, slots, assets}` |
| GET | `/assets/<目录>/<文件>` | — | 素材原图，可当缩略图 |

字段细节：

```json
{
  "schema": 1,
  "slots": [
    {"id": "bangs", "label": {"zh": "发型", "en": "Bangs"}, "z": 30,
     "tintable": true, "default_color": "#3B2B23",
     "assets": [{"id": "bangs_straight_01", "file": "02_bangs/bangs_straight_01.png"}]}
  ],
  "default_recipe": {"version": 1, "slots": {"skin": "skin_base", "mouth": null}, "colors": {"skin": "#F2D5B8"}}
}
```

错误统一为 `{"error": {"code": "...", "message": "...", "field": "..."}}`，
`code` 目前有 `BAD_SIZE`、`UNKNOWN_ASSET`、`INVALID_REQUEST`。

## 7 数据模型要点（最容易理解错的四条）

1. **12 个槽位、8 个启用**：`cheeks / side_hair / brows / nose` 只保留枚举与 z 序，不出素材；配方里这 4 个键固定为 `null`。
2. **z 序是唯一真源**：只写在 `models.SLOTS`，渲染、清单、前端都读它。改顺序 = 改文档 + 改测试，不允许各处各写一份。
3. **白色打底 + 相乘着色**：素材的可着色区域必须画成白色，渲染时乘目标色。直接用深色画发丝，换色后会发灰甚至变黑。
4. **manifest 只输出有素材的槽位**：现在只有 3 个；D/E 交图后自动出现，前端不要写死类目数量。

## 8 已经踩过的坑（别再踩）

| 坑 | 现象 | 处理 |
| --- | --- | --- |
| pytest 的 `tmp_path` | `PermissionError: WinError 5` 打不开系统 Temp | 用 `workdir` 夹具（`tests/reports/tmp`，已 gitignore） |
| `index` 名字冲突 | `RecursionError`，因为路由函数覆盖了 `catalog.index` | 导入时用 `build_index` 别名 |
| ASGI 测试客户端 | 静态文件返回 200 但 body 为空 | `receive` 不能立刻回 `http.disconnect`，等响应体结束 |
| tint 的 mask | 整层被染色，高光也变了 | `mask.convert("L")`，不要用 `getchannel("A")` |
| 沙箱里跑 git 钩子 | `couldn't create signal pipe` | 只有受限环境才需要 `git commit --no-verify`；正常机器不绕 |
| 中文路径 / 换行 | 全文件 diff | `.gitattributes` 已统一 LF，`*.png` 标 binary |
| Gitee HTTPS 令牌 | `The token username invalid` | 用户名是 `chords-of-fate`，密码填私人令牌，不是登录密码 |

## 9 下一步（按角色，谁接手看对应一节）

| 角色 | 下一步 | 验收 |
| --- | --- | --- |
| B 前端 | 按 ONBOARDING §4.2 做三栏 UI、素材格、去抖预览、取色、下载分享 | 375px 无横向滚动；连点 10 次显示最后一个 |
| A 渲染 | M2：`verify` 补体积与 `_tint.png` 配对、`build-thumbs` 生成缩略图 | 坏素材能精确报出文件名与规则 |
| D 素材·头部 | 21 张（发型 8 / 眼睛 8 / 帽子 5），先交 3 张跑通 | 尺寸 1024、RGBA、命名合规 |
| E 素材·面部 | 22 张（脸型 2 / 嘴 7 / 眼镜 5 / 衣服 5 / 配饰 3），先画脸型 | 与 D 的素材任意组合不穿模 |
| F 质量 | 契约测试、覆盖率门槛、素材校验脚本 | `pytest --cov` 低于 85% 失败 |

## 10 PR 前的自检

- [ ] `python -m pytest` 全绿，没有新增 skip。
- [ ] 改了渲染逻辑 → 跑 `pytest tests/test_golden.py`；素材换了 → `pytest --update-golden` 并在 PR 里说明。
- [ ] 改了接口 → 同步更新本文件 §6 与 `docs/ONBOARDING.md`。
- [ ] 没有提交临时文件、密钥、设计源文件。
- [ ] PR 描述里贴了实际执行的命令与结果。

## 11 对 DSH 的行为要求

1. **先读再改**：动手前看 `src/diyface/app.py`、`models.py` 与相关测试，别凭印象改。
2. **不臆造契约**：字段以代码与 §6 为准；不确定就先问，别猜着写。
3. **红就是红**：测试失败要修到绿，不允许 `--no-verify`、`-k` 跳过或删断言来「通过」。
4. **一次一件事**：一个 commit / PR 只解决一个问题，改动超过 400 行就拆。
5. **同步文档**：改了行为就改文档，文档和代码不一致视为缺陷。
6. **回答用中文**：先给结论，再给证据（命令、输出、文件路径）。

---

## 附：30 秒版（直接粘给 DSH 的对话开头）

```
项目：分层 DIY 头像生成器（FastAPI + Pillow），仓库 D:\头像diy，远端 Gitee（公开）。
硬约定：每改必提 commit、每改必测、不直推 main、不改已定契约（槽位 id/目录编号/z 序/接口字段）。
现状：152 passed, 11 skipped；M0 完成，A 的渲染链路与 C 的接口已完成，B 前端、D/E 素材、F 质量未完成。
跑：pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn jinja2 pillow pydantic pytest numpy httpx && pip install -e .
     python -m pytest ；python -m uvicorn diyface.app:app --reload --port 8000
接口：GET /api/manifest、POST /api/render {recipe,size}、POST /api/random {seed?}、GET /healthz、GET /assets/<file>。
要点：12 槽位 8 启用；z 序只在 models.SLOTS；素材白色打底靠相乘着色；manifest 只输出有素材的槽位。
先读：AGENTS.md 与 docs/AGENT-BRIEF.md，再读 docs/ONBOARDING.md 里你负责的那一节。
```
