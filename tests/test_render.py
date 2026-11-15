"""渲染管线的测试。

用临时目录里现场生成的图，验证四件事：空槽位透明、图层顺序、着色生效、
尺寸与错误处理。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from diyface.catalog import index, scan
from diyface.models import AvatarRecipe, SlotId
from diyface.render import CANVAS, compose, render
from tests.helpers import write_png

ROOT = Path(__file__).resolve().parents[1]


def build_catalog(workdir: Path) -> dict:
    """造四张带明确色块的素材：脸、前发、帽子、眼镜。"""
    write_png(
        workdir / "01_skin" / "skin_base.png",
        bbox=(300, 220, 724, 780),
        color=(255, 255, 255, 255),
    )
    write_png(
        workdir / "04_hair" / "hair_straight_01.png",
        bbox=(300, 150, 724, 400),
        color=(255, 255, 255, 255),
    )
    write_png(
        workdir / "09_hat" / "hat_beret_01.png",
        bbox=(350, 100, 674, 300),
        color=(255, 255, 255, 255),
    )
    write_png(
        workdir / "08_glasses" / "glasses_round_01.png",
        bbox=(380, 440, 644, 500),
        color=(43, 43, 43, 255),
    )
    return index(scan(workdir))


def recipe_with(**slots: str | None) -> AvatarRecipe:
    """构造只填了部分槽位的配方。"""
    return AvatarRecipe(slots={SlotId(key): value for key, value in slots.items()})


def test_empty_recipe_is_fully_transparent() -> None:
    recipe = AvatarRecipe(slots={slot: None for slot in SlotId})

    image = compose(recipe, {})

    assert image.size == (CANVAS, CANVAS)
    assert image.getchannel("A").getextrema() == (0, 0)


def test_none_slot_is_not_drawn(workdir: Path) -> None:
    catalog = build_catalog(workdir)

    image = compose(recipe_with(skin="skin_base"), catalog)

    assert image.getpixel((512, 500))[3] == 255, "脸型区域应当被画出"
    assert image.getpixel((512, 120))[3] == 0, "没有帽子时顶部应保持透明"


def test_later_layer_covers_earlier_one(workdir: Path) -> None:
    catalog = build_catalog(workdir)
    recipe = recipe_with(hair="hair_straight_01", hat="hat_beret_01")
    recipe.colors = {SlotId.HAIR: "#FF0000", SlotId.HAT: "#0000FF"}

    image = compose(recipe, catalog)

    # 重叠区 (512, 250)：帽子在前发之上，应当是蓝色
    assert image.getpixel((512, 250))[:3] == (0, 0, 255)
    # 只有前发没有帽子的区域 (400, 380)：应当是红色
    assert image.getpixel((400, 380))[:3] == (255, 0, 0)


def test_tintable_slot_uses_recipe_color(workdir: Path) -> None:
    catalog = build_catalog(workdir)
    recipe = recipe_with(skin="skin_base")
    recipe.colors = {SlotId.SKIN: "#E8B98A"}

    image = compose(recipe, catalog)

    assert image.getpixel((512, 500))[:3] == (232, 185, 138)


def test_untintable_slot_keeps_original_pixels(workdir: Path) -> None:
    catalog = build_catalog(workdir)
    recipe = recipe_with(glasses="glasses_round_01")
    recipe.colors = {SlotId.GLASSES: "#FF0000"}

    image = compose(recipe, catalog)

    assert image.getpixel((512, 470))[:3] == (43, 43, 43), "眼镜不可着色，应保持原色"


def test_unknown_asset_raises(workdir: Path) -> None:
    catalog = build_catalog(workdir)

    with pytest.raises(KeyError, match="没有素材"):
        compose(recipe_with(hair="hair_not_exist"), catalog)


def test_render_returns_png_bytes(workdir: Path) -> None:
    import io

    catalog = build_catalog(workdir)
    data = render(recipe_with(skin="skin_base"), catalog, size=256)

    assert data.startswith(b"\x89PNG")
    image = Image.open(io.BytesIO(data))
    assert image.size == (256, 256)


def test_render_supports_1024(workdir: Path) -> None:
    import io

    catalog = build_catalog(workdir)
    data = render(recipe_with(skin="skin_base"), catalog, size=1024)

    image = Image.open(io.BytesIO(data))
    assert image.size == (1024, 1024)


@pytest.mark.parametrize("bad_size", [0, 512, 2048])
def test_render_rejects_unsupported_size(workdir: Path, bad_size: int) -> None:
    catalog = build_catalog(workdir)

    with pytest.raises(ValueError, match="size"):
        render(recipe_with(skin="skin_base"), catalog, size=bad_size)


def test_real_assets_pipeline_runs() -> None:
    """仓库里的占位素材必须能走完整条渲染链路。"""
    catalog = index(scan(ROOT / "assets"))
    recipe = AvatarRecipe(
        slots={
            SlotId.SKIN: "skin_base",
            SlotId.HAIR: "hair_straight_01",
            SlotId.EYES: "eyes_round_01",
        },
        colors={SlotId.SKIN: "#E8B98A", SlotId.HAIR: "#2B1B12"},
    )

    data = render(recipe, catalog, size=256)

    assert data.startswith(b"\x89PNG")
    assert len(data) > 1000
