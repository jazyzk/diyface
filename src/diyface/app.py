"""FastAPI 应用：首页、素材清单、渲染接口与健康检查。

接口只做三件事：下发清单、按配方渲染、返回图像字节。
「怎么画」全部留在 render.py，接口层保持薄，方便单独测试。
"""

from __future__ import annotations

import hashlib
import random
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from . import __version__
from .catalog import Asset, manifest, scan
from .catalog import index as build_index
from .models import ACTIVE, SLOTS, AvatarRecipe, SlotId
from .randomizer import random_recipe
from .render import SIZES, render

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_catalog()
    yield


app = FastAPI(title="diyface", version=__version__, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class RenderRequest(BaseModel):
    recipe: AvatarRecipe
    size: int = 256


class RandomRequest(BaseModel):
    seed: int | None = None


def first_recipe(catalog: dict[SlotId, dict[str, Asset]]) -> AvatarRecipe:
    """首次进入时的默认脸：每个有素材的槽位取第一张。"""
    slots = {
        slot.id: (next(iter(catalog[slot.id])) if slot.id in catalog else None)
        for slot in SLOTS
    }
    colors = {slot.id: slot.default_color for slot in ACTIVE}
    return AvatarRecipe(slots=slots, colors=colors)


def manifest_payload() -> dict:
    """清单里直接带上默认配方，前端首屏不用再请求一次。"""
    data = manifest(scan(ASSETS_DIR))
    data["default_recipe"] = first_recipe(load_catalog()).model_dump(mode="json")
    return data


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    payload = manifest_payload()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "title": "DIY 头像生成器",
            "slots": payload["slots"],
            "version": __version__,
        },
    )


@app.get("/api/manifest")
def api_manifest() -> dict:
    return manifest_payload()


@app.get("/api/recipe/default")
def api_default_recipe() -> dict:
    return first_recipe(load_catalog()).model_dump(mode="json")


@app.post("/api/random")
def api_random(payload: RandomRequest | None = None) -> dict:
    """返回一份合法配方；带 seed 时结果可复现。"""
    rng = random.Random(payload.seed if payload else None)
    return random_recipe(load_catalog(), rng).model_dump(mode="json")


@app.post("/api/render")
def api_render(payload: RenderRequest, request: Request) -> Response:
    if payload.size not in SIZES:
        raise HTTPException(
            status_code=422,
            detail={"code": "BAD_SIZE", "message": f"size 只能是 {SIZES} 之一"},
        )

    try:
        png = render(payload.recipe, load_catalog(), payload.size)
    except KeyError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "UNKNOWN_ASSET", "message": str(exc)},
        ) from exc

    etag = '"' + hashlib.sha1(png).hexdigest()[:16] + '"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)

    return Response(
        png,
        media_type="image/png",
        headers={"ETag": etag, "Cache-Control": "public, max-age=86400"},
    )


@app.get("/healthz")
def healthz() -> dict:
    catalog = load_catalog()
    return {
        "ok": True,
        "version": __version__,
        "slots": len(catalog),
        "assets": sum(len(assets) for assets in catalog.values()),
    }


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = (
        exc.detail
        if isinstance(exc.detail, dict)
        else {"code": "ERROR", "message": str(exc.detail)}
    )
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": "请求体不符合约定",
                "field": errors[0]["loc"][-1] if errors else None,
            }
        },
    )
