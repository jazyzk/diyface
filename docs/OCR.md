# OCR（可选）：让图纸截图自动认出色号

不装也能用：图纸导入会走「自动切格 + 图案聚类 + 手动选色号」。
装了之后，每一类图案会自动预填色号，你只需要核对一下再点「应用图纸」。

## 安装（Windows）

1. **Tesseract-OCR**

   下载安装包（UB Mannheim 维护的 Windows 版）：
   <https://github.com/UB-Mannheim/tesseract/wiki>

   安装时**勾选 Chinese (Simplified)** 与默认英文即可；装完默认路径：

   ```
   C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

   装到别的目录也没关系，设置环境变量 `TESSERACT_CMD` 指向 `tesseract.exe` 即可。

2. **pytesseract**（纯 Python，很小）

   ```powershell
   & "D:\tools\Python314\python.exe" -m pip install pytesseract
   ```

3. **重启服务**

   ```powershell
   cd D:\头像diy
   python scripts/serve.py --port 8123
   ```

## 确认是否生效

```powershell
cd D:\头像diy
& "D:\tools\Python314\python.exe" -c "import diyface.ocr as o; print(o.available(), o._tesseract_path())"
```

- 输出 `True C:\Program Files\Tesseract-OCR\tesseract.exe` → 已启用；
- 输出 `False None` → 没找到 tesseract，检查安装路径或设置 `TESSERACT_CMD`。

页面上的表现：图纸导入成功后提示会变成「已用 OCR 预填色号，请核对」。

## 识别策略

1. 格子放大 5 倍、二值化，再按「单行文本」模式识别；
2. 只允许字母和数字，识别结果做常见混淆纠正（`O→0`、`I→1`、`S→5` 等）；
3. 同一类图案最多取 5 个样本投票，降低单格误判；
4. 识别结果必须是 Mard 色号（295 色表内），否则留空让你手选。

## 已知限制

| 情况 | 结果 |
|---|---|
| 格子清晰、字号 ≥ 8px | 基本都能认对 |
| 字体很花、格子太小 | 会漏认，需手动补 |
| 图纸只有颜色没有文字 | OCR 无用，请用「导入图片」 |

OCR 是**辅助**，不是替代人工：最终仍建议扫一眼下拉框，确认每类颜色对不对。
