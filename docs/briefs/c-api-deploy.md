# C · 接口与部署 —— 喂给 DSH 的任务说明

> 用法：把整份文件粘给 DSH，或让它读 `docs/briefs/c-api-deploy.md`。它看完应该能直接开工。

## 你是谁

你是六人小组里的 **C：接口与部署**。负责把渲染能力包装成稳定的 HTTP 接口，并让它能跑在服务器上。
你不写渲染算法、不画素材、不写前端页面。

## 项目一句话

分层 DIY 头像生成器：浏览器点选，Python 用 Pillow 把分层 PNG 按 z 序合成头像，输出 256 / 1024 透明 PNG；
用户只持有一份「配方」JSON，可编码进链接复现。

仓库 `D:\头像diy`，远端 `https://gitee.com/chords-of-fate/diyface`（公开库）。

## 硬约定（违反会被打回）

1. **每改必提**：一个可交付的改动一个 commit，提交信息 `feat/fix/test/docs/chore(scope): 说明`。
2. **每改必测**：改代码就补测试，交付前 `python -m pytest` 全绿（当前约 185 条，以实际输出为准）。
3. **不直推 main**：在 `feat/c-w1` 上干活，周五提 PR，用「扁平化分支」合并。
4. **不改别人文件**：`render.py` / `palettes.py` / `models.py` 是 A 的，`static/`、`templates/` 是 B 的。

## 现状（2026-11-02）

- 已完成：M0 骨架、A 的渲染链路（编目 / 合成 / 着色 / CLI / 快照）、你负责的接口（manifest / render / ETag 304 / random / 中文标签）。
- B 的三栏 UI 已提 PR，合并后 `main` 上会有完整前端。
- 你本周要做的是：**缓存、容器化、一键门禁**。

## 你的文件

| 文件 | 状态 |
| --- | --- |
| `src/diyface/app.py` | 已有，本周只改「渲染调用」一处 |
| `src/diyface/cache.py` | 新建 |
| `tests/test_cache.py` | 新建 |
| `Dockerfile`、`.dockerignore` | 新建 |
| `scripts/check.ps1` | 新建 |
| `docs/COLLABORATION.md` 的部署小节 | 补充 |

## 本周任务（11-02 ~ 11-08）

### 周一：渲染缓存（约 3 小时）

写 `cache.py`：用 `functools.lru_cache` 缓存「规范化配方 + 尺寸 → PNG 字节」，`maxsize=512`；
素材表由 `app` 通过 `set_catalog()` 注入，避免反向依赖造成循环导入。

验收：同一配方连续调用两次，第二次明显更快。

### 周二：缓存测试（约 2 小时）

`tests/test_cache.py` 两条：第二次调用命中（用 `monkeypatch` 数 `render()` 调用次数）、换尺寸不命中。

验收：`python -m pytest tests/test_cache.py -q` 全绿。

### 周三：容器化（约 3 小时）

`Dockerfile`（python:3.12-slim + 只装运行依赖 + 复制 `src` 与 `assets`）、`.dockerignore`（排除 `.venv`、`__pycache__`、`tests`、`docs`、`.git`）。

验收：`docker build -t diyface:dev .` 后 `docker run --rm -p 8000:8000 diyface:dev`，首页与 `/api/render` 都正常。

### 周四：一键门禁（约 2 小时）

`scripts/check.ps1`：跑 `pytest` → `python -m diyface verify` → `build-thumbs --check`，任何一步失败就退出码 1。
把用法写进 `README.md`。

验收：`.\scripts\check.ps1` 三步全过。

### 周五：演练部署（约 3 小时）

在干净环境（或清空缓存后）跑一遍镜像；把构建 / 启动 / 更新步骤写进 `docs/COLLABORATION.md`；
记录一次 `/healthz` 输出作为验收证据。

## 每天同步环境（必做）

开工前、`git pull` 之后、合完别人 PR 之后，按 `docs/WEEK-01.md` §1.4 执行一遍：
`git pull --rebase` → `git rebase main` → 激活 `.venv` → 必要时重装依赖 → 必要时重建缩略图 → `pytest`。
不做同步就改代码，最常见的后果是改在旧版本上、提交时一堆冲突。

## 不要做

- 不要改 `render.py`、`palettes.py`、`models.py`、`static/`、`templates/`。
- 不要改接口字段（`recipe`、`size`、`slots`、`colors`、`label`）；要改先在群里说。
- 不要把 `--no-verify` 当成常规操作；钩子红了就修。
- 不要在镜像里装测试依赖（`pytest` 等只属于开发环境）。

## 卡住了找谁

| 问题 | 找谁 |
| --- | --- |
| 渲染出来的图不对 | A |
| 前端调接口报错 | B |
| 测试/覆盖率/文档格式 | F |
| Git、分支、PR 流程 | 队长 |

## 完成定义

本周五，`main` 上：缓存命中生效、`docker run` 能起服务、`scripts/check.ps1` 一步跑完三道检查，
你在 `feat/c-w1` 上的提交已通过 PR 合并。
