# 新人上手与六人分工执行方案

这份文档解决三件事：**怎么进仓库**、**怎么配环境**、**六个人各自按什么顺序干活**。
代码层面的逐步教程在 [HANDBOOK.md](HANDBOOK.md)，这里只写「先做什么、做到什么算完」。

当前基线：M0 已完成，仓库里有 10 个提交，测试 56 条通过、11 条跳过。

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
| `python -m pytest` | 最后一行 `69 passed, 11 skipped` |
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

每个人的第一周都只做一件事：**让 M1 的链路跑起来**。下面按角色给出顺序、交付物和验收。

### 4.1 A 渲染内核

**本周目标**：命令行输入一份配方，输出一张 256 的 PNG。

| 顺序 | 动作 | 文件 | 验收 |
| --- | --- | --- | --- |
| 1 | 造 3 张占位素材 | `assets/01_skin/`、`02_bangs/`、`06_eyes/` | 能被扫描到 |
| 2 | 扫描目录生成清单 | `catalog.py` | 打印出 3 个槽位与素材 id |
| 3 | 按 z 序叠图层 | `render.py` | 输出透明底 PNG，空槽位不画 |
| 4 | 实现颜色相乘 | `palettes.py` | 换发色只影响头发，描边仍黑 |
| 5 | 命令行出图 | `__main__.py` | `python -m diyface render r.json --out a.png` |
| 6 | 三张快照基线 | `tests/test_golden.py` | `pytest` 绿 |

**依赖与配合**：D/E 的素材没好之前，占位图自己用 Pillow 生成；C 的 `/api/render` 会调用你的 `render()`，所以接口签名（配方进、字节串出）不要随意改。

**本周结束时的状态**：`python -m diyface render` 能出图，`pytest` 里多出 6 条以上渲染测试。

### 4.2 B 前端交互

**本周目标**：把 M0 的静态页换成能用假数据点动的三栏界面。

| 顺序 | 动作 | 文件 | 验收 |
| --- | --- | --- | --- |
| 1 | 三栏布局与响应式 | `templates/index.html`、`static/style.css` | 375 像素宽无横向滚动 |
| 2 | 用清单渲染类目与素材格 | `static/app.js` | 点类目能切换素材列表 |
| 3 | 接预览接口（去抖 + 序号） | `static/app.js` | 连点 10 次显示最后一个 |
| 4 | 取色器与预设色板 | `static/app.js` | 换色只改当前槽位 |
| 5 | 下载与分享链接 | `static/app.js` | 下载的 PNG 四角透明 |

**依赖与配合**：M1 期间 `/api/render` 可能还没接上，先用 `/api/manifest` 的真实数据把界面跑起来；预览可以用一张静态占位图顶着。等 C 接上接口后只改一个 URL。

**本周结束时的状态**：界面可以完整点选，预览图能随选择变化（哪怕是占位图）。

### 4.3 C 接口与部署

**本周目标**：把 M0 的清单接口扩展成能出图的完整接口，并保证 304 缓存生效。

| 顺序 | 动作 | 文件 | 验收 |
| --- | --- | --- | --- |
| 1 | `/api/manifest` 接上真实扫描 | `app.py` | 返回的 assets 非空 |
| 2 | `/api/render` 接上 A 的 `render()` | `app.py` | 返回 image/png |
| 3 | 加 ETag 与 304 | `app.py`、`cache.py` | 带 If-None-Match 返回 304 |
| 4 | `/api/random` 合法随机 | `randomizer.py` | 1000 次随机无空脸 |
| 5 | 错误结构统一 | `app.py` | 非法 size 返回 422 且结构一致 |

**依赖与配合**：等 A 的 `render()` 能跑就立刻接上；在此之前用一张写死的 PNG 占位，保证 B 可以联调。

**本周结束时的状态**：`curl` 能拿到 PNG，第二次请求返回 304。

### 4.4 D 素材·头部（21 张）

**本周目标**：先交 3 张跑通流程，再批量生产。

| 顺序 | 动作 | 产物 | 验收 |
| --- | --- | --- | --- |
| 1 | 建目录、拉三条参考线 | `assets/_guide.png` | 参考线不会被导出 |
| 2 | 画 3 张试作 | 直发、圆眼、贝雷帽 | `verify` 零报错 |
| 3 | 批量画到 21 张 | 发型 8、眼睛 8、帽子 5 | 尺寸与命名全合规 |
| 4 | 交叉验收 | 与 E 换素材互查 | 两套素材任意组合不穿模 |

**依赖与配合**：`verify` 命令要等 A 写完，在此之前用图片属性自查（1024 见方、RGBA、文件名合规）。**不要等代码，先画。**

**本周结束时的状态**：至少 3 张能被 A 的渲染器叠出来，看起来不歪。

### 4.5 E 素材·面部与服饰（22 张）

**本周目标**：先画脸型，因为它是所有层的基准。

| 顺序 | 动作 | 产物 | 验收 |
| --- | --- | --- | --- |
| 1 | 画两款脸型 | `01_skin` 共 2 张 | 能容纳所有发型 |
| 2 | 画嘴与眼镜 | 嘴 7、眼镜 5 | 位置不飘 |
| 3 | 画衣服与配饰 | 衣服 5、配饰 3 | 领口接住下巴 |
| 4 | 与 D 对位 | 叠加检查 | 无悬空、无穿模 |

**依赖与配合**：脸型先交给 D 做发型对位，所以**第一周先把两张脸型画完**，其余按顺序补。

**本周结束时的状态**：两张脸型被 A 的渲染器正确显示，D 可以拿去做重合检查。

### 4.6 F 质量与文档

**本周目标**：让「红了不能合」这件事真正生效。

| 顺序 | 动作 | 文件 | 验收 |
| --- | --- | --- | --- |
| 1 | 补齐测试装置 | `tests/conftest.py` | 假素材与假配方可用 |
| 2 | 契约测试 | `tests/test_api.py` | 5 个路由各 3 条 |
| 3 | 快照比对工具 | `tests/test_golden.py` | RMSE 阈值 1% |
| 4 | 素材校验脚本 | `scripts/verify_assets.py` | 精确报出文件名与规则 |
| 5 | 覆盖率门槛 | `pyproject.toml` | 低于 85% 时失败 |

**依赖与配合**：你的测试会成为别人的红灯，所以**先把工具写好，再逐步加严**；一开始不要卡覆盖率，等 M2 再开。

**本周结束时的状态**：任何人提交坏代码都会被钩子或 CI 拦住，且提示能看懂。

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

- [ ] `python -m pytest` 全绿（至少 56 passed）。
- [ ] 提交信息符合 `feat / fix / test / docs / chore(scope): 说明`。
- [ ] 一个 PR 只做一件事，改动不超过 400 行。
- [ ] PR 描述里贴了实际跑的命令与结果。
- [ ] 没有提交 `.venv`、`__pycache__`、`assets/` 里的设计源文件。

### 6.2 阶段验收（团队）

| 里程碑 | 验收标准 | 谁来验收 |
| --- | --- | --- |
| M0 | 首页能开、56 条测试绿 | 已完成 |
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
