"""素材合规校验：一条规则一段逻辑，便于单独测试与复用。

``python -m diyface verify`` 就是逐张调用这里的 :func:`validate_asset`。
规则都写成「返回问题列表」，空列表表示合规，方便测试与批量汇总。
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

CANVAS = 1024
MAX_BYTES = 80 * 1024
TINT_SUFFIX = "_tint.png"

_NAME = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*")


def is_tint_mask(path: Path) -> bool:
    """蒙版文件本身不算素材，扫描与校验都要跳过。"""
    return path.name.endswith(TINT_SUFFIX)


def tint_mask_path(source: Path) -> Path:
    """素材对应的蒙版路径：同名加 ``_tint`` 后缀。"""
    return source.with_name(f"{source.stem}{TINT_SUFFIX}")


def validate_asset(path: Path, *, tintable: bool = True) -> list[str]:
    """返回这张图的所有问题；空列表表示合规。"""
    problems: list[str] = []

    if is_tint_mask(path):
        problems.append("这是蒙版文件，不应该出现在素材清单里")
        return problems

    if not _NAME.fullmatch(path.stem):
        problems.append("文件名只允许小写字母、数字与下划线")

    if not path.is_file():
        problems.append("文件不存在")
        return problems

    if path.stat().st_size > MAX_BYTES:
        problems.append(f"体积 {path.stat().st_size // 1024}KB 超过 80KB 上限")

    try:
        with Image.open(path) as image:
            if image.size != (CANVAS, CANVAS):
                problems.append(f"尺寸 {image.size} 不是 {CANVAS}x{CANVAS}")
            if image.mode != "RGBA":
                problems.append(f"模式 {image.mode} 不是 RGBA")
            else:
                low, high = image.getchannel("A").getextrema()
                if low != 0:
                    problems.append("没有任何透明像素，叠图时会盖住下层")
                if high != 255:
                    problems.append("没有任何不透明像素，等于一张空图")
    except OSError as exc:
        problems.append(f"打不开图片：{exc}")

    if tintable and not tint_mask_path(path).is_file():
        problems.append(f"可着色素材缺少蒙版 {tint_mask_path(path).name}")

    return problems


def validate_mask(source: Path) -> list[str]:
    """校验蒙版本身：尺寸与模式必须与素材一致。"""
    mask = tint_mask_path(source)
    if not mask.is_file():
        return [f"缺少蒙版 {mask.name}"]

    problems: list[str] = []
    with Image.open(mask) as image:
        if image.size != (CANVAS, CANVAS):
            problems.append(f"蒙版尺寸 {image.size} 不是 {CANVAS}x{CANVAS}")
        if image.mode not in {"L", "RGBA"}:
            problems.append(f"蒙版模式 {image.mode} 应为 L 或 RGBA")
    return problems
