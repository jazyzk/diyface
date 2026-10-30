# 团队协作与 Gitee 托管指南（6 人）

配套 [docs/PLAN.md](PLAN.md)：那份讲「做什么」，这份只讲「怎么一起做」。
第一次加入的新人先看 [docs/ONBOARDING.md](ONBOARDING.md)（加入仓库、配环境、练手 PR）；
角色分工的逐步操作教程在 [docs/HANDBOOK.md](HANDBOOK.md)，六个人各看自己那一章。

## 1. 现状与卡点

| 事项 | 状态 | 说明 |
| --- | --- | --- |
| 本地仓库 | 就绪 | `main` 分支，M0 已提交，工作区干净 |
| 网络至 GitHub | 不稳定 | 实测出现过 21 秒连接超时，组员无法登录 |
| 网络至 Gitee | 稳定 | 同一时段实测 0.1 秒连通 |
| 远端仓库 | GitHub 已有，Gitee 待建 | 建好后 GitHub 降级为备份镜像 |
| Gitee 账号 | 需要实名 | 公开仓库要求实名认证 |

结论：**主力远端换成 Gitee，GitHub 保留为备份镜像**。原因是可访问性和注册门槛，不是技术偏好。

## 2. 一次性建仓（约 5 分钟）

1. 打开 <https://gitee.com/projects/new>。
2. 仓库名 `diyface`，选 **公开**，**不要**勾选「使用 Readme 文件初始化仓库」（否则首次推送要额外合并）。
3. 建完后在本机执行：

```powershell
cd D:\头像diy
git remote add gitee https://gitee.com/chords-of-fate/diyface.git
git push gitee main
git branch -u gitee/main
```

4. 其余 5 位成员：

```powershell
git clone https://gitee.com/chords-of-fate/diyface.git
```

两个注意点：

- 分支名统一 `main`，Gitee 新建仓库默认也是 `master`，别被默认值带偏。
- 首次推送前确认 `.gitattributes` 与 `.gitignore` 已在仓库里，否则队友一 clone 就撞上换行与缓存问题。

## 3. 授权方式三选一

| 方式 | 步骤 | 优点 | 注意 |
| --- | --- | --- | --- |
| SSH 密钥（推荐） | `ssh-keygen` 生成 → 公钥贴到 Gitee → `ssh -T git@gitee.com` 验证 | 一次配置长期免密 | 每台新机器各配一次 |
| HTTPS + 私人令牌 | Gitee 设置 → 私人令牌 → 勾选 projects → 首次 push 时当密码填 | 不用装东西，能过公司网络 | 令牌等同密码，泄露立刻重置 |
| 账号密码 | 首次 push 直接输入 Gitee 账号密码 | 最快 | 开了两步验证后不可用 |

SSH 具体命令（PowerShell）：

```powershell
ssh-keygen -t ed25519 -C "gitee@diyface"
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | Set-Clipboard
ssh -T git@gitee.com
```

公钥贴到 Gitee → 设置 → SSH 公钥 → 添加公钥。返回 `Hi <用户名>! You've successfully authenticated` 即成功。若设了口令，需要启动 ssh-agent：

```powershell
Set-Service ssh-agent -StartupType Automatic
Start-Service ssh-agent
ssh-add "$env:USERPROFILE\.ssh\id_ed25519"
```

## 4. 仓库设置（建完立刻做）

1. **加成员**：仓库 → 管理 → 仓库成员管理 → 添加成员，5 人权限选「开发者」。公开仓库不受「私有仓库最多 5 人」的限制，6 个人都能加。
2. **保护 `main`**：管理 → 保护分支设置 → 保护 `main`，禁止直接 push、要求 PR 合并。免费版若提示受限，就靠 §6 的约定执行。
3. **合并请求**：至少 1 人审核通过才能合并。
4. **备份镜像**：GitHub 仓库保留，定期 `git push origin main` 同步一次；GitHub Actions 继续在镜像侧跑 CI。
5. **仓库信息**：写一句描述，许可证按课程要求选 MIT 或留空。

Gitee 没有 GitHub Actions，所以 CI 分两处：**本地提交钩子**（见 §6，每次 commit 自动跑测试）和 **Gitee Go**（可选，配额有限）。真正的「红灯拦截」靠本地钩子，够用。

## 5. 6 人分工（按目录归属）

一人一块地，路径不重叠，冲突自然少。

