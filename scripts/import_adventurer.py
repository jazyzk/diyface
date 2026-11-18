"""用 Adventurer（CC BY 4.0）生成项目的面部素材。

规则抄自官方的合成模板：

* 画布 762×762，我们放大到 1024
* 除 base 外，所有部件都套 ``translate(-161 -83)``

挑选：见 ``CURATED``，编号对应 ``tests/reports/pick-*.png`` 里的序号（从 1 开始）。
可着色槽位输出「白底 + 黑线」并配一张只覆盖主色的蒙版；眼睛、眼镜保留原色。
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from fetch_library import BLACK, WHITE, download, recolour, variants  # noqa: E402
from svg_render import render_paths  # noqa: E402

CANVAS = 1024
LIBRARY = "adventurer"
VIEWBOX = 762.0
SCALE = CANVAS / VIEWBOX
SHIFT = (-161.0 * SCALE, -83.0 * SCALE)

#: 槽位目录 -> (部件, 是否可着色, 保留的旧文件名, 挑中的变体序号（从 1 开始）)
CURATED: dict[str, tuple[str, bool, str, list[int]]] = {
    "01_skin": ("base", True, "skin_base", [1, 1]),
    "04_hair": (
        "hair", True, "hair_straight_01", [1, 5, 9, 10, 15, 17, 21, 25, 32, 39]
    ),
    "05_eyes": (
        "eyes", False, "eyes_round_01", [1, 8, 9, 10, 15, 19, 21, 23, 24, 26]
    ),
    "06_brows": ("eyebrows", True, "brows_soft_01", [1, 4, 8, 12]),
    "07_mouth": ("mouth", True, "mouth_smile_01", [1, 2, 3, 4, 5, 9, 16, 19]),
    "08_glasses": ("glasses", False, "glasses_round_01", [1, 2, 3, 4, 5]),
}


def transform_for(part: str) -> tuple[float, tuple[float, float]]:
    return (SCALE, (0.0, 0.0)) if part == "base" else (SCALE, SHIFT)


def render(key_paths: list[tuple[str, str]], part: str, colour: str) -> Image.Image:
    scale, offset = transform_for(part)
    return render_paths(recolour(key_paths, colour), scale=scale, offset=offset)


def main() -> int:
    assets = ROOT / "assets"
    for folder, (part, tintable, legacy, picks) in CURATED.items():
        table = variants(download(LIBRARY) / f"{part}.js")
        keys = sorted(table)
        target_dir = assets / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        for old in target_dir.glob("*.png"):
            old.unlink()

        for position, number in enumerate(picks, start=1):
            key = keys[number - 1]
            paths = table[key]
            image = render(paths, part, "#ffffff" if tintable else "#2B2B2B")

            if folder == "01_skin" and position == 2:
                name = "skin_slim"
                narrow = image.resize((int(CANVAS * 0.9), CANVAS), Image.LANCZOS)
                canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
                canvas.alpha_composite(narrow, (int(CANVAS * 0.05), 0))
                image = canvas
            else:
                name = legacy if position == 1 else f"{folder.split('_', 1)[1]}_adv_{position:02d}"
            target = target_dir / f"{name}.png"
            image.save(target, optimize=True)
            if target.stat().st_size > 80 * 1024:
                image.quantize(colors=96, method=Image.FASTOCTREE).convert("RGBA").save(
                    target, optimize=True
                )

            if tintable:
                mask_paths = [
                    (d, "#ffffff")
                    for d, fill in paths
                    if fill.strip().lower() not in BLACK and fill.strip().lower() not in WHITE
                ]
                scale, offset = transform_for(part)
                render_paths(mask_paths, scale=scale, offset=offset).save(
                    target.with_name(f"{target.stem}_tint.png")
                )
            print(f"{folder}/{target.name} <- {part}/{key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
