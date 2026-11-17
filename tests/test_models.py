"""槽位常量与配方校验的测试。

这些断言是「唯一真源」的护栏：z 序被改动、槽位被误删、校验被放松，都会红。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from diyface.models import (
    ACTIVE,
    RESERVED,
    SLOTS,
    SLOTS_BY_Z,
    AvatarRecipe,
    SlotId,
    default_recipe,
)


def test_ten_slots_with_unique_z() -> None:
    assert len(SLOTS) == 10
    z_values = [slot.z for slot in SLOTS]
    assert len(set(z_values)) == 10, "z 序必须唯一"
    assert SLOTS_BY_Z == tuple(sorted(SLOTS, key=lambda slot: slot.z))


def test_all_slots_are_active() -> None:
    """本期 10 个槽位全部交付，没有预留槽位。"""
    assert len(ACTIVE) == 10
    assert RESERVED == frozenset()


def test_z_order_matches_design_doc() -> None:
    expected = [
        "skin",
        "clothes",
        "hair_back",
        "hair",
        "eyes",
        "brows",
        "mouth",
        "glasses",
        "hat",
        "extra",
    ]
    assert [slot.id.value for slot in SLOTS_BY_Z] == expected


def test_tintable_flags_match_design_doc() -> None:
    untintable = {slot.id.value for slot in SLOTS if not slot.tintable}
    assert untintable == {"eyes", "glasses", "extra"}


def test_folder_names_follow_convention() -> None:
    for index, slot in enumerate(SLOTS, start=1):
        assert slot.folder_no == f"{index:02d}_{slot.folder}", f"{slot.id} 的目录编号不连续"


def test_default_recipe_shape() -> None:
    recipe = default_recipe()

    assert set(recipe.slots) == set(SlotId)
    assert all(value is None for value in recipe.slots.values())
    assert set(recipe.colors) == {slot.id for slot in ACTIVE}


def test_recipe_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        AvatarRecipe.model_validate({"unknown": 1})


def test_recipe_rejects_bad_color() -> None:
    with pytest.raises(ValidationError):
        AvatarRecipe(colors={SlotId.HAIR: "red"})


def test_recipe_rejects_bad_asset_id() -> None:
    with pytest.raises(ValidationError):
        AvatarRecipe(slots={SlotId.HAIR: "Hair Straight!"})


def test_recipe_accepts_none_and_valid_values() -> None:
    recipe = AvatarRecipe(
        slots={SlotId.HAIR: "hair_straight_01", SlotId.HAT: None},
        colors={SlotId.HAIR: "#2B1B12"},
    )

    assert recipe.slots[SlotId.HAIR] == "hair_straight_01"
    assert recipe.slot_ids() == [SlotId.HAIR]
