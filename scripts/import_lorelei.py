"""把 Lorelei（手绘线稿风）导入成项目的第二套风格。

产出 ``assets/<slot>/lorelei_<part>_<variant>.png``：

* 可着色的部件写白底 + ``_tint.png`` 蒙版（主色留白，黑线与高光保留）；
* 眼睛、嘴、眼镜保留原色，对齐方式与 Adventurer 一致（同一块 1024 画布）。

用法：``python scripts/import_lorelei.py``，之后跑 ``python -m diyface build-thumbs``。
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_library import BLACK, WHITE, download, recolour, variants  # noqa: E402
from svg_render import render_paths  # noqa: E402

CANVAS = 1024
LIBRARY = "lorelei"
STYLE = "lorelei"

#: 每套风格挑多少个变体（按名称排序后的下标）
PICKS: dict[str, list[int]] = {
    "head": [0, 1, 2, 3],
    # 9/14/20 这几款在 Lorelei 里是「长发盖脸」，叠在本项目前面会糊住五官，剔除
    "hair": [0, 2, 5, 26, 33],
    "eyes": [1, 0, 3, 5, 8, 11, 14, 18],
    "eyebrows": [0, 2, 5, 8],
    "mouth": [0, 3, 6, 9, 12, 16, 20, 24],
    "glasses": [0, 1, 2, 4],
}

#: 部件 -> (槽位目录, 是否可着色, 非着色部件的颜色, 命名后缀)
LAYOUT: dict[str, tuple[str, bool, str, str]] = {
    "head": ("01_skin", True, "#E8B98A", "skin"),
    "hair": ("04_hair", True, "#2B1B12", "hair"),
    "eyes": ("05_eyes", False, "#2B1B12", "eyes"),
    "eyebrows": ("06_brows", True, "#2B1B12", "brows"),
    "mouth": ("07_mouth", False, "#C0504D", "mouth"),
    "glasses": ("08_glasses", False, "#2B2B2B", "glasses"),
}

#: 底脸额外叠一个鼻子，避免脸中间空着
NOSE_VARIANT = "variant03"


def mask_paths(paths: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return [
        (d, "#ffffff")
        for d, fill in paths
        if fill.strip().lower() not in BLACK and fill.strip().lower() not in WHITE
    ]


def main() -> int:
    root = download(LIBRARY)
    assets = ROOT / "assets"
    nose_table = variants(root / "nose.js")
    nose_key = NOSE_VARIANT if NOSE_VARIANT in nose_table else sorted(nose_table)[0]
    nose_paths = nose_table[nose_key]

    total = 0
    for part, indexes in PICKS.items():
        table = variants(root / f"{part}.js")
        keys = sorted(table)
        folder, tintable, color, suffix = LAYOUT[part]
        target_dir = assets / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        chosen = [keys[i] for i in indexes if i < len(keys)]
        for position, key in enumerate(chosen, start=1):
            paths = table[key]
            if part == "head":
                # 底脸 + 固定鼻子，一起当作肤色层
                merged = paths + nose_paths
                image = render_paths(recolour(merged, "#ffffff"))
                mask = render_paths(mask_paths(merged))
            elif tintable:
                image = render_paths(recolour(paths, "#ffffff"))
                mask = render_paths(mask_paths(paths))
            else:
                image = render_paths(recolour(paths, color))
                mask = None

            name = f"{STYLE}_{suffix}_{position:02d}"
            image.save(target_dir / f"{name}.png", optimize=True)
            if mask is not None:
                mask.save(target_dir / f"{name}_tint.png", optimize=True)
            total += 1
            print(f"{name:24s} <- {part}/{key}")

    print(f"完成：{total} 张")
    return 0


if __name__ == "__main__":
    sys.exit(main())
