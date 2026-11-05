"""外部素材导入的测试：推断槽位、命名、缩放、落盘。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from diyface.importer import Entry, fit_canvas, infer_slot, install, plan, slugify, verify_tree
from diyface.models import SLOT_BY_ID, SlotId
from tests.helpers import write_png


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Hair 3.png", SlotId.BANGS),
        ("lorelei-bangs-2.png", SlotId.BANGS),
        ("Eyes_5.png", SlotId.EYES),
        ("mouth smile.png", SlotId.MOUTH),
        ("glasses-round.png", SlotId.GLASSES),
        ("eyebrow 2.png", SlotId.BROWS),
        ("hat-beret.png", SlotId.HAT),
        ("shirt blue.png", SlotId.CLOTHES),
        ("head 1.png", SlotId.SKIN),
        ("random-thing.png", None),
    ],
)
def test_infer_slot(name: str, expected: SlotId | None) -> None:
    assert infer_slot(name) == expected


def test_eyebrow_wins_over_eye() -> None:
    """eyebrow 里也含 eye，必须优先匹配眉。"""
    assert infer_slot("eyebrow 4.png") is SlotId.BROWS


@pytest.mark.parametrize(
    ("name", "expected"),
    [("Hair 3.png", "hair_3"), ("a-b c.png", "a_b_c"), ("!!!.png", "asset")],
)
def test_slugify(name: str, expected: str) -> None:
    assert slugify(name) == expected


def test_fit_canvas_centers_non_square_image() -> None:
    source = Image.new("RGBA", (512, 256), (255, 0, 0, 255))

    canvas = fit_canvas(source)

    assert canvas.size == (1024, 1024)
    assert canvas.getpixel((512, 30))[3] == 0, "上下必须留透明边"
    assert canvas.getpixel((512, 512))[3] == 255, "内容必须居中"


def test_fit_canvas_anchors_hair_to_top() -> None:
    source = Image.new("RGBA", (400, 200), (255, 0, 0, 255))

    canvas = fit_canvas(source, slot=SlotId.BANGS)

    assert canvas.getpixel((512, 5))[3] == 255, "发型应贴顶"
    assert canvas.getpixel((512, 900))[3] == 0


def test_fit_canvas_keeps_aspect_ratio() -> None:
    source = Image.new("RGBA", (200, 100), (0, 255, 0, 255))

    canvas = fit_canvas(source)

    assert canvas.size == (1024, 1024)
    assert canvas.getpixel((512, 512))[3] == 255
    assert canvas.getpixel((512, 200))[3] == 0, "上下应留透明边"


def test_plan_maps_files_and_skips_unknown(workdir: Path) -> None:
    hair = write_png(workdir / "Hair 1.png", bbox=(300, 200, 724, 500))
    mouth = write_png(workdir / "mouth smile.png", bbox=(460, 560, 560, 640))
    unknown = write_png(workdir / "whatever.png")
    mask = write_png(workdir / "hair_tint.png")

    entries, skipped = plan([hair, mouth, unknown, mask])

    assert [entry.slot.id for entry in entries] == [SlotId.BANGS, SlotId.MOUTH]
    assert [entry.target for entry in entries] == ["bangs_hair_1.png", "mouth_smile.png"]
    assert {item.source.name for item in skipped} == {"whatever.png", "hair_tint.png"}


def test_plan_numbers_duplicates(workdir: Path) -> None:
    first = write_png(workdir / "a" / "hair.png")
    second = write_png(workdir / "b" / "hair.png")

    entries, _ = plan([first, second])

    assert len({entry.target for entry in entries}) == 2


def test_install_writes_files_and_masks(workdir: Path) -> None:
    source = write_png(workdir / "export" / "Hair 1.png", bbox=(300, 200, 724, 500))
    skin = write_png(workdir / "export" / "head 1.png", bbox=(250, 170, 774, 730))
    eye = write_png(workdir / "export" / "eyes 1.png", bbox=(440, 470, 590, 540))
    entries, _ = plan([source, skin, eye])

    root = workdir / "assets"
    stats = install(entries, root)

    assert stats["written"] == 3
    assert stats["masks"] == 2, "只有可着色槽位（发型、脸型）需要蒙版"
    assert (root / "02_bangs" / "bangs_hair_1.png").is_file()
    assert (root / "02_bangs" / "bangs_hair_1_tint.png").is_file()
    assert (root / "06_eyes" / "eyes_1_tint.png").exists() is False

    with Image.open(root / "01_skin" / "skin_head_1.png") as image:
        assert image.size == (1024, 1024)
        assert image.mode == "RGBA"


def test_install_skips_masks_for_untintable_slot(workdir: Path) -> None:
    eye = write_png(workdir / "export" / "eyes 1.png", bbox=(440, 470, 590, 540))
    entries, _ = plan([eye])

    root = workdir / "assets"
    stats = install(entries, root)

    assert stats["masks"] == 0
    assert (root / "06_eyes" / "eyes_1.png").is_file()


def test_entry_target_uses_slot_prefix() -> None:
    entry = Entry(slot=SLOT_BY_ID[SlotId.BANGS], source=Path("x/Hair 1.png"), name="bangs_hair_1")

    assert entry.target == "bangs_hair_1.png"


def test_verify_tree_respects_slot_tintable(workdir: Path) -> None:
    """眼镜、眼睛不可着色，不该因为缺蒙版被误报。"""
    root = workdir / "assets"
    skin = write_png(workdir / "export" / "head 1.png", bbox=(250, 170, 774, 730))
    eye = write_png(workdir / "export" / "eyes 1.png", bbox=(440, 470, 590, 540))
    entries, _ = plan([skin, eye])

    install(entries, root)
    problems = verify_tree(root)

    assert all("蒙版" not in " ".join(found) for _, found in problems), problems