| 角色 | 负责路径 | 主战场 | 交付物 |
| --- | --- | --- | --- |
| A 渲染内核 | `src/diyface/render.py`、`palettes.py`、`models.py`、`catalog.py` | M1、M5 | 合成管线 + 单测 + 快照基线 |
| B 前端交互 | `src/diyface/static/`、`templates/` | M3 | 三栏 UI、移动端、导出与分享 |
| C API 与部署 | `src/diyface/app.py`、`cache.py`、`randomizer.py`、`Dockerfile`、`.github/` | M0、M5、M6 | 接口契约、缓存、CI、上线 |
| D 素材·头部 | `assets/02_bangs/`、`06_eyes/`、`10_hat/` | M2、M4 | 21 张合规素材 + 对齐 |
| E 素材·面部与服饰 | `assets/01_skin/`、`07_mouth/`、`09_glasses/`、`11_clothes/`、`12_extra/` | M2、M4 | 22 张合规素材 + 对齐 |
| F 质量与文档 | `tests/`、`docs/`、`scripts/` | 全程 | 测试体系、素材校验脚本、进度同步 |

合计 21 + 22 = 43 张，与 PLAN §2.3 的预算一致。美术两人可互换一半素材做交叉验收，避免「自己画的自己验」。

## 6. 分支与提交

- `main` 只接受 PR（Gitee 里叫「Pull Request」）；功能分支命名 `feat/<域>-<简述>`，修复用 `fix/...`，例如 `feat/render-zorder`。
- 一个 PR 只做一件事，控制在 400 行内；超过就拆。
- 合并方式统一 **Squash**，保持 `main` 线性历史。
- 提交信息用 Conventional Commits：`feat / fix / test / docs / chore(scope): 说明`。
- 仓库根的 `AGENTS.md` 是硬约定：**每改必提、每改必测**。PR 描述里贴出执行的测试命令与结果。

每个成员的必做一步（只需执行一次）：

```powershell
git config core.hooksPath .githooks
```

之后每次 `git commit` 都会自动跑 `python -m pytest`，红了直接拒绝提交。这就是没有 GitHub Actions 时的门禁。

## 7. 二进制素材怎么不打架

Git 无法合并 PNG，所以靠规则而不是靠工具：

- **一人一目录**（见 §5），跨目录改动先在群里说一声。
- 素材成批提交：一次 PR 提交一个槽位的全部图，而不是一张一提，避免细碎历史。
- `.gitattributes` 已把 `*.png` 标成 binary，不做换行转换、不做文本合并。
- 当前 43 张约 4 MB，**不需要 Git LFS**；设计源文件（`.kra`、`.psd`、`.aseprite`）不进仓库，另存网盘。
- 真冲突了：以目录 owner 的版本为准，另一方重新导出，别手工合并二进制。

## 8. 日常节奏

| 时点 | 动作 |
| --- | --- |
| 每天开始 | `git switch main && git pull --rebase` 再开功能分支 |
| 编码中 | 每完成一个可验证小步就 commit（对应 AGENTS.md 第 1 条） |
| 收工前 | push 功能分支，PR 草稿也可以先开 |
| 每 2 天 | 一次集成：PR 合入 + 全量测试 + 部署预览环境 |
| 每周五 | 演示 10 分钟 + 打 tag（`v0.1`、`v0.2`…）+ 更新 PLAN 进度 |

晨会三句话即可：昨天做完什么、今天做什么、卡在哪。卡点超过半天就直接在群里喊，别自己憋着。

## 9. 常见坑

| 坑 | 症状 | 处理 |
| --- | --- | --- |
| 公开仓库未实名 | 建仓或推送被拒 | 先完成 Gitee 实名认证 |
| 私有仓库超过 5 人 | 仓库变成只读 | 本项目用公开仓库规避；必须私有就换阿里云 Codeup |
| SSH 22 端口不通 | `ssh -T` 超时 | 改用 HTTPS + 私人令牌 |
| 私人令牌权限不足 | push 报 403 | 重新生成令牌，勾选 projects 权限 |
| GitHub 时通时断 | push 失败 | 以 Gitee 为主，GitHub 有空再同步 |
| 忘了配钩子 | 红着测试也能提交 | 重新执行 `git config core.hooksPath .githooks` |
| `core.autocrlf=true` 混用 | 全文件 diff | 已用 `.gitattributes` 统一 LF；个人可 `git config core.autocrlf false` |
| 两人改同一文件 | 大面积冲突 | 小 PR + 目录归属，改前在群里说 |
| 素材对齐漂移 | 头像错位 | 改图后必须跑 `python -m diyface verify --all` 再提 PR |

## 10. 第一周检查表

- [ ] Gitee 仓库已建、公开，6 人都被加成「开发者」。
- [ ] 每人 `ssh -T git@gitee.com` 通过，或 HTTPS 私人令牌可用。
- [ ] 每人都执行过 `git config core.hooksPath .githooks`，提交时会自动跑测试。
- [ ] `main` 保护规则或「只走 PR」约定已确认。
- [ ] M0 骨架已在 Gitee 上，所有人 clone 后 `python -m pytest` 全绿。
- [ ] 分工表按实际意愿微调，并同步到 CODEOWNERS。
