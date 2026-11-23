"""拼豆贴纸的测试：裁切、等比缩放、右下角定位。"""

from __future__ import annotations

from PIL import Image

from diyface.pixel import CANVAS, CELL, GRID, PixelArt
from diyface.sticker import DEFAULT_SCALE, attach, build, place


def blank() -> PixelArt:
    return PixelArt(palette=["#FF0000"], cells=[-1] * (GRID * GRID))


def one_cell(col: int = 0, row: int = 0) -> PixelArt:
    cells = [-1] * (GRID * GRID)
    cells[row * GRID + col] = 0
    return PixelArt(palette=["#FF0000"], cells=cells)


def test_empty_art_has_no_sticker() -> None:
    assert build(blank()) is None


def test_sticker_is_trimmed_to_content() -> None:
    sticker = build(one_cell(5, 5))

    assert sticker is not None
    assert sticker.width < CANVAS, "应当裁掉四周透明区域"
    assert sticker.width >= CELL // 2


def test_sticker_keeps_colour() -> None:
    sticker = build(one_cell(0, 0), style="flat")

    assert sticker is not None
    assert sticker.getpixel((sticker.width // 2, sticker.height // 2))[:3] == (255, 0, 0)


def test_attach_puts_sticker_bottom_right() -> None:
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255))
    sticker = Image.new("RGBA", (100, 100), (255, 0, 0, 255))

    result = attach(canvas, sticker)

    assert result.getpixel((CANVAS - 60, CANVAS - 60))[:3] == (255, 0, 0)
    assert result.getpixel((10, 10))[:3] == (255, 255, 255), "左上角不应被影响"


def test_attach_scales_to_ratio() -> None:
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    sticker = Image.new("RGBA", (200, 100), (255, 0, 0, 255))

    result = attach(canvas, sticker)

    bbox = result.getchannel("A").getbbox()
    assert bbox is not None
    width = bbox[2] - bbox[0]
    assert abs(width - int(CANVAS * DEFAULT_SCALE)) <= 2, "宽度应缩放到默认比例"


def test_place_uses_normalised_coordinates() -> None:
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    sticker = Image.new("RGBA", (100, 100), (255, 0, 0, 255))

    result = place(canvas, sticker, x=0.25, y=0.25, scale=0.2)

    assert result.getpixel((int(CANVAS * 0.25), int(CANVAS * 0.25)))[:3] == (255, 0, 0)
    assert result.getpixel((int(CANVAS * 0.75), int(CANVAS * 0.75)))[3] == 0


def test_place_clamps_sticker_inside_canvas() -> None:
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    sticker = Image.new("RGBA", (100, 100), (255, 0, 0, 255))

    result = place(canvas, sticker, x=0.99, y=0.01, scale=0.3)

    bbox = result.getchannel("A").getbbox()
    assert bbox is not None
    assert 0 <= bbox[0] and bbox[2] <= CANVAS
    assert 0 <= bbox[1] and bbox[3] <= CANVAS
