"""生成 A 角色第 1 步要用的 3 张占位素材。

占位图不是随便涂个色块，它要能同时验证两件事：**叠图位置对不对**、**着色逻辑对不对**。
坐标按《项目说明与分工》v1.0 的基线：脸中心 y=500、头顶 y=170、眼睛 y=460。

三张图各自承担一个检查点：

* ``01_skin/skin_base.png``   白色脸型 + 深色轮廓：可着色，验证肤色相乘后描边不变黑
* ``04_hair/hair_straight_01`` 白色发片 + 黑色描边：可着色，验证发色可换而描边保持
* ``05_eyes/eyes_round_01``   白色眼白 + 黑瞳 + 黑描边：可着色，验证眼珠颜色可换

为什么底色是白：渲染器用「相乘」着色，白色乘任何颜色等于该颜色，
所以占位图用白色打底，换成真实的肤色/发色才不会发灰。

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
SOFT = (168, 168, 168, 255)


def draw_skin() -> Image.Image:
    """脸型：椭圆脸 + 简化的眉与鼻，占位用。"""
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    face = (252, 220, 772, 780)
    draw.ellipse(face, fill=PAPER, outline=INK, width=OUTLINE)

    # 简化鼻：一条短竖线
    draw.line([(512, 522), (512, 574)], fill=SOFT, width=8)
    # 简化眉：两条短弧
    draw.arc([(398, 378), (502, 444)], start=200, end=340, fill=SOFT, width=8)
    draw.arc([(522, 378), (626, 444)], start=200, end=340, fill=SOFT, width=8)
    return image


def draw_hair() -> Image.Image:
    """前发：一个压在头顶的弧形发片，边缘带描边。"""
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    top = (232, 110, 792, 520)
    draw.chord(top, start=180, end=360, fill=PAPER, outline=INK, width=OUTLINE)
    return image


def draw_eyes() -> Image.Image:
    """眼睛：白眼球可换色，黑瞳与描边保持不变。"""
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    for cx in (430, 594):
        draw.ellipse((cx - 34, 426, cx + 34, 494), fill=PAPER, outline=INK, width=6)
        draw.ellipse((cx - 14, 446, cx + 14, 474), fill=INK)
        draw.ellipse((cx - 10, 442, cx - 2, 450), fill=PAPER)
    return image


#: 相对 assets/ 的路径 -> 绘制函数。
TARGETS: dict[str, "object"] = {
    "01_skin/skin_base.png": draw_skin,
    "04_hair/hair_straight_01.png": draw_hair,
    "05_eyes/eyes_round_01.png": draw_eyes,
}

#: 可着色槽位需要一张同名 _tint 蒙版（全白表示整层都可上色）。
TINTABLE = {
    "01_skin/skin_base.png",
    "04_hair/hair_straight_01.png",
    "05_eyes/eyes_round_01.png",
}


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
