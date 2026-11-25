"""32×32 拼豆画布：把「格子 + 调色板」渲染成 PNG。

设计要点：

* 网格固定 32×32，一格 32 像素，输出 1024×1024，与现有素材同尺寸；
* 数据用 RLE 压缩（``索引x连续格数``），一面满画板通常几百字节，能塞进分享链接；
* 两种画法：``bead`` 画成带孔的圆珠（拼豆感），``flat`` 画成方块（像素感）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from PIL import Image, ImageDraw

CANVAS = 1024
GRID = 32
CELL = CANVAS // GRID
MAX_COLORS = 128

_HEX = re.compile(r"#[0-9A-Fa-f]{6}")
_RUN = re.compile(r"(-?\d+)x(\d+)")


class PixelError(ValueError):
    """画布数据不合法。"""


@dataclass
class PixelArt:
    """一块画好的拼豆板。``cells`` 长度必须是 1024，-1 表示空格子。"""

    palette: list[str]
    cells: list[int] = field(default_factory=lambda: [-1] * (GRID * GRID))

    def __post_init__(self) -> None:
        if not self.palette:
            raise PixelError("调色板不能为空")
        if len(self.palette) > MAX_COLORS:
            raise PixelError(f"调色板最多 {MAX_COLORS} 色，收到 {len(self.palette)} 色")
        for color in self.palette:
            if not _HEX.fullmatch(color):
                raise PixelError(f"颜色必须是 #RRGGBB，收到 {color!r}")
        if len(self.cells) != GRID * GRID:
            raise PixelError(f"格子数量必须是 {GRID * GRID}，收到 {len(self.cells)}")
        for index in self.cells:
            if index < -1 or index >= len(self.palette):
                raise PixelError(f"颜色索引越界：{index}")


def encode(cells: list[int]) -> str:
    """把格子压成 RLE，例如 ``0x3,5x2,-1x4``。"""
    if not cells:
        return ""
    parts: list[str] = []
    current = cells[0]
    run = 1
    for value in cells[1:]:
        if value == current:
            run += 1
        else:
            parts.append(f"{current}x{run}")
            current, run = value, 1
    parts.append(f"{current}x{run}")
    return ",".join(parts)


def decode(text: str) -> list[int]:
    """还原 RLE；格式不对直接抛错，避免脏数据进渲染器。"""
    if not text:
        raise PixelError("画布数据为空")
    cells: list[int] = []
    for chunk in text.split(","):
        match = _RUN.fullmatch(chunk.strip())
        if not match:
            raise PixelError(f"无法解析的片段：{chunk!r}")
        value, count = int(match.group(1)), int(match.group(2))
        if count <= 0:
            raise PixelError(f"连续格数必须为正：{chunk!r}")
        cells.extend([value] * count)
    if len(cells) != GRID * GRID:
        raise PixelError(f"展开后应为 {GRID * GRID} 格，实际 {len(cells)} 格")
    return cells


def _shade(color: str, factor: float) -> tuple[int, int, int, int]:
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    return (
        max(0, min(255, int(r * factor))),
        max(0, min(255, int(g * factor))),
        max(0, min(255, int(b * factor))),
        255,
    )


def _rgba(color: str) -> tuple[int, int, int, int]:
    return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), 255)


def render(art: PixelArt, style: str = "bead") -> Image.Image:
    """把画布画成 1024 的透明 PNG。"""
    if style not in {"bead", "flat"}:
        raise PixelError(f"未知画法：{style!r}，只支持 bead / flat")

    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    inset = 2 if style == "bead" else 0

    for row in range(GRID):
        for col in range(GRID):
            index = art.cells[row * GRID + col]
            if index < 0:
                continue
            color = art.palette[index]
            x0 = col * CELL + inset
            y0 = row * CELL + inset
            x1 = (col + 1) * CELL - inset
            y1 = (row + 1) * CELL - inset

            if style == "flat":
                draw.rectangle([x0, y0, x1, y1], fill=_rgba(color))
                continue

            draw.ellipse([x0, y0, x1, y1], fill=_rgba(color))
            # 中间的孔：用深一档的颜色，透明背景上也能看出“珠子”
            hole = CELL * 0.22
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2
            draw.ellipse(
                [cx - hole, cy - hole, cx + hole, cy + hole], fill=_shade(color, 0.72)
            )
    return image


def thumbnail(art: PixelArt, size: int = 256, style: str = "bead") -> Image.Image:
    return render(art, style).resize((size, size), Image.NEAREST)
