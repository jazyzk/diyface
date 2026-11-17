# 新人上手与六人分工执行方案

这份文档解决三件事：**怎么进仓库**、**怎么配环境**、**六个人各自本周干什么**。
计划与验收标准见 [PLAN.md](PLAN.md)，协作细则见 [COLLABORATION.md](COLLABORATION.md)。

## 1 加入仓库

1. 注册 Gitee 并完成实名（公开仓库要求）。
2. 把用户名发给队长，队长在「管理 → 仓库成员管理」里加你为**开发者**。
3. 克隆：

```powershell
git clone https://gitee.com/chords-of-fate/diyface.git
cd diyface
git config user.name "你的名字"
git config user.email "你的邮箱"
```

4. 配 SSH（推荐，一次到位）：

```powershell
ssh-keygen -t ed25519 -C "gitee@diyface"
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | Set-Clipboard
```

把公钥贴到 Gitee → 设置 → SSH 公钥；`ssh -T git@gitee.com` 看到 `Hi ...` 即成功。

## 2 配好环境

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e ".[dev]"
python -m pytest
git config core.hooksPath .githooks
```

macOS / Linux 把激活那行换成 `source .venv/bin/activate`。

跑起来：

```powershell
python -m flask --app diyface.app run --debug --port 8000
```

打开 <http://127.0.0.1:8000>，能看到三栏界面即成功。

素材相关的三条命令（P1 每天都要用）：

```powershell
python -m diyface verify          # 校验尺寸、模式、透明度、命名、体积、蒙版
python -m diyface build-thumbs    # 重建 256 缩略图
python scripts/make_guide.py      # 生成参考线图 assets/_guide.png
```

期望基线：`265 passed, 11 skipped`。看到这个数字才算环境对了。

## 3 第一次提交

练手 PR 走完四步，别只敲命令不理解：

```powershell
git switch -c feat/你的名字-hello
# 随便改一个文档里的错别字
git add -A
git commit -m "docs(onboarding): 修正错别字"
git push -u gitee feat/你的名字-hello
```

然后在 Gitee 网页上「Pull Requests → 新建」，源分支选你的，目标选 `main`，
找一位队友点「审查通过」，队长选 **Squash** 合并并删除源分支。

合并后回到本地：

```powershell
git switch main
git pull --rebase
```

## 4 六个人分别怎么干

### 4.1 P1 素材与美术

**本周目标**：交 22 张合规素材（脸型 2、前发 8、眼睛 8、嘴 4），并让 `verify` 零报错。

步骤：

1. 跑 `python scripts/make_guide.py --reference assets/01_skin/skin_base.png` 生成参考线。
2. 先画两张脸型（脸中心 y=500、头顶 y=170），当天提交，别人要拿去对位。
3. 按「前发 → 眼睛 → 嘴」顺序推进，每 3 张跑一次 `python -m diyface verify --slot hair`。
4. 可着色素材用白色打底；缺蒙版用 `python -c "from PIL import Image; Image.new('RGBA',(1024,1024),(255,255,255,255)).save('assets/04_hair/hair_x_01_tint.png')"` 补。
5. 每批提交：`feat(assets): 前发 4 张`，周五提 PR。

### 4.2 P2 渲染内核

**本周目标**：合成、着色、多尺寸、命令行全部可用，快照测试建立基线。

步骤：

1. 读懂 `models.py` 的 10 个槽位与 z 序，这是唯一真源。
2. 跑 `python -m pytest tests/test_render.py -q`，确认现有合成行为。
3. 用 `python -m diyface render tests/fixtures/recipes/base.json --out tests/reports/a.png` 手验一张图。
4. 改 `render.py` 前先加测试：空配方透明、图层顺序、着色不改描边。
5. 快照基线用 `pytest --update-golden` 重建，提交时说明为什么变。

### 4.3 P3 前端体验

**本周目标**：三栏布局、素材网格、「无」按钮、取色器、去抖预览全部可用。

步骤：

1. `templates/index.html` 里清单是内联注入的，类目由 manifest 生成，不要写死。
2. 打开页面看 `app.js` 是否按 `status` 渲染素材格。
3. 加「无」按钮：点它把该槽位置为 `null` 并重渲染。
4. 取色器预设色来自清单的 `default_color`，不要硬编码。
5. 用键盘 Tab 走一遍全流程，确认焦点可见。

### 4.4 P4 后端与数据

**本周目标**：Flask 骨架、清单接口、渲染接口、静态资源、健康检查全部可用。

步骤：

1. 读 `app.py` 的五个路由，`pytest tests/test_api.py -q` 确认契约。
2. 新增路由前先写契约测试（正常 + 异常 + 错误结构）。
3. 错误统一 `{"error": {"code", "message", "field"}}`。
4. 静态资源走 `/assets/<path>`，不要绕过 Flask 直接暴露目录。
5. 用 `curl http://127.0.0.1:8000/healthz` 验证部署探针。

