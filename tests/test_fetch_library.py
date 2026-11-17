"""素材库抓取脚本的测试（不联网，只测解析与上色）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_library import recolour, variants  # noqa: E402

FAKE = """
export const hair = {
    variant01: (components, colors) => `<path d="M0 0h10v10H0z" fill="${escape.xml(`${colors.hair}`)}"/>`,
    variant02: (components, colors) => `<path d="M0 0h20v20H0z" fill="#000"/><path d="M5 5h5v5H5z" fill="#fff"/>`,
};
"""


def test_variants_parses_named_and_numbered(workdir: Path) -> None:
    path = workdir / "hair.js"
    path.write_text(FAKE, encoding="utf-8")

    table = variants(path)

    assert set(table) == {"variant01", "variant02"}
    assert len(table["variant01"]) == 1
    assert len(table["variant02"]) == 2


def test_recolour_keeps_black_and_white() -> None:
    paths = [("M0 0h1v1H0z", "#000"), ("M0 0h1v1H0z", "#fff"), ("M0 0h1v1H0z", "${colors.hair}")]

    result = recolour(paths, "#2B1B12")

    assert result[0][1] == "#000", "黑线保持不变"
    assert result[1][1] == "#fff", "高光保持白色"
    assert result[2][1] == "#2B1B12", "主色替换成目标色"


def test_recolour_can_drop_black_keeping() -> None:
    paths = [("M0 0h1v1H0z", "#000")]

    result = recolour(paths, "#C0504D", keep_black=False)

    assert result[0][1] == "#C0504D"
