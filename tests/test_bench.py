"""渲染耗时测量的测试。

用假的 render 替换真实渲染，只验证「调用次数与统计口径」，不测性能数字。
"""

from __future__ import annotations

import pytest

from diyface import bench


def test_measure_calls_render_rounds_times(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    monkeypatch.setattr(bench, "render", lambda *args, **kwargs: calls.append(1) or b"")

    stats = bench.measure(recipe=None, catalog={}, size=256, rounds=3)

    assert len(calls) == 3
    assert set(stats) == {"median", "min", "max"}


def test_measure_returns_milliseconds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bench, "render", lambda *args, **kwargs: b"x")

    stats = bench.measure(recipe=None, catalog={}, size=256, rounds=5)

    assert 0 <= stats["min"] <= stats["median"] <= stats["max"]


def test_measure_rejects_zero_rounds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bench, "render", lambda *args, **kwargs: b"x")

    with pytest.raises(ValueError, match="rounds"):
        bench.measure(recipe=None, catalog={}, size=256, rounds=0)
