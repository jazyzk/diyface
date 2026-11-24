"""素材编目的测试。

覆盖四类行为：正常收录、跳过不该收的、遇到坏素材报错、清单结构与顺序。

关于目录：这里用仓库内的 ``tests/reports/tmp`` 而不是 pytest 的 ``tmp_path``。
某些 Windows 环境下系统临时目录的权限被策略收紧，``tmp_path`` 会直接报
``PermissionError``；把测试产物留在仓库里（已被 .gitignore 忽略）更稳。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from diyface.catalog import index, manifest, scan, scan_slot

ASSETS = Path(__file__).resolve().parents[1] / "assets"
from diyface.models import SLOTS, SlotId
from tests.helpers import write_png

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def assets_root(workdir: Path) -> Path:
    write_png(workdir / "04_hair" / "hair_straight_01.png")
    write_png(workdir / "04_hair" / "hair_wavy_01.png")
    write_png(workdir / "05_eyes" / "eyes_round_01.png")
    return workdir


def test_scan_collects_assets_grouped_by_slot(assets_root: Path) -> None:
    catalog = scan(assets_root)

    assert set(catalog) == {SlotId.HAIR, SlotId.EYES}
    assert [asset.id for asset in catalog[SlotId.HAIR]] == [
        "hair_straight_01",
        "hair_wavy_01",
    ]
    assert all(asset.path.is_file() for assets in catalog.values() for asset in assets)


def test_scan_sorts_assets_by_name(assets_root: Path) -> None:
    write_png(assets_root / "04_hair" / "hair_curly_01.png")
    ids = [asset.id for asset in scan(assets_root)[SlotId.HAIR]]
    assert ids == sorted(ids)


def test_scan_skips_underscore_files(assets_root: Path) -> None:
    write_png(assets_root / "04_hair" / "_guide.png")
    ids = [asset.id for asset in scan(assets_root)[SlotId.HAIR]]
    assert "_guide" not in ids
    assert len(ids) == 2


def test_scan_ignores_missing_folders(workdir: Path) -> None:
    assert scan(workdir) == {}


def test_scan_slot_returns_empty_for_unknown_folder(workdir: Path) -> None:
    bangs = next(slot for slot in SLOTS if slot.id is SlotId.HAIR)
    assert scan_slot(workdir, bangs) == []


def test_scan_rejects_wrong_size(workdir: Path) -> None:
    write_png(workdir / "04_hair" / "hair_straight_01.png", size=(512, 512))

    with pytest.raises(ValueError, match="尺寸"):
        scan(workdir)


def test_scan_rejects_wrong_mode(workdir: Path) -> None:
    write_png(workdir / "04_hair" / "hair_straight_01.png", mode="RGB")

    with pytest.raises(ValueError, match="RGBA"):
        scan(workdir)


def test_scan_rejects_illegal_filename(workdir: Path) -> None:
    write_png(workdir / "04_hair" / "Bangs Straight.png")

    with pytest.raises(ValueError, match="文件名"):
        scan(workdir)


def test_index_builds_two_level_lookup(assets_root: Path) -> None:
    table = index(scan(assets_root))

    assert set(table[SlotId.HAIR]) == {"hair_straight_01", "hair_wavy_01"}
    assert table[SlotId.HAIR]["hair_straight_01"].slot is SlotId.HAIR


def test_manifest_contains_only_slots_with_assets(assets_root: Path) -> None:
    data = manifest(scan(assets_root))

    ids = [slot["id"] for slot in data["slots"]]
    assert data["schema"] == 1
    assert ids == ["hair", "eyes"], "应只输出有素材的槽位，且按 z 序"
    assert "skin" not in ids


def test_manifest_carries_metadata_and_relative_paths(assets_root: Path) -> None:
    bangs = manifest(scan(assets_root))["slots"][0]

    assert bangs["z"] == 30
    assert bangs["label"] == {"zh": "前发", "en": "Hair"}
    assert bangs["tintable"] is True
    assert bangs["default_color"] == "#2B1B12"
    assert bangs["assets"][0] == {
        "id": "hair_straight_01",
        "file": "04_hair/hair_straight_01.png",
        "thumb": "04_hair/_thumb/hair_straight_01_256.png",
        "style": "adventurer",
    }


def test_scan_skips_tint_masks(assets_root: Path) -> None:
    """`*_tint.png` 是蒙版，不是可以叠的素材。"""
    write_png(assets_root / "04_hair" / "hair_straight_01_tint.png")

    ids = [asset.id for asset in scan(assets_root)[SlotId.HAIR]]

    assert "hair_straight_01_tint" not in ids
    assert len(ids) == 2


def test_real_assets_directory_is_scannable() -> None:
    """仓库里现有的素材必须能直接被扫出来。"""
    catalog = scan(ROOT / "assets")

    assert {SlotId.SKIN, SlotId.HAIR, SlotId.EYES} <= set(catalog)
    assert sum(len(assets) for assets in catalog.values()) >= 3


def test_manifest_lists_two_styles() -> None:
    """清单要带上风格列表，且默认风格排在第一位。"""
    data = manifest(scan(ASSETS))

    styles = data["styles"]
    assert [style["id"] for style in styles][0] == "pixel"
    assert {style["id"] for style in styles} == {"adventurer", "lorelei", "pixel"}
    for style in styles:
        assert style["label"]["zh"]
        assert style["defaults"], "每种风格至少要有默认素材"
        assert "glasses" not in style["defaults"], "默认不戴眼镜"


def test_style_of_uses_prefix() -> None:
    from diyface.catalog import style_of

    assert style_of("lorelei_hair_01") == "lorelei"
    assert style_of("hair_straight_01") == "adventurer"
