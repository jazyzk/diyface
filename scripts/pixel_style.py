"""第三套风格：像素方块（pixel）。

全部素材都画在 32×32 的网格上，再按 32 倍放大到 1024，好处是：

* 所有部件共享同一套格子坐标，天然对齐，不会出现「发遮眼」；
* 方块边缘硬朗，和拼豆画布是同一个视觉语言；
* 不依赖第三方库的 viewBox / transform，可复现。

用法：``python scripts/pixel_style.py``，之后跑 ``python -m diyface build-thumbs``。
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
GRID = 32
CELL = 32
SIZE = GRID * CELL

OUTLINE = "#2B1B12"
DARK = "#1F2430"
WHITE = "#FFFFFF"

CELLMAP = dict[tuple[int, int], str]


def rect(cells: CELLMAP, x0: int, y0: int, x1: int, y1: int, color: str) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cells[(x, y)] = color


def ring(cells: CELLMAP, x0: int, y0: int, x1: int, y1: int, color: str) -> None:
    for x in range(x0, x1 + 1):
        cells[(x, y0)] = color
        cells[(x, y1)] = color
    for y in range(y0, y1 + 1):
        cells[(x0, y)] = color
        cells[(x1, y)] = color


def copy_cells(source: CELLMAP) -> CELLMAP:
    return dict(source)


# ---------------------------------------------------------------- 底脸


def face(shape: str) -> CELLMAP:
    """返回整张脸的格子（肤色部分用 WHITE 占位，便于相乘上色）。"""
    cells: CELLMAP = {}
    if shape == "round":
        rect(cells, 9, 8, 22, 25, WHITE)
        for corner in ((9, 8), (22, 8), (9, 25), (22, 25)):
            cells.pop(corner, None)
        rect(cells, 8, 12, 8, 22, WHITE)
        rect(cells, 23, 12, 23, 22, WHITE)
    elif shape == "square":
        rect(cells, 8, 8, 23, 26, WHITE)
    else:  # long
        rect(cells, 10, 7, 21, 27, WHITE)

    # 描边
    edge = {}
    for (x, y) in list(cells):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbour = (x + dx, y + dy)
            if neighbour not in cells:
                edge[neighbour] = OUTLINE
    cells.update(edge)

    # 耳朵
    for y in range(13, 18):
        cells[(7, y)] = OUTLINE
        cells[(24, y)] = OUTLINE
    for y in range(14, 17):
        cells[(7, y)] = WHITE
        cells[(24, y)] = WHITE
    return cells


# ---------------------------------------------------------------- 头发

HAIR_STYLES = ["short", "bob", "long", "bun", "mohawk", "side"]


def hair(kind: str) -> CELLMAP:
    cells: CELLMAP = {}
    if kind == "short":
        rect(cells, 8, 6, 23, 11, OUTLINE)
        rect(cells, 9, 5, 22, 5, OUTLINE)
        rect(cells, 8, 11, 8, 12, OUTLINE)
        rect(cells, 23, 11, 23, 12, OUTLINE)
    elif kind == "bob":
        rect(cells, 7, 6, 24, 12, OUTLINE)
        rect(cells, 7, 12, 7, 20, OUTLINE)
        rect(cells, 24, 12, 24, 20, OUTLINE)
        rect(cells, 8, 5, 23, 5, OUTLINE)
    elif kind == "long":
        rect(cells, 7, 6, 24, 11, OUTLINE)
        rect(cells, 7, 11, 7, 27, OUTLINE)
        rect(cells, 24, 11, 24, 27, OUTLINE)
        rect(cells, 8, 5, 23, 5, OUTLINE)
    elif kind == "bun":
        rect(cells, 8, 7, 23, 11, OUTLINE)
        rect(cells, 14, 3, 17, 6, OUTLINE)
        rect(cells, 15, 4, 16, 5, OUTLINE)
    elif kind == "mohawk":
        rect(cells, 15, 3, 16, 12, OUTLINE)
        rect(cells, 14, 4, 14, 8, OUTLINE)
        rect(cells, 17, 4, 17, 8, OUTLINE)
    else:  # side
        rect(cells, 8, 6, 23, 10, OUTLINE)
        rect(cells, 20, 10, 23, 16, OUTLINE)
        rect(cells, 8, 10, 9, 14, OUTLINE)
    return cells


# ---------------------------------------------------------------- 五官

EYE_SHAPES = ["dot", "big", "star", "wink"]


def eyes(kind: str, color: str) -> CELLMAP:
    cells: CELLMAP = {}
    for side in (11, 18):
        if kind == "dot":
            rect(cells, side, 15, side + 2, 16, color)
        elif kind == "big":
            rect(cells, side, 14, side + 2, 17, color)
            cells[(side + 1, 15)] = WHITE
        elif kind == "star":
            cells[(side + 1, 14)] = color
            cells[(side + 1, 15)] = color
            cells[(side + 1, 16)] = color
            cells[(side, 15)] = color
            cells[(side + 2, 15)] = color
        else:  # wink
            if side == 11:
                rect(cells, side, 15, side + 2, 15, color)
            else:
                rect(cells, side, 15, side + 2, 16, color)
    return cells


BROW_SHAPES = ["flat", "arch", "thick"]


def brows(kind: str) -> CELLMAP:
    cells: CELLMAP = {}
    for side in (10, 17):
        if kind == "flat":
            rect(cells, side, 12, side + 4, 12, OUTLINE)
        elif kind == "arch":
            rect(cells, side, 12, side + 4, 12, OUTLINE)
            cells[(side, 11)] = OUTLINE
            cells[(side + 4, 11)] = OUTLINE
        else:
            rect(cells, side, 11, side + 4, 12, OUTLINE)
    return cells


MOUTH_SHAPES = ["smile", "laugh", "neutral", "smirk"]


def mouth(kind: str, color: str) -> CELLMAP:
    cells: CELLMAP = {}
    if kind == "smile":
        rect(cells, 13, 21, 18, 21, color)
        cells[(12, 20)] = color
        cells[(19, 20)] = color
    elif kind == "laugh":
        rect(cells, 13, 20, 18, 22, color)
        rect(cells, 14, 21, 17, 21, WHITE)
    elif kind == "neutral":
        rect(cells, 13, 21, 18, 21, color)
    else:  # smirk
        rect(cells, 14, 21, 18, 21, color)
        cells[(13, 20)] = color
        cells[(19, 20)] = color
    return cells


GLASSES_SHAPES = ["square", "round", "shades"]


def glasses(kind: str) -> CELLMAP:
    cells: CELLMAP = {}
    if kind == "square":
        for side in (9, 17):
            ring(cells, side, 13, side + 5, 18, DARK)
        rect(cells, 15, 15, 16, 15, DARK)
    elif kind == "round":
        for side in (10, 18):
            ring(cells, side, 14, side + 3, 17, DARK)
        rect(cells, 14, 15, 17, 15, DARK)
    else:  # shades
        for side in (9, 17):
            rect(cells, side, 14, side + 5, 17, DARK)
        rect(cells, 15, 15, 16, 15, DARK)
    return cells


# ---------------------------------------------------------------- 输出


def to_image(cells: CELLMAP, tintable: bool) -> tuple[Image.Image, Image.Image | None]:
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    mask = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0)) if tintable else None
    for (x, y), color in cells.items():
        px = (x * CELL, y * CELL, (x + 1) * CELL - 1, (y + 1) * CELL - 1)
        base.paste(color, px)
        if mask is not None and color == WHITE:
            mask.paste(WHITE, px)
    return base, mask


JOBS: list[tuple[str, str, bool, list[tuple[str, CELLMAP]]]] = [
    ("01_skin", "skin", True, [(name, face(name)) for name in ("round", "square", "long")]),
    ("04_hair", "hair", True, [(kind, hair(kind)) for kind in HAIR_STYLES]),
    ("05_eyes", "eyes", False, [(kind, eyes(kind, DARK)) for kind in EYE_SHAPES]),
    ("06_brows", "brows", True, [(kind, brows(kind)) for kind in BROW_SHAPES]),
    ("07_mouth", "mouth", False, [(kind, mouth(kind, "#C0504D")) for kind in MOUTH_SHAPES]),
    ("08_glasses", "glasses", False, [(kind, glasses(kind)) for kind in GLASSES_SHAPES]),
]


def main() -> int:
    total = 0
    for folder, slot, tintable, variants in JOBS:
        target_dir = ASSETS / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        for position, (kind, cells) in enumerate(variants, start=1):
            base, mask = to_image(cells, tintable)
            name = f"pixel_{slot}_{position:02d}"
            base.save(target_dir / f"{name}.png", optimize=True)
            if mask is not None:
                mask.save(target_dir / f"{name}_tint.png", optimize=True)
            total += 1
            print(f"{name:20s} <- {kind}")
    print(f"完成：{total} 张")
    return 0


if __name__ == "__main__":
    sys.exit(main())
