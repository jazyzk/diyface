"""槽位、图层顺序与配方模型。

这里是全项目的唯一真源：目录编号、z 序、可着色标记、默认颜色都只写一遍，
渲染器、清单生成、前端三边都从这里读，避免「文档写 30、代码写 60」。

槽位与 z 序按《虚拟头像设计系统 · 项目说明与分工》v1.0 的 10 槽位表定义。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SlotId(StrEnum):
    """10 个槽位，全部在本期交付。"""

    SKIN = "skin"
    CLOTHES = "clothes"
    HAIR_BACK = "hair_back"
    HAIR = "hair"
    EYES = "eyes"
    BROWS = "brows"
    MOUTH = "mouth"
    GLASSES = "glasses"
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
    label_zh: str = ""
    label_en: str = ""
    #: 首次进入时默认选中的素材 id；为空则退化为该槽位按名字排序的第一张。
    default_asset: str = ""


SLOTS: tuple[Slot, ...] = (
    Slot(SlotId.SKIN, 10, True, "#E8B98A", "skin", "01_skin", "脸型", "Skin", "skin_base"),
    Slot(SlotId.CLOTHES, 20, True, "#3A6EA5", "clothes", "02_clothes", "服装", "Clothes", "clothes_crew_01"),
    Slot(SlotId.HAIR_BACK, 25, True, "#2B1B12", "hair_back", "03_hair_back", "后发", "Back hair", "hair_back_long_straight_01"),
    Slot(SlotId.HAIR, 30, True, "#2B1B12", "hair", "04_hair", "前发", "Hair", "hair_straight_01"),
    Slot(SlotId.EYES, 40, False, "#2B2B2B", "eyes", "05_eyes", "眼睛", "Eyes", "eyes_round_01"),
    Slot(SlotId.BROWS, 45, True, "#2B1B12", "brows", "06_brows", "眉毛", "Brows", "brows_soft_01"),
    Slot(SlotId.MOUTH, 50, False, "#C0504D", "mouth", "07_mouth", "嘴", "Mouth", "mouth_smile_01"),
    Slot(SlotId.GLASSES, 60, False, "#2B2B2B", "glasses", "08_glasses", "眼镜", "Glasses", "glasses_round_01"),
    Slot(SlotId.HAT, 70, True, "#8E5A4A", "hat", "09_hat", "帽子", "Hats", "hat_beret_01"),
    Slot(SlotId.EXTRA, 80, False, "#D4A017", "extra", "10_extra", "配饰", "Extras", "extra_earring_01"),
)

SLOTS_BY_Z: tuple[Slot, ...] = tuple(sorted(SLOTS, key=lambda slot: slot.z))

#: 预留槽位（本期没有）：保留这个空集合，方便以后加槽位时区分启用范围。
RESERVED: frozenset[SlotId] = frozenset()

#: 本期对外提供的槽位，按 z 升序。
ACTIVE: tuple[Slot, ...] = tuple(slot for slot in SLOTS_BY_Z if slot.id not in RESERVED)

#: 每个槽位可选的预设颜色（前端渲染成色块，用户点一下就换）。
PALETTES: dict[SlotId, tuple[str, ...]] = {
    SlotId.SKIN: ("#F7D7BE", "#E8B98A", "#C68B59", "#A1663F", "#6E4227", "#4A2C1B"),
    SlotId.HAIR: ("#1B1B1B", "#2B1B12", "#4A312C", "#8B5A2B", "#C0392B", "#D9A441",
                  "#4A6FA5", "#7D5BA6"),
    SlotId.BROWS: ("#1B1B1B", "#2B1B12", "#4A312C", "#6E4227"),
    SlotId.MOUTH: ("#C0504D", "#A63A3F", "#D9776F", "#8E4A5B"),
}

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
    """空配方：10 个槽位齐备但都不画，颜色取各槽位默认值。"""
    return AvatarRecipe(
        slots={slot.id: None for slot in SLOTS},
        colors={slot.id: slot.default_color for slot in ACTIVE},
    )
