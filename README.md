# diyface · 分层 DIY 头像生成器

用 Python 把「分层素材 + 参数化合成」做成 Web 服务：浏览器点点鼠标，服务端用 Pillow 把
脸型、发型、眼睛、嘴、配饰叠成一张头像，支持 256 与 1024 两种尺寸导出，配方可编码进链接复现。

**当前进度：M3 前端交互**（三栏点选、实时预览、换色、随机、导出与分享已可用；渲染链路与接口已完成）。

## 三步跑起来

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m uvicorn diyface.app:app --reload --port 8000
```

打开 <http://127.0.0.1:8000> 。macOS 把激活那行换成 `source .venv/bin/activate`。

## 界面

- 左侧按清单生成类目与素材格，点素材立即更新预览，点「无」清空该图层。
- 中间是 1:1 预览；请求去抖 120ms、带序号防止旧响应闪回。
- 右侧取色（预设色来自清单，不硬编码）、随机、下载 256/1024、复制分享链接。
- 配方自动写入 `localStorage`；分享链接形如 `/?r=<base64url>`，打开即复现同一张脸。
- 窄屏自动收成单列：预览置顶，类目横向滑动，所有按钮至少 44px。

## 跑测试

```powershell
python -m pytest
```

clone 之后建议执行一次，让每次提交自动跑测试：

```powershell
git config core.hooksPath .githooks
```

## 代码托管

主力仓库在 Gitee（公开，6 人协作不受私有仓库人数限制），GitHub 保留为备份镜像：

```powershell
git clone https://gitee.com/chords-of-fate/diyface.git
```

## 现有接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 三栏交互首页，内联素材清单 |
| GET | `/api/manifest` | 素材清单与默认配方 |
| GET | `/api/recipe/default` | 默认配方 |
| POST | `/api/render` | 按配方返回 PNG，带 `ETag` 与 304 缓存 |
| POST | `/api/random` | 返回合法随机配方，可带 `seed` |
| GET | `/healthz` | 版本、槽位数与素材数，部署探针用 |
| GET | `/assets/<目录>/<文件>` | 素材原图，前端当缩略图用 |

## 目录

```
src/diyface/      应用代码（app.py 路由、models.py 槽位与配方）
src/diyface/templates/   Jinja2 模板（三栏首页）
src/diyface/static/      样式与脚本（app.js、style.css）
tests/            测试（当前 170 条：159 passed, 11 skipped）
docs/             计划书、协作指南、实施手册、实验任务书
```

## 文档

- [新人上手与分工执行方案](docs/ONBOARDING.md)
- [第 1 周任务清单（手把手）](docs/WEEK-01.md)
- [给 DSH 的项目交接简报](docs/AGENT-BRIEF.md)
- [实施计划书](docs/PLAN.md)
- [六人分工实施手册](docs/HANDBOOK.md)
- [协作与 Gitee 托管指南](docs/COLLABORATION.md)
- [实验任务书](docs/DIY头像生成器-实验任务书.docx)
