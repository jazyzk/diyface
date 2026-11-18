"""补充自定义眼睛：白眼球 + 深色虹膜 + 高光，比“纯圆点”更耐看。

坐标对齐 Adventurer 的眼睛位置（1024 画布）：左右眼中心约 (292, 547) 与 (561, 547)。
风格与素材库一致：黑描边、平涂、可保留高光。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

CANVAS = 1024
S = 2
INK = (35, 35, 35, 255)
PAPER = (255, 255, 255, 255)
IRIS = (60, 44, 36, 255)

LEFT = (292, 547)
RIGHT = (561, 547)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    return Image.new("RGBA", (CANVAS * S, CANVAS * S), (0, 0, 0, 0)), None  # type: ignore[return-value]


def new() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (CANVAS * S, CANVAS * S), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def ellipse(draw: ImageDraw.ImageDraw, cx: int, cy: int, rx: int, ry: int, **kwargs) -> None:
    draw.ellipse(
        ((cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S), **kwargs
    )


def finish(image: Image.Image) -> Image.Image:
    return image.resize((CANVAS, CANVAS), Image.LANCZOS)


def eye_round(iris_rx: int = 26, iris_ry: int = 30) -> Image.Image:
    image, draw = new()
    for cx, cy in (LEFT, RIGHT):
        ellipse(draw, cx, cy, 46, 34, fill=PAPER, outline=INK, width=6 * S)
        ellipse(draw, cx, cy + 2, iris_rx, iris_ry, fill=IRIS)
        ellipse(draw, cx - 8, cy - 10, 8, 8, fill=PAPER)
        ellipse(draw, cx + 12, cy + 12, 4, 4, fill=PAPER)
    return finish(image)


def eye_sleepy() -> Image.Image:
    image, draw = new()
    for cx, cy in (LEFT, RIGHT):
        ellipse(draw, cx, cy, 46, 34, fill=PAPER, outline=INK, width=6 * S)
        draw.chord(
            ((cx - 46) * S, (cy - 34) * S, (cx + 46) * S, (cy + 34) * S),
            start=0, end=180, fill=PAPER, outline=INK, width=5 * S,
        )
        ellipse(draw, cx, cy + 4, 22, 16, fill=IRIS)
        ellipse(draw, cx - 6, cy, 6, 6, fill=PAPER)
    return finish(image)


def eye_wink() -> Image.Image:
    image, draw = new()
    cx, cy = LEFT
    ellipse(draw, cx, cy, 46, 34, fill=PAPER, outline=INK, width=6 * S)
    ellipse(draw, cx, cy + 2, 26, 30, fill=IRIS)
    ellipse(draw, cx - 8, cy - 10, 8, 8, fill=PAPER)
    cx, cy = RIGHT
    draw.arc(
        ((cx - 34) * S, (cy - 20) * S, (cx + 34) * S, (cy + 26) * S),
        start=200, end=340, fill=INK, width=8 * S,
    )
    return finish(image)


def eye_star() -> Image.Image:
    import math

    image, draw = new()
    for cx, cy in (LEFT, RIGHT):
        ellipse(draw, cx, cy, 46, 34, fill=PAPER, outline=INK, width=6 * S)
        points = []
        for i in range(10):
            angle = math.radians(-90 + i * 36)
            radius = 26 if i % 2 == 0 else 11
            points.append(((cx + radius * math.cos(angle)) * S, (cy + radius * math.sin(angle)) * S))
        draw.polygon(points, fill=IRIS)
        ellipse(draw, cx - 10, cy - 8, 6, 6, fill=PAPER)
    return finish(image)


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "assets" / "05_eyes"
    root.mkdir(parents=True, exist_ok=True)
    for name, factory in (
        ("eyes_soft_01", eye_round),
        ("eyes_sleepy_02", eye_sleepy),
        ("eyes_wink_03", eye_wink),
        ("eyes_star_04", eye_star),
    ):
        factory().save(root / f"{name}.png", optimize=True)
        print("生成", root / f"{name}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
