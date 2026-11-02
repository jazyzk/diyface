"""颜色解析与着色。

着色用「相乘」而不是整层染色：白色区域变成目标色，黑色描边保持黑，
中间的明暗自然保留。素材如果是纯白底，换任何颜色都不会发灰。
"""

from __future__ import annotations

import re

from PIL import Image, ImageChops

_HEX = re.compile(r"#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})")


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """把 ``#RGB`` 或 ``#RRGGBB`` 转成三元组；非法输入直接报错。"""
    if not _HEX.fullmatch(value):
        raise ValueError(f"颜色必须是 #RGB 或 #RRGGBB，收到 {value!r}")

    digits = value.lstrip("#")
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    return tuple(int(digits[i : i + 2], 16) for i in (0, 2, 4))


def tint(layer: Image.Image, color: str, mask: Image.Image | None = None) -> Image.Image:
    """按目标颜色给图层着色，保留原有的 alpha。

    ``mask`` 给定时（白=上色、黑=保留原色），用于保护高光等不该变色的区域。
    """
    red, green, blue = hex_to_rgb(color)
    solid = Image.new("RGB", layer.size, (red, green, blue))
    tinted = ImageChops.multiply(layer.convert("RGB"), solid)
    tinted.putalpha(layer.getchannel("A"))

    if mask is None:
        return tinted
    gray = mask if mask.mode == "L" else mask.convert("L")
    return Image.composite(tinted, layer, gray)
