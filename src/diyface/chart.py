"""从「色号图纸」截图里还原网格。

不依赖 OCR：先找网格线，切出每个格子的图案，再把长得一样的格子聚成若干类，
由用户为每一类指定色号。这样对字体、分辨率都不敏感。

对外只暴露三个函数：``detect_grid``、``extract_cells``、``cluster_cells``。
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass

import numpy as np
from PIL import Image

MIN_LINE_RATIO = 0.35
CELL_PADDING = 0.18
CLUSTER_SIZE = 10
HAMMING_TOLERANCE = 6
MAX_CLUSTERS = 16


@dataclass
class Grid:
    left: int
    top: int
    right: int
    bottom: int
    cols: int
    rows: int


def _dark_ratio(image: Image.Image) -> np.ndarray:
    gray = np.asarray(image.convert("L"), dtype=np.uint8)
    # 截图里的细线常被抗锯齿成中灰，阈值放宽到 200，靠「连续段」筛掉文字
    return (gray < 200).astype(np.float32)


def _longest_run(flags: np.ndarray) -> int:
    best = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        if current > best:
            best = current
    return best


def _line_positions(mask: np.ndarray, axis: int) -> list[int]:
    """找网格线：要求该行/列有一大段连续的深色像素（文字达不到）。"""
    if axis == 0:
        lines = [bool(_longest_run(mask[:, x]) >= mask.shape[0] * 0.5) for x in range(mask.shape[1])]
    else:
        lines = [bool(_longest_run(mask[y, :]) >= mask.shape[1] * 0.5) for y in range(mask.shape[0])]

    positions: list[int] = []
    index = 0
    while index < len(lines):
        if lines[index]:
            start = index
            while index < len(lines) and lines[index]:
                index += 1
            positions.append((start + index - 1) // 2)
        else:
            index += 1
    return positions


def detect_grid(image: Image.Image) -> Grid | None:
    """从截图里找网格；找不到返回 None。"""
    mask = _dark_ratio(image)
    cols_lines = _line_positions(mask, axis=0)
    rows_lines = _line_positions(mask, axis=1)
    if len(cols_lines) < 3 or len(rows_lines) < 3:
        return None

    left, right = cols_lines[0], cols_lines[-1]
    top, bottom = rows_lines[0], rows_lines[-1]
    cols = len(cols_lines) - 1
    rows = len(rows_lines) - 1
    if cols < 2 or rows < 2:
        return None
    return Grid(left=left, top=top, right=right, bottom=bottom, cols=cols, rows=rows)


def _cell_box(grid: Grid, row: int, col: int) -> tuple[int, int, int, int]:
    cw = (grid.right - grid.left) / grid.cols
    ch = (grid.bottom - grid.top) / grid.rows
    x0 = grid.left + col * cw
    y0 = grid.top + row * ch
    return (
        int(x0 + cw * CELL_PADDING),
        int(y0 + ch * CELL_PADDING),
        int(x0 + cw * (1 - CELL_PADDING)),
        int(y0 + ch * (1 - CELL_PADDING)),
    )


def extract_cells(image: Image.Image, grid: Grid) -> list[list[Image.Image]]:
    """按网格切出每个格子，返回二维列表。"""
    result: list[list[Image.Image]] = []
    for row in range(grid.rows):
        line: list[Image.Image] = []
        for col in range(grid.cols):
            box = _cell_box(grid, row, col)
            if box[2] - box[0] < 2 or box[3] - box[1] < 2:
                line.append(Image.new("L", (CLUSTER_SIZE, CLUSTER_SIZE), 255))
                continue
            line.append(image.crop(box).convert("L"))
        result.append(line)
    return result


def _signature(cell: Image.Image) -> np.ndarray:
    small = cell.resize((CLUSTER_SIZE, CLUSTER_SIZE), Image.BILINEAR)
    array = np.asarray(small, dtype=np.float32)
    return (array < 190).astype(np.uint8).flatten()


def _preview(cell: Image.Image) -> str:
    big = cell.resize((48, 48), Image.NEAREST).convert("RGB")
    buffer = io.BytesIO()
    big.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def cluster_cells(cells: list[list[Image.Image]]) -> list[dict]:
    """把格子按图案聚类，返回 [{id, count, preview, cells: [[row, col], ...]}]。"""
    signatures: list[tuple[np.ndarray, Image.Image, tuple[int, int]]] = []
    for row, line in enumerate(cells):
        for col, cell in enumerate(line):
            signatures.append((_signature(cell), cell, (row, col)))

    groups: list[dict] = []
    for signature, cell, position in signatures:
        placed = False
        for group in groups:
            distance = int(np.count_nonzero(group["signature"] != signature))
            if distance <= HAMMING_TOLERANCE:
                group["signature"] = signature
                group["cells"].append(position)
                placed = True
                break
        if not placed:
            groups.append(
                {
                    "signature": signature,
                    "preview": _preview(cell),
                    "cells": [position],
                    "sample": cell,
                }
            )

    groups.sort(key=lambda item: len(item["cells"]), reverse=True)
    if len(groups) > MAX_CLUSTERS:
        groups = groups[:MAX_CLUSTERS]

    return [
        {
            "id": index,
            "count": len(group["cells"]),
            "preview": group["preview"],
            "cells": [list(position) for position in group["cells"]],
        }
        for index, group in enumerate(groups)
    ]
