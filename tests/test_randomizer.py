"""随机配方的测试。

三条底线各一组用例：必填不空、可选可空、同 seed 可复现。
"""

from __future__ import annotations

import random
from pathlib import Path

from diyface.catalog import index, scan
from diyface.models import ACTIVE, SLOTS, SlotId
from diyface.randomizer import OPTIONAL, random_recipe
from tests.helpers import write_png

REQUIRED = [slot for slot in ACTIVE if slot.id not in OPTIONAL]


def build_catalog(workdir: Path) -> dict:
    """每类造 2 张素材，确保随机有得选。"""
    layout = {
        "01_skin": ["skin_base", "skin_slim", "lorelei_skin_01", "lorelei_skin_02"],
        "02_clothes": ["clothes_crew_01", "clothes_shirt_01"],
        "03_hair_back": ["hair_back_long_01", "hair_back_short_01"],
        "04_hair": ["hair_straight_01", "hair_wavy_01", "lorelei_hair_01"],
        "05_eyes": ["eyes_round_01", "eyes_star_01", "lorelei_eyes_01", "lorelei_eyes_02"],
        "06_brows": ["brows_soft_01", "brows_sharp_01"],
        "07_mouth": ["mouth_smile_01", "mouth_laugh_01"],
        "08_glasses": ["glasses_round_01", "glasses_sun_01"],
        "09_hat": ["hat_beret_01", "hat_cap_01"],
        "10_extra": ["extra_earring_01", "extra_star_01"],
        "11_clothes": ["clothes_crew_01", "clothes_hoodie_01"],
        "12_extra": ["extra_earring_01", "extra_star_01"],
    }
    for folder, names in layout.items():
        for name in names:
            write_png(workdir / folder / f"{name}.png", bbox=(400, 400, 600, 600))
    return index(scan(workdir))


def test_required_slots_are_never_empty(workdir: Path) -> None:
    catalog = build_catalog(workdir)

    for seed in range(30):
        recipe = random_recipe(catalog, random.Random(seed))
        for slot in REQUIRED:
            assert recipe.slots[slot.id] is not None, f"{slot.id} 不该为空（seed={seed}）"


def test_optional_slots_sometimes_empty(workdir: Path) -> None:
    catalog = build_catalog(workdir)

    empties = sum(
        1
        for seed in range(100)
        for slot_id in OPTIONAL
        if random_recipe(catalog, random.Random(seed)).slots[slot_id] is None
    )

    assert 0 < empties < 100 * len(OPTIONAL), "可选槽位应当有时为空、有时不空"


def test_slots_without_assets_stay_empty(workdir: Path) -> None:
    catalog = build_catalog(workdir)
    recipe = random_recipe(catalog, random.Random(1))

    for slot in ACTIVE:
        if slot.id not in catalog:
            assert recipe.slots[slot.id] is None


def test_same_seed_gives_same_recipe(workdir: Path) -> None:
    catalog = build_catalog(workdir)

    first = random_recipe(catalog, random.Random(42))
    second = random_recipe(catalog, random.Random(42))

    assert first.slots == second.slots
    assert first.colors == second.colors
    assert first.seed == second.seed


def test_recipe_covers_all_twelve_slots(workdir: Path) -> None:
    catalog = build_catalog(workdir)
    recipe = random_recipe(catalog, random.Random(7))

    assert set(recipe.slots) == {slot.id for slot in SLOTS}


def test_colors_are_filled_for_active_slots(workdir: Path) -> None:
    catalog = build_catalog(workdir)
    recipe = random_recipe(catalog, random.Random(3))

    for slot in ACTIVE:
        assert recipe.colors.get(slot.id, "").startswith("#")


def test_random_never_mixes_styles(workdir: Path) -> None:
    """随机不准把两套风格拼在一起。"""
    from diyface.catalog import style_of

    catalog = build_catalog(workdir)
    for seed in range(30):
        recipe = random_recipe(catalog, random.Random(seed), style="lorelei")
        used = [asset_id for asset_id in recipe.slots.values() if asset_id]
        assert used, "至少要有素材"
        assert {style_of(asset_id) for asset_id in used} == {"lorelei"}


def test_random_without_style_keeps_old_behaviour(workdir: Path) -> None:
    recipe = random_recipe(build_catalog(workdir), random.Random(1))

    assert recipe.slots["skin"]


def test_random_without_style_picks_one_style(workdir: Path) -> None:
    """不指定风格时，随机也要整套来自同一套库。"""
    from diyface.catalog import style_of

    catalog = build_catalog(workdir)
    for seed in range(20):
        recipe = random_recipe(catalog, random.Random(seed))
        used = {style_of(asset_id) for asset_id in recipe.slots.values() if asset_id}
        assert len(used) == 1, f"混了风格：{used}"
