"""把 DiceBear 素材库（CC0）的部件转成我们的 1024 PNG。

DiceBear 各风格的素材以「JS 模块 + SVG 路径字符串」发布，这里做三件事：

1. 从 npm 镜像下载指定风格的包并缓存；
2. 解析 ``lib/components/<部件>.js``，取出每个 variant 的 ``<path>`` 列表；
3. 用 :mod:`svg_render` 栅格化成 PNG，并把主色替换成目标色（黑线与眼睛保持黑）。

风格与许可：Lorelei、Notionists 均为 CC0；Adventurer/Micah 为 CC BY 4.0，需署名。

用法：

    python scripts/fetch_library.py --list lorelei
    python scripts/fetch_library.py --library lorelei --part hair --variant 1 \\
        --color "#2B1B12" --out tests/reports/hair1.png
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from svg_render import paths_from_fragment, render_paths  # noqa: E402

MIRROR = "https://registry.npmmirror.com/@dicebear/{name}/-/{name}-{version}.tgz"
DEFAULT_VERSION = "9.3.1"
CACHE = Path(__file__).resolve().parents[1] / "tests" / "reports" / "libs"

#: 视为「描边/瞳孔」的颜色，转换时保持黑色。
BLACK = {"#000", "#000000", "black", "#0f0f0f"}


def download(library: str, version: str = DEFAULT_VERSION) -> Path:
    """下载并解包到缓存目录，返回 ``lib/components`` 路径。"""
    target = CACHE / f"{library}-{version}"
    components = target / "package" / "lib" / "components"
    if components.is_dir():
        return components

    url = MIRROR.format(name=library, version=version)
    data = urllib.request.urlopen(url, timeout=120).read()
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(target)
    return components


_VARIANT = re.compile(r"(?m)^\s{4}([A-Za-z_][\w]*):\s*\(components, colors\)")


def variants(component_js: Path) -> dict[str, list[tuple[str, str]]]:
    """解析一个部件文件，返回 {variant_id: [(d, fill)]}。"""
    text = component_js.read_text(encoding="utf-8")
    marks = [(m.group(1), m.start()) for m in _VARIANT.finditer(text)]
    result: dict[str, list[tuple[str, str]]] = {}
    for index, (variant_id, start) in enumerate(marks):
        end = marks[index + 1][1] if index + 1 < len(marks) else len(text)
        block = text[start:end]
        paths = paths_from_fragment(block)
        if paths:
            result[variant_id] = paths
    return result


WHITE = {"#fff", "#ffffff", "white"}


def recolour(
    paths: list[tuple[str, str]], color: str, keep_black: bool = True, keep_white: bool = True
) -> list[tuple[str, str]]:
    """把主色替换成目标色；黑线保持黑、高光保持白，避免五官糊成一团。"""
    output = []
    for d, fill in paths:
        plain = fill.strip().lower()
        if keep_black and plain in BLACK:
            output.append((d, "#000"))
        elif keep_white and plain in WHITE:
            output.append((d, "#fff"))
        else:
            output.append((d, color))
    return output


def render_part(
    library: str, part: str, variant: str, color: str, version: str = DEFAULT_VERSION
):
    """渲染单个部件，返回 PIL 图。"""
    folder = download(library, version)
    table = variants(folder / f"{part}.js")
    if variant not in table:
        raise SystemExit(f"{library}/{part} 没有 variant {variant}，可选：{sorted(table)[:8]}")
    return render_paths(recolour(table[variant], color))


def main() -> int:
    parser = argparse.ArgumentParser(description="转换 DiceBear 部件为 PNG")
    parser.add_argument("--library", required=True)
    parser.add_argument("--list", action="store_true", help="只列出部件与变体数量")
    parser.add_argument("--part")
    parser.add_argument("--variant", default="1")
    parser.add_argument("--color", default="#2B1B12")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    folder = download(args.library)
    parts = sorted(path.stem for path in folder.glob("*.js"))

    if args.list:
        for part in parts:
            count = len(variants(folder / f"{part}.js"))
            if count:
                print(f"{part:16} {count} 个变体")
        return 0

    if not args.part or not args.out:
        parser.error("需要 --part 与 --out")

    image = render_part(args.library, args.part, args.variant, args.color)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.out)
    print(f"已生成 {args.out} ({image.size[0]}x{image.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
