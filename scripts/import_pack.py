"""把外部导出的图层 PNG 导入成项目素材。

用法：

    # 先预演，看看会导入到哪
    python scripts/import_pack.py --src D:\\导出\\lorelei --dry-run

    # 确认无误后真正导入
    python scripts/import_pack.py --src D:\\导出\\lorelei

    # 只导入某个槽位（文件名认不出时手动指定）
    python scripts/import_pack.py --src D:\\导出\\glasses --slot glasses
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from diyface.importer import install, plan, verify_tree  # noqa: E402
from diyface.models import SLOTS                        # noqa: E402
from diyface.thumbs import build_thumbs                 # noqa: E402

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def main() -> int:
    parser = argparse.ArgumentParser(description="导入外部导出的图层素材")
    parser.add_argument("--src", type=Path, required=True, help="导出文件夹")
    parser.add_argument("--root", type=Path, default=ROOT / "assets", help="素材根目录")
    parser.add_argument("--slot", choices=[slot.id.value for slot in SLOTS], default=None)
    parser.add_argument("--dry-run", action="store_true", help="只预演，不写文件")
    parser.add_argument("--no-thumbs", action="store_true", help="导入后不重建缩略图")
    args = parser.parse_args()

    if not args.src.is_dir():
        print(f"目录不存在：{args.src}")
        return 1

    files = [p for p in args.src.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
    if not files:
        print(f"{args.src} 里没有图片")
        return 1

    entries, skipped = plan(files, only_slot=args.slot)

    print(f"可导入 {len(entries)} 张，跳过 {len(skipped)} 张")
    for entry in entries:
        print(f"  {entry.source.name:32} -> {entry.slot.folder_no}/{entry.target}")
    for item in skipped:
        print(f"  跳过 {item.source.name:26} {item.reason}")

    if args.dry_run:
        print("预演结束，未写文件")
        return 0
    if not entries:
        print("没有可导入的文件")
        return 1

    stats = install(entries, args.root)
    print(f"已写入 {stats['written']} 张素材，生成 {stats['masks']} 张蒙版")

    problems = verify_tree(args.root)
    for path, found in problems:
        for problem in found:
            print(f"FAIL {path.name}  {problem}")

    if not args.no_thumbs:
        print(f"已生成 {build_thumbs(args.root)} 张缩略图")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
