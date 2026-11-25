# 任务卡：在目标电脑上复现并上线 diyface（给 DSH 代理）

把下面「复制这段」整段发给对方的 DSH，它会照做。人也可以照着做，命令一样。

---

## 复制这段

```
任务：在目标电脑上把 diyface 项目跑起来，并（可选）部署到公网。

代码：https://gitee.com/chords-of-fate/diyface
分支：feat/flask-contract
说明：仓库里的 docs/REPRODUCE.md 是完整手册，按它执行；下面是要点。

必须按顺序做，每步核对输出：
1. git clone 上面的仓库，切到 feat/flask-contract
2. 建虚拟环境并安装：pip install -e ".[dev]"
3. 跑 python scripts/doctor.py，必须全部 [OK]
   - 若「素材总数」不是 179，停止并报告
4. 跑 python -m pytest -q，必须全绿（无 tesseract 时 OCR 用例会 skip，属正常）
5. 跑 python -m diyface verify，最后一行必须是「问题 0」
6. 启动：python -m flask --app diyface.app run --port 8000
7. 打开 http://127.0.0.1:8000 验收：
   - /healthz 返回 {"assets":179,"ok":true,"slots":7,...}
   - 首页有三套风格标签，默认「像素方块」
   - 左侧类目数量：脸型31 前发32 眼睛40 眉毛11 嘴33 眼镜14 配饰18
   - 点「随机一张」只出当前风格
   - /pixel 有 32×32 画布、128 色板、能导出 1024

约束（不要做这些）：
- 不要提交 .venv/、tools/、tessdata/、*.exe、*.dll、tests/reports/、dist/
- 不要改被测断言的期望值来让测试通过；失败就报告原文
- 改任何代码都必须带测试，且 pytest 全绿后才能提交

部署（可选，用户明确要求再做）：
- 照 docs/DEPLOY-FREE.md，Render 选 Blueprint 最省事
- 手动建服务时：Language=Docker（或 Python 3）、Branch=main、
  Build=pip install .、Start=waitress-serve --listen=0.0.0.0:$PORT diyface.app:app、
  Health Check Path=/healthz、Instance=Free
- 部署完打开 <网址>/healthz，assets 必须是 179

报告格式：
- 每步：命令 + 退出码 + 关键输出（各 1~3 行）
- 失败：贴最后 15 行日志，说明卡在第几步
- 成功：给出启动地址；如果部署了，给出公网地址
```

---

## 这一步在干什么（给人看）

| 步骤 | 目的 | 不通过说明 |
| --- | --- | --- |
| `doctor.py` | 环境/依赖/素材是否齐 | 少素材 → clone 不完整；缺依赖 → 装包失败 |
| `pytest` | 代码与素材规格是否自洽 | 有红 → 环境或版本问题，别硬跑 |
| `verify` | 179 张素材是否合规 | 有问题 → 素材被改坏或缩略图没生成 |
| `/healthz` | 服务真的起来了 | assets≠179 → 工作目录或素材路径不对 |

## 一个必须知道的差异

OCR（图纸截图自动认色号）依赖本地 `tesseract.exe` + `tessdata/`，**没有进仓库**。
对方没装时：图纸导入仍能自动切格，只是要手动选色号。装法见 [OCR.md](OCR.md)。
