# 换美术风格：从 Figma 导出并导入

我们的渲染器只认「1024×1024、RGBA、按槽位分目录的 PNG」，所以换风格不需要改代码，
只要把新素材导出来、命名对、跑一次导入脚本。

本文以 [DiceBear 的 Lorelei 风格](https://www.dicebear.com/styles/lorelei/)（CC0，公共领域）为例，
换成 Notionists、Open Peeps 流程完全一样。

## 1 选风格

| 风格 | 许可 | 视觉 | 链接 |
| --- | --- | --- | --- |
| Lorelei | CC0 | 圆脸大眼、柔和，最接近「可爱头像」 | <https://www.figma.com/community/file/1198749693280469639> |
| Notionists | CC0 | 手绘线条、极简 | 见 DiceBear 风格页里的 Figma 链接 |
| Open Peeps | CC0 | 黑白手绘，可上色 | <https://www.openpeeps.com/> |
| Adventurer / Micah | CC BY 4.0 | 手绘卡通，风格更「欧美」 | 需在 README 署名 |

CC0 不需要署名，也允许商用；CC BY 4.0 只要求写明来源。

## 2 在 Figma 里导出

1. 打开上面的 Figma 社区链接，点 **Duplicate**（复制到自己的草稿）。需要免费 Figma 账号。
2. 打开文件，找到组件页（通常叫 `Components` 或按部件分页：Hair / Eyes / Mouth …）。
3. **关键一步：保住位置。**

   Figma 直接导出图层时，会裁到内容边界（bounding box），原始坐标就丢了；
   直接丢进素材目录会全部挤在画布中央。

   两个办法，二选一：

   | 办法 | 操作 | 效果 |
   | --- | --- | --- |
   | **A 完整画板**（推荐） | 把部件复制到一个 1024×1024 的 Frame 里，位置与组件页一致，导出**这个 Frame** | 位置 100% 正确 |
   | B 直接导出图层 | 选中图层 → 右侧 Export → PNG | 位置会丢，导入脚本按槽位估算（发型贴顶、眼睛居中…），需要肉眼复核 |

4. 导出设置：**PNG、1x、1024×1024、透明背景**。
5. 命名尽量带关键词，脚本按「词」识别槽位：

   | 文件名示例 | 识别为 |
   | --- | --- |
   | `Hair 1.png` / `bangs-2.png` | 发型 |
   | `Eyes 3.png` | 眼睛 |
   | `Mouth Smile.png` | 嘴 |
   | `Glasses Round.png` | 眼镜 |
   | `Eyebrow 2.png` | 眉毛（优先于 eye） |
   | `Head 1.png` | 脸型 |
   | `Hat Beret.png` | 帽子 |

   认不出的文件名会被跳过并提示；也可以用 `--slot` 手动指定。

6. 按槽位分文件夹（可选，脚本会递归找图）：

   ```
   D:\导出\lorelei\
   ├── hair\      Hair 1.png  Hair 2.png …
   ├── eyes\      Eyes 1.png …
   ├── mouth\     Mouth 1.png …
   └── glasses\   Glasses 1.png …
   ```

## 3 导入

先预演，看一眼映射对不对：

```powershell
python scripts/import_pack.py --src D:\导出\lorelei --dry-run
```

输出类似：

```
可导入 3 张，跳过 1 张
  Eyes 2.png            -> 05_eyes/eyes_2.png
  Glasses Round.png     -> 08_glasses/glasses_round.png
  Hair 1.png            -> 04_hair/hair_1.png
  跳过 whatever.png     文件名里认不出槽位（可加 --slot 指定）
```

确认后去掉 `--dry-run` 真正导入：

```powershell
python scripts/import_pack.py --src D:\导出\lorelei
```

脚本会做四件事：缩放到 1024、按槽位摆放、给可着色槽位补 `_tint.png` 蒙版、重建缩略图。

## 4 复核

```powershell
python -m diyface verify
python -m diyface build-thumbs --check
python -m flask --app diyface.app run --debug --port 8000
```

浏览器里逐个类目点一遍：**位置比数量重要**——一张偏 20 像素的刘海，会让整张脸看起来歪。

## 5 授权

- CC0（Lorelei / Notionists / Open Peeps）：无需署名，建议在 README 的「致谢」里提一句。
- CC BY 4.0（Adventurer / Micah / Miniavs …）：**必须**在 README 写明来源与许可，例如：

```markdown
## 素材来源

- 角色素材：[Adventurer](https://www.dicebear.com/styles/adventurer/) by Lisa Wischofsky，
  经 [DiceBear](https://www.dicebear.com/) 提供，[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。
  本项目对其做了裁切与重新分层。
```

课程作业也建议保留这段——老师如果问「素材哪来的」，一句话就能答上。

## 6 常见问题

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 导入后素材全挤在中间 | 导出的是被裁切的图层 | 用办法 A（1024 画板导出），或导入后用 `make_guide.py --reference` 对照重导 |
| 头发盖不住额头 | 贴顶锚点估算偏了 | 把该图放进 1024 画板重导，或手工调 y |
| `verify` 报缺 `_tint.png` | 该槽位是可着色槽位 | 脚本会自动补；手工放的图要自己补 |
| 素材模糊 | 导出分辨率低于 1024 | Figma 导出选 2x/3x 再让脚本缩到 1024 |
