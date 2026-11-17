"""把 SVG 片段栅格化成 1024 PNG（离线，无浏览器依赖）。

为什么需要它：DiceBear 的 Lorelei 等 CC0 素材以「SVG 路径字符串」形式发布，
而我们的渲染器只吃 PNG。这里实现一个够用的子集：

* 路径命令：M/L/H/V/C/S/Q/T/A/Z（大小写都支持）
* 填充规则：偶奇（用逐子路径 XOR 近似）
* 只处理 ``<path>``，忽略描边（Lorelei 的素材本身是纯填充）

用法：

    python scripts/svg_render.py --svg in.svg --out out.png
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

CANVAS = 1024
S = 2  # 超采样倍数，用来消锯齿

_NUMBER = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_COMMAND = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")
_TOKENS = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")


def _numbers(text: str) -> list[float]:
    return [float(value) for value in _NUMBER.findall(text)]


def _arc_points(
    x0: float, y0: float, rx: float, ry: float, rotation: float, large: int, sweep: int,
    x1: float, y1: float, steps: int = 24,
) -> list[tuple[float, float]]:
    """把椭圆弧采样成折线（SVG 规范 F.6.5 的端点参数转中心参数）。"""
    if rx == 0 or ry == 0:
        return [(x1, y1)]
    phi = math.radians(rotation)
    dx2, dy2 = (x0 - x1) / 2, (y0 - y1) / 2
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)
    x1p = cos_phi * dx2 + sin_phi * dy2
    y1p = -sin_phi * dx2 + cos_phi * dy2

    rx, ry = abs(rx), abs(ry)
    lam = (x1p**2) / (rx**2) + (y1p**2) / (ry**2)
    if lam > 1:
        scale = math.sqrt(lam)
        rx, ry = rx * scale, ry * scale

    sign = -1 if large == sweep else 1
    num = rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2
    den = rx**2 * y1p**2 + ry**2 * x1p**2
    coef = sign * math.sqrt(max(0.0, num / den)) if den else 0.0
    cxp = coef * rx * y1p / ry
    cyp = -coef * ry * x1p / rx
    cx = cos_phi * cxp - sin_phi * cyp + (x0 + x1) / 2
    cy = sin_phi * cxp + cos_phi * cyp + (y0 + y1) / 2

    def angle(ux: float, uy: float, vx: float, vy: float) -> float:
        dot = ux * vx + uy * vy
        norm = math.hypot(ux, uy) * math.hypot(vx, vy)
        value = math.acos(max(-1.0, min(1.0, dot / norm))) if norm else 0.0
        return -value if ux * vy - uy * vx < 0 else value

    theta1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    delta = angle((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and delta > 0:
        delta -= 2 * math.pi
    elif sweep and delta < 0:
        delta += 2 * math.pi

    points = []
    for i in range(1, steps + 1):
        t = theta1 + delta * i / steps
        px = rx * math.cos(t)
        py = ry * math.sin(t)
        points.append((cos_phi * px - sin_phi * py + cx, sin_phi * px + cos_phi * py + cy))
    return points


def parse_path(d: str) -> list[list[tuple[float, float]]]:
    """把 path 的 d 属性拆成若干条折线（每条对应一个子路径）。"""
    tokens = _TOKENS.findall(d)
    subpaths: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    x = y = 0.0
    start_x = start_y = 0.0
    last_ctrl: tuple[float, float] | None = None
    command = ""
    index = 0

    def take(count: int) -> list[float]:
        nonlocal index
        values = [float(tokens[index + i]) for i in range(count)]
        index += count
        return values

    while index < len(tokens):
        token = tokens[index]
        if _COMMAND.fullmatch(token):
            command = token
            index += 1
            if command in "Zz":
                if current:
                    current.append((start_x, start_y))
                    subpaths.append(current)
                    current = []
                x, y = start_x, start_y
                continue
        if not command:
            break

        relative = command.islower()
        code = command.upper()

        if code == "M":
            nx, ny = take(2)
            x, y = (x + nx, y + ny) if relative else (nx, ny)
            if current:
                subpaths.append(current)
            current = [(x, y)]
            start_x, start_y = x, y
            command = "l" if relative else "L"
        elif code == "L":
            nx, ny = take(2)
            x, y = (x + nx, y + ny) if relative else (nx, ny)
            current.append((x, y))
        elif code == "H":
            (nx,) = take(1)
            x = x + nx if relative else nx
            current.append((x, y))
        elif code == "V":
            (ny,) = take(1)
            y = y + ny if relative else ny
            current.append((x, y))
        elif code in "CS":
            if code == "C":
                x1, y1, x2, y2, nx, ny = take(6)
                if relative:
                    x1, y1, x2, y2, nx, ny = x + x1, y + y1, x + x2, y + y2, x + nx, y + ny
                ctrl1 = (x1, y1)
            else:
                x2, y2, nx, ny = take(4)
                if relative:
                    x2, y2, nx, ny = x + x2, y + y2, x + nx, y + ny
                ctrl1 = (2 * x - last_ctrl[0], 2 * y - last_ctrl[1]) if last_ctrl else (x, y)
            for i in range(1, 17):
                t = i / 16
                mt = 1 - t
                px = mt**3 * x + 3 * mt**2 * t * ctrl1[0] + 3 * mt * t**2 * x2 + t**3 * nx
                py = mt**3 * y + 3 * mt**2 * t * ctrl1[1] + 3 * mt * t**2 * y2 + t**3 * ny
                current.append((px, py))
            last_ctrl = (x2, y2)
            x, y = nx, ny
        elif code in "QT":
            if code == "Q":
                x1, y1, nx, ny = take(4)
                if relative:
                    x1, y1, nx, ny = x + x1, y + y1, x + nx, y + ny
                ctrl = (x1, y1)
            else:
                nx, ny = take(2)
                if relative:
                    nx, ny = x + nx, y + ny
                ctrl = (2 * x - last_ctrl[0], 2 * y - last_ctrl[1]) if last_ctrl else (x, y)
            for i in range(1, 17):
                t = i / 16
                mt = 1 - t
                px = mt**2 * x + 2 * mt * t * ctrl[0] + t**2 * nx
                py = mt**2 * y + 2 * mt * t * ctrl[1] + t**2 * ny
                current.append((px, py))
            last_ctrl = ctrl
            x, y = nx, ny
        elif code == "A":
            rx, ry, rotation, large, sweep, nx, ny = take(7)
            if relative:
                nx, ny = x + nx, y + ny
            _arc_steps = max(16, min(160, int((abs(rx) + abs(ry)) * 0.8)))
            current.extend(_arc_points(x, y, rx, ry, rotation, int(large), int(sweep), nx, ny, steps=_arc_steps))
            x, y = nx, ny
        else:
            index += 1
            continue

        if code not in "CSQT":
            last_ctrl = None

    if current:
        subpaths.append(current)
    return subpaths


def render_paths(
    paths: list[tuple[str, str]],
    size: int = CANVAS,
    scale: float = 1.0,
    offset: tuple[float, float] = (0.0, 0.0),
) -> Image.Image:
    """paths = [(d, fill)]，返回带 alpha 的 PNG 图。"""
    big = size * S
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))

    for d, fill in paths:
        subpaths = parse_path(d)
        if not subpaths:
            continue

        mask = Image.new("1", (big, big), 0)
        for subpath in subpaths:
            points = [
                (round((px * scale + offset[0]) * S), round((py * scale + offset[1]) * S))
                for px, py in subpath
            ]
            if len(points) < 3:
                continue
            layer = Image.new("1", (big, big), 0)
            ImageDraw.Draw(layer).polygon(points, fill=1)
            mask = ImageChops.logical_xor(mask, layer)

        color = Image.new("RGBA", (big, big), _rgba(fill))
        color.putalpha(mask.convert("L"))
        image = Image.alpha_composite(image, color)

    return image.resize((size, size), Image.LANCZOS)


def _rgba(fill: str) -> tuple[int, int, int, int]:
    fill = (fill or "#000").strip()
    if fill.startswith("#") and len(fill) in (4, 7):
        if len(fill) == 4:
            fill = "#" + "".join(ch * 2 for ch in fill[1:])
        return (int(fill[1:3], 16), int(fill[3:5], 16), int(fill[5:7], 16), 255)
    return (0, 0, 0, 255)


_PATH_TAG = re.compile(r"<path\b([^>]*)/?>", re.S)
_ATTR = re.compile(r'([\w-]+)="([^"]*)"')


def paths_from_fragment(fragment: str) -> list[tuple[str, str]]:
    """从 SVG 片段里抽出 (d, fill) 列表。"""
    result = []
    for match in _PATH_TAG.finditer(fragment):
        attrs = dict(_ATTR.findall(match.group(1)))
        if "d" in attrs:
            result.append((attrs["d"], attrs.get("fill", "#000")))
    return result


def render_fragment(fragment: str, size: int = CANVAS) -> Image.Image:
    return render_paths(paths_from_fragment(fragment), size=size)


def main() -> int:
    parser = argparse.ArgumentParser(description="把 SVG 片段渲染成 PNG")
    parser.add_argument("--svg", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    fragment = args.svg.read_text(encoding="utf-8")
    image = render_fragment(fragment)
    image.save(args.out)
    print(f"已生成 {args.out}  {image.size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
