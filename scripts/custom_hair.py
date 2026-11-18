"""补充 Adventurer 没有的发型：秃头、飞机头。

画法与素材库一致：白色填充 + 黑色描边（可着色槽位，运行时会乘上发色），
坐标对齐我们 1024 画布上的头部：头顶大约 y=219，脸宽 192..866。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

CANVAS = 1024
S = 2
INK = (40, 40, 40, 255)
PAPER = (255, 255, 255, 255)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (CANVAS * S, CANVAS * S), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def finish(image: Image.Image) -> Image.Image:
    return image.resize((CANVAS, CANVAS), Image.LANCZOS)


def draw_bald() -> Image.Image:
    """秃头：只留几根发茬和头顶高光，整体透明。"""
    image, draw = canvas()
    draw.arc((300 * S, 300 * S, 724 * S, 420 * S), start=200, end=340,
             fill=INK, width=6 * S)
    for x, y in ((420, 330), (470, 322), (530, 324), (580, 332)):
        draw.line([(x * S, y * S), ((x + 6) * S, (y - 10) * S)], fill=INK, width=4 * S)
    draw.arc((360 * S, 250 * S, 520 * S, 330 * S), start=210, end=300,
             fill=PAPER, width=10 * S)
    return finish(image)


def draw_mohawk() -> Image.Image:
    """飞机头：中间一撮竖起的尖刺，两侧剃短。"""
    image, draw = canvas()
    spikes = [
        (452, 300), (470, 150), (500, 250), (516, 120), (536, 250),
        (560, 150), (580, 300),
    ]
    points = [(x * S, y * S) for x, y in spikes]
    points += [(560 * S, 330 * S), (470 * S, 330 * S)]
    draw.polygon(points, fill=PAPER, outline=INK)
    draw.line(points + [points[0]], fill=INK, width=8 * S, joint="curve")

    # 两侧短发
    for x0, x1 in ((250, 430), (600, 790)):
        draw.arc((x0 * S, 300 * S, x1 * S, 470 * S), start=200, end=340,
                 fill=INK, width=7 * S)
    return finish(image)


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "assets" / "04_hair"
    root.mkdir(parents=True, exist_ok=True)
    for name, factory in (("hair_bald", draw_bald), ("hair_mohawk", draw_mohawk)):
        image = factory()
        image.save(root / f"{name}.png", optimize=True)
        Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255)).save(
            root / f"{name}_tint.png"
        )
        print("生成", root / f"{name}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
