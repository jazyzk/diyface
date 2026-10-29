"""槽位、图层顺序与配方模型。

这里是全项目的唯一真源：目录编号、z 序、可着色标记、默认颜色都只写一遍，
渲染器、清单生成、前端三边都从这里读，避免「文档写 30、代码写 60」。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SlotId(StrEnum):
    """12 个槽位。v1 启用 8 个，其余 4 个只保留枚举与 z 序。"""

    SKIN = "skin"
    CHEEKS = "cheeks"
    BANGS = "bangs"
    SIDE_HAIR = "side_hair"
    BROWS = "brows"
    EYES = "eyes"
    NOSE = "nose"
    MOUTH = "mouth"
    GLASSES = "glasses"
    CLOTHES = "clothes"
    HAT = "hat"
    EXTRA = "extra"


@dataclass(frozen=True)
class Slot:
    """一个图层槽位的静态描述。"""

    id: SlotId
    z: int
    tintable: bool
    default_color: str
    folder: str
    folder_no: str


SLOTS: tuple[Slot, ...] = (
    Slot(SlotId.SKIN, 10, True, "#F2D5B8", "skin", "01_skin"),
    Slot(SlotId.CHEEKS, 20, True, "#F2A6A6", "cheeks", "05_cheeks"),
    Slot(SlotId.BANGS, 30, True, "#3B2B23", "bangs", "02_bangs"),
    Slot(SlotId.SIDE_HAIR, 40, True, "#3B2B23", "side_hair", "03_side_hair"),
    Slot(SlotId.BROWS, 50, True, "#3B2B23", "brows", "04_brows"),
    Slot(SlotId.EYES, 60, False, "#2B2B2B", "eyes", "06_eyes"),
    Slot(SlotId.NOSE, 70, True, "#E8B79A", "nose", "08_nose"),
    Slot(SlotId.MOUTH, 80, True, "#C0504D", "mouth", "07_mouth"),
    Slot(SlotId.GLASSES, 90, False, "#2B2B2B", "glasses", "09_glasses"),
    Slot(SlotId.CLOTHES, 100, True, "#4A6FA5", "clothes", "11_clothes"),
    Slot(SlotId.HAT, 110, True, "#8E5A4A", "hat", "10_hat"),
    Slot(SlotId.EXTRA, 120, True, "#D4A017", "extra", "12_extra"),
)

SLOTS_BY_Z: tuple[Slot, ...] = tuple(sorted(SLOTS, key=lambda slot: slot.z))

#: 只保留枚举与 z 序、v1 不产出素材的槽位。
RESERVED: frozenset[SlotId] = frozenset(
    {SlotId.CHEEKS, SlotId.SIDE_HAIR, SlotId.BROWS, SlotId.NOSE}
)

#: v1 真正对外提供的槽位，按 z 升序。
ACTIVE: tuple[Slot, ...] = tuple(slot for slot in SLOTS_BY_Z if slot.id not in RESERVED)

SLOT_BY_ID: dict[SlotId, Slot] = {slot.id: slot for slot in SLOTS}

_HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}")
_ASSET_ID = re.compile(r"[a-z0-9_]+")


class AvatarRecipe(BaseModel):
    """一份「配方」：每个槽位选了哪张素材、用了什么颜色。"""

    version: int = 1
    slots: dict[SlotId, str | None] = Field(default_factory=dict)
    colors: dict[SlotId, str] = Field(default_factory=dict)
    seed: int | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("colors")
    @classmethod
    def check_hex_color(cls, value: dict[SlotId, str]) -> dict[SlotId, str]:
        for slot_id, color in value.items():
            if not _HEX_COLOR.fullmatch(color):
                raise ValueError(f"{slot_id} 的颜色必须是 #RRGGBB，收到 {color!r}")
        return value

    @field_validator("slots")
    @classmethod
    def check_asset_id(cls, value: dict[SlotId, str | None]) -> dict[SlotId, str | None]:
        for slot_id, asset_id in value.items():
            if asset_id is None:
                continue
            if not _ASSET_ID.fullmatch(asset_id):
                raise ValueError(f"{slot_id} 的素材 id 非法：{asset_id!r}")
        return value

    def slot_ids(self) -> list[SlotId]:
        """按 z 序返回本配方真正要画的槽位（值为 None 的槽位不算）。"""
        return [slot.id for slot in SLOTS_BY_Z if self.slots.get(slot.id) is not None]


def default_recipe() -> AvatarRecipe:
    """空配方：12 个槽位齐备但都不画，颜色取各槽位默认值。

    M1 会把「每个槽位的第一张素材」作为默认选择，这里刻意保持为空，
    让渲染器先学会处理「什么都不画」的边界情况。
    """
    return AvatarRecipe(
        slots={slot.id: None for slot in SLOTS},
        colors={slot.id: slot.default_color for slot in ACTIVE},
    )
