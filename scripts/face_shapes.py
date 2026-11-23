"""由 Adventurer 底脸派生多种脸型。

做法：保持画风与锚点不变，只对「脸的轮廓」做平滑的横向/纵向形变：

* 纵向：整体缩放 ``sy``，以脸的中心为基准；
* 横向：每行的缩放由「颧骨」和「下颌」两处平滑隆起叠加，形成圆脸、瓜子脸、方脸等差异。

输出与导入器一致：白底 PNG + ``_tint.png`` 蒙版，1024×1024 RGBA。
用法：``python scripts/face_shapes.py``（需先跑过 import_adventurer.py）
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SKIN_DIR = ASSETS / "01_skin"
CANVAS = 1024

# name -> (纵向缩放, 颧骨横向增减, 下颌横向增减, 下巴额外收窄)
SHAPES: dict[str, tuple[float, float, float, float]] = {
    "skin_round": (0.94, 0.09, 0.06, 0.03),
    "skin_oval": (1.05, 0.00, -0.13, -0.12),
    "skin_square": (0.99, 0.03, 0.15, 0.11),
    "skin_long": (1.15, -0.03, -0.01, 0.00),
    "skin_wide": (0.95, 0.13, 0.09, 0.02),
    "skin_baby": (0.97, 0.14, -0.02, -0.07),
    "skin_heart": (1.03, 0.08, -0.17, -0.16),
    "skin_slim": (1.02, -0.07, -0.09, -0.04),
}


def _bump(t: np.ndarray, center: float, width: float) -> np.ndarray:
    """在 [0,1] 上做一个平滑的钟形权重。"""
    return np.exp(-((t - center) ** 2) / (2 * width**2))


def _row_scale(t: np.ndarray, cheek: float, jaw: float, chin: float) -> np.ndarray:
    """按行给出横向缩放系数：额头 1.0，颧骨与下颌各加一个隆起。"""
    scale = np.ones_like(t)
    scale += cheek * _bump(t, 0.45, 0.22)
    scale += jaw * _bump(t, 0.82, 0.16)
    scale += chin * _bump(t, 0.97, 0.06)
    return scale


def _premultiply(arr: np.ndarray) -> np.ndarray:
    alpha = arr[..., 3:4] / 255.0
    return np.concatenate([arr[..., :3] * alpha, arr[..., 3:4]], axis=-1)


def _unpremultiply(arr: np.ndarray) -> np.ndarray:
    alpha = np.clip(arr[..., 3:4], 0, 255) / 255.0
    rgb = np.where(alpha > 0, arr[..., :3] / np.maximum(alpha, 1e-6), 0)
    return np.concatenate([np.clip(rgb, 0, 255), np.clip(arr[..., 3:4], 0, 255)], axis=-1)


def warp(
    image: Image.Image,
    sy: float,
    cheek: float,
    jaw: float,
    chin: float,
) -> Image.Image:
    """按行做横向缩放、整体做纵向缩放，返回新的 RGBA 图。"""
    source = np.asarray(image.convert("RGBA").resize((CANVAS, CANVAS), Image.NEAREST)).astype(np.float32)
    alpha_bbox = Image.fromarray(source[..., 3].astype(np.uint8)).getbbox()
    if not alpha_bbox:
        return image

    top, bottom = alpha_bbox[1], alpha_bbox[3]
    center_y = (top + bottom) / 2
    center_x = (alpha_bbox[0] + alpha_bbox[2]) / 2

    # 纵向：以脸中心为基准缩放，透明区域裁掉也不影响对齐
    target = Image.fromarray(np.clip(source, 0, 255).astype(np.uint8))
    new_height = max(1, int(round(CANVAS * sy)))
    scaled = target.resize((CANVAS, new_height), Image.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    offset = int(round(center_y - new_height * (center_y / CANVAS)))
    canvas.alpha_composite(scaled, (0, max(0, min(CANVAS - new_height, offset))))

    premultiplied = _premultiply(np.asarray(canvas).astype(np.float32))
    t = np.clip((np.arange(CANVAS) - top) / max(1, bottom - top), 0, 1)
    scales = _row_scale(t, cheek, jaw, chin)

    rows = np.arange(CANVAS, dtype=np.float32)
    out = np.zeros_like(premultiplied)
    for y in range(CANVAS):
        s = float(scales[y])
        if abs(s - 1.0) < 1e-4:
            out[y] = premultiplied[y]
            continue
        src_x = center_x + (rows - center_x) / s
        for channel in range(4):
            out[y, :, channel] = np.interp(
                src_x, rows, premultiplied[y, :, channel], left=0.0, right=0.0
            )

    return Image.fromarray(np.clip(_unpremultiply(out), 0, 255).astype(np.uint8))


def main() -> int:
    base_path = SKIN_DIR / "skin_base.png"
    mask_path = SKIN_DIR / "skin_base_tint.png"
    if not base_path.exists() or not mask_path.exists():
        print("缺少 skin_base.png / skin_base_tint.png，请先运行 import_adventurer.py")
        return 1

    base = Image.open(base_path).convert("RGBA")
    mask = Image.open(mask_path).convert("RGBA")

    for name, (sy, cheek, jaw, chin) in SHAPES.items():
        warped = warp(base, sy, cheek, jaw, chin)
        warped.save(SKIN_DIR / f"{name}.png", optimize=True)
        warped_mask = warp(mask, sy, cheek, jaw, chin)
        warped_mask.save(SKIN_DIR / f"{name}_tint.png", optimize=True)
        print(f"{name:12s} sy={sy:.2f} cheek={cheek:+.2f} jaw={jaw:+.2f} chin={chin:+.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
