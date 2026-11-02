"""命令行入口的测试。

直接调 ``main(argv)`` 而不是开子进程，跑得快且能精确断言返回码。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from diyface.__main__ import main

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
RECIPES = ROOT / "tests" / "fixtures" / "recipes"


def write_recipe(path: Path, slots: dict, colors: dict | None = None) -> Path:
    path.write_text(
        json.dumps({"version": 1, "slots": slots, "colors": colors or {}}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def test_render_writes_png(workdir: Path) -> None:
    out = workdir / "out.png"

    code = main(["render", str(RECIPES / "base.json"), "--out", str(out), "--root", str(ASSETS)])

    assert code == 0
    assert out.is_file()
    with Image.open(out) as image:
        assert image.size == (256, 256)
        assert image.mode == "RGBA"


def test_render_supports_1024(workdir: Path) -> None:
    out = workdir / "big.png"

    code = main(
        ["render", str(RECIPES / "base.json"), "--out", str(out), "--size", "1024", "--root", str(ASSETS)]
    )

    assert code == 0
    with Image.open(out) as image:
        assert image.size == (1024, 1024)


def test_render_fails_on_unknown_asset(workdir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    recipe = write_recipe(
        workdir / "bad.json",
        {"skin": "skin_base", "bangs": "bangs_not_exist", "eyes": None, "mouth": None,
         "glasses": None, "hat": None, "clothes": None, "extra": None,
         "cheeks": None, "side_hair": None, "brows": None, "nose": None},
    )
    out = workdir / "never.png"

    code = main(["render", str(recipe), "--out", str(out), "--root", str(ASSETS)])

    assert code == 1
    assert not out.exists()
    assert "没有素材" in capsys.readouterr().err


def test_render_fails_on_missing_recipe(workdir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["render", str(workdir / "nope.json"), "--root", str(ASSETS)])

    assert code == 1
    assert "配方不存在" in capsys.readouterr().err


def test_verify_lists_slots(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["verify", "--root", str(ASSETS)])

    assert code == 0
    output = capsys.readouterr().out
    assert "bangs" in output
    assert "共 3 张素材" in output


def test_render_rejects_bad_size(workdir: Path) -> None:
    with pytest.raises(SystemExit):
        main(["render", str(RECIPES / "base.json"), "--size", "512"])
