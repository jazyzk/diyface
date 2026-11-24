"""背景预设的测试：渲染尺寸、未知名字、清单。"""

from __future__ import annotations

from diyface.backdrop import PRESETS, manifest, render
from diyface.models import AvatarRecipe


def test_presets_have_labels() -> None:
    items = manifest()

    assert len(items) == len(PRESETS)
    for item in items:
        assert item["label"]["zh"]
        assert item["label"]["en"]


def test_render_returns_full_canvas() -> None:
    image = render("grass")

    assert image is not None
    assert image.size == (1024, 1024)
    assert image.getpixel((10, 10))[3] == 255, "背景必须不透明"


def test_unknown_background_returns_none() -> None:
    assert render("rainbow-road") is None


def test_recipe_rejects_unknown_background() -> None:
    import pytest

    with pytest.raises(ValueError):
        AvatarRecipe.model_validate({"slots": {}, "background": "unknown"})


def test_recipe_accepts_preset() -> None:
    recipe = AvatarRecipe.model_validate({"slots": {}, "background": "night"})

    assert recipe.background == "night"
