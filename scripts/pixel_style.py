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
    "a": "#4A90D9",
    "v": "#6D8EAE",
    "q": "#D7ECFF",
    "c": "#E8CBA4",
    "k": "#3B2B23",
    "o": "#F39C12",
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
......xxxx......
.....xaaaax.....
....xaaxaax.....
....xaaaaax.....
.....xaaax......
......xxx.......
.....xxxxx......
....xaaaaax.....
...xaxaaaxax....
...xax...xax....
....xx...xx.....
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
....xxxx........
...xaaaax...xx..
..xaaaaaaaxxaax.
.xaawaaaawaaxax.
.xaawaaaawaaax..
..xaaaaaaaxxaax.
...xaaaax...xx..
....xxxx........
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
....xqqqqqx.....
...xqqqqqqqx....
...xqqqqqqqx....
..xqqkqqkqqqx...
..xqqkqqkqqqx...
..xqqqqqqqqqx...
..xqqqqqqqqqx...
..xqqqqqqqqqx...
..xqqqqqqqqqx...
..xqqqqqqqqqx...
..xqqqqqqqqqx...
..xqxqxqxqxqx...
...x.x.x.x.x....
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
......xxxx......
.....xaaaax.....
....xaaxaax.....
....xaaaaax.....
.....xaaax......
......xxx.......
.....xxxxx......
....xaaaaax.....
...xaxaaaxax....
...xax...xax....
....xx...xx.....
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
....xxxx........
...xaaaax...xx..
..xaaaaaaaxxaax.
.xaawaaaawaaxax.
.xaawaaaawaaax..
..xaaaaaaaxxaax.
...xaaaax...xx..
....xxxx........
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


PIG_SPRITE = """
................
...xx......xx...
..xppx....xppx..
..xpppxxxxpppx..
.xpppppppppppx..
.xppwppppwpppx..
.xpppppppppppx..
.xppxxxxxxpppx..
.xppxpwwpxpppx..
.xppxxxxxxpppx..
.xpppppppppppx..
..xpppppppppx...
...xxxppppxx....
......xxxx......
................
................
"""

SHEEP_SPRITE = """
................
...wwwwww.......
..wwwwwwww......
.wwwwwwwwww.....
.wwxxxxxxxxww...
wwxkkkkkkkkxww..
wwxkkkkkkkkxww..
.wwxkwwkkwxww...
.wwxkkkkkkxww...
..wwxxxxxxww....
..wwwwwwwwww....
.wwwwwwwwwwww...
.wwwwwwwwwwww...
..wwwwwwwwww....
..xx..xx..xx....
................
"""

DUCK_SPRITE = """
................
.....xxxxx......
....xyyyyyx.....
...xyyyyyyyx....
...xywyywyyx....
....xyyyyyx.....
.....xooox......
....xyyyyyx.....
...xyyyyyyyx....
..xyyyyyyyyyx...
..xyyyyyyyyyx...
...xyyyyyyyx....
....xxxxxxxx....
.....x..x.......
....xx..xx......
................
"""

RABBIT_SPRITE = """
................
...xx....xx.....
..xwwx..xwwx....
..xwwx..xwwx....
..xwwx..xwwx....
..xwwxxxxwwx....
..xwwwwwwwwx....
..xwwkwwkwwx....
..xwwwwwwwwx....
..xwwwppwwwx....
..xwwwwwwwwx....
...xwwwwwwx.....
....xwwwwx......
.....xxxx.......
................
................
"""

FOX_SPRITE = """
................
..x........x....
..xx......xx....
..xoxxxxxxox....
..xoooooooox....
..xowxooxwxox...
..xoooooooox....
...xowwwwwox....
....xowwox......
...xooooooox....
..xoooooooooox..
..xoowwwooooox..
..xooowwwoooox..
...xxoooooox....
.....xxxxxx.....
................
"""

BEAR_SPRITE = """
................
...xx......xx...
..xbbx....xbbx..
..xbbbbbbbbbx...
.xbbbbbbbbbbbx..
.xbbwbbbbwbbbx..
.xbbbbbbbbbbbx..
.xbbbwwwwbbbbx..
.xbbbwppwbbbbx..
.xbbbbwwbbbbbx..
..xbbbbbbbbbx...
...xbbbbbbbx....
....xxxxxxx.....
................
................
................
"""

