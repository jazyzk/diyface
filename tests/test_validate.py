"""素材校验规则的测试。

每条规则一个用例：尺寸、模式、透明区、体积、命名、tint 蒙版配对。
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest
from PIL import Image

from diyface.validate import (
    MAX_BYTES,
    is_tint_mask,
    tint_mask_path,
    validate_asset,
    validate_mask,
)
from tests.helpers import write_png


def make_asset(workdir: Path, name: str = "bangs_straight_01", **kwargs) -> Path:
    """造一张合规的素材图（1024 见方、有透明区）。"""
    options = {"bbox": (400, 200, 624, 400)}
    options.update(kwargs)
    return write_png(workdir / "02_bangs" / f"{name}.png", **options)


def add_mask(source: Path) -> Path:
    mask = tint_mask_path(source)
    Image.new("RGBA", (1024, 1024), (255, 255, 255, 255)).save(mask)
    return mask


def test_valid_asset_with_mask_has_no_problem(workdir: Path) -> None:
    asset = make_asset(workdir)
    add_mask(asset)

    assert validate_asset(asset) == []


def test_missing_tint_mask_is_reported(workdir: Path) -> None:
    asset = make_asset(workdir)

    problems = validate_asset(asset)

    assert any("蒙版" in problem for problem in problems)


def test_untintable_asset_does_not_need_mask(workdir: Path) -> None:
    asset = make_asset(workdir, name="eyes_round_01")

    assert validate_asset(asset, tintable=False) == []


def test_wrong_size_is_reported(workdir: Path) -> None:
    asset = make_asset(workdir, size=(512, 512), bbox=(10, 10, 20, 20))

    problems = validate_asset(asset, tintable=False)

    assert any("尺寸" in problem for problem in problems)


def test_wrong_mode_is_reported(workdir: Path) -> None:
    asset = make_asset(workdir, mode="RGB", bbox=None)

    problems = validate_asset(asset, tintable=False)

    assert any("RGBA" in problem for problem in problems)


def test_fully_opaque_asset_is_reported(workdir: Path) -> None:
    asset = make_asset(workdir, bbox=None)

    problems = validate_asset(asset, tintable=False)

    assert any("透明" in problem for problem in problems)


def test_fully_transparent_asset_is_reported(workdir: Path) -> None:
    asset = make_asset(workdir, bbox=(0, 0, 1, 1), color=(0, 0, 0, 0))

    problems = validate_asset(asset, tintable=False)

    assert any("不透明" in problem for problem in problems)


def test_illegal_filename_is_reported(workdir: Path) -> None:
    asset = make_asset(workdir, name="Bangs Straight")

    problems = validate_asset(asset, tintable=False)

    assert any("文件名" in problem for problem in problems)


def test_oversized_file_is_reported(workdir: Path) -> None:
    noise = Image.effect_noise((1024, 1024), 120).convert("RGBA")
    asset = workdir / "02_bangs" / "bangs_noise_01.png"
    asset.parent.mkdir(parents=True, exist_ok=True)
    noise.save(asset)
    assert asset.stat().st_size > MAX_BYTES, "测试素材本身要够大，否则用例没意义"

    problems = validate_asset(asset, tintable=False)

    assert any("体积" in problem for problem in problems)


def test_tint_mask_is_not_treated_as_asset(workdir: Path) -> None:
    asset = make_asset(workdir)
    mask = add_mask(asset)

    assert is_tint_mask(mask) is True
    assert any("蒙版文件" in problem for problem in validate_asset(mask))


def test_validate_mask_reports_missing(workdir: Path) -> None:
    asset = make_asset(workdir)

    assert any("缺少蒙版" in problem for problem in validate_mask(asset))


def test_validate_mask_checks_size(workdir: Path) -> None:
    asset = make_asset(workdir)
    mask = tint_mask_path(asset)
    Image.new("RGBA", (512, 512), (255, 255, 255, 255)).save(mask)

    assert any("尺寸" in problem for problem in validate_mask(asset))


@pytest.mark.parametrize("name", ["a.png", "bangs_straight_01.png"])
def test_tint_mask_naming(name: str) -> None:
    source = Path("assets/02_bangs") / name

    assert tint_mask_path(source).name == f"{source.stem}_tint.png"
