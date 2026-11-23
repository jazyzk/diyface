"""把拼豆画布变成头像上的贴纸。

规则：

* 只保留有颜色的格子，四周裁掉透明边；
* 统一缩放到画布宽度的 28%，贴右下角，留 4% 边距；
* 贴纸保持原比例，不会被拉变形。
"""

from __future__ import annotations

from PIL import Image

from .pixel import CANVAS, CELL, GRID, PixelArt, render

STICKER_RATIO = 0.22
MARGIN_RATIO = 0.02


def build(art: PixelArt, style: str = "bead") -> Image.Image | None:
    """返回裁切好的贴纸图层；整块空白则返回 None。"""
    full = render(art, style)
    bbox = full.getchannel("A").getbbox()
    if not bbox:
        return None
    return full.crop(bbox)


def attach(canvas: Image.Image, sticker: Image.Image) -> Image.Image:
    """把贴纸等比缩放后贴到右下角。"""
    size = canvas.size[0]
    target = int(size * STICKER_RATIO)
    scale = min(target / sticker.width, target / sticker.height)
    resized = sticker.resize(
        (max(1, round(sticker.width * scale)), max(1, round(sticker.height * scale))),
        Image.LANCZOS,
    )
    margin = int(size * MARGIN_RATIO)
    position = (size - resized.width - margin, size - resized.height - margin)
    canvas = canvas.copy()
    canvas.alpha_composite(resized, position)
    return canvas
