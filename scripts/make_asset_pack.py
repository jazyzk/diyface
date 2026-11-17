"""生成 A（素材与美术）负责的 54 张分层素材里剩下的 38 张。

风格统一为「白色打底 + 黑描边」的几何扁平风：可着色槽位靠运行时相乘上色，
所以形状只用白与黑，颜色全部交给 Recipe。坐标严格对齐文档基线：
头顶 y=170、眼睛 y=460、脸中心 y=500、嘴 y=620、肩线 y=880。

用法：

    python scripts/make_asset_pack.py            # 只补缺失的
    python scripts/make_asset_pack.py --force    # 全部重画（会覆盖手工修改）
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

CANVAS = 1024
S = 2
BIG = CANVAS * S

INK = (40, 40, 40, 255)
PAPER = (255, 255, 255, 255)
GOLD = (212, 160, 23, 255)
BEIGE = (240, 214, 180, 255)
YELLOW = (250, 205, 60, 255)

EYE_Y = 460
EYE_X = (430, 594)
BROW_Y = 415
MOUTH_Y = 620


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def box(x0: int, y0: int, x1: int, y1: int) -> tuple[int, int, int, int]:
    return (x0 * S, y0 * S, x1 * S, y1 * S)


def lw(value: int) -> int:
    return value * S


def pt(x: float, y: float) -> tuple[int, int]:
    return (round(x * S), round(y * S))


def finish(image: Image.Image) -> Image.Image:
    return image.resize((CANVAS, CANVAS), Image.LANCZOS)



def punch_face(image: Image.Image) -> Image.Image:
    """把脸的位置挖空：后发 z=25 在脸之上，必须留出脸的形状，否则会把脸盖住。"""
    hole = Image.new("L", (BIG, BIG), 255)
    ImageDraw.Draw(hole).ellipse(box(266, 232, 758, 772), fill=0)
    image.putalpha(ImageChops.multiply(image.getchannel("A"), hole))
    return image


# --------------------------------------------------------------------------- #
# 后发（z=25，压在服装与脸之间，只露出轮廓）
# --------------------------------------------------------------------------- #
def draw_hair_back(kind: str) -> Image.Image:
    image, draw = canvas()
    if kind == "long_straight":
        draw.rounded_rectangle(box(212, 196, 812, 924), radius=110 * S, fill=PAPER,
                               outline=INK, width=lw(8))
    elif kind == "long_wavy":
        draw.rounded_rectangle(box(206, 196, 818, 880), radius=120 * S, fill=PAPER,
                               outline=INK, width=lw(8))
        for cx in (280, 400, 512, 624, 744):
            draw.ellipse(box(cx - 70, 800, cx + 70, 940), fill=PAPER, outline=INK, width=lw(6))
    elif kind == "ponytail":
        draw.rounded_rectangle(box(218, 196, 806, 740), radius=120 * S, fill=PAPER,
                               outline=INK, width=lw(8))
        draw.ellipse(box(660, 520, 900, 940), fill=PAPER, outline=INK, width=lw(8))
    elif kind == "twin_braid":
        draw.rounded_rectangle(box(218, 196, 806, 720), radius=120 * S, fill=PAPER,
                               outline=INK, width=lw(8))
        for cx in (230, 794):
            for cy in (620, 720, 820):
                draw.ellipse(box(cx - 58, cy - 58, cx + 58, cy + 58), fill=PAPER,
                             outline=INK, width=lw(6))
    elif kind == "bob":
        draw.rounded_rectangle(box(208, 196, 816, 700), radius=130 * S, fill=PAPER,
                               outline=INK, width=lw(8))
    else:  # long_curly
        draw.ellipse(box(198, 190, 826, 900), fill=PAPER, outline=INK, width=lw(8))
        for cx in (300, 420, 512, 604, 724):
            draw.ellipse(box(cx - 66, 800, cx + 66, 930), fill=PAPER, outline=INK, width=lw(6))
    return finish(punch_face(image))


# --------------------------------------------------------------------------- #
# 前发（z=30，压住额头）
# --------------------------------------------------------------------------- #
def draw_hair(kind: str) -> Image.Image:
    image, draw = canvas()
    if kind == "straight":
        draw.chord(box(232, 110, 792, 520), start=180, end=360, fill=PAPER,
                   outline=INK, width=lw(9))
    elif kind == "wavy":
        points = [pt(232, 300)]
        for i in range(9):
            x = 232 + i * 62
            y = 300 if i % 2 == 0 else 250
            points.append(pt(x, y))
        points += [pt(792, 300), pt(792, 232), pt(232, 232)]
        draw.polygon(points, fill=PAPER, outline=INK)
        draw.line(points + [points[0]], fill=INK, width=lw(8), joint="curve")
    elif kind == "twin_tail":
        draw.chord(box(232, 110, 792, 500), start=180, end=360, fill=PAPER,
                   outline=INK, width=lw(9))
        for cx in (200, 824):
            draw.ellipse(box(cx - 78, 300, cx + 78, 600), fill=PAPER, outline=INK, width=lw(8))
    elif kind == "bang_full":
        draw.chord(box(232, 110, 792, 640), start=180, end=360, fill=PAPER,
                   outline=INK, width=lw(9))
    elif kind == "messy":
        points = [pt(232, 330)]
        for i in range(7):
            x = 250 + i * 76
            points.append(pt(x, 210 if i % 2 == 0 else 300))
        points += [pt(792, 330), pt(792, 220), pt(232, 220)]
        draw.polygon(points, fill=PAPER, outline=INK)
        draw.line(points + [points[0]], fill=INK, width=lw(8), joint="curve")
    elif kind == "short":
        draw.chord(box(252, 120, 772, 430), start=180, end=360, fill=PAPER,
                   outline=INK, width=lw(9))
    elif kind == "bun":
        draw.chord(box(240, 140, 784, 470), start=180, end=360, fill=PAPER,
                   outline=INK, width=lw(9))
        draw.ellipse(box(462, 46, 562, 146), fill=PAPER, outline=INK, width=lw(8))
    else:  # bald：只剩一条发际线
        draw.arc(box(300, 150, 724, 300), start=200, end=340, fill=INK, width=lw(10))
    return finish(image)


# --------------------------------------------------------------------------- #
# 眼睛（z=40，白眼球可换色，黑瞳不变）
# --------------------------------------------------------------------------- #
def _pupil(draw: ImageDraw.ImageDraw, cx: int, r: int = 14) -> None:
    draw.ellipse(box(cx - r, EYE_Y - r, cx + r, EYE_Y + r), fill=INK)


def draw_eyes(kind: str) -> Image.Image:
    image, draw = canvas()
    if kind == "round":
        for cx in EYE_X:
            draw.ellipse(box(cx - 34, EYE_Y - 34, cx + 34, EYE_Y + 34), fill=PAPER,
                         outline=INK, width=lw(6))
            _pupil(draw, cx)
            draw.ellipse(box(cx - 10, EYE_Y - 18, cx - 2, EYE_Y - 10), fill=PAPER)
    elif kind == "slim":
        for cx in EYE_X:
            draw.ellipse(box(cx - 42, EYE_Y - 16, cx + 42, EYE_Y + 16), fill=PAPER,
                         outline=INK, width=lw(6))
            draw.ellipse(box(cx - 10, EYE_Y - 12, cx + 10, EYE_Y + 12), fill=INK)
    elif kind == "smile":
        for cx in EYE_X:
            draw.arc(box(cx - 32, EYE_Y - 18, cx + 32, EYE_Y + 30), start=200, end=340,
                     fill=INK, width=lw(11))
    elif kind == "star":
        for cx in EYE_X:
            points = []
            for i in range(10):
                angle = math.radians(-90 + i * 36)
                radius = 40 if i % 2 == 0 else 17
                points.append(pt(cx + radius * math.cos(angle), EYE_Y + radius * math.sin(angle)))
            draw.polygon(points, fill=PAPER, outline=INK)
            draw.line(points + [points[0]], fill=INK, width=lw(5), joint="curve")
            _pupil(draw, cx, r=10)
    elif kind == "squint":
        for cx in EYE_X:
            draw.arc(box(cx - 34, EYE_Y - 26, cx + 34, EYE_Y + 18), start=20, end=160,
                     fill=INK, width=lw(10))
    elif kind == "surprise":
        for cx in EYE_X:
            draw.ellipse(box(cx - 44, EYE_Y - 44, cx + 44, EYE_Y + 44), fill=PAPER,
                         outline=INK, width=lw(7))
            _pupil(draw, cx, r=11)
    elif kind == "sleepy":
        for cx in EYE_X:
            draw.chord(box(cx - 36, EYE_Y - 30, cx + 36, EYE_Y + 30), start=0, end=180,
                       fill=PAPER, outline=INK, width=lw(6))
            draw.line([pt(cx - 36, EYE_Y), pt(cx + 36, EYE_Y)], fill=INK, width=lw(6))
    else:  # hetero：左圆右星
        draw.ellipse(box(EYE_X[0] - 34, EYE_Y - 34, EYE_X[0] + 34, EYE_Y + 34), fill=PAPER,
                     outline=INK, width=lw(6))
        _pupil(draw, EYE_X[0])
        cx = EYE_X[1]
        points = []
        for i in range(10):
            angle = math.radians(-90 + i * 36)
            radius = 40 if i % 2 == 0 else 17
            points.append(pt(cx + radius * math.cos(angle), EYE_Y + radius * math.sin(angle)))
        draw.polygon(points, fill=PAPER, outline=INK)
        draw.line(points + [points[0]], fill=INK, width=lw(5), joint="curve")
        _pupil(draw, cx, r=10)
    return finish(image)


# --------------------------------------------------------------------------- #
# 眉毛（z=45）
# --------------------------------------------------------------------------- #
def draw_brows(kind: str) -> Image.Image:
    image, draw = canvas()
    for cx in EYE_X:
        if kind == "soft":
            draw.arc(box(cx - 44, BROW_Y - 24, cx + 44, BROW_Y + 24), start=200, end=340,
                     fill=INK, width=lw(11))
        elif kind == "arched":
            draw.arc(box(cx - 50, BROW_Y - 44, cx + 50, BROW_Y + 20), start=200, end=340,
                     fill=INK, width=lw(10))
        elif kind == "sharp":
            draw.line([pt(cx - 46, BROW_Y + 12), pt(cx + 46, BROW_Y - 18)], fill=INK, width=lw(10))
        else:  # thick
            draw.arc(box(cx - 46, BROW_Y - 18, cx + 46, BROW_Y + 34), start=200, end=340,
                     fill=INK, width=lw(16))
    return finish(image)


# --------------------------------------------------------------------------- #
# 服装（z=20，肩线 y=880）
# --------------------------------------------------------------------------- #
def _torso_outline() -> list[tuple[int, int]]:
    return [pt(190, 1024), pt(210, 900), pt(360, 800), pt(664, 800), pt(814, 900), pt(834, 1024)]


def draw_clothes(kind: str) -> Image.Image:
    image, draw = canvas()
    body = _torso_outline()
    draw.polygon(body, fill=PAPER, outline=INK)
    draw.line(body + [body[0]], fill=INK, width=lw(9), joint="curve")

    if kind == "crew":
        draw.arc(box(432, 770, 592, 880), start=0, end=180, fill=INK, width=lw(9))
    elif kind == "shirt":
        draw.polygon([pt(440, 790), pt(512, 900), pt(470, 930), pt(420, 830)], fill=PAPER,
                     outline=INK)
        draw.line([pt(440, 790), pt(512, 900), pt(470, 930), pt(420, 830), pt(440, 790)],
                  fill=INK, width=lw(7), joint="curve")
        draw.polygon([pt(584, 790), pt(512, 900), pt(554, 930), pt(604, 830)], fill=PAPER,
                     outline=INK)
        draw.line([pt(584, 790), pt(512, 900), pt(554, 930), pt(604, 830), pt(584, 790)],
                  fill=INK, width=lw(7), joint="curve")
        draw.line([pt(512, 900), pt(512, 1010)], fill=INK, width=lw(6))
    elif kind == "hoodie":
        draw.ellipse(box(392, 730, 632, 850), fill=PAPER, outline=INK, width=lw(9))
        draw.line([pt(470, 850), pt(462, 960)], fill=INK, width=lw(7))
        draw.line([pt(554, 850), pt(562, 960)], fill=INK, width=lw(7))
    elif kind == "overall":
        for x0 in (392, 556):
            draw.rectangle(box(x0, 800, x0 + 56, 900), fill=PAPER, outline=INK, width=lw(7))
        draw.arc(box(432, 780, 592, 860), start=0, end=180, fill=INK, width=lw(8))
    elif kind == "scarf":
        draw.rounded_rectangle(box(380, 760, 644, 850), radius=40 * S, fill=PAPER,
                               outline=INK, width=lw(9))
        draw.polygon([pt(592, 830), pt(660, 830), pt(668, 1000), pt(600, 1000)], fill=PAPER,
                     outline=INK)
        draw.line([pt(592, 830), pt(660, 830), pt(668, 1000), pt(600, 1000), pt(592, 830)],
                  fill=INK, width=lw(7), joint="curve")
    else:  # hood
        draw.arc(box(300, 700, 724, 1000), start=180, end=360, fill=PAPER, width=lw(46))
        draw.arc(box(300, 700, 724, 1000), start=180, end=360, fill=INK, width=lw(6))
    return finish(image)


# --------------------------------------------------------------------------- #
# 帽子（z=70）
# --------------------------------------------------------------------------- #
def draw_hat(kind: str) -> Image.Image:
    image, draw = canvas()
    if kind == "beret":
        draw.ellipse(box(296, 168, 728, 348), fill=PAPER, outline=INK, width=lw(9))
        draw.line([pt(512, 168), pt(512, 124)], fill=INK, width=lw(10))
    elif kind == "cap":
        draw.chord(box(310, 140, 714, 340), start=180, end=360, fill=PAPER, outline=INK,
                   width=lw(9))
        draw.rounded_rectangle(box(300, 320, 800, 366), radius=22 * S, fill=PAPER,
                               outline=INK, width=lw(8))
    elif kind == "beanie":
        draw.chord(box(318, 158, 706, 368), start=180, end=360, fill=PAPER, outline=INK,
                   width=lw(9))
        draw.rounded_rectangle(box(316, 330, 708, 402), radius=26 * S, fill=PAPER,
                               outline=INK, width=lw(8))
        draw.ellipse(box(486, 98, 538, 150), fill=PAPER, outline=INK, width=lw(7))
    elif kind == "bunny":
        draw.chord(box(330, 180, 694, 380), start=180, end=360, fill=PAPER, outline=INK,
                   width=lw(9))
        for x0 in (400, 560):
            draw.ellipse(box(x0 - 44, 40, x0 + 44, 230), fill=PAPER, outline=INK, width=lw(8))
    else:  # crown
        points = [pt(312, 316), pt(312, 150), pt(396, 238), pt(512, 112), pt(628, 238),
                  pt(712, 150), pt(712, 316)]
        draw.polygon(points, fill=PAPER, outline=INK)
        draw.line(points + [points[0]], fill=INK, width=lw(9), joint="curve")
    return finish(image)


# --------------------------------------------------------------------------- #
# 配饰（z=80，不可着色，颜色写死）
# --------------------------------------------------------------------------- #
def draw_extra(kind: str) -> Image.Image:
    image, draw = canvas()
    if kind == "earring":
        for cx in (238, 786):
            draw.ellipse(box(cx - 26, 560, cx + 26, 612), fill=GOLD, outline=INK, width=lw(6))
            draw.line([pt(cx, 560), pt(cx, 528)], fill=GOLD, width=lw(6))
    elif kind == "bandaid":
        draw.rounded_rectangle(box(600, 548, 700, 600), radius=16 * S, fill=BEIGE,
                               outline=INK, width=lw(6))
        draw.rounded_rectangle(box(636, 512, 664, 636), radius=12 * S, fill=BEIGE,
                               outline=INK, width=lw(6))
    else:  # star_sticker
        cx, cy = 330, 600
        points = []
        for i in range(10):
            angle = math.radians(-90 + i * 36)
            radius = 52 if i % 2 == 0 else 22
            points.append(pt(cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        draw.polygon(points, fill=YELLOW, outline=INK)
        draw.line(points + [points[0]], fill=INK, width=lw(6), joint="curve")
    return finish(image)


# --------------------------------------------------------------------------- #
# 清单：相对 assets/ 的路径 -> (绘制函数, 是否需要 tint 蒙版)
# --------------------------------------------------------------------------- #
TARGETS: dict[str, tuple] = {}

for name in ("long_straight", "long_wavy", "ponytail", "twin_braid", "bob", "long_curly"):
    TARGETS[f"03_hair_back/hair_back_{name}_01.png"] = (
        lambda n=name: draw_hair_back(n), True)

for name in ("wavy", "twin_tail", "bang_full", "messy", "short", "bun", "bald"):
    TARGETS[f"04_hair/hair_{name}_01.png"] = (lambda n=name: draw_hair(n), True)

for name in ("slim", "smile", "star", "squint", "surprise", "sleepy", "hetero"):
    TARGETS[f"05_eyes/eyes_{name}_01.png"] = (lambda n=name: draw_eyes(n), True)

for name in ("soft", "arched", "sharp", "thick"):
    TARGETS[f"06_brows/brows_{name}_01.png"] = (lambda n=name: draw_brows(n), True)

for name in ("crew", "shirt", "hoodie", "overall", "scarf", "hood"):
    TARGETS[f"02_clothes/clothes_{name}_01.png"] = (lambda n=name: draw_clothes(n), True)

for name in ("beret", "cap", "beanie", "bunny", "crown"):
    TARGETS[f"09_hat/hat_{name}_01.png"] = (lambda n=name: draw_hat(n), True)

for name in ("earring", "bandaid", "star"):
    TARGETS[f"10_extra/extra_{name}_01.png"] = (lambda n=name: draw_extra(n), False)


def main() -> int:
    parser = argparse.ArgumentParser(description="补齐 A 负责的分层素材")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的同名素材")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1] / "assets"
    written = skipped = 0
    for relative, (factory, needs_tint) in TARGETS.items():
        path = root / relative
        if path.exists() and not args.force:
            skipped += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        factory().save(path, optimize=True)

        if needs_tint:
            Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255)).save(
                path.with_name(f"{path.stem}_tint.png"))
        written += 1
        print(f"生成 assets/{relative}  ({path.stat().st_size / 1024:.1f} KB)")

    print(f"新生成 {written} 张，跳过已存在 {skipped} 张")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
