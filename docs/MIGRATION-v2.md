# 契约迁移说明 v2（10 槽位 / Flask / 80KB）

2026-11-15，项目按《虚拟头像设计系统 · 项目说明与分工》v1.0 调整了数据契约与技术栈。
这份文档记录**改了什么、为什么改、谁需要跟着改**，避免有人拿旧文档对着新代码。

## 1 三个变化

| 项 | 迁移前 | 迁移后 | 影响 |
| --- | --- | --- | --- |
| 槽位 | 12 个（含鼻子、腮红，4 个预留） | **10 个全部启用**，新增后发 `hair_back` | `models.py`、素材目录、清单、全部测试 |
| Web 框架 | FastAPI + uvicorn | **Flask 3 + Jinja2** | `app.py`、接口测试、启动命令 |
| 单张素材体积 | 120KB | **80KB** | `validate.py` 阈值、素材压缩 |
| 对齐基线 | 脸中心 448、头顶 256 | **脸中心 500、头顶 170、眼 460、嘴 620、肩线 880** | 参考图、所有素材坐标 |

## 2 新槽位表（唯一真源：`src/diyface/models.py`）

| z | 槽位 | 中文 | 可着色 | 目录 | 目标数量 |
| --- | --- | --- | --- | --- | --- |
| 10 | skin | 脸型 | 是 | `01_skin/` | 2 |
| 20 | clothes | 服装 | 是 | `02_clothes/` | 6 |
| 25 | hair_back | 后发 | 是 | `03_hair_back/` | 6 |
| 30 | hair | 前发 | 是 | `04_hair/` | 8 |
| 40 | eyes | 眼睛 | 是 | `05_eyes/` | 8 |
| 45 | brows | 眉毛 | 是 | `06_brows/` | 4 |
| 50 | mouth | 嘴 | 是 | `07_mouth/` | 7 |
| 60 | glasses | 眼镜 | 否 | `08_glasses/` | 5 |
| 70 | hat | 帽子 | 是 | `09_hat/` | 5 |
| 80 | extra | 配饰 | 否 | `10_extra/` | 3 |
| — | 合计 | — | — | — | 54 |

与旧表的差异：

- **去掉** `nose`、`cheeks`（鼻子直接画在脸型上，腮红本期不做）；
- **`bangs` 改名 `hair`**（前发），**`side_hair` 改名 `hair_back`**（后发）；
- `eyes` 由「不可着色」改为**可着色**（眼珠颜色可换），所以眼睛素材要白底 + 蒙版；
- `extra` 由可着色改为**不可着色**；
- z 序整体重排，服装压在最下面（z=20），帽子在 z=70。

## 3 需要跟着改的地方

| 角色 | 要改什么 |
| --- | --- |
| 素材（P1） | 按新目录与新基线画；示例文件名见 `docs/PLAN.md` §6 与 `docs/WEEK-01.md` |
| 渲染（P2） | 无代码改动，`models.SLOTS` 已是新表；确认 `verify` 与快照仍绿 |
| 前端（P3） | 类目仍从 manifest 读，不写死；把「发型」文案改成「前发/后发」 |
| 后端（P4） | 启动命令改为 `python -m flask --app diyface.app run`；新增 `/api/analyze`、`/api/works` |
| 视觉（P5） | 照片分析产出的 Recipe 必须写这 10 个键 |
| 质量（P6） | 覆盖率、素材校验阈值（80KB）、契约测试全部按新表 |

## 4 启动与依赖

```powershell
pip install -e ".[dev]"
python -m flask --app diyface.app run --debug --port 8000
```

`pyproject.toml` 的依赖里已经去掉了 `fastapi` / `uvicorn`，加上了 `flask>=3.0`。
如果本地环境是旧的，先 `pip install -e ".[dev]"` 重装一次。

## 5 一个容易踩的细节：眼睛的 tint 蒙版

`eyes` 曾计划改为可着色；改用 Adventurer 素材后，眼睛是黑白线稿，没有可染的虹膜区，
最终**定为不可着色**（`tintable=False`）。
否则换色时眼白也会被染色——现在的占位素材就是整只涂白，看起来像蓝色巩膜。

正确做法：在蒙版里只把虹膜区域填白，眼白保持黑色（= 不上色），瞳孔与描边本来就不该变色。

## 6 兼容性说明

- **旧配方不再合法**：带 `bangs` / `side_hair` / `nose` / `cheeks` 键的 JSON 会被 422 拒绝。
  如果手上有旧分享链接，把键名按上表替换即可。
- **旧素材路径变化**：`02_bangs/` → `04_hair/`，`06_eyes/` → `05_eyes/`，`09_glasses/` → `08_glasses/`。
  仓库里已有的素材已在迁移提交中随之移动。
- **快照基准已重建**：因为脸型坐标与眼睛着色方式变了，`tests/fixtures/golden/*.png` 重新生成过。

## 7 还没做的部分

| 功能 | 归属 | 状态 |
| --- | --- | --- |
| `POST /api/analyze`（照片转配方） | P5 | 未开始 |
| `POST/GET /api/works`（SQLite 作品存储） | P4 | 未开始 |
| 6 套预设模板 | P3 | 未开始 |
| 54 张正式素材 | P1 | 现有 16 张（占位 3 + 面部 13） |

`docs/ONBOARDING.md`、`docs/WEEK-01.md`、`docs/COLLABORATION.md` 已按 P1–P6 重写；
角色归属与素材数量以 `docs/PLAN.md` 与 docx 为准。
