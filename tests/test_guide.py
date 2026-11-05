"""参考图生成的测试。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from diyface.guide import CANVAS, build_guide
from tests.helpers import write_png


def test_guide_is_1024_transparent_canvas(workdir: Path) -> None:
    path = build_guide(workdir / "_guide.png")

    with Image.open(path) as image:
        assert image.size == (CANVAS, CANVAS)
        assert image.mode == "RGBA"
        assert image.getpixel((300, 620))[3] == 0, "空白处必须透明"


def test_guide_draws_all_three_reference_lines(workdir: Path) -> None:
    path = build_guide(workdir / "_guide.png")

    with Image.open(path) as image:
        assert image.getpixel((512, 100))[3] > 0, "缺垂直中线"
        assert image.getpixel((100, 448))[3] > 0, "缺脸中心线"
        assert image.getpixel((100, 256))[3] > 0, "缺头顶基线"


def test_guide_can_ghost_a_reference(workdir: Path) -> None:
    reference = write_png(workdir / "skin.png", bbox=(300, 200, 724, 700))
    plain = build_guide(workdir / "_guide_plain.png")
    ghosted = build_guide(workdir / "_guide_ghost.png", reference=reference)

    with Image.open(plain) as a, Image.open(ghosted) as b:
        assert a.getpixel((400, 300))[3] == 0, "无底稿时该处应透明"
        assert b.getpixel((400, 300))[3] > 0, "叠了底稿后该处应有淡淡的图"
