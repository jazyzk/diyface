"""把用户上传的图片转成 32×32 拼豆网格。

流程：
1. 居中裁成正方形（保留主体）；
2. 缩到 32×32：原图就是 32 的用最近邻，其它用面积平均，避免细节糊掉；
3. 每个格子按 Lab 色差匹配到 Mard 64 色板，透明像素记为空格子（-1）。

这样「拍一张拼豆作品」和「导出一张像素图」都能还原成可编辑的画布。
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image

from .mard import HEXES

GRID = 32
ALPHA_CUTOFF = 128
WHITE_CUTOFF = 246


def _rgb(hex_color: str) -> tuple[float, float, float]:
    return (
        int(hex_color[1:3], 16),
        int(hex_color[3:5], 16),
        int(hex_color[5:7], 16),
    )


def _to_lab(rgb: tuple[float, float, float]) -> np.ndarray:
    channels = np.array(rgb, dtype=float) / 255.0
    channels = np.where(
        channels <= 0.04045, channels / 12.92, ((channels + 0.055) / 1.055) ** 2.4
    )
    matrix = np.array(
        [[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]
    )
    xyz = matrix @ channels
    xyz = xyz / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), (7.787 * xyz) + (16 / 116))
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


PALETTE_LAB = np.array([_to_lab(_rgb(hex_color)) for hex_color in HEXES])


def _square(image: Image.Image) -> Image.Image:
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    return image.crop((left, top, left + side, top + side))


def quantize(image: Image.Image) -> list[int]:
    """返回 1024 个格子（32×32），值是 Mard 色板下标，-1 表示空。"""
    image = _square(image.convert("RGBA"))
    resample = Image.NEAREST if image.size == (GRID, GRID) else Image.BOX
    small = image.resize((GRID, GRID), resample)

    cells: list[int] = []
    for y in range(GRID):
        for x in range(GRID):
            red, green, blue, alpha = small.getpixel((x, y))
            if alpha < ALPHA_CUTOFF:
                cells.append(-1)
                continue
            if red >= WHITE_CUTOFF and green >= WHITE_CUTOFF and blue >= WHITE_CUTOFF:
                # 白底照片：纯白当背景，不硬塞成 H2 珠子
                cells.append(-1)
                continue
            lab = _to_lab((red, green, blue))
            distances = np.linalg.norm(PALETTE_LAB - lab, axis=1)
            cells.append(int(np.argmin(distances)))
    return _despeckle(cells)


def _despeckle(cells: list[int]) -> list[int]:
    """去掉孤立噪点：邻格里多数同色的，就把自己并过去。"""
    result = list(cells)
    for y in range(GRID):
        for x in range(GRID):
            index = y * GRID + x
            neighbours = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID and 0 <= ny < GRID:
                    neighbours.append(cells[ny * GRID + nx])
            if not neighbours:
                continue
            counts: dict[int, int] = {}
            for value in neighbours:
                counts[value] = counts.get(value, 0) + 1
            winner, count = max(counts.items(), key=lambda item: item[1])
            if count >= 3 and winner != cells[index]:
                result[index] = winner
    return result


def used_colors(cells: list[int]) -> int:
    return len({index for index in cells if index >= 0})
