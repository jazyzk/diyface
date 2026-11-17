"""SVG 栅格化脚本的测试。

它只服务素材生产（A 的活），但出错会让整批 PNG 变形，所以关键行为要锁住。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from svg_render import parse_path, paths_from_fragment, render_paths  # noqa: E402


def test_parse_path_handles_line_commands() -> None:
    subpaths = parse_path("M0 0 H10 V10 H0 Z")

    assert len(subpaths) == 1
    assert subpaths[0][0] == (0, 0)
    assert subpaths[0][1] == (10, 0)
    assert subpaths[0][-1] == (0, 0), "Z 应当闭合回起点"


def test_parse_path_handles_relative_cubic() -> None:
    subpaths = parse_path("M0 0 c 10 0 10 10 0 10")

    assert len(subpaths) == 1
    assert len(subpaths[0]) > 4
    assert subpaths[0][-1] == pytest.approx((0, 10))


def test_render_fills_rectangle() -> None:
    image = render_paths([("M100 100 H900 V900 H100 Z", "#ff0000")])

    assert image.size == (1024, 1024)
    assert image.getpixel((512, 512))[:3] == (255, 0, 0)
    assert image.getpixel((50, 50))[3] == 0, "矩形外必须透明"


def test_even_odd_hole_is_transparent() -> None:
    d = "M100 100 H900 V900 H100 Z M400 400 H600 V600 H400 Z"

    image = render_paths([(d, "#00ff00")])

    assert image.getpixel((150, 150))[3] == 255, "外圈应填充"
    assert image.getpixel((500, 500))[3] == 0, "内圈应镂空（偶奇规则）"


def test_arc_becomes_circle() -> None:
    image = render_paths([("M512 212 a 300 300 0 1 1 -1 0 Z", "#0000ff")])

    assert image.getpixel((512, 500))[3] == 255, "圆内应填充"
    assert image.getpixel((512, 100))[3] == 0


def test_paths_from_fragment_extracts_fill() -> None:
    fragment = '<path d="M0 0 H10 V10 Z" fill="#123456"/><path d="M1 1 H2 V2 Z"/>'

    paths = paths_from_fragment(fragment)

    assert len(paths) == 2
    assert paths[0][1] == "#123456"
    assert paths[1][1] == "#000", "缺省 fill 按黑色处理"
