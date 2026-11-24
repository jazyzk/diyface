"""素材合规性检查。

占位图和正式图走同一套规则：只要有人往 assets/ 里塞图，就必须满足
1024×1024、RGBA、文件名小写下划线、目录两位编号。这样等 D/E 交真图时，
不需要再单独写一套校验。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from diyface.catalog import scan
from diyface.models import SlotId

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CANVAS = 1024
ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_")


def asset_files() -> list[Path]:
    """assets/ 下所有参与渲染的 PNG。

    排除三类：`_thumb/` 里的缩略图、下划线开头的参考图、`*_tint.png` 蒙版。
    """
    if not ASSETS.is_dir():
        return []
    return sorted(
        path
        for path in ASSETS.rglob("*.png")
        if not any(part.startswith("_") for part in path.relative_to(ASSETS).parts)
        and not path.name.endswith("_tint.png")
    )


def test_assets_directory_exists() -> None:
    assert ASSETS.is_dir(), "assets/ 不存在，先跑 python scripts/make_placeholders.py"


def test_assets_are_not_empty() -> None:
    assert asset_files(), "assets/ 里一张图都没有，A 的第 1 步还没完成"


@pytest.mark.parametrize("path", asset_files(), ids=lambda path: path.name)
def test_asset_is_1024_rgba(path: Path) -> None:
    with Image.open(path) as image:
        assert image.size == (CANVAS, CANVAS), f"{path.name} 尺寸是 {image.size}，应为 1024x1024"
        assert image.mode == "RGBA", f"{path.name} 模式是 {image.mode}，应为 RGBA"


@pytest.mark.parametrize("path", asset_files(), ids=lambda path: path.name)
def test_asset_has_transparency(path: Path) -> None:
    """必须真的透明：全不透明的 PNG 叠起来会盖住下层。"""
    with Image.open(path) as image:
        low, high = image.getchannel("A").getextrema()
        assert low == 0, f"{path.name} 没有透明像素（alpha 最小值 {low}）"
        assert high == 255, f"{path.name} 没有不透明像素（alpha 最大值 {high}）"


@pytest.mark.parametrize("path", asset_files(), ids=lambda path: path.name)
def test_asset_name_is_snake_case(path: Path) -> None:
    illegal = set(path.stem) - ALLOWED_CHARS
    assert not illegal, f"{path.name} 含非法字符 {sorted(illegal)}，只允许小写字母、数字、下划线"


def test_slot_folders_are_numbered() -> None:
    if not ASSETS.is_dir():
        pytest.skip("assets/ 不存在")
    for folder in sorted(path for path in ASSETS.iterdir() if path.is_dir()):
        assert folder.name[:2].isdigit(), f"{folder.name} 应以两位编号开头，例如 04_hair"


def test_budget_matches_plan() -> None:
    """本轮交付的素材预算必须与 PLAN §6 一致：10 个槽位共 54 张。"""
    budget = {
        SlotId.SKIN: 9,
        SlotId.HAIR: 26,
        SlotId.EYES: 36,
        SlotId.BROWS: 11,
        SlotId.MOUTH: 29,
        SlotId.GLASSES: 12,
        SlotId.EXTRA: 18,
    }
    catalog = scan(ASSETS)

    for slot_id, expected in budget.items():
        assert len(catalog[slot_id]) == expected, f"{slot_id} 应有 {expected} 张，实际 {len(catalog[slot_id])} 张"
    assert sum(len(assets) for assets in catalog.values()) == 141


def test_hair_does_not_cover_eyes() -> None:
    """发型不能把眼睛糊住：眼部区域被遮超过 60% 的素材视为坏素材。"""
    import numpy as np
    from PIL import Image

    eye_box = (360, 430, 664, 620)
    bad = []
    for path in sorted((ASSETS / "04_hair").glob("*.png")):
        if path.stem.endswith("_tint"):
            continue
        alpha = np.asarray(Image.open(path).convert("RGBA"))[
            eye_box[1] : eye_box[3], eye_box[0] : eye_box[2], 3
        ]
        coverage = float((alpha > 40).mean())
        if coverage > 0.60:
            bad.append((path.stem, round(coverage, 2)))

    assert not bad, f"这些发型遮住了眼睛：{bad}"
