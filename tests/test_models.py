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


def test_twelve_slots_with_unique_z() -> None:
    assert len(SLOTS) == 12
    z_values = [slot.z for slot in SLOTS]
    assert len(set(z_values)) == 12, "z 序必须唯一"
    assert SLOTS_BY_Z == tuple(sorted(SLOTS, key=lambda slot: slot.z))


def test_eight_active_slots_and_four_reserved() -> None:
    assert len(ACTIVE) == 8
    assert len(RESERVED) == 4
    assert set(RESERVED).isdisjoint(slot.id for slot in ACTIVE)


def test_folder_names_follow_convention() -> None:
    for slot in SLOTS:
        assert slot.folder_no.endswith("_" + slot.folder), f"{slot.id} 的目录名与槽位不一致"
        assert slot.folder_no[:2].isdigit(), f"{slot.folder_no} 应以两位编号开头"


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
        AvatarRecipe(colors={SlotId.BANGS: "red"})


def test_recipe_rejects_bad_asset_id() -> None:
    with pytest.raises(ValidationError):
        AvatarRecipe(slots={SlotId.BANGS: "Bangs Straight!"})


def test_recipe_accepts_none_and_valid_values() -> None:
    recipe = AvatarRecipe(
        slots={SlotId.BANGS: "bangs_straight_01", SlotId.HAT: None},
        colors={SlotId.BANGS: "#3B2B23"},
    )

    assert recipe.slots[SlotId.BANGS] == "bangs_straight_01"
    assert recipe.slot_ids() == [SlotId.BANGS]
