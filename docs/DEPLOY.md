# 部署：让别人打开一个网址就能用

三种方式，按「省事程度」从高到低排。前两种都不需要别人和你同一个网络。

## 方案 A：Render 免费托管（推荐，网址长期有效）

适合：交给老师验收、组员随时打开、不用一直开着自己的电脑。

1. 注册 <https://render.com>（用 GitHub 账号登录最省事）。
2. 把仓库镜像到 GitHub（Gitee 也能被拉取，但 Render 对 GitHub 支持最好）：

   ```powershell
   git remote add github https://github.com/<你的用户名>/diyface.git
   git push github feat/flask-contract:main
   ```

3. Render 控制台 → **New → Blueprint** → 选这个仓库。
   仓库根目录已有 `render.yaml`，它会自动读：

   ```yaml
   buildCommand: pip install .
   startCommand: python -m waitress --host=0.0.0.0 --port=$PORT diyface.app:app
   healthCheckPath: /healthz
   ```

4. 等 2~4 分钟，拿到 `https://diyface-xxxx.onrender.com`，谁都能打开。

注意：
- 免费档 15 分钟没人访问会休眠，**第一次打开要等 30 秒左右**唤醒；
- 素材 67 张 PNG 都在仓库里，冷启动会稍慢，属正常。

## 方案 B：临时隧道（最快，10 分钟就能发链接）

适合：课上现场演示、发给组员临时看。**你的电脑要开着**。

```powershell
# 1) 本机起服务（监听所有网卡）
python scripts/serve.py --port 8123 --tunnel

# 2) 另开一个窗口，选一种隧道
cloudflared tunnel --url http://127.0.0.1:8123      # 无需账号，返回 *.trycloudflare.com
ssh -R 80:localhost:8123 nokey@localhost.run        # 无需账号，返回 *.lhr.life
```

`cloudflared` 下载：<https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/>
Windows 下解压得到一个 `cloudflared.exe`，放在 PATH 里或直接写全路径。

隧道地址是临时的，关掉窗口就失效，**不要写进报告当正式链接**。

## 方案 C：自己的云服务器（最稳）

适合：想长期挂着、或者课程要求「部署上线」。

```bash
# Ubuntu 服务器上
git clone https://gitee.com/chords-of-fate/diyface.git
cd diyface
python3 -m venv .venv && source .venv/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e ".[prod]"

# 用 gunicorn（Linux）或 waitress（跨平台）跑起来
python -m waitress --host=0.0.0.0 --port=8000 diyface.app:app
```

再配 nginx 反向代理 + 域名 + HTTPS（Let's Encrypt）。开 80/443 端口，安全组放行。

## 常见问题

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 别人打开「拒绝连接」 | 服务只监听 127.0.0.1 | 用 `--host 0.0.0.0`，或直接用 `scripts/serve.py` |
| 同一 Wi-Fi 也打不开 | 校园网开了客户端隔离 | 换方案 A 或 B |
| 页面能开但预览不更新 | 后端没起来 / 500 | 看 `/healthz` 是否 200 |
| Render 第一次打开很慢 | 免费档休眠唤醒 | 正常，等 30 秒 |
| 图片 404 | 素材没提交 | `git status` 看 `assets/` 是否完整 |

## 关于端口

- 本地开发：`python -m flask --app diyface.app run --debug`（8000）
- 演示/部署：`python scripts/serve.py` 或 `waitress`，监听 `0.0.0.0`
- Render 会通过 `$PORT` 注入端口，`render.yaml` 已经处理好了
