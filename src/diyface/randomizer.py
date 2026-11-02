"""生成合法的随机配方。

随机的三条底线：必填槽位不能空、可选槽位要有一定概率为空、颜色不能全撞成一片。
"""

from __future__ import annotations

import random

from .catalog import Asset
from .models import ACTIVE, RESERVED, SLOTS, AvatarRecipe, SlotId

#: 允许整个槽位留空（不戴眼镜、不戴帽子也不违和）。
OPTIONAL = frozenset({SlotId.GLASSES, SlotId.HAT, SlotId.CLOTHES, SlotId.EXTRA})

#: 可选槽位留空的概率。
EMPTY_CHANCE = 0.35

#: 保证「同一 seed 出同一张脸」的种子上限。
SEED_LIMIT = 1_000_000


def random_recipe(
    catalog: dict[SlotId, dict[str, Asset]],
    rng: random.Random | None = None,
) -> AvatarRecipe:
    """按素材表随机拼一份配方；可传入带种子的 Random 以便复现。"""
    rng = rng or random.Random()

    slots: dict[SlotId, str | None] = {}
    colors: dict[SlotId, str] = {}

    for slot in SLOTS:
        options = sorted(catalog.get(slot.id, {}))
        if slot.id in RESERVED or not options:
            slots[slot.id] = None
            continue

        if slot.id in OPTIONAL and rng.random() < EMPTY_CHANCE:
            slots[slot.id] = None
        else:
            slots[slot.id] = rng.choice(options)

        colors[slot.id] = slot.default_color

    return AvatarRecipe(slots=slots, colors=colors, seed=rng.randrange(SEED_LIMIT))
