"""Flask 应用：首页、素材清单、渲染接口与健康检查。

接口只做三件事：下发清单、按配方渲染、返回图像字节。
「怎么画」全部留在 render.py，接口层保持薄，方便单独测试。
"""

from __future__ import annotations

import hashlib
import random
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from pydantic import ValidationError

from . import __version__
from .catalog import Asset, manifest, scan
from .catalog import index as build_index
from .models import ACTIVE, SLOTS, AvatarRecipe, SlotId
from .randomizer import random_recipe
from .render import SIZES, render

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    template_folder=str(BASE_DIR / "templates"),
)

CATALOG: dict[SlotId, dict[str, Asset]] = {}


def load_catalog() -> dict[SlotId, dict[str, Asset]]:
    """懒加载素材表：第一次调用时扫盘，之后复用。"""
    global CATALOG
    if not CATALOG:
        CATALOG = build_index(scan(ASSETS_DIR))
    return CATALOG


def reset_catalog() -> None:
    """测试用：强制下次请求重新扫盘。"""
    global CATALOG
    CATALOG = {}


def first_recipe(catalog: dict[SlotId, dict[str, Asset]]) -> AvatarRecipe:
    """首次进入时的默认脸：每个有素材的槽位取第一张。"""
    slots = {}
    optional = {SlotId.GLASSES, SlotId.HAT, SlotId.EXTRA}
    for slot in SLOTS:
        available = catalog.get(slot.id, {})
        if not available or slot.id in optional:
            slots[slot.id] = None
        elif slot.default_asset in available:
            slots[slot.id] = slot.default_asset
        else:
            slots[slot.id] = next(iter(available))
    colors = {slot.id: slot.default_color for slot in ACTIVE}
    return AvatarRecipe(slots=slots, colors=colors)


def manifest_payload() -> dict:
    """清单里直接带上默认配方，前端首屏不用再请求一次。"""
    data = manifest(scan(ASSETS_DIR))
    data["default_recipe"] = first_recipe(load_catalog()).model_dump(mode="json")
    return data


def error(status: int, code: str, message: str, field: str | None = None):
    """统一的错误结构：{"error": {code, message, field}}。"""
    payload: dict[str, str] = {"code": code, "message": message}
    if field:
        payload["field"] = field
    return jsonify({"error": payload}), status


@app.get("/")
def index():
    payload = manifest_payload()
    return render_template(
        "index.html",
        title="DIY 头像生成器",
        slots=payload["slots"],
        version=__version__,
        manifest=payload,
    )


@app.get("/api/manifest")
def api_manifest():
    return jsonify(manifest_payload())


@app.get("/api/recipe/default")
def api_default_recipe():
    return jsonify(first_recipe(load_catalog()).model_dump(mode="json"))


@app.post("/api/random")
def api_random():
    payload = request.get_json(silent=True) or {}
    seed = payload.get("seed")
    rng = random.Random(seed if isinstance(seed, int) else None)
    return jsonify(random_recipe(load_catalog(), rng).model_dump(mode="json"))


@app.post("/api/render")
def api_render():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error(422, "INVALID_REQUEST", "请求体必须是 JSON 对象")

    try:
        recipe = AvatarRecipe.model_validate(payload.get("recipe"))
    except (ValidationError, ValueError):
        return error(422, "INVALID_REQUEST", "配方不符合约定", field="recipe")

    size = payload.get("size", 256)
    if not isinstance(size, int) or isinstance(size, bool) or size not in SIZES:
        return error(422, "BAD_SIZE", f"size 只能是 {SIZES} 之一", field="size")

    try:
        png = render(recipe, load_catalog(), size)
    except KeyError as exc:
        return error(422, "UNKNOWN_ASSET", str(exc), field="recipe")

    etag = '"' + hashlib.sha1(png).hexdigest()[:16] + '"'
    if request.headers.get("If-None-Match") == etag:
        return Response(status=304)

    return Response(
        png,
        mimetype="image/png",
        headers={"ETag": etag, "Cache-Control": "public, max-age=86400"},
    )


@app.get("/assets/<path:filename>")
def asset_file(filename: str):
    """素材原图与 256 缩略图，前端直接当图片用。"""
    return send_from_directory(ASSETS_DIR, filename)


@app.get("/healthz")
def healthz():
    catalog = load_catalog()
    return jsonify(
        {
            "ok": True,
            "version": __version__,
            "slots": len(catalog),
            "assets": sum(len(assets) for assets in catalog.values()),
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
