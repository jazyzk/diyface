"""渲染耗时基线：python scripts/bench_render.py

输出 256 与 1024 两个尺寸的中位/最快/最慢耗时，作为 M5 优化的对比基线。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from diyface.bench import measure                        # noqa: E402
from diyface.catalog import index, scan                   # noqa: E402
from diyface.models import AvatarRecipe                   # noqa: E402

RECIPE = ROOT / "tests" / "fixtures" / "recipes" / "base.json"
ROUNDS = 10


def main() -> int:
    catalog = index(scan(ROOT / "assets"))
    if not catalog:
        print("assets/ 里没有素材，先跑 python scripts/make_placeholders.py")
        return 1

    recipe = AvatarRecipe.model_validate_json(RECIPE.read_text(encoding="utf-8"))

    for size in (256, 1024):
        stats = measure(recipe, catalog, size, ROUNDS)
        print(
            f"{size:4d} px  "
            f"中位 {stats['median']:6.1f} ms  "
            f"最快 {stats['min']:6.1f} ms  "
            f"最慢 {stats['max']:6.1f} ms"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
