"""批量生成 256 缩略图，供前端素材格使用。

素材是 1024 的原图，几十张一起加载会明显卡顿；缩略图放在同目录的 ``_thumb/`` 下
（下划线开头，扫描时自动跳过），前端用 ``/assets/<槽位>/_thumb/<名字>_256.png``。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from .catalog import scan

THUMB_SIZE = 256
THUMB_DIR = "_thumb"


def thumb_path(source: Path) -> Path:
    """缩略图路径：同目录 `_thumb/<stem>_256.png`。"""
    return source.parent / THUMB_DIR / f"{source.stem}_{THUMB_SIZE}.png"


def build_thumbs(root: Path, slot: str | None = None) -> int:
    """生成（或重建）缩略图，返回处理张数。"""
    count = 0
    for slot_id, assets in scan(root).items():
        if slot and slot_id.value != slot:
            continue
        for asset in assets:
            target = thumb_path(asset.path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(asset.path) as image:
                image.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS).save(
                    target, optimize=True
                )
            count += 1
    return count


def stale_thumbs(root: Path, slot: str | None = None) -> list[Path]:
    """返回缺失或比源文件旧的缩略图。"""
    stale: list[Path] = []
    for slot_id, assets in scan(root).items():
        if slot and slot_id.value != slot:
            continue
        for asset in assets:
            target = thumb_path(asset.path)
            if not target.exists():
                stale.append(target)
                continue
            if target.stat().st_mtime < asset.path.stat().st_mtime:
                stale.append(target)
    return stale