### 4.5 P5 视觉与训练

**本周目标**：人脸检测 Demo 跑通，CelebA 子集下载完成，CPU 训练可行。

步骤：

1. 装 `opencv-python` 与 `scikit-learn`（写进 `pyproject.toml` 的 dev 依赖前先和队长确认）。人脸检测用 OpenCV 自带的 YuNet，模型文件 `face_detection_yunet_2023mar.onnx` 约 340 KB。
2. 用 `cv2.FaceDetectorYN` 对一张正脸照跑检测，输出人脸框与五个关键点，并保存调试图。
3. 下载 CelebA 子集 5000 张与属性标签，放 `data/`（`.gitignore` 里忽略）。
4. 用预训练特征 + `LogisticRegression` 跑一次眼镜分类，记录准确率。
5. 照片只在内存处理，不落盘；接口返回后丢弃原图。

### 4.6 P6 质量与交付

**本周目标**：测试框架、素材校验进 CI、文档骨架、提交钩子全部可用。

步骤：

1. 确认 `python -m pytest` 全绿，覆盖率 `pytest --cov=src/diyface`。
2. 检查 `.githooks/pre-commit` 是否会自动跑测试。
3. 把素材校验加进 CI：`python -m diyface verify`。
4. 维护 `docs/`：契约变了就同步 PLAN 与 MIGRATION。
5. 周五整理本周测试数量、覆盖率、素材张数，发到群里。

## 5 每周节奏

| 时间 | 动作 |
| --- | --- |
| 每天开工 | `git pull --rebase`，跑一次 `python -m pytest` |
| 每天站会 | 昨天做了什么、今天做什么、卡在哪 |
| 周二 / 周四 | 集成日：合 PR、跑全量测试、重建缩略图 |
| 周五 | 演示 10 分钟；`git tag v0.x`；下周计划写进 PR 草稿 |

## 6 交付与验收

| 里程碑 | 判定标准 | 验收人 |
| --- | --- | --- |
| M1 | 捏脸路径闭环可用（点选、预览、下载） | P6 与队长 |
| M2 | 照片路径可用、作品可存可分享 | P6 与队长 |
| M3 | 功能冻结、测试全绿、材料齐备 | 全员 |

日常自检：

- [ ] `python -m pytest` 全绿。
- [ ] `python -m diyface verify` 零报错。
- [ ] 新素材的缩略图已重建。
- [ ] 提交信息符合 `类型(范围): 说明`。

## 7 速查

| 我要做什么 | 命令 |
| --- | --- |
| 跑服务 | `python -m flask --app diyface.app run --debug` |
| 跑测试 | `python -m pytest` |
| 只跑接口测试 | `python -m pytest tests/test_api.py -q` |
| 校验素材 | `python -m diyface verify` |
| 重建缩略图 | `python -m diyface build-thumbs` |
| 渲染一张 | `python -m diyface render <recipe.json> --out a.png` |
| 重建快照 | `python -m pytest tests/test_golden.py --update-golden` |
| 看提交历史 | `git log --oneline -10` |
