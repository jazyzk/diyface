# 免费二级域名上线（不买域名、不备案）

目标：**拿到一个 `https://xxx.onrender.com` 这样的网址，谁都能打开，不花钱、不用备案。**

## 部署前必须知道的两件事

1. **仓库要能被平台拉到**。Gitee 公开仓库理论上可以，但多数平台（Render / Railway / Vercel）对 GitHub 支持最好；
   如果卡在拉取那一步，用 GitHub 镜像（见文末）。
2. **OCR 不会带上线**。`tesseract.exe` 和 `tessdata/` 是本地运行库，没有进仓库（约 50MB）。
   线上图纸导入仍能自动切格，只是没有 OCR 预填色号，需要手选——这是有意的取舍。

## 方案 A：Render（推荐，免费额度足够演示）

1. 打开 <https://render.com>，用 GitHub 账号登录；
2. 右上 **New +** → **Web Service**；
3. 选择仓库：
   - 有 GitHub 镜像 → 直接选仓库（能自动读 `render.yaml`）；
   - 只有 Gitee → 选 **Public Git repository**，粘贴：
     `https://gitee.com/chords-of-fate/diyface.git`
4. 按下表填写：

   | 字段 | 值 |
   | --- | --- |
   | Name | `diyface` |
   | Branch | `feat/flask-contract` |
   | Runtime | `Python 3` |
   | Build Command | `pip install .` |
   | Start Command | `waitress-serve --listen=0.0.0.0:$PORT diyface.app:app` |
   | Health Check Path | `/healthz` |
   | Instance Type | `Free` |

5. 点 **Deploy**，等 2～4 分钟，日志出现 `Serving on http://0.0.0.0:10000` 即成功；
6. 顶部会给网址：`https://diyface-xxxx.onrender.com`。

免费档注意：**15 分钟无人访问会休眠**，第一次打开要等 20～30 秒唤醒，属正常。

## 方案 B：Railway

1. <https://railway.app> 用 GitHub 登录；
2. **New Project → Deploy from GitHub repo**；
3. 仓库根目录已有 `Procfile`，Railway 会自动读：

   ```
   web: waitress-serve --listen=0.0.0.0:$PORT diyface.app:app
   ```

4. 在 **Settings → Networking → Generate Domain** 生成 `https://xxx.up.railway.app`。

## 方案 C：Zeabur（国内访问相对快）

1. <https://zeabur.com> 用 GitHub 登录；
2. 新建项目 → 部署 Git 仓库 → 选择本仓库；
3. 平台会识别 `Procfile` / `Dockerfile`，直接构建；
4. 在「网络」里生成免费二级域名。

## 只有 Gitee 仓库怎么办

把仓库镜像到 GitHub（不用迁移，只是多一个 remote）：

```powershell
cd D:\头像diy
git remote add github https://github.com/<你的用户名>/diyface.git
git push github feat/flask-contract:main
```

之后在 Render 里选这个 GitHub 仓库即可，`render.yaml` 会被自动识别。

## 上线后自查

打开 `https://你的域名/healthz`，应返回：

```json
{"assets": 179, "ok": true, "slots": 7, "version": "0.1.0"}
```

再检查三处：

1. `/pixel` 能画、能导出；
2. 编辑器切换风格、随机、下载正常；
3. 素材图片能加载（`/assets/01_skin/...`）。

## 常见问题

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 构建失败 `No matching distribution` | 依赖太新 | 换成 `python-3.12.6`（`runtime.txt` 已写） |
| 打开 500，日志 `assets not found` | 工作目录不对 | 设环境变量 `DIYFACE_ASSETS=/opt/render/project/src/assets` |
| 首次打开很慢 | 免费档休眠 | 正常，等 30 秒 |
| 图纸导入没有 OCR | 运行库没上传 | 正常；线上用「导入图片」或手动选色号 |
| 页面样式旧 | 浏览器缓存 | `Ctrl+F5` |
