"""把 CC0 素材库（Lorelei）转成项目格式的小样包。

产出两类文件：

* ``<slot>/<lib>_<part>_<variant>.png``：白底 + 黑线的可着色素材
* 同名 ``_tint.png``：整层可上色的蒙版

再拼几张预览图用于确认风格（256 与 1024 各一组），不直接写进 ``assets/``。

用法：

    python scripts/build_style_pack.py --library lorelei --out tests/reports/style-pack
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_library import download, recolour, variants  # noqa: E402
from svg_render import render_paths  # noqa: E402

CANVAS = 1024

#: 部件 -> (目标槽位目录, 是否可着色, 默认色)
PARTS = {
    "head": ("01_skin", True, "#E8B98A"),
    "hair": ("04_hair", True, "#2B1B12"),
    "eyes": ("05_eyes", False, "#2B1B12"),
    "eyebrows": ("06_brows", True, "#2B1B12"),
    "mouth": ("07_mouth", True, "#C0504D"),
    "glasses": ("08_glasses", False, "#2B2B2B"),
}

#: 小样要渲染的变体（下标，按名称排序后取值）。
SAMPLE = {
    "head": [0],
    "hair": [0, 4, 25],
    "eyes": [8],
    "eyebrows": [0],
    "mouth": [0, 6],
    "glasses": [],
}


def part_table(library: str, part: str) -> dict[str, list[tuple[str, str]]]:
    return variants(download(library) / f"{part}.js")


def white_base(paths: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """把主色替换成白色，黑线与高光保持原样；相乘上色时主色才会变成目标色。"""
    return recolour(paths, "#ffffff")


def build(library: str, out: Path) -> dict[str, dict[str, Path]]:
    """渲染小样并落盘，返回 {part: {variant: 路径}}。"""
    saved: dict[str, dict[str, Path]] = {}
    for part, (folder, tintable, color) in PARTS.items():
        table = part_table(library, part)
        if not table:
            continue
        keys = sorted(table)
        chosen = [keys[i] for i in SAMPLE.get(part, []) if i < len(keys)]
        if not chosen:
            continue

        slot_dir = out / folder
        slot_dir.mkdir(parents=True, exist_ok=True)
        saved[part] = {}
        for key in chosen:
            paths = white_base(table[key]) if tintable else recolour(table[key], color)
            image = render_paths(paths)
            target = slot_dir / f"{library}_{part}_{key}.png"
            image.save(target)
            if tintable:
                Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255)).save(
                    target.with_name(f"{target.stem}_tint.png")
                )
            saved[part][key] = target
    return saved


def compose(layers: list[Image.Image]) -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    for layer in layers:
        canvas = Image.alpha_composite(canvas, layer)
    return canvas


def make_sheets(library: str, out: Path, parts: list[str], columns: int) -> None:
    """把部件所有变体排成网格，用于人工挑选。"""
    from diyface.palettes import tint  # noqa: PLC0415

    for part in parts:
        folder, tintable, color = PARTS[part]
        table = part_table(library, part)
        keys = sorted(table)
        tiles = []
        for key in keys:
            paths = white_base(table[key]) if tintable else recolour(table[key], color)
            image = render_paths(paths)
            if tintable:
                image = tint(image, color)
            tiles.append(image.resize((200, 200), Image.LANCZOS))

        rows = (len(tiles) + columns - 1) // columns
        sheet = Image.new("RGBA", (200 * columns, 200 * rows), (250, 250, 252, 255))
        for index, tile in enumerate(tiles):
            sheet.alpha_composite(tile, (200 * (index % columns), 200 * (index // columns)))
        target = out / f"{part}-sheet.png"
        sheet.convert("RGB").save(target)
        print(f"{part}: {len(keys)} 个变体 -> {target}")


#: 贴脸预览用的默认部件下标（挑过：不遮脸的发型、睁眼、微笑）。
DEFAULT_INDEX = {"head": 0, "hair": 1, "eyes": 8, "eyebrows": 0, "mouth": 0}


def _render_part(library: str, part: str, index: int):
    from diyface.palettes import tint  # noqa: PLC0415

    folder, tintable, color = PARTS[part]
    table = part_table(library, part)
    key = sorted(table)[index]
    paths = white_base(table[key]) if tintable else recolour(table[key], color)
    image = render_paths(paths)
    return tint(image, color) if tintable else image


def make_on_face(library: str, out: Path, parts: list[str], columns: int) -> None:
    """把某部件的每个变体贴到同一张脸上，方便判断真实效果。"""
    for part in parts:
        folder, tintable, color = PARTS[part]
        table = part_table(library, part)
        keys = sorted(table)
        tiles = []
        for index in range(len(keys)):
            layers = []
            for base_part in ("head", "hair", "eyes", "eyebrows", "mouth"):
                if base_part == part:
                    layers.append(_render_part(library, part, index))
                elif base_part in DEFAULT_INDEX and base_part in PARTS:
                    layers.append(_render_part(library, base_part, DEFAULT_INDEX[base_part]))
            canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
            for layer in layers:
                canvas = Image.alpha_composite(canvas, layer)
            tiles.append(canvas.resize((200, 200), Image.LANCZOS))

        rows = (len(tiles) + columns - 1) // columns
        sheet = Image.new("RGBA", (200 * columns, 200 * rows), (250, 250, 252, 255))
        for index, tile in enumerate(tiles):
            sheet.alpha_composite(tile, (200 * (index % columns), 200 * (index // columns)))
        target = out / f"{part}-on-face.png"
        sheet.convert("RGB").save(target)
        print(f"{part}: {len(keys)} 个变体贴脸 -> {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 Lorelei 小样包与预览图")
    parser.add_argument("--library", default="lorelei")
    parser.add_argument("--out", type=Path, default=Path("tests/reports/style-pack"))
    parser.add_argument("--sheet", default="", help="只出变体网格，如 hair,eyes,mouth")
    parser.add_argument("--on-face", default="", help="把某部件的变体逐个贴到脸上出图")
    parser.add_argument("--columns", type=int, default=8)
    args = parser.parse_args()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    if args.sheet:
        make_sheets(args.library, out, [name.strip() for name in args.sheet.split(",")], args.columns)
        return 0

    if args.on_face:
        make_on_face(args.library, out, [name.strip() for name in args.on_face.split(",")], args.columns)
        return 0
    saved = build(args.library, out)

    from diyface.palettes import tint  # noqa: PLC0415

    def load(part: str, index: int = 0, color: str | None = None) -> Image.Image:
        keys = sorted(saved[part])
        image = Image.open(saved[part][keys[index]]).convert("RGBA")
        return tint(image, color) if color else image

    head = load("head", color="#E8B98A")
    eyes = load("eyes")
    brows = load("brows", color="#2B1B12") if "brows" in saved else None

    tiles = []
    for hair_index in range(len(saved["hair"])):
        layers = [head, load("hair", hair_index, "#2B1B12"), eyes]
        if brows is not None:
            layers.append(brows)
        layers.append(load("mouth", 0, "#C0504D"))
        tiles.append(compose(layers).resize((256, 256), Image.LANCZOS))

    for mouth_index in range(1, len(saved["mouth"])):
        layers = [head, load("hair", 0, "#2B1B12"), eyes]
        if brows is not None:
            layers.append(brows)
        layers.append(load("mouth", mouth_index, "#C0504D"))
        tiles.append(compose(layers).resize((256, 256), Image.LANCZOS))

    sheet = Image.new("RGBA", (256 * len(tiles), 256), (250, 250, 252, 255))
    for index, tile in enumerate(tiles):
        sheet.alpha_composite(tile, (256 * index, 0))
    sheet.convert("RGB").save(out / "samples.png")

    # 着色测试：同一张白底发型换三种颜色
    from diyface.palettes import tint  # noqa: PLC0415

    hair_image = load("hair", 0)
    tinted = []
    for color in ("#2B1B12", "#C0392B", "#4A6FA5"):
        layers = [head, tint(hair_image, color), eyes, load("mouth", 0, "#C0504D")]
        tinted.append(compose(layers).resize((256, 256), Image.LANCZOS))
    sheet = Image.new("RGBA", (256 * len(tinted), 256), (250, 250, 252, 255))
    for index, tile in enumerate(tinted):
        sheet.alpha_composite(tile, (256 * index, 0))
    sheet.convert("RGB").save(out / "tinted.png")

    # 1024 细节图
    layers = [head, load("hair", 0, "#2B1B12"), eyes]
    if brows is not None:
        layers.append(brows)
    layers.append(load("mouth", 0, "#C0504D"))
    compose(layers).save(out / "detail-1024.png")

    print(f"小样已生成：{out}")
    for part, items in saved.items():
        print(f"  {part}: {len(items)} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
