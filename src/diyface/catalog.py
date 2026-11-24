"""扫描 assets/ 目录，生成素材清单。

约定：
* 每个槽位一个目录，目录名与 ``models.SLOTS`` 里的 ``folder_no`` 一致（如 ``04_hair``）；
* 只收目录顶层的 ``*.png``，下划线开头的文件（参考图、缩略图）跳过；
* 每张图必须 1024×1024、RGBA，文件名必须是 ``<槽位>_<形状>_<两位序号>`` 形式。

这套校验放在扫描阶段，是为了让不合规的素材在开发期就报错，
而不是等渲染出图才发现「某张图偏了」。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .models import PALETTES, SLOTS, Slot, SlotId

CANVAS = 1024
_ASSET_NAME = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*")


@dataclass(frozen=True)
class Asset:
    """一张可用的图层素材。"""

    id: str
    slot: SlotId
    path: Path


def scan_slot(root: Path, slot: Slot) -> list[Asset]:
    """扫描单个槽位目录；目录不存在时返回空列表（槽位还没开工）。"""
    folder = root / slot.folder_no
    if not folder.is_dir():
        return []

    assets: list[Asset] = []
    for path in sorted(folder.glob("*.png")):
        if path.name.startswith("_") or path.name.endswith("_tint.png"):
            continue                          # 参考图、缩略图、tint 蒙版都不算素材
        if not _ASSET_NAME.fullmatch(path.stem):
            raise ValueError(f"{path.name} 文件名不合规，只允许小写字母、数字与下划线")
        with Image.open(path) as image:
            if image.size != (CANVAS, CANVAS):
                raise ValueError(f"{path.name} 尺寸 {image.size} 应为 {CANVAS}x{CANVAS}")
            if image.mode != "RGBA":
                raise ValueError(f"{path.name} 必须是 RGBA，当前 {image.mode}")
        assets.append(Asset(id=path.stem, slot=slot.id, path=path))
    return assets


def scan(root: Path) -> dict[SlotId, list[Asset]]:
    """扫描全部槽位，只返回有素材的槽位。"""
    catalog: dict[SlotId, list[Asset]] = {}
    for slot in SLOTS:
        assets = scan_slot(root, slot)
        if assets:
            catalog[slot.id] = assets
    return catalog


STYLE_PREFIXES: dict[str, str] = {
    "lorelei_": "lorelei",
    "pixel_": "pixel",
}

STYLE_LABELS: dict[str, dict[str, str]] = {
    "adventurer": {"zh": "美式卡通", "en": "Adventurer"},
    "lorelei": {"zh": "手绘线稿", "en": "Lorelei"},
    "pixel": {"zh": "像素方块", "en": "Pixel"},
}


#: 整身像素形象的 id 前缀（放在 skin 槽位，但不参与相乘上色）
SPRITE_PREFIXES: tuple[str, ...] = ("pixel_subject",)


def is_sprite(asset_id: str) -> bool:
    return any(asset_id.startswith(prefix) for prefix in SPRITE_PREFIXES)


def style_of(asset_id: str) -> str:
    """从素材 id 判断属于哪套风格；没有前缀的归入默认风格。"""
    for prefix, style in STYLE_PREFIXES.items():
        if asset_id.startswith(prefix):
            return style
    return "adventurer"


def styles(catalog: dict[SlotId, list[Asset]]) -> list[dict]:
    """给前端的风格列表：每种风格在每个槽位上的默认素材。"""
    defaults: dict[str, dict[str, str]] = {}
    for slot in SLOTS:
        if slot.id is SlotId.GLASSES:
            continue
        for asset in catalog.get(slot.id, []):
            style = style_of(asset.id)
            defaults.setdefault(style, {}).setdefault(slot.id.value, asset.id)
    ordered = sorted(defaults.items(), key=lambda item: (item[0] != "pixel", item[0]))
    return [
        {"id": style, "label": STYLE_LABELS.get(style, {"zh": style, "en": style}), "defaults": slots}
        for style, slots in ordered
    ]


def index(catalog: dict[SlotId, list[Asset]]) -> dict[SlotId, dict[str, Asset]]:
    """转成渲染器需要的「槽位 → 素材 id → 素材」两层字典。"""
    return {slot: {asset.id: asset for asset in assets} for slot, assets in catalog.items()}


def manifest(catalog: dict[SlotId, list[Asset]]) -> dict:
    """给前端的素材清单，按 z 序输出，空槽位不出现。"""
    slots = []
    for slot in SLOTS:
        assets = catalog.get(slot.id, [])
        if not assets:
            continue
        slots.append(
            {
                "id": slot.id.value,
                "label": {"zh": slot.label_zh, "en": slot.label_en},
                "z": slot.z,
                "tintable": slot.tintable,
                "default_color": slot.default_color,
                "colors": list(PALETTES.get(slot.id, (slot.default_color,))),
                "assets": [
                    {
                        "id": asset.id,
                        "file": f"{slot.folder_no}/{asset.path.name}",
                        "thumb": f"{slot.folder_no}/_thumb/{asset.path.stem}_256.png",
                        "style": style_of(asset.id),
                    }
                    for asset in assets
                ],
            }
        )
    return {"schema": 1, "slots": slots, "styles": styles(catalog)}
