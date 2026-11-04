"""命令行入口。

用法（在项目根目录）：

    python -m diyface render tests/fixtures/recipes/base.json --out out.png
    python -m diyface verify

``render`` 把配方渲染成 PNG，``verify`` 扫描素材目录并打印每个槽位的数量。
两者都不依赖 Web 服务，便于在没有前端时验证渲染链路。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .catalog import index, scan
from .models import SLOTS, AvatarRecipe
from .render import render
from .thumbs import build_thumbs, stale_thumbs
from .validate import validate_asset

DEFAULT_ROOT = Path("assets")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="diyface", description="分层头像生成器")
    sub = parser.add_subparsers(dest="command", required=True)

    render_cmd = sub.add_parser("render", help="按配方渲染 PNG")
    render_cmd.add_argument("recipe", type=Path, help="配方 JSON 路径")
    render_cmd.add_argument("--out", type=Path, default=Path("out.png"), help="输出路径")
    render_cmd.add_argument("--size", type=int, default=256, choices=[256, 1024])
    render_cmd.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="素材目录")

    verify_cmd = sub.add_parser("verify", help="扫描素材并统计")
    verify_cmd.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="素材目录")
    verify_cmd.add_argument(
        "--slot",
        choices=[slot.id.value for slot in SLOTS],
        default=None,
        help="只检查指定槽位",
    )

    thumbs_cmd = sub.add_parser("build-thumbs", help="生成 256 缩略图")
    thumbs_cmd.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="素材目录")
    thumbs_cmd.add_argument(
        "--slot",
        choices=[slot.id.value for slot in SLOTS],
        default=None,
        help="只处理指定槽位",
    )
    thumbs_cmd.add_argument(
        "--check",
        action="store_true",
        help="只检查是否过期，不写文件；过期时退出码为 1",
    )

    return parser


def cmd_render(args: argparse.Namespace) -> int:
    if not args.recipe.is_file():
        raise FileNotFoundError(f"配方不存在：{args.recipe}")

    catalog = index(scan(args.root))
    recipe = AvatarRecipe.model_validate_json(args.recipe.read_text(encoding="utf-8"))
    data = render(recipe, catalog, args.size)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(data)
    print(f"已生成 {args.out}（{args.size}×{args.size}，{len(data) / 1024:.1f} KB）")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        catalog = scan(args.root)
    except ValueError as exc:
        # 扫描阶段就会拦下尺寸/模式/命名问题，把文件名与原因直接抛给作者
        print(f"FAIL {exc}")
        print("检查中断：目录里有不合法的文件，先修掉再跑")
        return 1

    total = 0
    failures = 0

    for slot in SLOTS:
        if args.slot and slot.id.value != args.slot:
            continue
        assets = catalog.get(slot.id, [])
        if not assets:
            continue
        print(f"{slot.folder_no:14} {slot.id.value:10} {len(assets):3} 张")
        for asset in assets:
            total += 1
            for problem in validate_asset(asset.path, tintable=slot.tintable):
                print(f"FAIL {asset.path}  {problem}")
                failures += 1

    print(f"检查 {total} 张素材，问题 {failures} 个")
    return 1 if failures else 0


def cmd_build_thumbs(args: argparse.Namespace) -> int:
    if args.check:
        stale = stale_thumbs(args.root, args.slot)
        for path in stale:
            print(f"过期 {path}")
        print(f"过期 {len(stale)} 张")
        return 1 if stale else 0

    count = build_thumbs(args.root, args.slot)
    print(f"已生成 {count} 张缩略图")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "render":
            return cmd_render(args)
        if args.command == "build-thumbs":
            return cmd_build_thumbs(args)
        return cmd_verify(args)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
