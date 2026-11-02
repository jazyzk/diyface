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
from diyface.models import SLOTS, SlotId
from tests.helpers import write_png

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def assets_root(workdir: Path) -> Path:
    write_png(workdir / "02_bangs" / "bangs_straight_01.png")
    write_png(workdir / "02_bangs" / "bangs_wavy_01.png")
    write_png(workdir / "06_eyes" / "eyes_round_01.png")
    return workdir


def test_scan_collects_assets_grouped_by_slot(assets_root: Path) -> None:
    catalog = scan(assets_root)

    assert set(catalog) == {SlotId.BANGS, SlotId.EYES}
    assert [asset.id for asset in catalog[SlotId.BANGS]] == [
        "bangs_straight_01",
        "bangs_wavy_01",
    ]
    assert all(asset.path.is_file() for assets in catalog.values() for asset in assets)


def test_scan_sorts_assets_by_name(assets_root: Path) -> None:
    write_png(assets_root / "02_bangs" / "bangs_curly_01.png")
    ids = [asset.id for asset in scan(assets_root)[SlotId.BANGS]]
    assert ids == sorted(ids)


def test_scan_skips_underscore_files(assets_root: Path) -> None:
    write_png(assets_root / "02_bangs" / "_guide.png")
    ids = [asset.id for asset in scan(assets_root)[SlotId.BANGS]]
    assert "_guide" not in ids
    assert len(ids) == 2


def test_scan_ignores_missing_folders(workdir: Path) -> None:
    assert scan(workdir) == {}


def test_scan_slot_returns_empty_for_unknown_folder(workdir: Path) -> None:
    bangs = next(slot for slot in SLOTS if slot.id is SlotId.BANGS)
    assert scan_slot(workdir, bangs) == []


def test_scan_rejects_wrong_size(workdir: Path) -> None:
    write_png(workdir / "02_bangs" / "bangs_straight_01.png", size=(512, 512))

    with pytest.raises(ValueError, match="尺寸"):
        scan(workdir)


def test_scan_rejects_wrong_mode(workdir: Path) -> None:
    write_png(workdir / "02_bangs" / "bangs_straight_01.png", mode="RGB")

    with pytest.raises(ValueError, match="RGBA"):
        scan(workdir)


def test_scan_rejects_illegal_filename(workdir: Path) -> None:
    write_png(workdir / "02_bangs" / "Bangs Straight.png")

    with pytest.raises(ValueError, match="文件名"):
        scan(workdir)


def test_index_builds_two_level_lookup(assets_root: Path) -> None:
    table = index(scan(assets_root))

    assert set(table[SlotId.BANGS]) == {"bangs_straight_01", "bangs_wavy_01"}
    assert table[SlotId.BANGS]["bangs_straight_01"].slot is SlotId.BANGS


def test_manifest_contains_only_slots_with_assets(assets_root: Path) -> None:
    data = manifest(scan(assets_root))

    ids = [slot["id"] for slot in data["slots"]]
    assert data["schema"] == 1
    assert ids == ["bangs", "eyes"], "应只输出有素材的槽位，且按 z 序"
    assert "skin" not in ids


def test_manifest_carries_metadata_and_relative_paths(assets_root: Path) -> None:
    bangs = manifest(scan(assets_root))["slots"][0]

    assert bangs["z"] == 30
    assert bangs["label"] == {"zh": "发型", "en": "Bangs"}
    assert bangs["tintable"] is True
    assert bangs["default_color"] == "#3B2B23"
    assert bangs["assets"][0] == {
        "id": "bangs_straight_01",
        "file": "02_bangs/bangs_straight_01.png",
    }


def test_real_assets_directory_is_scannable() -> None:
    """仓库里现有的素材必须能直接被扫出来（当前是 3 张占位图）。"""
    catalog = scan(ROOT / "assets")

    assert set(catalog) == {SlotId.SKIN, SlotId.BANGS, SlotId.EYES}
    assert sum(len(assets) for assets in catalog.values()) == 3
