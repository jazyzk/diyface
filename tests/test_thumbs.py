"""缩略图生成的测试。"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PIL import Image

from diyface.__main__ import main
from diyface.catalog import scan
from diyface.models import SlotId
from diyface.thumbs import THUMB_DIR, THUMB_SIZE, build_thumbs, stale_thumbs, thumb_path
from tests.helpers import write_png


@pytest.fixture
def assets_root(workdir: Path) -> Path:
    write_png(workdir / "01_skin" / "skin_base.png", bbox=(300, 200, 724, 700))
    write_png(workdir / "04_hair" / "hair_straight_01.png", bbox=(300, 150, 724, 400))
    write_png(workdir / "05_eyes" / "eyes_round_01.png", bbox=(440, 470, 590, 540))
    return workdir


def test_build_creates_thumbnail_for_each_asset(assets_root: Path) -> None:
    count = build_thumbs(assets_root)

    assert count == 3
    thumbs = sorted(assets_root.rglob(f"*_{THUMB_SIZE}.png"))
    assert len(thumbs) == 3
    for thumb in thumbs:
        with Image.open(thumb) as image:
            assert image.size == (THUMB_SIZE, THUMB_SIZE)
            assert image.mode == "RGBA"


def test_thumbnail_lives_in_thumb_dir(assets_root: Path) -> None:
    source = assets_root / "04_hair" / "hair_straight_01.png"

    assert thumb_path(source) == source.parent / THUMB_DIR / "hair_straight_01_256.png"


def test_thumbnails_are_not_scanned_as_assets(assets_root: Path) -> None:
    build_thumbs(assets_root)

    catalog = scan(assets_root)

    assert [asset.id for asset in catalog[SlotId.HAIR]] == ["hair_straight_01"]


def test_slot_filter_only_builds_that_slot(assets_root: Path) -> None:
    count = build_thumbs(assets_root, slot="hair")

    assert count == 1
    assert thumb_path(assets_root / "04_hair" / "hair_straight_01.png").exists()
    assert not thumb_path(assets_root / "05_eyes" / "eyes_round_01.png").exists()


def test_stale_reports_missing_before_build(assets_root: Path) -> None:
    assert len(stale_thumbs(assets_root)) == 3


def test_stale_is_empty_after_build(assets_root: Path) -> None:
    build_thumbs(assets_root)

    assert stale_thumbs(assets_root) == []


def test_stale_detects_newer_source(assets_root: Path) -> None:
    build_thumbs(assets_root)
    source = assets_root / "04_hair" / "hair_straight_01.png"
    future = source.stat().st_mtime + 60
    os.utime(source, (future, future))

    assert [path.name for path in stale_thumbs(assets_root)] == ["hair_straight_01_256.png"]


def test_cli_builds_and_checks(assets_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["build-thumbs", "--root", str(assets_root)]) == 0
    assert "已生成 3 张缩略图" in capsys.readouterr().out

    assert main(["build-thumbs", "--root", str(assets_root), "--check"]) == 0
    assert "过期 0 张" in capsys.readouterr().out


def test_cli_check_fails_when_stale(assets_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build_thumbs(assets_root)
    thumb_path(assets_root / "01_skin" / "skin_base.png").unlink()

    code = main(["build-thumbs", "--root", str(assets_root), "--check"])

    assert code == 1
    output = capsys.readouterr().out
    assert "过期 1 张" in output
    assert "skin_base_256.png" in output
