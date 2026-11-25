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



# ---------------------------------------------------------------- 像素小装饰

#: ASCII 画稿：. 空，o 描边，其余字母见 DECOR_COLORS
DECOR_COLORS = {
    "o": OUTLINE,
    "b": "#A97142",
    "w": "#FFFFFF",
    "r": "#D50000",
    "y": "#F1C40F",
    "g": "#27AE60",
    "p": "#E84393",
    "k": "#1F2430",
}

CAT = """
.o....o.
.ob..bo.
obbbbbbo
obwbbwbo
obbbbbbo
obbbbbbo
.obbbbo.
..oooo..
"""

DOG = """
.oo..oo.
.obbbbo.
obbbbbbo
obwbbwbo
obbbbbbo
.obbbbo.
..oooo..
........
"""

BEAR = """
.oo..oo.
obbbbbbo
obwbbwbo
obbbbbbo
obbbbbbo
.obbbbo.
..oooo..
........
"""

BUNNY = """
.o..o...
.o..o...
.obbo...
obbbbbbo
obwbbwbo
.obbbbo.
..oooo..
........
"""

APPLE = """
...og...
..orro..
.orrrro.
orrrrrro
orrrrrro
.orrrro.
..orro..
...oo...
"""

CHERRY = """
....og..
...og...
..og....
.orro...
orrrro..
.orrrro.
..orro..
........
"""

MELON = """
........
.oooooo.
orrrrrro
orwwrwro
.orroo..
..oo....
........
........
"""

SUNFLOWER = """
.y..y...
..yy....
.yyyy...
yykyyy..
.yyyy...
..yy....
.y..y...
........
"""

TULIP = """
.o..o...
.orro...
orrrro..
.orro...
..og....
..og....
..og....
........
"""

ROSE = """
..oo....
.orro...
orrrro..
.orrrro.
..orro..
...oo...
........
........
"""

STAR = """
...y....
...y....
.yyy.y..
..yyy...
..yyy...
.yy.yy..
........
........
"""

HEART = """
........
.orrro..
orrrrro.
orrrrro.
.orrrro.
..orro..
...oo...
........
"""


BUTTERFLY = """
.o...o..
oro.oro.
orrrrro.
.orrrro.
orrrrro.
oro.oro.
.o...o..
........
"""

MUSHROOM = """
..oooo..
.orrrro.
orrrrrro
.owwwwo.
..owwo..
..owwo..
..oooo..
........
"""

LEAF = """
....og..
...ogg..
..oggo..
.oggo...
.oggo...
..oggo..
...ogg..
....og..
"""

ICECREAM = """
..oooo..
..oyyo..
..oyyo..
..owwo..
.owwwwo.
..owwo..
...oo...
........
"""

RAINBOW = """
.oooooo.
orrrrrro
oyyyyyyo
oggggggo
........
........
........
........
"""

CLOUD = """
..oo....
.oowo...
oowwwoo.
owwwwwwo
.oooooo.
........
........
........
"""

#: (名字, 画稿, 左上角锚点)
DECORS = [
    ("cat", CAT, (23, 20)),
    ("dog", DOG, (23, 20)),
    ("bear", BEAR, (23, 20)),
    ("bunny", BUNNY, (23, 20)),
    ("apple", APPLE, (23, 20)),
    ("cherry", CHERRY, (23, 20)),
    ("melon", MELON, (23, 20)),
    ("sunflower", SUNFLOWER, (23, 3)),
    ("tulip", TULIP, (23, 3)),
    ("rose", ROSE, (23, 3)),
    ("star", STAR, (3, 4)),
    ("heart", HEART, (3, 20)),
    ("butterfly", BUTTERFLY, (23, 6)),
    ("mushroom", MUSHROOM, (23, 21)),
    ("leaf", LEAF, (2, 6)),
    ("icecream", ICECREAM, (23, 21)),
    ("rainbow", RAINBOW, (20, 2)),
    ("cloud", CLOUD, (23, 3)),
]


