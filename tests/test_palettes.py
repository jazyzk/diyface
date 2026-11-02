"""颜色解析与着色的测试。"""

from __future__ import annotations

import pytest
from PIL import Image

from diyface.palettes import hex_to_rgb, tint


def test_hex_to_rgb_parses_six_digits() -> None:
    assert hex_to_rgb("#3B2B23") == (59, 43, 35)
    assert hex_to_rgb("#FFFFFF") == (255, 255, 255)


def test_hex_to_rgb_expands_three_digits() -> None:
    assert hex_to_rgb("#fff") == (255, 255, 255)
    assert hex_to_rgb("#0f0") == (0, 255, 0)


@pytest.mark.parametrize("bad", ["red", "#12", "#12345", "3B2B23", "#GGGGGG"])
def test_hex_to_rgb_rejects_invalid(bad: str) -> None:
    with pytest.raises(ValueError, match="颜色必须是"):
        hex_to_rgb(bad)


def test_white_layer_takes_target_color() -> None:
    layer = Image.new("RGBA", (8, 8), (255, 255, 255, 255))

    result = tint(layer, "#C0392B")

    assert result.getpixel((0, 0)) == (192, 57, 43, 255)


def test_black_outline_stays_black() -> None:
    layer = Image.new("RGBA", (8, 8), (0, 0, 0, 255))

    result = tint(layer, "#C0392B")

    assert result.getpixel((0, 0))[:3] == (0, 0, 0)


def test_mid_gray_keeps_shading() -> None:
    layer = Image.new("RGBA", (4, 4), (128, 128, 128, 255))

    result = tint(layer, "#FFFFFF")

    assert result.getpixel((0, 0))[:3] == (128, 128, 128)


def test_alpha_is_preserved() -> None:
    layer = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    layer.putpixel((1, 1), (255, 255, 255, 255))

    result = tint(layer, "#3B2B23")

    assert result.getpixel((0, 0))[3] == 0
    assert result.getpixel((1, 1))[3] == 255


def test_mask_keeps_original_color_where_black() -> None:
    layer = Image.new("RGBA", (4, 4), (255, 255, 255, 255))
    mask = Image.new("RGBA", (4, 4), (0, 0, 0, 255))
    mask.paste((255, 255, 255, 255), (2, 0, 4, 4))

    result = tint(layer, "#0000FF", mask)

    assert result.getpixel((0, 0))[:3] == (255, 255, 255), "掩码为黑的一侧保持原色"
    assert result.getpixel((3, 3))[:3] == (0, 0, 255), "掩码为白的一侧被着色"
