"""像素头像的背景预设。

不占素材槽位、不增加 PNG：每个背景都是 32×32 的规则图案，运行时按名字现画再放大 32 倍，
好处是「可选」但仓库里不多一堆图片，分享链接也只需要存一个名字。

新增背景只需在 ``PRESETS`` 里加一项并写一个绘制函数。
"""

from __future__ import annotations

import random
from collections.abc import Callable

from PIL import Image

GRID = 32
CELL = 32
SIZE = GRID * CELL

#: 每个背景用固定种子，保证同一名字每次画出来一样
SEED = 20261124


def _color(hex_color: str) -> tuple[int, int, int, int]:
    return (
        int(hex_color[1:3], 16),
        int(hex_color[3:5], 16),
        int(hex_color[5:7], 16),
        255,
    )


def _canvas() -> Image.Image:
    return Image.new("RGBA", (GRID, GRID), (0, 0, 0, 0))




def _put(image: Image.Image, xy: tuple[int, int], color: str | tuple[int, int, int, int]) -> None:
    image.putpixel(xy, _color(color) if isinstance(color, str) else color)


def _fill(image: Image.Image, y0: int, y1: int, color: str) -> None:
    for y in range(y0, y1):
        for x in range(GRID):
            _put(image, (x, y), _color(color))


def _grass(image: Image.Image) -> None:
    _fill(image, 0, 20, "#8FD3F4")
    _fill(image, 20, GRID, "#4CAF50")
    rng = random.Random(SEED)
    for _ in range(40):
        x = rng.randrange(GRID)
        y = rng.randrange(21, GRID)
        _put(image, (x, y), _color("#2E7D32"))
    for x, y in ((25, 4), (26, 4), (25, 5), (26, 5), (24, 3), (27, 3)):
        _put(image, (x, y), _color("#FFE44B"))


def _sky(image: Image.Image) -> None:
    _fill(image, 0, 22, "#9AD0F5")
    _fill(image, 22, GRID, "#BDE7C8")
    for cx, cy in ((6, 6), (18, 9), (26, 4)):
        for dx in range(-2, 3):
            _put(image, ((cx + dx) % GRID, cy), "#FFFFFF")
        for dx in range(-1, 2):
            _put(image, ((cx + dx) % GRID, cy + 1), "#FFFFFF")


def _sunset(image: Image.Image) -> None:
    _fill(image, 0, 12, "#FF8A65")
    _fill(image, 12, 22, "#FFB74D")
    _fill(image, 22, GRID, "#5D4037")
    for x in range(12, 20):
        _put(image, (x, 17), _color("#FFE082"))
    for x in range(13, 19):
        _put(image, (x, 16), _color("#FFE082"))


def _night(image: Image.Image) -> None:
    _fill(image, 0, 22, "#1B2A4A")
    _fill(image, 22, GRID, "#16281F")
    rng = random.Random(SEED + 1)
    for _ in range(30):
        x, y = rng.randrange(GRID), rng.randrange(0, 20)
        _put(image, (x, y), _color("#FFFFFF"))
    for x, y in ((24, 5), (25, 5), (26, 5), (24, 6), (26, 6), (25, 7)):
        _put(image, (x, y), _color("#FFF59D"))


def _forest(image: Image.Image) -> None:
    _fill(image, 0, 18, "#A8D8C8")
    _fill(image, 18, GRID, "#2E7D32")
    rng = random.Random(SEED + 2)
    for _ in range(8):
        x = rng.randrange(GRID)
        for dy in range(0, 10):
            for dx in range(-2, 3):
                if abs(dx) <= (10 - dy) // 2:
                    _put(image, ((x + dx) % GRID, 8 + dy), "#1B5E20")


def _desert(image: Image.Image) -> None:
    _fill(image, 0, 16, "#FFCC80")
    _fill(image, 16, GRID, "#E6B85C")
    for x in range(10, 18):
        _put(image, (x, 12), _color("#FFF176"))
    for x in range(11, 17):
        _put(image, (x, 13), _color("#FFF176"))


def _snow(image: Image.Image) -> None:
    _fill(image, 0, 20, "#DCEBF7")
    _fill(image, 20, GRID, "#FFFFFF")
    rng = random.Random(SEED + 3)
    for _ in range(26):
        x, y = rng.randrange(GRID), rng.randrange(0, 20)
        _put(image, (x, y), _color("#FFFFFF"))


def _water(image: Image.Image) -> None:
    _fill(image, 0, 18, "#81D4FA")
    _fill(image, 18, GRID, "#0288D1")
    for y in range(19, GRID, 2):
        for x in range(0, GRID, 4):
            _put(image, (x, y), _color("#4FC3F7"))


#: 名字 -> (中文名, 英文名, 绘制函数)
PRESETS: dict[str, tuple[str, str, Callable[[Image.Image], None]]] = {
    "grass": ("草地", "Grass", _grass),
    "sky": ("晴空", "Sky", _sky),
    "sunset": ("黄昏", "Sunset", _sunset),
    "night": ("夜晚", "Night", _night),
    "forest": ("森林", "Forest", _forest),
    "desert": ("沙漠", "Desert", _desert),
    "snow": ("雪地", "Snow", _snow),
    "water": ("水面", "Water", _water),
}


def render(name: str) -> Image.Image | None:
    """按名字画出 1024 的背景；未知名字返回 None。"""
    preset = PRESETS.get(name)
    if preset is None:
        return None
    image = _canvas()
    preset[2](image)
    return image.resize((SIZE, SIZE), Image.NEAREST)


def manifest() -> list[dict]:
    return [
        {"id": name, "label": {"zh": zh, "en": en}} for name, (zh, en, _) in PRESETS.items()
    ]