def parse_art(art: str, anchor: tuple[int, int]) -> CELLMAP:
    cells: CELLMAP = {}
    ax, ay = anchor
    for row, line in enumerate(art.strip("\n").splitlines()):
        for col, mark in enumerate(line):
            if mark == "." or mark not in DECOR_COLORS:
                continue
            x, y = ax + col, ay + row
            if 0 <= x < GRID and 0 <= y < GRID:
                cells[(x, y)] = DECOR_COLORS[mark]
    return cells



# ---------------------------------------------------------------- 整身形象（星露谷风）

SUBJECT_COLORS = {
    "x": OUTLINE,
    "w": "#FFFFFF",
    "c": "#F2D5B8",
    "g": "#95A5A6",
    "b": "#A97142",
    "r": "#D50000",
    "y": "#F1C40F",
    "n": "#27AE60",
    "k": "#1F2430",
    "o": "#FF6D00",
    "p": "#FFB3C7",
}

CAT_SPRITE = """
................
....xx....xx....
...xggx..xggx...
...xggxxxxggx...
...xggggggggx...
...xgwxggxwgx...
...xggggggggx...
....xgwxxwgx....
.....xxggxx.....
....xggggggx....
...xggggggggx...
..xgxggggggxgx..
..xgx.xxxx.xgx..
..xxx......xxx..
................
................
"""

DOG_SPRITE = """
................
...xx......xx...
..xbbx....xbbx..
..xbbxxxxxxbbx..
...xbbbbbbbbx...
...xbwxbbxwbx...
...xbbbbbbbbx...
....xbwxxwbx....
.....xxbbxx.....
....xbbbbbbx....
...xbbbbbbbbx...
..xbxbbbbbbxbx..
..xbx.xxxx.xbx..
..xxx......xxx..
................
................
"""

CHICKEN_SPRITE = """
................
.......xx.......
......xrrx......
.....xrrrrx.....
.....xrrrrx.....
....xwwwwwx.....
...xwwwwwwwx....
...xwkwwwkwx....
....xwwwwwx.....
.....xwowx......
....xwwwwwx.....
...xwwwwwwwx....
...xwwwwwwx.....
....xx..xx......
.....x..x.......
.....x..x.......
"""

COW_SPRITE = """
................
...xx......xx...
..xwwx....xwwx..
..xwwxxxxxxwwx..
...xwwkkwwwwx...
...xwkwwkwwkx...
...xwwkkwwwwx...
....xwpwwpwx....
.....xxwwxx.....
....xwwkkwwx....
...xwwkwwkwwx...
..xwxwwkkwwxwx..
..xwx.xxxx.xwx..
..xxx......xxx..
................
................
"""

APPLE_SPRITE = """
................
.......xx.......
.......xnx......
......xnnnx.....
...xxxxxnxxxx...
..xrrrrrrrrrrx..
.xrrrrrrrrrrrrx.
.xrrwrrrrrrwrrx.
xrrrrrrrrrrrrrrx
xrrrrrrrrrrrrrrx
.xrrrrrrrrrrrrx.
.xrrrrrrrrrrrrx.
..xrrrrrrrrrrx..
...xxxxxxxxxx...
................
................
"""

SUNFLOWER_SPRITE = """
................
....y..y..y.....
...yyy.y.yyy....
..yyyyyyy.yyy...
...yyykkkyyy....
..yyyykkkyyyy...
...yyykkkyyy....
..yyyyyyy.yyy...
...yyy.y.yyy....
....y..y..y.....
.......nn.......
.......nn.......
.......nn.......
......xnnx......
.......xx.......
................
"""

MUSHROOM_SPRITE = """
................
.....xxxxxx.....
...xxrrrrrrxx...
..xrrrwrrrwrrx..
..xrrrrrrrrrrx..
.xrrrwrrrrwrrrx.
.xrrrrrrrrrrrrx.
..xxxxxxxxxxxx..
....xcccccx.....
....xcwwwcx.....
....xcwwwcx.....
....xcccccx.....
.....xxxxx......
................
................
................
"""

