"""把外部导出的图层 PNG 导入成项目素材。

从 Figma / Sketch / 其他工具导出的图层，命名通常五花八门。这里做四件事：

1. 按文件名关键词推断它属于哪个槽位；
2. 统一缩放到 1024 画布（保持比例、居中、透明填充）；
3. 给可着色槽位补一张全白蒙版；
4. 输出导入报告，可疑文件跳过而不是硬塞。

真正的写盘动作在 :func:`install`，可以先用 :func:`plan` 只做预演。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .models import SLOT_BY_ID, SlotId, Slot

CANVAS = 1024
TINT_SUFFIX = "_tint.png"

#: 文件名关键词 -> 槽位；按顺序匹配，先命中先用。
HINTS: tuple[tuple[tuple[str, ...], SlotId], ...] = (
    (("hairback", "backhair", "side", "long"), SlotId.HAIR_BACK),
    (("hair", "fringe", "bangs"), SlotId.HAIR),
    (("eyebrow", "brow"), SlotId.BROWS),
    (("eye",), SlotId.EYES),
    (("mouth", "lip"), SlotId.MOUTH),
    (("glass", "specs"), SlotId.GLASSES),
    (("hat", "cap", "beanie"), SlotId.HAT),
    (("shirt", "cloth", "collar"), SlotId.CLOTHES),
    (("earring", "accessor", "extra"), SlotId.EXTRA),
    (("head", "face", "skin"), SlotId.SKIN),
)

_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Entry:
    """一条待导入的素材。"""

    slot: Slot
    source: Path
    name: str

    @property
    def target(self) -> str:
        return f"{self.name}.png"


@dataclass(frozen=True)
class Skipped:
    source: Path
    reason: str


def infer_slot(name: str) -> SlotId | None:
    """从文件名猜槽位；猜不出返回 None。

    按「词」匹配而不是子串，避免 ``whatever.png`` 因为含 ``hat`` 被认成帽子。
    """
    tokens = [token for token in re.split(r"[^a-z0-9]+", name.lower()) if token]
    for keywords, slot_id in HINTS:
        if any(token.startswith(keyword) for token in tokens for keyword in keywords):
            return slot_id
    return None


def slugify(name: str) -> str:
    """把任意文件名转成小写下划线形式。"""
    slug = _SLUG.sub("_", Path(name).stem.lower()).strip("_")
    return slug or "asset"


#: 从 Figma 等工具导出的图层会被裁到内容边界，原始位置丢失。
#: 这些槽位按「贴顶居中」摆放，其余按画布高度的比例居中。
TOP_ANCHORED = frozenset({SlotId.HAIR, SlotId.HAIR_BACK, SlotId.HAT, SlotId.BROWS})

#: 非贴顶槽位的垂直中心（相对 1024 画布的比例）。
#: 对应文档基线：脸中心 y=500、眼睛 y=460、嘴 y=620、肩线 y=880。
CENTER_Y: dict[SlotId, float] = {
    SlotId.SKIN: 0.488,
    SlotId.EYES: 0.449,
    SlotId.MOUTH: 0.605,
    SlotId.GLASSES: 0.449,
    SlotId.CLOTHES: 0.859,
    SlotId.EXTRA: 0.50,
}


def fit_canvas(
    image: Image.Image, size: int = CANVAS, slot: SlotId | None = None
) -> Image.Image:
    """缩放到画布上：保持比例，按槽位决定摆放位置。

    已经就是 1024 见方的图原样返回——这种通常是按完整画板导出的，位置是对的。
    被裁切过的图按 :data:`TOP_ANCHORED` 与 :data:`CENTER_Y` 估算位置。
    """
    image = image.convert("RGBA")
    if image.size == (size, size):
        return image

    scale = min(size / image.width, size / image.height)
    new_size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    resized = image.resize(new_size, Image.LANCZOS)

    x = (size - new_size[0]) // 2
    if slot in TOP_ANCHORED:
        y = 0
    elif slot is not None and slot in CENTER_Y:
        y = int(size * CENTER_Y[slot]) - new_size[1] // 2
    else:
        y = (size - new_size[1]) // 2
    y = max(0, min(size - new_size[1], y))

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(resized, (x, y))
    return canvas


def plan(files: list[Path], *, only_slot: str | None = None) -> tuple[list[Entry], list[Skipped]]:
    """把文件列表映射成导入计划，返回 (可导入, 跳过)。"""
    entries: list[Entry] = []
    skipped: list[Skipped] = []
    used: dict[str, int] = {}

    for path in sorted(files):
        if path.name.endswith(TINT_SUFFIX):
            skipped.append(Skipped(path, "这是蒙版文件，导入时会自动生成"))
            continue

        slot_id = infer_slot(path.name)
        if slot_id is None:
            skipped.append(Skipped(path, "文件名里认不出槽位（可加 --slot 指定）"))
            continue
        if only_slot and slot_id.value != only_slot:
            continue

        slot = SLOT_BY_ID[slot_id]
        prefix = slot.id.value
        slug = slugify(path.name)
        base = slug if slug.startswith(prefix) else f"{prefix}_{slug}"

        count = used.get(base, 0) + 1
        used[base] = count
        name = base if count == 1 else f"{base}_{count:02d}"

        entries.append(Entry(slot=slot, source=path, name=name))

    return entries, skipped


def verify_tree(root: Path) -> list[tuple[Path, list[str]]]:
    """对整个素材目录跑一遍校验，返回 [(文件, 问题列表)]。

    按槽位的 ``tintable`` 判断是否需要蒙版——眼镜、眼睛不需要，
    统一按 True 判会把它们全部误报成「缺蒙版」。
    """
    from .catalog import scan
    from .models import SLOT_BY_ID
    from .validate import validate_asset

    problems: list[tuple[Path, list[str]]] = []
    for slot_id, assets in scan(root).items():
        slot = SLOT_BY_ID[slot_id]
        for asset in assets:
            found = validate_asset(asset.path, tintable=slot.tintable)
            if found:
                problems.append((asset.path, found))
    return problems


def install(entries: list[Entry], root: Path, *, make_masks: bool = True) -> dict[str, int]:
    """把计划落盘：缩放、写入、生成蒙版。返回统计。"""
    written = 0
    masks = 0

    for entry in entries:
        folder = root / entry.slot.folder_no
        folder.mkdir(parents=True, exist_ok=True)

        with Image.open(entry.source) as image:
            canvas = fit_canvas(image, slot=entry.slot.id)
        target = folder / entry.target
        canvas.save(target, optimize=True)
        written += 1

        if make_masks and entry.slot.tintable:
            mask = target.with_name(f"{target.stem}{TINT_SUFFIX}")
            Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255)).save(mask)
            masks += 1

    return {"written": written, "masks": masks}
