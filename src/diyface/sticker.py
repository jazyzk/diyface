"""把拼豆画布变成头像上的贴纸。

贴纸可以随意摆放、叠加多张：

* 只保留有颜色的格子，四周裁掉透明边；
* ``x`` / ``y`` 是**归一化中心坐标**（0~1），``scale`` 是贴纸占画布宽度的比例；
* 贴纸保持原比例，不会被拉变形。
"""

from __future__ import annotations

from PIL import Image

from .pixel import PixelArt, render

DEFAULT_SCALE = 0.22
MIN_SCALE = 0.06
MAX_SCALE = 0.6
DEFAULT_X = 0.88
DEFAULT_Y = 0.88


def build(art: PixelArt, style: str = "bead") -> Image.Image | None:
    """返回裁切好的贴纸图层；整块空白则返回 None。"""
    full = render(art, style)
    bbox = full.getchannel("A").getbbox()
    if not bbox:
        return None
    return full.crop(bbox)


def place(
    canvas: Image.Image,
    sticker: Image.Image,
    x: float = DEFAULT_X,
    y: float = DEFAULT_Y,
    scale: float = DEFAULT_SCALE,
) -> Image.Image:
    """把贴纸等比缩放后放到归一化坐标 (x, y) 处，返回新画布。"""
    size = canvas.size[0]
    scale = max(MIN_SCALE, min(MAX_SCALE, float(scale)))
    target = max(1, int(size * scale))
    factor = min(target / sticker.width, target / sticker.height)
    resized = sticker.resize(
        (max(1, round(sticker.width * factor)), max(1, round(sticker.height * factor))),
        Image.LANCZOS,
    )

    left = round(x * size - resized.width / 2)
    top = round(y * size - resized.height / 2)
    left = max(0, min(size - resized.width, left))
    top = max(0, min(size - resized.height, top))

    result = canvas.copy()
    result.alpha_composite(resized, (left, top))
    return result


def attach(canvas: Image.Image, sticker: Image.Image) -> Image.Image:
    """兼容旧用法：贴到默认位置。"""
    return place(canvas, sticker)
