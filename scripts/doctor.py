"""环境自检：换一台电脑后，先跑这个确认能否复现。

    python scripts/doctor.py

输出一张检查表；有任何 ❌ 就按提示修，全 ✅ 才继续。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

EXPECTED_ASSETS = 179
EXPECTED_SLOTS = 7


def _check(name: str, ok: bool, detail: str, hard: bool = True) -> dict:
    return {"name": name, "ok": ok, "detail": detail, "hard": hard}


def collect() -> list[dict]:
    checks: list[dict] = []

    checks.append(
        _check(
            "Python 版本",
            sys.version_info >= (3, 10),
            f"{sys.version_info.major}.{sys.version_info.minor}",
        )
    )

    for module in ("flask", "pydantic", "PIL"):
        try:
            __import__(module)
            checks.append(_check(f"依赖 {module}", True, "已安装"))
        except Exception as exc:  # noqa: BLE001
            checks.append(_check(f"依赖 {module}", False, str(exc)[:60]))

    try:
        from diyface.catalog import manifest, scan

        catalog = scan(ROOT / "assets")
        total = sum(len(assets) for assets in catalog.values())
        checks.append(
            _check("素材总数", total == EXPECTED_ASSETS, f"{total} 张（期望 {EXPECTED_ASSETS}）")
        )
        checks.append(
            _check("槽位数量", len(catalog) == EXPECTED_SLOTS, f"{len(catalog)} 个（期望 {EXPECTED_SLOTS}）")
        )
        data = manifest(catalog)
        checks.append(
            _check("风格数量", len(data["styles"]) == 3, f"{len(data['styles'])} 套（期望 3）")
        )
        checks.append(
            _check("背景数量", len(data["backgrounds"]) == 8, f"{len(data['backgrounds'])} 个（期望 8）")
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("扫描素材", False, str(exc)[:80]))

    try:
        __import__("waitress")
        checks.append(_check("生产服务器 waitress", True, "已安装"))
    except Exception:
        checks.append(_check("生产服务器 waitress", False, "未安装（仅部署需要）", hard=False))

    try:
        from diyface.ocr import available

        checks.append(
            _check(
                "OCR（可选）",
                available(),
                "可用" if available() else "未安装：图纸截图需手动选色号",
                hard=False,
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("OCR（可选）", False, str(exc)[:40], hard=False))

    return checks


def main() -> int:
    checks = collect()
    width = max(len(item["name"]) for item in checks)
    for item in checks:
        mark = "[OK]  " if item["ok"] else ("[FAIL]" if item["hard"] else "[SKIP]")
        print(f"{mark} {item['name'].ljust(width)}  {item['detail']}")

    failed = [item for item in checks if not item["ok"] and item["hard"]]
    print()
    if failed:
        print(f"有 {len(failed)} 项硬性检查未通过，先修好再继续。")
        return 1
    print("全部通过，可以启动服务：python -m flask --app diyface.app run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