SCARECROW_SPRITE = """
................
.....xxxxxx.....
....xyyyyyyx....
....xyyyyyyx....
.....xxxxxx.....
...xxxxxxxxxx...
..xyyyyyyyyyyx..
..xyykxyykxyyx..
..xyyyyyyyyyyx..
...xxyyyyyyxx...
.....xrrrrx.....
....xrrrrrrx....
...xrrrrrrrrx...
...xrrrrrrrrx...
....xxxxxxxx....
................
"""


SLIME_SPRITE = """
................
................
.....xxxxx......
....xnnnnnx.....
...xnnwnnwnx....
...xnnwnnwnx....
...xnnnnnnnx....
...xnnnnnnnx....
....xnnnnnx.....
.....xxxxx......
................
................
................
................
................
................
"""

PUMPKIN_SPRITE = """
................
.......nn.......
......xnnx......
...xxxxxxxxxx...
..xooooooooox...
.xoowoooowooox..
.xooooooooooox..
.xoowoooowooox..
.xooooooooooox..
..xooooooooox...
...xxxxxxxxxx...
................
................
................
................
................
"""

BIRD_SPRITE = """
................
.....xxxxx......
....xbbbxxx.....
...xbwbbbbbx....
...xbbbbbbbx....
....xbbbbbx.....
.....xxxxx......
....xxxxxxx.....
...xbbbbbbbx....
..xbxxbbbxbbx...
..xx..xxx..xx...
................
................
................
................
................
"""

TREE_SPRITE = """
................
.....xxxxx......
...xxnnnnnxx....
..xnnnnnnnnnx...
..xnnnnnnnnnx...
.xnnnnnnnnnnnx..
.xnnnnnnnnnnnx..
..xnnnnnnnnnx...
...xxnnnnnxx....
.....xbbb.......
.....xbbb.......
.....xbbb.......
....xxbbbxx.....
................
................
................
"""

FISH_SPRITE = """
................
................
......xxxx......
....xxbbbbxx....
..xxbbbbbbbbxx..
.xbbwbbbbbbbbbx.
.xbbbbbbbbbbbbx.
..xxbbbbbbbbxx..
....xxbbbbxx....
......xxxx......
................
................
................
................
................
................
"""

GHOST_SPRITE = """
................
.....xxxxx......
...xxwwwwwxx....
..xwwwwwwwwwx...
..xwwkwwwkwwx...
..xwwwwwwwwwx...
..xwwwwwwwwwwx..
..xwwkwwkwwwwx..
..xwwwwwwwwwwx..
.xwwwwwwwwwwwwx.
.xwxxwxxwxxwwwx.
..xx..xx..xx....
................
................
................
................
"""

#: (名字, 画稿)
SUBJECTS = [
    ("cat", CAT_SPRITE),
    ("dog", DOG_SPRITE),
    ("chicken", CHICKEN_SPRITE),
    ("cow", COW_SPRITE),
    ("apple", APPLE_SPRITE),
    ("sunflower", SUNFLOWER_SPRITE),
    ("mushroom", MUSHROOM_SPRITE),
    ("scarecrow", SCARECROW_SPRITE),
    ("slime", SLIME_SPRITE),
    ("pumpkin", PUMPKIN_SPRITE),
    ("bird", BIRD_SPRITE),
    ("tree", TREE_SPRITE),
    ("fish", FISH_SPRITE),
    ("ghost", GHOST_SPRITE),
]


def parse_sprite(art: str, block: int = 2) -> CELLMAP:
    """把 16×16 画稿放大 2 倍贴进 32×32 网格，保证每个像素是方块。"""
    cells: CELLMAP = {}
    lines = art.strip("\n").splitlines()
    if len(lines) != 16 or any(len(line) != 16 for line in lines):
        raise ValueError(f"画稿必须是 16×16，实际 {len(lines)} 行")
    for row, line in enumerate(lines):
        for col, mark in enumerate(line):
            if mark == "." or mark not in SUBJECT_COLORS:
                continue
            for dy in range(block):
                for dx in range(block):
                    cells[(col * block + dx, row * block + dy)] = SUBJECT_COLORS[mark]
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



# ======================================================================
# 第二代画法：更接近「农场像素游戏」的味道
# 粗描边、两档肤色阴影、眼睛带高光、鼻子与嘴有层次
# ======================================================================

