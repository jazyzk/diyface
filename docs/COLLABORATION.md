# 团队协作工具使用说明（Gitee + VS Code）

配套 [docs/PLAN.md](PLAN.md)：那份讲「做什么」，这份只讲「怎么一起做」。
适用项目：虚拟头像设计系统（Flask + Pillow，6 人 / 3 周）。

## 1 现状与卡点

| 事项 | 状态 | 说明 |
| --- | --- | --- |
| 本地仓库 | 就绪 | `main` 分支，工作区干净 |
| 网络至 GitHub | 不稳定 | 组员无法登录，实测多次超时 |
| 网络至 Gitee | 稳定 | 同一时段连通正常 |
| 远端仓库 | Gitee 为主，GitHub 备份 | `gitee` 为主力远端 |
| 账号 | 需实名 | 公开仓库要求实名认证 |

结论：**主力远端用 Gitee，GitHub 保留为备份镜像**。原因是可访问性与注册门槛，不是技术偏好。

## 2 一次性建仓

1. 打开 <https://gitee.com/projects/new>。
2. 仓库名 `diyface`，选 **公开**，**不要**勾选「使用 Readme 初始化」（否则首次推送要额外合并）。
3. 建完后在本机执行：

```powershell
cd D:\头像diy
git remote add gitee https://gitee.com/chords-of-fate/diyface.git
git push gitee main
git branch -u gitee/main
```

4. 其余 5 位成员克隆：

```powershell
git clone https://gitee.com/chords-of-fate/diyface.git
```

两个注意点：分支名统一 `main`；`.gitignore` 与 `.gitattributes` 必须先就位，否则队友一 clone 就撞上换行与缓存问题。

## 3 授权方式

| 方式 | 步骤 | 优点 | 注意 |
| --- | --- | --- | --- |
| SSH 密钥（推荐） | `ssh-keygen` → 公钥贴到 Gitee → `ssh -T git@gitee.com` | 一次配置长期免密 | 每台机器各配一次 |
| HTTPS + 私人令牌 | 设置 → 私人令牌 → 勾选 projects → 当密码填 | 不用装东西 | 令牌等同密码，泄露立刻重置 |
| 账号密码 | 首次 push 直接输入 | 最快 | 开了两步验证后不可用 |

```powershell
ssh-keygen -t ed25519 -C "gitee@diyface"
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | Set-Clipboard
ssh -T git@gitee.com
```

返回 `Hi <用户名>! You've successfully authenticated` 即成功。

## 4 仓库设置

1. **加成员**：仓库 → 管理 → 仓库成员管理 → 添加成员，5 人权限选「开发者」。公开仓库不受私有库人数限制。
2. **保护 `main`**：禁止直接 push、要求 PR 合并。免费版若受限，靠 §6 的约定执行。
3. **合并请求**：至少 1 人审核通过才能合并。
4. **备份镜像**：GitHub 保留，定期 `git push origin main`。
5. **版本号**：每周五 `git tag v0.x` 后 `git push gitee --tags`，答辩时能展示迭代。

Gitee 没有 GitHub Actions，所以门禁分两处：**本地提交钩子**（每次 commit 自动跑测试）与**约定**。
真正的「红灯拦截」靠本地钩子。

## 5 6 人分工

一人一块地，路径不重叠，冲突自然少。

| 角色 | 负责路径 | 主战场 | 交付物 |
| --- | --- | --- | --- |
| P1 素材与美术 | `assets/` | 素材生产与对位 | 54 张分层素材 + 规格文档 |
| P2 渲染内核 | `src/diyface/render.py`、`palettes.py`、`models.py`、`catalog.py` | 合成与着色 | 合成管线 + 快照测试 |
| P3 前端体验 | `src/diyface/static/`、`templates/` | 编辑器交互 | 三栏 UI、移动端、导出分享 |
| P4 后端与数据 | `src/diyface/app.py`、`cache.py`、`randomizer.py`、SQLite | 接口与存储 | 接口契约、作品存储、部署 |
| P5 视觉与训练 | `src/diyface/vision/`、`scripts/train_*.py` | 照片分析 | 照片转配方 + 分类器准确率 |
| P6 质量与交付 | `tests/`、`docs/` | 质量与材料 | 测试体系、报告与演示 |

素材总量 54 张，与 PLAN §5.1 的预算一致。P1 的产能是全组关键路径，D3 与 D7 各有一个检查点。

## 6 分支与提交

- `main` 只接受 PR；功能分支 `feat/<域>-<简述>`，修复 `fix/...`。
- 一个 PR 只做一件事，控制在 400 行内；超过就拆。
- 合并方式统一 **Squash**，保持 `main` 线性历史。
- 提交信息：`类型(范围): 中文说明`，类型限 `feat / fix / test / docs / chore`。
- 仓库根的 `AGENTS.md` 是硬约定：**每改必提、每改必测**。PR 描述里贴出执行的测试命令与结果。

每个成员必做一次：

```powershell
git config core.hooksPath .githooks
```

之后每次 `git commit` 自动跑 `python -m pytest`，红了直接拒绝提交。

## 7 二进制素材怎么不打架

Git 无法合并 PNG，所以靠规则：

- **一人一目录**，跨目录改动先在群里说一声。
- 成批提交：一次 PR 交一个槽位的全部图，而不是一张一提。
- `.gitattributes` 里声明 `*.png binary`，避免行尾转换。
- 缩略图 `_thumb/` 由脚本生成，谁改素材谁负责重建。

## 8 日常节奏

```powershell
git pull --rebase                  # 开工前
git switch -c feat/xxx             # 开新分支
python -m pytest                   # 提交前
git add -A && git commit -m "feat(scope): 说明"
git push -u gitee feat/xxx         # 收工前，草稿也推
```

每天 10 分钟站会：昨天做了什么、今天做什么、卡在哪。
每周二、周四为集成日；每周五 10 分钟演示，每人 1 分钟。

## 9 VS Code 用法

必装扩展（六个够用）：

| 扩展 | 用途 |
| --- | --- |
| Python | 语法、调试、解释器切换 |
| Pylance | 类型提示 |
| GitLens | 看每行谁改的 |
| Chinese (Simplified) | 中文界面 |
| Even Better TOML | 改 `pyproject.toml` |
| Live Server（可选） | 单独调静态页 |

推荐设置：`"files.eol": "\n"`、`"editor.formatOnSave": true`，解释器选 `.venv` 里的 Python。
调试按 F5，`.vscode/launch.json` 里配 `flask --app diyface.app run`。

## 10 常见坑

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `non-fast-forward` | 远端有新提交 | `git pull --rebase` 再推 |
| 冲突标记 `<<<<<<<` | 两人改了同一处 | 手改到最终版本，删标记，`git add` 后继续 |
| push 要密码 | 没用 SSH 或令牌 | 按 §3 配 |
| `ModuleNotFoundError: diyface` | 没装包 | `pip install -e ".[dev]"` |
| 提交被钩子拒绝 | 测试红了 | 修到绿；不要用 `--no-verify` 绕过 |
| 页面样式没变 | 浏览器缓存 | `Ctrl+F5` |

## 11 第一周检查表

- [ ] 已加入仓库为「开发者」，能 push。
- [ ] `.venv` 建好，`pip install -e ".[dev]"` 成功。
- [ ] `python -m pytest` 全绿（391 passed, 11 skipped 是当前基线）。
- [ ] `python -m flask --app diyface.app run` 能打开首页。
- [ ] `git config core.hooksPath .githooks` 已执行。
- [ ] 已推第一个分支并提了 PR。
