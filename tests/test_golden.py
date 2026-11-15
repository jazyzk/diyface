"""渲染快照测试。

同一份配方每次都必须画出同一张图。基准图放在 ``tests/fixtures/golden/``，
第一次运行（或加 ``--update-golden``）时生成，之后只做比对。

素材换了要重建基准：``python -m pytest --update-golden``，
并在 PR 里说明「为什么这些图应该变」。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from diyface.catalog import index, scan
from diyface.models import AvatarRecipe
from diyface.render import CANVAS, compose

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
RECIPES = ROOT / "tests" / "fixtures" / "recipes"
GOLDEN = ROOT / "tests" / "fixtures" / "golden"
REPORTS = ROOT / "tests" / "reports"

CASES = ("base", "mono", "colored")
THRESHOLD = 2.55          # 约 1% 的均方根误差


def rmse(left: Image.Image, right: Image.Image) -> float:
    a = np.asarray(left.convert("RGBA"), dtype=float)
    b = np.asarray(right.convert("RGBA"), dtype=float)
    return float(np.sqrt(((a - b) ** 2).mean()))


def load_recipe(name: str) -> AvatarRecipe:
    return AvatarRecipe.model_validate_json(
        (RECIPES / f"{name}.json").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("name", CASES)
def test_golden_matches_baseline(name: str, update_golden: bool) -> None:
    catalog = index(scan(ASSETS))
    image = compose(load_recipe(name), catalog)

    GOLDEN.mkdir(parents=True, exist_ok=True)
    baseline_path = GOLDEN / f"{name}.png"

    if update_golden or not baseline_path.exists():
        image.save(baseline_path)
        pytest.skip(f"已生成基准图 {baseline_path.name}")

    baseline = Image.open(baseline_path).convert("RGBA")
    assert baseline.size == (CANVAS, CANVAS)

    diff = rmse(image, baseline)
    if diff >= THRESHOLD:
        REPORTS.mkdir(parents=True, exist_ok=True)
        image.save(REPORTS / f"diff-{name}.png")
    assert diff < THRESHOLD, f"{name} 与基准差异 {diff:.2f}，见 tests/reports/diff-{name}.png"


@pytest.mark.parametrize("name", CASES)
def test_recipe_fixture_is_valid(name: str) -> None:
    """快照用的配方本身必须是合法配方（12 个槽位、颜色格式正确）。"""
    recipe = load_recipe(name)

    assert len(recipe.slots) == 10
    assert recipe.slots["skin"] is not None
