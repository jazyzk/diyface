"""测试用的小工具：造一张合规的占位 PNG、准备临时目录。

放在单独的模块里，是为了让 conftest 的夹具和各测试文件共用同一套实现，
避免每个测试文件各写一遍「怎么造图」。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

CANVAS = 1024

#: 测试产物统一放在仓库内、已被 .gitignore 忽略的目录。
#: 不用系统临时目录是因为部分 Windows 环境的 Temp 权限被收紧，pytest 的
#: ``tmp_path`` 会直接抛 PermissionError。
TMP_ROOT = Path(__file__).resolve().parents[1] / "tests" / "reports" / "tmp"


def write_png(
    path: Path,
    bbox: tuple[int, int, int, int] | None = None,
    color: tuple[int, int, int, int] = (255, 255, 255, 255),
    size: tuple[int, int] = (CANVAS, CANVAS),
    mode: str = "RGBA",
) -> Path:
    """写一张 PNG。``bbox`` 给定时只在该矩形内涂色，其余保持透明。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode == "RGBA":
        image = Image.new("RGBA", size, (0, 0, 0, 0))
        if bbox is not None:
            image.paste(color, bbox)
    else:
        image = Image.new(mode, size, color[:3])
    image.save(path)
    return path
