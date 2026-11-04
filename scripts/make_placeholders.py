"""生成 A 角色第 1 步要用的 3 张占位素材。

占位图不是随便涂个色块，它要能同时验证两件事：**叠图位置对不对**、**着色逻辑对不对**。
所以三张图各自承担一个检查点：

* ``01_skin/skin_base.png``      白色脸型 + 深色轮廓：可着色，验证肤色相乘后描边不变黑
* ``02_bangs/bangs_straight_01`` 白色发片 + 黑色描边：可着色，验证发色可换而描边保持
* ``06_eyes/eyes_round_01``      黑色眼珠 + 白高光：不可着色，验证固定颜色不被污染

为什么底色是白：渲染器用「相乘」着色，白色乘任何颜色等于该颜色，
所以占位图用白色打底，换成真实的 #F2D5B8 肤色才不会发灰。

用法（在项目根目录）：

    python scripts/make_placeholders.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

CANVAS = 1024
OUTLINE = 8
INK = (40, 40, 40, 255)
PAPER = (255, 255, 255, 255)


def draw_skin() -> Image.Image:
    """脸型：椭圆脸 + 简化的眉与鼻，占位用。"""
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    face = (252, 168, 772, 728)
    draw.ellipse(face, fill=PAPER, outline=INK, width=OUTLINE)

    # 简化鼻：一条短竖线
    draw.line([(512, 470), (512, 522)], fill=(205, 205, 205, 255), width=8)
    # 简化眉：两条短弧
    draw.arc([(398, 372), (502, 438)], start=200, end=340, fill=(190, 190, 190, 255), width=8)
    draw.arc([(522, 372), (626, 438)], start=200, end=340, fill=(190, 190, 190, 255), width=8)
    return image


def draw_bangs() -> Image.Image:
    """发型：一个压在头顶的弧形发片，边缘带描边。"""
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    top = (232, 150, 792, 560)
    draw.chord(top, start=180, end=360, fill=PAPER, outline=INK, width=OUTLINE)
    return image


def draw_eyes() -> Image.Image:
    """眼睛：两颗黑眼珠 + 白高光，位置围绕脸中心对称。"""
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    for cx in (430, 594):
        draw.ellipse((cx - 34, 470, cx + 34, 538), fill=(43, 43, 43, 255))
        draw.ellipse((cx - 12, 486, cx + 2, 500), fill=PAPER)
    return image


#: 相对 assets/ 的路径 -> 绘制函数。
TARGETS: dict[str, "object"] = {
    "01_skin/skin_base.png": draw_skin,
    "02_bangs/bangs_straight_01.png": draw_bangs,
    "06_eyes/eyes_round_01.png": draw_eyes,
}

#: 可着色槽位需要一张同名 _tint 蒙版（全白表示整层都可上色）。
#: eyes 在 models 里是 tintable=False，不需要蒙版。
TINTABLE = {"01_skin/skin_base.png", "02_bangs/bangs_straight_01.png"}


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "assets"
    for relative, factory in TARGETS.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        factory().save(path)
        size_kb = path.stat().st_size / 1024
        print(f"已生成 assets/{relative}  ({size_kb:.1f} KB)")

        if relative in TINTABLE:
            mask = path.with_name(f"{path.stem}_tint.png")
            Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255)).save(mask)
            print(f"已生成 assets/{relative.replace(path.name, mask.name)}  (蒙版)")


if __name__ == "__main__":
    main()
