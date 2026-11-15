"""生成画素材用的参考图。

手绘时把它放在最上层、把不透明度调到 20% 左右，照着画就能保证所有图层共用同一套坐标。
可选：把已有一张素材淡化叠上去，当作临摹底稿。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

CANVAS = 1024

#: (位置, 方向, 颜色, 线宽)。基线取自《项目说明与分工》v1.0 §5.1：
#: 脸中心 y=500、头顶 y=170、眼睛 y=460、嘴 y=620、肩线 y=880。
LINES: tuple[tuple[int, str, tuple[int, int, int, int], int], ...] = (
    (512, "vertical", (0, 160, 255, 220), 3),      # 垂直中线：左右对称
    (170, "horizontal", (0, 200, 120, 220), 3),    # 头顶基线：头发与帽子的起点
    (460, "horizontal", (120, 200, 0, 200), 2),    # 眼睛水平线
    (500, "horizontal", (255, 120, 0, 220), 3),    # 脸中心：五官围绕它排布
    (620, "horizontal", (220, 60, 90, 200), 2),    # 嘴水平线
    (880, "horizontal", (170, 90, 220, 180), 2),   # 肩线：服装上缘
)

#: 临摹底稿的不透明度（百分比）。
GHOST_ALPHA = 30


def build_guide(target: Path, reference: Path | None = None) -> Path:
    """在 ``target`` 写出参考图，返回路径。"""
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    for position, direction, color, width in LINES:
        if direction == "vertical":
            draw.line([(position, 0), (position, CANVAS)], fill=color, width=width)
        else:
            draw.line([(0, position), (CANVAS, position)], fill=color, width=width)

    if reference is not None and reference.is_file():
        with Image.open(reference) as ref:
            ghost = ref.convert("RGBA").resize((CANVAS, CANVAS))
        ghost.putalpha(ghost.getchannel("A").point(lambda value: value * GHOST_ALPHA // 100))
        image = Image.alpha_composite(image, ghost)

    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target)
    return target
