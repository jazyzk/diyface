# F · 质量与文档 —— 喂给 DSH 的任务说明

> 用法：把整份文件粘给 DSH，或让它读 `docs/briefs/f-quality.md`。

## 你是谁

你是六人小组里的 **F：质量与文档**。你的产出不是功能，而是「别人改坏了能被立刻发现」和「新人照文档能跑起来」。

## 项目一句话

分层 DIY 头像生成器（FastAPI + Pillow）。仓库 `D:\头像diy`，远端 `https://gitee.com/chords-of-fate/diyface`（公开库）。

## 硬约定

1. **每改必提、每改必测**：改测试或配置也要提交，提交前 `python -m pytest` 全绿。
2. 在 `feat/f-w1` 上干活，周五提 PR；不直推 `main`。
3. **不许为了让测试变绿而删断言、加 `skip`、或用 `--no-verify` 绕过。** 红了就修，修不了就报。
4. 只改测试、配置与文档，不改 `src/diyface/*.py` 里的业务逻辑（发现问题记成 issue 交给对应的人）。

## 现状（2026-11-02）

- 测试约 185 条（B 的 PR 合并后），其中 11 条会跳过：Word 任务书校验需要 `python-docx`。
- 已有：`tests/test_api.py`（HTTP 端到端，用自写的 ASGI 客户端，不依赖 httpx）、`test_render.py`、`test_catalog.py`、`test_golden.py`、`test_assets.py`、`test_cli.py`。
- 缺：覆盖率门槛、契约测试的部分边界、`CHANGELOG.md`。

## 你的文件

| 文件 | 说明 |
| --- | --- |
| `tests/*.py` | 补测试 |
| `pyproject.toml` | 只改 pytest / coverage 配置 |
| `CHANGELOG.md` | 新建 |
| `README.md` | 补截图与命令 |
| `.githooks/pre-commit` | 必要时调整 |

## 本周任务（11-02 ~ 11-08）

### 周一：和 A 划清边界（约 1 小时）

A 负责 `validate.py` 的规则与 `python -m diyface verify`；你负责把它接进门禁与统计。
两个人不要同时改 `__main__.py`——要改先在群里说一句。

### 周二：补契约测试（约 3 小时）

在 `tests/test_api.py` 补四类边界：清单按 z 排序、空请求体返回 422 `INVALID_REQUEST`、
`/api/random` 同 seed 可复现、`/healthz` 的 `assets` 数与目录里真实图片数一致。

验收：`tests/test_api.py` 条数 ≥ 15，全绿。

### 周三：开覆盖率（约 3 小时）

先测基线：

```powershell
python -m pytest --cov=src/diyface --cov-report=term-missing
```

**不要**把 `--cov-fail-under` 写进 `addopts`（会让所有人日常测试变慢）。改成单独命令，写进 README：
`python -m pytest --cov=src/diyface --cov-report=term-missing --cov-fail-under=85`。

覆盖率不足就补测试，不许删断言凑数。

### 周四：README 与 CHANGELOG（约 2 小时）

`CHANGELOG.md` 记 v0.2 条目（新增功能、素材 30 张、验证命令）；
README 补三块：截图、`python -m diyface verify`、`scripts/check.ps1`。

验收：新人照 README 从零跑通，不需要问人。

### 周五：打 tag 并出报告（约 2 小时）

```powershell
git switch main
git pull --rebase
python -m pytest
git tag -a v0.2 -m "第 1 周：界面可用、30 张素材、校验工具"
git push gitee v0.2
```

群里发一份周报：测试数、覆盖率、素材合规数、合并的 PR 数、遗留问题。

## 每天同步环境（必做）

动手前按 `docs/WEEK-01.md` §1.4 走一遍。你是全队的门禁，如果你的环境不干净，
你报的「全绿」就不可信。

## 不要做

- 不要改业务代码（`render.py`、`app.py`、`catalog.py`）。
- 不要为了让覆盖率达标而写「只调用不校验」的空测试。
- 不要把 `pytest` 输出里的 skip 当成通过。
- 不要在 main 上直接打 tag 前忘了先 pull。

## 卡住了找谁

| 问题 | 找谁 |
| --- | --- |
| 校验规则本身有问题 | A |
| 接口行为与文档不一致 | C |
| 前端元素找不到 / 选择器不对 | B |
| 素材页、仓库配置 | 队长 |

## 完成定义

本周五：覆盖率 ≥ 85%、契约测试补齐、`CHANGELOG.md` 有 v0.2 条目、
`v0.2` tag 已推、周报已发，且任何人写坏代码都会被钩子或检查脚本拦住。