SHADE = "#D8D8D8"      # 阴影格（白底相乘后自动变成更深的肤色）
BLUSH = "#F0B9A8"      # 腮红（非着色层，保留原色）

FACE_GEOMETRY = {
    # 名字: (左, 右, 上, 下)
    "round": (9, 22, 8, 25),
    "square": (8, 23, 8, 26),
    "long": (10, 21, 7, 27),
}


def face(shape: str) -> CELLMAP:  # noqa: F811 - 覆盖第一代实现
    left, right, top, bottom = FACE_GEOMETRY.get(shape, FACE_GEOMETRY["round"])
    cells: CELLMAP = {}

    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            cells[(x, y)] = WHITE

    # 圆角：切掉四角
    for x, y in (
        (left, top), (left + 1, top), (right, top), (right - 1, top),
        (left, bottom), (left + 1, bottom), (right, bottom), (right - 1, bottom),
    ):
        cells.pop((x, y), None)
    for x, y in ((left, top + 1), (right, top + 1), (left, bottom - 1), (right, bottom - 1)):
        cells.pop((x, y), None)

    # 右下阴影两格，制造体积感
    for y in range(top + 2, bottom - 1):
        for x in (right - 1, right - 2):
            if (x, y) in cells:
                cells[(x, y)] = SHADE
    for x in range(left + 2, right - 1):
        for y in (bottom - 1, bottom - 2):
            if (x, y) in cells:
                cells[(x, y)] = SHADE

    # 鼻子（两格阴影，给脸一点起伏）
    nose_y = bottom - 7
    cells[(15, nose_y)] = SHADE
    cells[(16, nose_y)] = SHADE

    # 耳朵
    for y in (top + 6, top + 7, top + 8):
        cells[(left - 1, y)] = WHITE
        cells[(right + 1, y)] = SHADE

    # 兜底描边：所有与空格相邻的格子
    edge: CELLMAP = {}
    for (x, y) in list(cells):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbour = (x + dx, y + dy)
            if neighbour not in cells:
                edge[neighbour] = OUTLINE
    cells.update(edge)
    return cells


def hair(kind: str) -> CELLMAP:  # noqa: F811
    MAIN = "#F2F2F2"      # 主色（相乘后就是发色）
    SHADOW = "#C9C9C9"    # 阴影
    LIGHT = "#FFFFFF"     # 高光
    cells: CELLMAP = {}

    def cap(x0: int, y0: int, x1: int, y1: int) -> None:
        rect(cells, x0, y0, x1, y1, MAIN)
        rect(cells, x0, y1, x1, y1, SHADOW)
        rect(cells, x0 + 2, y0 + 1, x1 - 2, y0 + 1, LIGHT)

    if kind == "short":
        cap(8, 6, 23, 10)
        rect(cells, 8, 10, 9, 11, SHADOW)
        rect(cells, 22, 10, 23, 11, SHADOW)
    elif kind == "bob":
        cap(7, 5, 24, 10)
        rect(cells, 7, 10, 7, 20, MAIN)
        rect(cells, 24, 10, 24, 20, SHADOW)
    elif kind == "long":
        cap(7, 5, 24, 10)
        rect(cells, 7, 10, 7, 27, MAIN)
        rect(cells, 24, 10, 24, 27, SHADOW)
        rect(cells, 9, 12, 9, 22, SHADOW)
    elif kind == "bun":
        cap(8, 7, 23, 10)
        rect(cells, 14, 3, 17, 6, MAIN)
        rect(cells, 16, 3, 17, 6, SHADOW)
    elif kind == "mohawk":
        rect(cells, 15, 3, 16, 11, MAIN)
        rect(cells, 16, 3, 16, 11, SHADOW)
        rect(cells, 14, 4, 14, 8, MAIN)
        rect(cells, 17, 4, 17, 8, SHADOW)
    else:  # side
        cap(8, 5, 23, 9)
        rect(cells, 20, 9, 23, 15, MAIN)
        rect(cells, 23, 9, 23, 15, SHADOW)
        rect(cells, 8, 9, 9, 13, SHADOW)
    return cells


