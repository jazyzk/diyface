"""渲染耗时测量。

只做一件事：把同一份配方渲染若干次，返回中位/最快/最慢耗时（毫秒）。
M5 做缓存与性能优化时，用它对比「优化前 / 优化后」。
"""

from __future__ import annotations

import statistics
import time

from .render import render


def measure(recipe, catalog: dict, size: int, rounds: int = 10) -> dict[str, float]:
    """渲染 ``rounds`` 次，返回毫秒统计。"""
    if rounds < 1:
        raise ValueError("rounds 至少要 1")

    samples: list[float] = []
    for _ in range(rounds):
        start = time.perf_counter()
        render(recipe, catalog, size)
        samples.append((time.perf_counter() - start) * 1000)

    return {
        "median": statistics.median(samples),
        "min": min(samples),
        "max": max(samples),
    }
