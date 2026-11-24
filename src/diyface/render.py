"""把配方合成为一张 1024 的 RGBA 图。

合成只有四步：按 z 序取层、按槽位着色、alpha 合成、按尺寸缩放编码。
全程不读全局状态，输入配方与素材表，输出图像或字节串，便于脱离 Web 测试。
"""

from __future__ import annotations

import io
from functools import lru_cache

from PIL import Image

from .catalog import Asset, is_sprite
from .models import AvatarRecipe, SLOTS_BY_Z, SlotId
from .palettes import tint
from .sticker import place as place_sticker

CANVAS = 1024
SIZES = (256, 1024)


@lru_cache(maxsize=512)
def load_layer(path: str) -> Image.Image:
    """按路径缓存已解码的图层，避免同一张图反复读盘。"""
    return Image.open(path).convert("RGBA")


def compose(recipe: AvatarRecipe, catalog: dict[SlotId, dict[str, Asset]]) -> Image.Image:
    """把配方涉及的所有图层按 z 序叠成一张 1024 的图。"""
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))

    for slot in SLOTS_BY_Z:
        asset_id = recipe.slots.get(slot.id)
        if not asset_id:
            continue                      # 空槽位不画，也不影响其他层

        try:
            asset = catalog[slot.id][asset_id]
        except KeyError as exc:
            raise KeyError(f"{slot.id.value} 没有素材 {asset_id!r}") from exc

        layer = load_layer(str(asset.path))
        if slot.tintable and not is_sprite(asset_id):
            layer = tint(layer, recipe.colors.get(slot.id, slot.default_color))
        canvas = Image.alpha_composite(canvas, layer)

    return canvas


def render(
    recipe: AvatarRecipe,
    catalog: dict[SlotId, dict[str, Asset]],
    size: int = 256,
    stickers: list[tuple[Image.Image, float, float, float]] | None = None,
) -> bytes:
    """合成并按指定尺寸输出 PNG 字节串；`stickers` 是 (图, x, y, scale) 列表。"""
    if size not in SIZES:
        raise ValueError(f"size 只能是 {SIZES}，收到 {size}")

    image = compose(recipe, catalog)
    for sticker, x, y, scale in stickers or []:
        image = place_sticker(image, sticker, x=x, y=y, scale=scale)
    if size != CANVAS:
        image = image.resize((size, size), Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