FROG_SPRITE = """
................
...xx......xx...
..xnnx....xnnx..
..xnwnxxxxnwnx..
..xnnnnnnnnnnx..
.xnnnnnnnnnnnnx.
.xnwwnnnnnnwwnx.
.xnnnnnnnnnnnnx.
.xnnnxxxxxxnnnx.
.xnnnnnnnnnnnnx.
..xnnnnnnnnnnx..
...xxnnnnnnxx...
.....xxxxxx.....
................
................
................
"""

OWL_SPRITE = """
................
..xx......xx....
.xccx....xccx...
.xcccxxxxcccx...
xccccccccccccx..
xccwwccccwwccx..
xcwkkwccwkkwcx..
xccwwccccwwccx..
xccccooocccccx..
xcccccoocccccx..
xccccccccccccx..
.xccccccccccx...
..xccccccccx....
...xxccccxx.....
.....xxxx.......
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
    ("pig", PIG_SPRITE),
    ("sheep", SHEEP_SPRITE),
    ("duck", DUCK_SPRITE),
    ("rabbit", RABBIT_SPRITE),
    ("fox", FOX_SPRITE),
    ("bear", BEAR_SPRITE),
    ("frog", FROG_SPRITE),
    ("owl", OWL_SPRITE),
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


HAIR_MAIN = "#F2F2F2"
HAIR_SHADOW = "#C9C9C9"
HAIR_LIGHT = "#FFFFFF"


def _cap(x: int, y: int) -> bool:
    dx = (x + 0.5 - 16) / 8.9
    dy = (y + 0.5 - 13.0) / 8.6
    return dx * dx + dy * dy <= 1.0 and y <= 12


def hair(kind: str) -> CELLMAP:  # noqa: F811
    cells: CELLMAP = {}

    if kind not in ("bun", "mohawk"):
        for y in range(3, 13):
            for x in range(32):
                if _cap(x, y):
                    cells[(x, y)] = HAIR_MAIN
        for x in range(32):
            if cells.get((x, 12)) == HAIR_MAIN:
                cells[(x, 12)] = HAIR_SHADOW
        for x in range(32):
            if cells.get((x, 7)) == HAIR_MAIN:
                cells[(x, 7)] = HAIR_LIGHT

    if kind == "short":
        for y in range(11, 14):
            for x in (8, 9, 22, 23):
                if _cap(x, y):
                    cells[(x, y)] = HAIR_SHADOW
    elif kind == "bob":
        for y in range(12, 21):
            for x in (8, 9, 22, 23):
                cells[(x, y)] = HAIR_MAIN
            for x in (9, 22):
                cells[(x, y)] = HAIR_SHADOW
    elif kind == "long":
        for y in range(12, 28):
            for x in (7, 8, 9, 22, 23, 24):
                cells[(x, y)] = HAIR_MAIN
            for x in (9, 22):
                cells[(x, y)] = HAIR_SHADOW
    elif kind == "bun":
        for y in range(5, 13):
            for x in range(9, 23):
                if _cap(x, y) or y >= 11:
                    cells[(x, y)] = HAIR_MAIN
        for x in range(32):
            if cells.get((x, 12)) == HAIR_MAIN:
                cells[(x, 12)] = HAIR_SHADOW
        for y in range(1, 6):
            for x in (14, 15, 16, 17):
                cells[(x, y)] = HAIR_MAIN
        for x in (16, 17):
            cells[(x, 5)] = HAIR_SHADOW
    else:  # mohawk
        for y in range(3, 12):
            for x in (15, 16):
                cells[(x, y)] = HAIR_MAIN
        for y in range(3, 12):
            cells[(16, y)] = HAIR_SHADOW
        for y in range(9, 13):
            for x in (10, 11, 20, 21):
                cells[(x, y)] = HAIR_SHADOW
    return cells


# ======================================================================
# 第三代画法：借鉴 BotPixel（MIT）的 32×32 布局思路
# 头用椭圆/收下巴的掩膜，五官用 4×4 ASCII 精灵，明暗走 3 档
# 代码为原创实现，仅参考其网格布局与「精灵式五官」的组织方式
# ======================================================================

INK = "#2B1B12"
EYE_COLORS = {"K": INK, "W": "#FFFFFF", "I": "#2B2B2B", "D": "#7A8471", "L": "#FFFFFF"}
BROW_COLOR = INK
MOUTH_COLORS = {"K": "#B0504D", "W": "#FFFFFF", "M": "#6E1F1F", "T": "#E5807A"}


def _ellipse(cx: float, cy: float, rx: float, ry: float):
    def mask(x: int, y: int) -> bool:
        dx = (x + 0.5 - cx) / rx
        dy = (y + 0.5 - cy) / ry
        return dx * dx + dy * dy <= 1.0

    return mask


HEAD_SHAPES = {
    "round": _ellipse(16, 16.2, 7.8, 8.2),
    "square": _ellipse(16, 16.0, 8.4, 7.9),
    "long": _ellipse(16, 16.6, 6.8, 9.3),
}


def face(shape: str) -> CELLMAP:  # noqa: F811
    mask = HEAD_SHAPES.get(shape, HEAD_SHAPES["round"])
    cells: CELLMAP = {}

    for y in range(32):
        for x in range(32):
            if not mask(x, y):
                continue
            border = any(
                not mask(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            cells[(x, y)] = "#C9C9C9" if border else WHITE

    # 下巴与右颊再压一档
    for y in range(20, 27):
        for x in range(18, 23):
            if cells.get((x, y)) == WHITE:
                cells[(x, y)] = "#E2E2E2"

    # 鼻子
    cells[(15, 18)] = "#BFBFBF"
    cells[(16, 18)] = "#BFBFBF"

    # 耳朵
    for y in (15, 16, 17):
        if (7, y) not in cells:
            cells[(7, y)] = WHITE
        if (24, y) not in cells:
            cells[(24, y)] = WHITE

    edge: CELLMAP = {}
    for (x, y) in list(cells):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbour = (x + dx, y + dy)
            if neighbour not in cells:
                edge[neighbour] = INK
    cells.update(edge)
    return cells


EYE_ART = {
    "dot": ["....", ".KK.", ".KK.", "...."],
    "big": ["KKKK", "DWDD", "IDDI", "LIIL"],
    "star": ["KKKK", "DWDW", "IDDI", "LIWL"],
    "wink": ["KKKK", "DWDD", "IDDI", "LIIL"],
}


def eyes(kind: str, color: str) -> CELLMAP:  # noqa: F811
    art = EYE_ART.get(kind, EYE_ART["big"])
    cells: CELLMAP = {}
    for start_x in (11, 18):
        for row, line in enumerate(art):
            for col, mark in enumerate(line):
                if mark == ".":
                    continue
                cells[(start_x + col, 13 + row)] = EYE_COLORS.get(mark, color)
    if kind == "wink":
        # 左眼改成一条闭眼线
        for x in range(11, 15):
            for y in range(13, 17):
                cells.pop((x, y), None)
        for x in range(11, 15):
            cells[(x, 15)] = INK
    return cells


BROW_ART = {"flat": ["BBBB"], "arch": [".BB."], "thick": ["BBBB", "BBBB"]}


def brows(kind: str) -> CELLMAP:  # noqa: F811
    art = BROW_ART.get(kind, BROW_ART["flat"])
    cells: CELLMAP = {}
    for start_x in (11, 18):
        for row, line in enumerate(art):
            for col, mark in enumerate(line):
                if mark != ".":
                    cells[(start_x + col, 11 + row)] = BROW_COLOR
    return cells


MOUTH_ART = {
    "smile": ["K..K", ".KK."],
    "laugh": ["KWWK", ".KK."],
    "neutral": [".KK."],
    "smirk": ["...K", ".KK."],
}


def mouth(kind: str, color: str) -> CELLMAP:  # noqa: F811
    art = MOUTH_ART.get(kind, MOUTH_ART["smile"])
    cells: CELLMAP = {}
    start_x = 14
    start_y = 20
    for row, line in enumerate(art):
        for col, mark in enumerate(line):
            if mark == ".":
                continue
            cells[(start_x + col, start_y + row)] = MOUTH_COLORS.get(mark, color)
    return cells



# ======================================================================
# 第四代：方块脸回归 + 更丰富的头发/眼睛/嘴/眼镜
# 布局参考 DiceBear pixel-art（CC0）的部件分类，画法为本项目自有实现
# ======================================================================

FACE_SHAPES_V4 = {
    "round": (9, 22, 8, 25),
    "square": (8, 23, 8, 26),
    "long": (10, 21, 7, 27),
}

SKIN_SHADE = "#CFCFCF"
SKIN_SHADE_2 = "#E3E3E3"


def face(shape: str) -> CELLMAP:  # noqa: F811
    left, right, top, bottom = FACE_SHAPES_V4.get(shape, FACE_SHAPES_V4["round"])
    cells: CELLMAP = {}
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            cells[(x, y)] = WHITE

    # 切角，保持方块感但不要太硬
    for x, y in (
        (left, top), (right, top), (left, bottom), (right, bottom),
    ):
        cells.pop((x, y), None)

    # 右侧与下巴阴影
    for y in range(top + 1, bottom):
        cells[(right, y)] = SKIN_SHADE
    for x in range(left + 1, right):
        cells[(x, bottom)] = SKIN_SHADE
    for x in range(left + 2, right - 1):
        cells[(x, bottom - 1)] = SKIN_SHADE_2

    # 鼻子
    cells[(15, bottom - 7)] = SKIN_SHADE
    cells[(16, bottom - 7)] = SKIN_SHADE

    # 耳朵
    for y in (top + 6, top + 7, top + 8):
        cells[(left - 1, y)] = WHITE
        cells[(right + 1, y)] = SKIN_SHADE

    edge: CELLMAP = {}
    for (x, y) in list(cells):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbour = (x + dx, y + dy)
            if neighbour not in cells:
                edge[neighbour] = INK
    cells.update(edge)
    return cells


HAIR_KINDS_V4 = [
    "short", "bob", "long", "bun", "mohawk", "side",
    "twin", "pony", "afro", "fringe", "curly", "bald",
]


def hair(kind: str) -> CELLMAP:  # noqa: F811
    MAIN, SHADOW, LIGHT = "#F2F2F2", "#C9C9C9", "#FFFFFF"
    cells: CELLMAP = {}

    def cap(x0=8, y0=6, x1=23, y1=10) -> None:
        rect(cells, x0, y0, x1, y1, MAIN)
        rect(cells, x0, y0, x1, y0, LIGHT)
        rect(cells, x0, y1, x1, y1, SHADOW)

    if kind == "bald":
        for y in (11, 12):
            cells[(8, y)] = MAIN
            cells[(23, y)] = MAIN
        return cells

    if kind == "mohawk":
        rect(cells, 15, 3, 16, 11, MAIN)
        rect(cells, 16, 3, 16, 11, SHADOW)
        rect(cells, 14, 8, 14, 10, MAIN)
        rect(cells, 17, 8, 17, 10, MAIN)
        return cells

    if kind == "afro":
        rect(cells, 6, 4, 25, 11, MAIN)
        for x, y in ((6, 4), (25, 4), (6, 11), (25, 11)):
            cells.pop((x, y), None)
        rect(cells, 9, 4, 22, 4, LIGHT)
        rect(cells, 6, 11, 25, 11, SHADOW)
        return cells

    if kind == "bun":
        cap()
        rect(cells, 14, 2, 17, 5, MAIN)
        rect(cells, 16, 2, 17, 5, SHADOW)
        return cells

    cap()

    if kind == "short":
        rect(cells, 8, 11, 9, 12, MAIN)
        rect(cells, 22, 11, 23, 12, SHADOW)
    elif kind == "bob":
        rect(cells, 7, 11, 8, 20, MAIN)
        rect(cells, 23, 11, 24, 20, SHADOW)
    elif kind == "long":
        rect(cells, 7, 11, 8, 27, MAIN)
        rect(cells, 23, 11, 24, 27, SHADOW)
        rect(cells, 9, 13, 9, 22, SHADOW)
    elif kind == "side":
        rect(cells, 18, 10, 23, 15, MAIN)
        rect(cells, 19, 10, 23, 11, LIGHT)
        rect(cells, 8, 11, 9, 13, SHADOW)
    elif kind == "twin":
        rect(cells, 6, 11, 8, 24, MAIN)
        rect(cells, 22, 11, 24, 24, SHADOW)
        rect(cells, 6, 24, 8, 25, SHADOW)
    elif kind == "pony":
        rect(cells, 20, 11, 23, 15, SHADOW)
        rect(cells, 22, 15, 23, 26, MAIN)
        rect(cells, 22, 26, 23, 27, SHADOW)
    elif kind == "fringe":
        rect(cells, 9, 11, 22, 11, SHADOW)
        rect(cells, 10, 12, 14, 12, SHADOW)
    elif kind == "curly":
        for x in range(7, 25, 3):
            rect(cells, x, 11, x + 1, 13, SHADOW)
    return cells


EYE_ART_V4 = {
    "dot": ["....", ".KK.", ".KK.", "...."],
    "big": ["KKKK", "DWDD", "IDDI", "LIIL"],
    "sparkle": ["KKKK", "DWDW", "IDDI", "LIWL"],
    "wink": ["KKKK", "DWDD", "IDDI", "LIIL"],
    "sleepy": ["....", "KKKK", "IDDI", "LIIL"],
    "sharp": ["KK..", ".KKK", ".DWD", "..LI"],
    "happy": ["....", ".KK.", "K..K", "...."],
    "closed": ["....", "....", "KKKK", "...."],
}

EYE_KINDS_V4 = list(EYE_ART_V4)


def eyes(kind: str, color: str) -> CELLMAP:  # noqa: F811
    art = EYE_ART_V4.get(kind, EYE_ART_V4["big"])
    cells: CELLMAP = {}
    for start_x in (11, 18):
        for row, line in enumerate(art):
            for col, mark in enumerate(line):
                if mark == ".":
                    continue
                cells[(start_x + col, 13 + row)] = EYE_COLORS.get(mark, color)
    if kind == "wink":
        for x in range(11, 15):
            for y in range(13, 17):
                cells.pop((x, y), None)
        for x in range(11, 15):
            cells[(x, 15)] = INK
    return cells


BROW_ART_V4 = {"flat": ["BBBB"], "arch": [".BB."], "thick": ["BBBB", "BBBB"]}


def brows(kind: str) -> CELLMAP:  # noqa: F811
    art = BROW_ART_V4.get(kind, BROW_ART_V4["flat"])
    cells: CELLMAP = {}
    for start_x in (11, 18):
        for row, line in enumerate(art):
            for col, mark in enumerate(line):
                if mark != ".":
                    cells[(start_x + col, 11 + row)] = BROW_COLOR
    return cells


MOUTH_ART_V4 = {
    "smile": ["K..K", ".KK."],
    "laugh": ["KWWK", ".KK."],
    "neutral": [".KK."],
    "smirk": ["...K", ".KK."],
    "open": ["KKK", "MTM"],
    "cat": ["K.K.K", ".K.K."],
    "tongue": ["KKKK", ".TT."],
    "o": [".K.", "KMK", ".K."],
}

MOUTH_KINDS_V4 = list(MOUTH_ART_V4)


def mouth(kind: str, color: str) -> CELLMAP:  # noqa: F811
    art = MOUTH_ART_V4.get(kind, MOUTH_ART_V4["smile"])
    cells: CELLMAP = {}
    start_x = 14 - (len(art[0]) - 4) // 2
    start_y = 20
    for row, line in enumerate(art):
        for col, mark in enumerate(line):
            if mark == ".":
                continue
            cells[(start_x + col, start_y + row)] = MOUTH_COLORS.get(mark, color)
    return cells


GLASSES_KINDS_V4 = ["square", "round", "shades", "thin", "sport"]


def glasses(kind: str) -> CELLMAP:  # noqa: F811
    cells: CELLMAP = {}
    if kind == "square":
        for side in (10, 18):
            ring(cells, side, 12, side + 4, 16, INK)
        rect(cells, 15, 14, 16, 14, INK)
    elif kind == "round":
        for side in (10, 18):
            ring(cells, side, 13, side + 4, 16, INK)
        rect(cells, 15, 14, 16, 14, INK)
    elif kind == "shades":
        for side in (10, 18):
            rect(cells, side, 13, side + 4, 15, INK)
        rect(cells, 15, 14, 16, 14, INK)
    elif kind == "thin":
        for side in (10, 18):
            rect(cells, side, 14, side + 4, 14, INK)
        rect(cells, 15, 14, 16, 14, INK)
    else:  # sport
        for side in (9, 17):
            rect(cells, side, 13, side + 5, 15, INK)
            cells[(side + 1, 13)] = "#4A90D9"
            cells[(side + 3, 13)] = "#4A90D9"
        rect(cells, 15, 14, 16, 14, INK)
    return cells


JOBS: list[tuple[str, str, bool, list[tuple[str, CELLMAP]]]] = [
    ("01_skin", "skin", True, [(name, face(name)) for name in ("round", "square", "long")]),
    ("04_hair", "hair", True, [(kind, hair(kind)) for kind in HAIR_KINDS_V4]),
    ("05_eyes", "eyes", False, [(kind, eyes(kind, DARK)) for kind in EYE_KINDS_V4]),
    ("06_brows", "brows", True, [(kind, brows(kind)) for kind in BROW_SHAPES]),
    ("07_mouth", "mouth", False, [(kind, mouth(kind, "#C0504D")) for kind in MOUTH_KINDS_V4]),
    ("08_glasses", "glasses", False, [(kind, glasses(kind)) for kind in GLASSES_KINDS_V4]),
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
