"""生成素材参考图。

用法：

    python scripts/make_guide.py
    python scripts/make_guide.py --reference assets/01_skin/skin_base.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from diyface.guide import build_guide  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 1024 画布的参考图")
    parser.add_argument("--out", type=Path, default=Path("assets/_guide.png"))
    parser.add_argument(
        "--reference",
        type=Path,
        default=None,
        help="把已有素材淡化后叠上去，便于临摹",
    )
    args = parser.parse_args()

    path = build_guide(args.out, args.reference)
    print(f"已生成 {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