def eyes(kind: str, color: str) -> CELLMAP:  # noqa: F811
    cells: CELLMAP = {}
    pairs = ((11, 18),)

    for (lx, rx) in pairs:
        if kind == "dot":
            for x, y in ((lx, 15), (lx + 1, 15), (rx, 15), (rx + 1, 15)):
                cells[(x, y)] = color
        elif kind == "big":
            for side in (lx, rx):
                rect(cells, side, 14, side + 2, 16, "#FFFFFF")
                rect(cells, side, 14, side + 2, 14, color)
                cells[(side + 1, 15)] = color
                cells[(side + 1, 16)] = color
                cells[(side, 15)] = color
                cells[(side + 2, 15)] = color
                cells[(side, 15)] = "#FFFFFF"
        elif kind == "star":
            for side in (lx, rx):
                cells[(side + 1, 13)] = color
                cells[(side, 14)] = color
                cells[(side + 1, 14)] = color
                cells[(side + 2, 14)] = color
                cells[(side + 1, 15)] = "#FFFFFF"
                cells[(side + 1, 16)] = color
        else:  # wink
            rect(cells, lx, 15, lx + 2, 15, color)
            cells[(lx + 1, 14)] = color
            rect(cells, rx, 14, rx + 2, 16, "#FFFFFF")
            cells[(rx + 1, 14)] = color
            cells[(rx, 15)] = color
            cells[(rx + 1, 15)] = color
            cells[(rx + 2, 15)] = color
            cells[(rx + 1, 16)] = color
    return cells


def brows(kind: str) -> CELLMAP:  # noqa: F811
    cells: CELLMAP = {}
    for side in (10, 17):
        if kind == "flat":
            rect(cells, side, 11, side + 4, 11, OUTLINE)
        elif kind == "arch":
            rect(cells, side + 1, 11, side + 3, 11, OUTLINE)
            cells[(side, 12)] = OUTLINE
            cells[(side + 4, 12)] = OUTLINE
        else:
            rect(cells, side, 10, side + 4, 11, OUTLINE)
    return cells


def mouth(kind: str, color: str) -> CELLMAP:  # noqa: F811
    cells: CELLMAP = {}
    LIP = color
    if kind == "smile":
        rect(cells, 13, 21, 18, 21, LIP)
        cells[(12, 20)] = LIP
        cells[(19, 20)] = LIP
        cells[(15, 22)] = LIP
        cells[(16, 22)] = LIP
    elif kind == "laugh":
        rect(cells, 13, 20, 18, 22, LIP)
        rect(cells, 14, 20, 17, 20, "#FFFFFF")
        cells[(13, 20)] = LIP
        cells[(18, 20)] = LIP
    elif kind == "neutral":
        rect(cells, 13, 21, 18, 21, LIP)
        cells[(13, 22)] = LIP
        cells[(18, 22)] = LIP
    else:  # smirk
        rect(cells, 14, 21, 18, 21, LIP)
        cells[(13, 22)] = LIP
        cells[(19, 20)] = LIP
    return cells


JOBS: list[tuple[str, str, bool, list[tuple[str, CELLMAP]]]] = [
    ("01_skin", "skin", True, [(name, face(name)) for name in ("round", "square", "long")]),
    ("04_hair", "hair", True, [(kind, hair(kind)) for kind in HAIR_STYLES]),
    ("05_eyes", "eyes", False, [(kind, eyes(kind, DARK)) for kind in EYE_SHAPES]),
    ("06_brows", "brows", True, [(kind, brows(kind)) for kind in BROW_SHAPES]),
    ("07_mouth", "mouth", False, [(kind, mouth(kind, "#C0504D")) for kind in MOUTH_SHAPES]),
    ("08_glasses", "glasses", False, [(kind, glasses(kind)) for kind in GLASSES_SHAPES]),
    ("10_extra", "extra", False, [(name, parse_art(art, anchor)) for name, art, anchor in DECORS]),
    ("01_skin", "subject", False, [(name, parse_sprite(art)) for name, art in SUBJECTS]),
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
