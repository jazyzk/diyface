"""生成 E 负责的面部与服饰素材（脸型 / 嘴 / 眼镜）。

这些是**几何风格的正式素材**，不是占位图：坐标按 1024 画布对齐脸中心 (512, 448)，
可着色槽位一律白色打底（渲染时相乘上色不会发灰），并自动生成同名 `_tint.png` 蒙版。

用法（项目根目录）：

    python scripts/make_face_assets.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

CANVAS = 1024
S = 2                                   # 超采样倍数，用来消除锯齿
BIG = CANVAS * S

INK = (40, 40, 40, 255)
PAPER = (255, 255, 255, 255)
SOFT = (168, 168, 168, 255)
DARK = (43, 43, 43, 255)

FACE_CENTER = (512, 448)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def box(x0: int, y0: int, x1: int, y1: int) -> tuple[int, int, int, int]:
    """把 1024 坐标换算成超采样坐标。"""
    return (x0 * S, y0 * S, x1 * S, y1 * S)


def line_width(value: int) -> int:
    return value * S


def finish(image: Image.Image) -> Image.Image:
    return image.resize((CANVAS, CANVAS), Image.LANCZOS)


# --------------------------------------------------------------------------- #
# 脸型：白色打底 + 灰阶五官，肤色靠渲染时相乘
# --------------------------------------------------------------------------- #
def draw_face(radius_x: int, radius_y: int) -> Image.Image:
    image, draw = canvas()
    cx, cy = FACE_CENTER

    face = box(cx - radius_x, cy - radius_y, cx + radius_x, cy + radius_y)
    draw.ellipse(face, fill=PAPER, outline=INK, width=line_width(9))

    # 简化眉
    draw.arc(box(cx - 120, cy - 70, cx - 30, cy - 10), start=200, end=340,
             fill=SOFT, width=line_width(7))
    draw.arc(box(cx + 30, cy - 70, cx + 120, cy - 10), start=200, end=340,
             fill=SOFT, width=line_width(7))

    # 简化鼻
    draw.line([(cx * S, (cy + 20) * S), (cx * S, (cy + 70) * S)], fill=SOFT, width=line_width(7))

    return finish(image)


def draw_skin_base() -> Image.Image:
    return draw_face(radius_x=260, radius_y=280)


def draw_skin_slim() -> Image.Image:
    return draw_face(radius_x=220, radius_y=290)


# --------------------------------------------------------------------------- #
# 嘴：7 种，白色打底（可着色）
# --------------------------------------------------------------------------- #
def draw_mouth_smile() -> Image.Image:
    image, draw = canvas()
    draw.arc(box(452, 560, 572, 650), start=20, end=160, fill=INK, width=line_width(9))
    return finish(image)


def draw_mouth_laugh() -> Image.Image:
    image, draw = canvas()
    draw.chord(box(462, 556, 562, 646), start=0, end=180, fill=PAPER, outline=INK,
               width=line_width(9))
    return finish(image)


def draw_mouth_small() -> Image.Image:
    image, draw = canvas()
    draw.ellipse(box(492, 584, 532, 616), fill=PAPER, outline=INK, width=line_width(8))
    return finish(image)


def draw_mouth_pout() -> Image.Image:
    image, draw = canvas()
    draw.arc(box(470, 596, 554, 668), start=200, end=340, fill=INK, width=line_width(9))
    return finish(image)


def draw_mouth_tongue() -> Image.Image:
    image, draw = canvas()
    draw.chord(box(468, 560, 556, 640), start=0, end=180, fill=PAPER, outline=INK,
               width=line_width(8))
    draw.ellipse(box(486, 600, 538, 650), fill=SOFT, outline=INK, width=line_width(6))
    return finish(image)


def draw_mouth_cat() -> Image.Image:
    image, draw = canvas()
    draw.arc(box(462, 576, 512, 626), start=0, end=180, fill=INK, width=line_width(8))
    draw.arc(box(512, 576, 562, 626), start=0, end=180, fill=INK, width=line_width(8))
    return finish(image)


def draw_mouth_flat() -> Image.Image:
    image, draw = canvas()
    draw.line([(478 * S, 604 * S), (546 * S, 604 * S)], fill=INK, width=line_width(9))
    return finish(image)


# --------------------------------------------------------------------------- #
# 眼镜：5 副，不可着色，颜色写死
# --------------------------------------------------------------------------- #
EYE_Y = 500


def draw_glasses_round() -> Image.Image:
    image, draw = canvas()
    for cx in (430, 594):
        draw.ellipse(box(cx - 62, EYE_Y - 50, cx + 62, EYE_Y + 50), outline=DARK,
                     width=line_width(10))
    draw.line([(492 * S, EYE_Y * S), (532 * S, EYE_Y * S)], fill=DARK, width=line_width(10))
    draw.line([(368 * S, EYE_Y * S), (300 * S, (EYE_Y - 20) * S)], fill=DARK, width=line_width(8))
    draw.line([(656 * S, EYE_Y * S), (724 * S, (EYE_Y - 20) * S)], fill=DARK, width=line_width(8))
    return finish(image)


def draw_glasses_square() -> Image.Image:
    image, draw = canvas()
    for cx in (430, 594):
        draw.rounded_rectangle(box(cx - 68, EYE_Y - 46, cx + 68, EYE_Y + 46), radius=18 * S,
                               outline=DARK, width=line_width(10))
    draw.line([(498 * S, EYE_Y * S), (526 * S, EYE_Y * S)], fill=DARK, width=line_width(10))
    return finish(image)


def draw_glasses_sun() -> Image.Image:
    image, draw = canvas()
    for cx in (430, 594):
        draw.rounded_rectangle(box(cx - 68, EYE_Y - 46, cx + 68, EYE_Y + 46), radius=16 * S,
                               fill=(30, 30, 30, 235), outline=DARK, width=line_width(10))
    draw.line([(498 * S, EYE_Y * S), (526 * S, EYE_Y * S)], fill=DARK, width=line_width(10))
    return finish(image)


def draw_glasses_half() -> Image.Image:
    image, draw = canvas()
    for cx in (430, 594):
        draw.arc(box(cx - 66, EYE_Y - 50, cx + 66, EYE_Y + 30), start=180, end=360,
                 fill=DARK, width=line_width(10))
        draw.line([((cx - 66) * S, EYE_Y * S), ((cx + 66) * S, EYE_Y * S)], fill=DARK,
                  width=line_width(8))
    return finish(image)


def draw_glasses_goggle() -> Image.Image:
    image, draw = canvas()
    draw.rounded_rectangle(box(340, EYE_Y - 58, 684, EYE_Y + 52), radius=28 * S,
                           outline=DARK, width=line_width(11))
    draw.line([(340 * S, EYE_Y * S), (286 * S, (EYE_Y - 14) * S)], fill=DARK, width=line_width(10))
    draw.line([(684 * S, EYE_Y * S), (738 * S, (EYE_Y - 14) * S)], fill=DARK, width=line_width(10))
    return finish(image)


# --------------------------------------------------------------------------- #
# 清单与输出
# --------------------------------------------------------------------------- #
#: 相对 assets/ 的路径 -> (绘制函数, 是否需要 tint 蒙版)
TARGETS: dict[str, tuple] = {
    "01_skin/skin_base.png": (draw_skin_base, True),
    "01_skin/skin_slim.png": (draw_skin_slim, True),
    "07_mouth/mouth_smile_01.png": (draw_mouth_smile, True),
    "07_mouth/mouth_laugh_01.png": (draw_mouth_laugh, True),
    "07_mouth/mouth_small_01.png": (draw_mouth_small, True),
    "07_mouth/mouth_pout_01.png": (draw_mouth_pout, True),
    "07_mouth/mouth_tongue_01.png": (draw_mouth_tongue, True),
    "07_mouth/mouth_cat_01.png": (draw_mouth_cat, True),
    "07_mouth/mouth_flat_01.png": (draw_mouth_flat, True),
    "09_glasses/glasses_round_01.png": (draw_glasses_round, False),
    "09_glasses/glasses_square_01.png": (draw_glasses_square, False),
    "09_glasses/glasses_sun_01.png": (draw_glasses_sun, False),
    "09_glasses/glasses_half_01.png": (draw_glasses_half, False),
    "09_glasses/glasses_goggle_01.png": (draw_glasses_goggle, False),
}


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "assets"
    for relative, (factory, needs_tint) in TARGETS.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        factory().save(path, optimize=True)
        size_kb = path.stat().st_size / 1024
        print(f"已生成 assets/{relative}  ({size_kb:.1f} KB)")

        if needs_tint:
            mask = path.with_name(f"{path.stem}_tint.png")
            Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255)).save(mask)
    print(f"共 {len(TARGETS)} 张素材")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
