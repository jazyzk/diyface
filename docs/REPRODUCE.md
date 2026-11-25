# 复现与上线指南（给另一台电脑 / 另一个 DSH 会话）

> 目标读者：没有参与开发的人，或者另一个 AI 代理（DSH）。
> 照着做完，应该得到一个**和原作者本机一模一样的网站**，并能把它部署到公网。

## 0. 先给结论

| 问题 | 答案 |
| --- | --- |
| Gitee 仓库能完整复现本机网页吗？ | **能**。代码、179 张素材（含缩略图与蒙版）、测试、文档全部在库里 |
| 有什么是库里没有的？ | 只有**可选的 OCR 运行库**（`tesseract.exe` + `tessdata/`，约 50MB，见 §6）和本地缓存 |
| 部署到公网要花钱吗？ | 不需要，免费二级域名即可，见 §7 |

## 1. 环境要求

| 项 | 要求 | 说明 |
| --- | --- | --- |
| Git | 任意版本 | 拉代码 |
| Python | **3.12**（3.10+ 可用） | 部署平台统一 3.12；本机 3.14 也跑得通 |
| 磁盘 | ≥ 200MB | 素材 + 依赖 |
| Tesseract | **可选** | 只有「导入图纸截图自动认色号」需要 |

## 2. 获取代码

```powershell
git clone https://gitee.com/chords-of-fate/diyface.git
cd diyface
git checkout feat/flask-contract
```

## 3. 安装并自检（关键）

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"

python scripts/doctor.py            # 环境自检，全 [OK] 才继续
python -m pytest -q                 # 应全绿（少数 OCR 用例在无 tesseract 时跳过）
python -m diyface verify            # 应输出「149 张素材，问题 0」（含缩略图与蒙版）
```

`doctor.py` 期望输出（数值必须一致）：

```
[OK]   素材总数      179 张（期望 179）
[OK]   槽位数量      7 个（期望 7）
[OK]   风格数量      3 套（期望 3）
[OK]   背景数量      8 个（期望 8）
```

> `verify` 统计的是全部 PNG（含 `_thumb` 与 `_tint`），数量会比 179 多，只要「问题 0」即可。

## 4. 启动

```powershell
python -m flask --app diyface.app run --port 8000
# 或：python scripts/serve.py --port 8000   （会打印本机与局域网地址）
```

打开 <http://127.0.0.1:8000>。

## 5. 功能验收清单

逐项走一遍，任何一项不符就停下来查：

| 路径 / 操作 | 期望 |
| --- | --- |
| `/healthz` | `{"assets":179,"ok":true,"slots":7,"version":"0.1.0"}` |
| 首页 | 三套风格标签（美式卡通 / 手绘线稿 / 像素方块），默认像素 |
| 左侧类目 | 脸型 31、前发 32、眼睛 40、眉毛 11、嘴 33、眼镜 14、配饰 18 |
| 点「随机一张」 | 只出当前一套风格，不会混搭 |
| `/pixel` | 32×32 画布、128 色板（Mard 色号）、行列标尺 |
| `/pixel` →「导入图片」 | 上传彩色像素图，能还原成画布 |
| `/pixel` →「导入色号表」 | 粘贴 `H2 H7 E15` 这样的文本能生成 |
| `/pixel` →「导入图纸截图」 | 自动切格；装没装 OCR 的区别见 §6 |
| 「贴到头像上」 | 回到编辑器后可拖动、缩放、删除、导出带贴纸 |
| 下载 1024 | 透明 PNG，1024×1024 |

## 6. 和作者本机的唯一差异：OCR

`tesseract.exe`、`tessdata/`、`*.dll` 是本地运行库，**没有进仓库**（`.gitignore` 已排除），原因：

- 体积约 50MB，且属于第三方二进制；
- 不装也能用：图纸导入会退化成「自动切格 + 手选色号」。

想启用自动识别：

1. 把便携版 `tesseract.exe` 与 `tessdata/` 放到**项目根目录**；
2. 重跑 `python scripts/doctor.py`，OCR 一行应为 `[OK] … 可用`；
3. 页面提示会变成「已用 OCR 预填色号，请核对」。

详细步骤见 [OCR.md](OCR.md)。

## 7. 部署到公网（免费二级域名）

按 [DEPLOY-FREE.md](DEPLOY-FREE.md) 做，最短路径：

1. 仓库镜像到 GitHub（Gitee 仓库对部分平台不友好）：

   ```powershell
   git remote add github https://github.com/<你的账号>/diyface.git
   git push github feat/flask-contract:main
   ```

2. Render → **New + → Blueprint** → 选仓库（自动读 `render.yaml`）；
3. 等 2～4 分钟，拿到 `https://diyface-xxxx.onrender.com`；
4. 打开 `/healthz` 复核。

若不用 Blueprint 而是手动建 Web Service，填：

| 字段 | 值 |
| --- | --- |
| Language | Docker（仓库有 Dockerfile）或 Python 3 |
| Branch | `main` |
| Build Command | `pip install .` |
| Start Command | `waitress-serve --listen=0.0.0.0:$PORT diyface.app:app` |
| Health Check Path | `/healthz` |
| Instance Type | Free |

> Docker 模式已改成读 `$PORT`，不要再把端口写死。

## 8. 给 AI 代理（DSH）的执行约定

1. **每步都验证**：跑完命令核对期望输出，不符就停，不要"继续下一步看看"。
2. **失败要报原文**：贴命令 + 退出码 + 最后 15 行日志，不要只写"失败了"。
3. **不要提交这些**：`.venv/`、`tools/`、`tessdata/`、`*.exe`、`*.dll`、`tests/reports/`、`dist/`。
4. **改代码必须带测试**：至少 `python -m pytest -q` 全绿再提交。
5. **提交信息格式**：`<type>(<scope>): <中文摘要>`，例如 `fix(deploy): Docker 监听 PORT`。
6. **素材改动必须重建缩略图**：`python -m diyface build-thumbs`，再跑 `verify`。
7. **同步两个远端**（如果同时维护 GitHub 镜像）：

   ```powershell
   git push gitee feat/flask-contract
   git push github feat/flask-contract:main
   ```

## 9. 故障排查

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `ModuleNotFoundError: diyface` | 没装包 | `pip install -e ".[dev]"` |
| `assets not found` / `/healthz` 里 assets 为 0 | 工作目录不对 | 在仓库根目录启动，或设 `DIYFACE_ASSETS=<repo>/assets` |
| 素材 404 | 缩略图没生成 | `python -m diyface build-thumbs` |
| 页面样式很旧 | 浏览器缓存 | `Ctrl+F5` |
| Render 构建失败 | 依赖或端口 | 看日志；Docker 已读 `$PORT`，Python 模式用上面的 Start Command |
| Render 打开 500 | 多半是素材路径 | 设 `DIYFACE_ASSETS=/opt/render/project/src/assets` |
| 图纸 OCR 没反应 | 没装 tesseract | 见 §6，或手动选色号 |
| `waitress-serve` 找不到 | 没装 waitress | `pip install waitress` |
