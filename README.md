# diyface · 分层 DIY 头像生成器

用 Python 把「分层素材 + 参数化合成」做成 Web 服务：浏览器点点鼠标，服务端用 Pillow 把
脸型、发型、眼睛、嘴、配饰叠成一张头像，支持 256 与 1024 两种尺寸导出，配方可编码进链接复现。

**当前进度：M0 骨架**（页面与接口可用，渲染管线在 M1 接入）。

## 三步跑起来

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m uvicorn diyface.app:app --reload --port 8000
```

打开 <http://127.0.0.1:8000> 。macOS 把激活那行换成 `source .venv/bin/activate`。

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
| GET | `/` | 首页，列出 v1 启用的 8 个槽位 |
| GET | `/api/manifest` | 素材清单骨架（M1 接上目录扫描） |
| GET | `/api/recipe/default` | 默认配方 |
| GET | `/healthz` | 版本与槽位数，部署探针用 |

## 目录

```
src/diyface/      应用代码（app.py 路由、models.py 槽位与配方）
src/diyface/templates/   Jinja2 模板
src/diyface/static/      样式与脚本
tests/            测试（当前 51 条）
docs/             计划书、协作指南、实施手册、实验任务书
```

## 文档

- [实施计划书](docs/PLAN.md)
- [六人分工实施手册](docs/HANDBOOK.md)
- [协作与 GitHub 托管指南](docs/COLLABORATION.md)
- [实验任务书](docs/DIY头像生成器-实验任务书.docx)
