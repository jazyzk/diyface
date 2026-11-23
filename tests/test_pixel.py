"""拼豆画布的测试：RLE 编解码、校验、渲染位置。"""

from __future__ import annotations

import pytest
from PIL import Image

from diyface.pixel import (
    CANVAS,
    CELL,
    GRID,
    MAX_COLORS,
    PixelArt,
    PixelError,
    decode,
    encode,
    render,
    thumbnail,
)


def filled(index: int = 0) -> list[int]:
    return [index] * (GRID * GRID)


def test_encode_decode_roundtrip() -> None:
    cells = filled(0)
    cells[0] = 1
    cells[1] = 1
    cells[-1] = 2

    restored = decode(encode(cells))

    assert restored == cells


def test_encode_is_compact_for_blank_canvas() -> None:
    assert encode(filled(-1)) == "-1x1024"


def test_decode_rejects_wrong_length() -> None:
    with pytest.raises(PixelError):
        decode("0x10")


def test_decode_rejects_bad_fragment() -> None:
    with pytest.raises(PixelError):
        decode("0x3,,1x5")


def test_palette_must_be_hex() -> None:
    with pytest.raises(PixelError):
        PixelArt(palette=["red"])


def test_palette_has_limit() -> None:
    with pytest.raises(PixelError):
        PixelArt(palette=[f"#0000{i:02X}" for i in range(MAX_COLORS + 1)])


def test_cells_length_is_validated() -> None:
    with pytest.raises(PixelError):
        PixelArt(palette=["#000000"], cells=[0] * 10)


def test_index_out_of_range_is_rejected() -> None:
    cells = filled(0)
    cells[5] = 3
    with pytest.raises(PixelError):
        PixelArt(palette=["#000000"], cells=cells)


def test_render_draws_cell_at_expected_position() -> None:
    cells = filled(-1)
    cells[0] = 0  # 左上角
    art = PixelArt(palette=["#FF0000"], cells=cells)

    image = render(art, style="flat")

    assert image.size == (CANVAS, CANVAS)
    assert image.getpixel((CELL // 2, CELL // 2))[:3] == (255, 0, 0)
    assert image.getpixel((CELL * 5, CELL * 5))[3] == 0, "空格子必须透明"


def test_bead_style_has_hole() -> None:
    cells = filled(-1)
    cells[0] = 0
    art = PixelArt(palette=["#FF0000"], cells=cells)

    image = render(art, style="bead")

    center = image.getpixel((CELL // 2, CELL // 2))
    assert center[:3] != (255, 0, 0), "珠子中心应当是深一档的孔"
    assert center[3] == 255


def test_unknown_style_is_rejected() -> None:
    art = PixelArt(palette=["#000000"], cells=filled(-1))
    with pytest.raises(PixelError):
        render(art, style="oil-painting")


def test_thumbnail_keeps_crisp_edges() -> None:
    art = PixelArt(palette=["#00FF00"], cells=filled(0))

    small = thumbnail(art, size=64)

    assert small.size == (64, 64)
    assert small.getpixel((32, 32))[:3] == (0, 255, 0)


def test_palette_is_rich_enough() -> None:
    """拼豆色板要够丰富，补满上限。"""
    assert MAX_COLORS >= 64


def test_render_accepts_full_palette() -> None:
    palette = [f"#{index:06X}" for index in range(1, 49)]
    art = PixelArt(palette=palette, cells=filled(47))

    image = render(art, style="flat")

    assert image.size == (CANVAS, CANVAS)


def test_frontend_palette_matches_share_palette() -> None:
    """拼豆页与分享编码用的是同一套颜色，顺序也必须一致。"""
    import re
    from pathlib import Path as _Path

    root = _Path(__file__).resolve().parents[1] / "src" / "diyface" / "static"
    pattern = re.compile(r"const (?:PALETTE|STANDARD_PALETTE) = \[(.*?)\];", re.S)

    def colors(name: str) -> list[str]:
        text = (root / name).read_text(encoding="utf-8")
        block = pattern.search(text)
        assert block, f"{name} 里找不到调色板定义"
        return re.findall(r"#[0-9A-Fa-f]{6}", block.group(1))

    canvas = colors("pixel.js")
    shared = colors("app.js")
    assert len(canvas) == MAX_COLORS, "前端色板应当补满后端上限"
    assert canvas == shared, "两处调色板必须完全一致，否则分享链接会串色"
    assert len(canvas) <= MAX_COLORS, "前端色板不能超过后端上限"


def test_mard_white_is_h2() -> None:
    """Mard 色卡里白色就是 H2，和实物一致。"""
    from diyface.mard import MARD_64

    assert MARD_64[0] == ("H2", "#FFFFFF")


def test_mard_palette_is_single_source_of_truth() -> None:
    """前端两份色板必须与 mard.py 完全一致，色号也不能漂移。"""
    import re
    from pathlib import Path as _Path

    from diyface.mard import CODES, HEXES

    root = _Path(__file__).resolve().parents[1] / "src" / "diyface" / "static"
    assert len(HEXES) == MAX_COLORS == 64
    assert len(set(CODES)) == 64, "色号不能重复"

    pixel = (root / "pixel.js").read_text(encoding="utf-8")
    app = (root / "app.js").read_text(encoding="utf-8")

    palette = re.search(r"const PALETTE = \[(.*?)\];", pixel, re.S).group(1)
    codes = re.search(r"const CODES = \[(.*?)\];", pixel, re.S).group(1)
    shared = re.search(r"const STANDARD_PALETTE = \[(.*?)\];", app, re.S).group(1)

    assert re.findall(r"#[0-9A-F]{6}", palette) == HEXES
    assert re.findall(r"#[0-9A-F]{6}", shared) == HEXES
    assert re.findall(r"\"([A-Z]{1,2}[0-9]+)\"", codes) == CODES
