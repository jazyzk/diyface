# 团队协作与 GitHub 托管指南（6 人）

配套 [docs/PLAN.md](PLAN.md)：那份讲「做什么」，这份只讲「怎么一起做」。
角色分工的逐步操作教程在 [docs/HANDBOOK.md](HANDBOOK.md)，六个人各看自己那一章。

## 1. 现状与卡点

| 事项 | 状态 | 说明 |
| --- | --- | --- |
| 本地仓库 | 就绪 | `master` 分支，3 个提交，工作区干净 |
| 网络至 GitHub | 可用 | 需 `http.sslBackend=openssl`，默认 schannel 握手失败 |
| `gh` CLI | 未安装 | 可用 `winget install --id GitHub.cli -e` 补上 |
| SSH 密钥 | 无 | 需生成并把公钥加到 GitHub |
| 远端仓库 | 未创建 | 见 §2 |
| 账号授权 | 待你完成 | 登录/授权必须在浏览器里由人完成，我无法代办 |

结论：**可以上传，只差一个远端地址和一次授权**。

## 2. 一次性建仓（约 5 分钟）

先定归属：课程/社团项目建议建在**个人账号 + 邀请协作者**，长期维护再迁 Organization。仓库名建议 `diyface`，Private 即可。

路线 A（网页建仓，最稳）：

1. GitHub → New repository → 名称 `diyface` → **不要**勾选 README / .gitignore / license（避免首次推送冲突）。
2. 回到本机执行：

```powershell
git remote add origin git@github.com:<你的用户名>/diyface.git
git branch -M main
git push -u origin main
```

路线 B（`gh` CLI 一步到位）：

```powershell
winget install --id GitHub.cli -e
gh auth login --git-protocol ssh
gh repo create diyface --private --source . --remote origin --push
```

注意两点：

- 当前分支叫 `master`，建议改 `main` 与外网惯例一致（上面已含 `git branch -M main`）。
- 首次推送前确认 `.gitignore` 与 `.gitattributes` 已提交，否则队友一 clone 就撞上换行与缓存问题。

## 3. 授权方式三选一

| 方式 | 步骤 | 优点 | 注意 |
| --- | --- | --- | --- |
| SSH 密钥（推荐） | 生成 ed25519 → 公钥贴到 GitHub → `ssh -T git@github.com` 验证 | 一次配置长期免密；不涉及令牌泄露 | 每台新机器各配一次 |
| `gh` CLI | `gh auth login`，浏览器点一下 | 顺手能建仓、开 PR、看 CI | 需先安装，200MB 级依赖 |
| HTTPS + PAT | 生成细粒度令牌（repo 权限）→ 首次 push 时粘贴 | 无需装东西 | 令牌会进凭据管理器，需定期轮换，泄露后要立刻吊销 |

SSH 具体命令（PowerShell）：

```powershell
ssh-keygen -t ed25519 -C "luna@diyface"
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | Set-Clipboard
ssh -T git@github.com
```

把剪贴板内容贴到 GitHub → Settings → SSH and GPG keys → New SSH key；`ssh -T` 回一句 `Hi <用户名>! You've successfully authenticated` 即成功。若设了口令，需启动 ssh-agent：

```powershell
Set-Service ssh-agent -StartupType Automatic
Start-Service ssh-agent
ssh-add "$env:USERPROFILE\.ssh\id_ed25519"
```

## 4. 仓库设置（建完立刻做）

1. **邀请成员**：Settings → Collaborators → Add people，逐个加 5 人；或建 Organization + Team 统一管理。
2. **保护 `main`**：Settings → Branches → 要求 Pull Request、至少 1 个审批、必须通过状态检查、禁止直推。
3. **开启 Actions**：M0 提交 CI 后，把 `pytest` 设为必需检查。
4. **仓库信息**：写一句描述、加 Topics（`avatar` `fastapi` `pillow`），许可证按课程要求选 MIT 或不加。

一个现实限制：**私有仓库的分支保护在免费计划下不可用**（公开仓库免费）。若没有付费计划，就靠约定执行「不直推 main、一律 PR」；这条已写进 §6。

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

- `main` 只接受 PR；功能分支命名 `feat/<域>-<简述>`，修复用 `fix/...`，例：`feat/render-zorder`。
- 一个 PR 只做一件事，控制在 400 行内；超过就拆。
- 合并方式统一 **Squash and merge**，保持 `main` 线性历史。
- 提交信息用 Conventional Commits：`feat / fix / test / docs / chore(scope): 说明`。
- 仓库根的 `AGENTS.md` 是硬约定：**每改必提、每改必测**。PR 描述里贴出实际执行的测试命令与结果，CI 未绿不合并、不交付。

## 7. 二进制素材怎么不打架

Git 无法合并 PNG，所以靠规则而不是靠工具：

- **一人一目录**（见 §5），跨目录改动先在群里说一声。
- 素材成批提交：一次 PR 提交一个槽位的全部图，而不是一张一提，避免细碎历史。
- `.gitattributes` 已把 `*.png` 标成 binary，不做换行转换、不做文本合并。
- 当前 43 张约 4 MB，**不需要 Git LFS**；设计源文件（`.kra`、`.psd`、`.aseprite`）不进仓库，另存网盘。
- 真冲突了：以目录 owner 的版本为准，另一方 `git rebase --onto` 或重新导出，别手工合并二进制。

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
| `core.autocrlf=true` 混用 | 全文件 diff、互相覆盖 | 已用 `.gitattributes` 统一 LF；个人可 `git config core.autocrlf false` |
| 强推覆盖 `main` | 队友提交消失 | 保护规则 + 禁止 force push；永远只强推自己的功能分支 |
| 提交了密钥或大文件 | 仓库体积暴涨、令牌泄露 | `.gitignore` 前置；泄露立即吊销令牌；历史用 `git filter-repo` 清理 |
| 路径大小写不一致 | macOS/Linux 下文件丢失 | 文件名一律小写，含中文的文件名尽量避免 |
| 两人改同一文件 | 大面积冲突 | CODEOWNERS + 小 PR + 目录归属 |
| 素材对齐漂移 | 头像错位 | 改图后必须跑 `python -m diyface verify --all` 再提 PR |

## 10. 第一周检查表

- [ ] 仓库已在 GitHub，6 人全部收到邀请并 clone 成功。
- [ ] 每人 `ssh -T git@github.com` 通过（或 `gh auth status` 正常）。
- [ ] `main` 保护规则或「只走 PR」约定已确认。
- [ ] CI 在首个 PR 上跑通（哪怕是 3 条冒烟测试）。
- [ ] M0 骨架合入，所有人本地 `python -m unittest discover -s tests` 能绿。
- [ ] 分工表已按实际意愿微调，并同步到 CODEOWNERS。
