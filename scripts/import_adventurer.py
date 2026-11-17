"""用 Adventurer（CC BY 4.0）替换项目的面部素材。

策略：保持文件名不变（skin_base、hair_straight_01……），只换画的内容。
这样 Recipe、fixtures、快照测试都不用改，只有像素变化。

* 可着色槽位（皮肤、头发、眉毛、嘴）：白底 + 黑线 + 全白蒙版
* 不可着色槽位（眼睛、眼镜）：保留原色
* 鼻子/腮红等 Adventurer 没有独立部件，鼻形画在脸型里，腮红放 extra 暂不处理
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from fetch_library import download, recolour, variants  # noqa: E402
from svg_render import render_paths  # noqa: E402

CANVAS = 1024
LIBRARY = "adventurer"

#: 槽位目录 -> (Adventurer 部件, 是否可着色)
SLOTS = {
    "01_skin": ("base", True),
    "04_hair": ("hair", True),
    "05_eyes": ("eyes", False),
    "06_brows": ("eyebrows", True),
    "07_mouth": ("mouth", True),
    "08_glasses": ("glasses", False),
}


def load_table(part: str) -> dict[str, list[tuple[str, str]]]:
    folder = download(LIBRARY)
    return variants(folder / f"{part}.js")


#: DiceBear Adventurer 的原始画布是 762×762，我们统一放大到 1024。
VIEWBOX = 762.0
SCALE = 1024 / VIEWBOX
#: 合成模板里，除 base 外所有部件都套了 translate(-161 -83)。
PART_SHIFT = (-161.0 * SCALE, -83.0 * SCALE)


def transform_for(part: str) -> tuple[float, tuple[float, float]]:
    """返回该部件在 1024 画布上的缩放与偏移（规则抄自官方 index.js）。"""
    if part == 'base':
        return SCALE, (0.0, 0.0)
    return SCALE, PART_SHIFT


def main() -> int:
    assets = ROOT / "assets"
    for folder_name, (part, tintable) in SLOTS.items():
        table = load_table(part)
        keys = sorted(table)
        files = sorted(
            path
            for path in (assets / folder_name).glob("*.png")
            if not path.stem.endswith("_tint")
        )
        if not files:
            print(f"{folder_name}: 没有素材，跳过")
            continue

        for index, path in enumerate(files):
            key = keys[index * len(keys) // len(files)] if len(keys) > len(files) else keys[
                min(index, len(keys) - 1)
            ]
            paths = table[key]
            scale, offset = transform_for(part)
            image = render_paths(
                recolour(paths, "#ffffff" if tintable else "#2B2B2B"),
                scale=scale,
                offset=offset,
            )

            if path.stem == "skin_slim":
                image = image.resize((int(CANVAS * 0.9), CANVAS), Image.LANCZOS)
                canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
                canvas.alpha_composite(image, (int(CANVAS * 0.05), 0))
                image = canvas

            image.save(path, optimize=True)
            if path.stat().st_size > 80 * 1024:
                image.quantize(colors=96, method=Image.FASTOCTREE).convert("RGBA").save(path, optimize=True)
            if tintable:
                Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255)).save(
                    path.with_name(f"{path.stem}_tint.png")
                )
            else:
                stale = path.with_name(f"{path.stem}_tint.png")
                if stale.exists():
                    stale.unlink()
            print(f"{folder_name}/{path.name} <- {part}/{key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
