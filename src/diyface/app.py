"""FastAPI 应用：首页、素材清单与健康检查。

M0 只提供骨架：清单里的 ``assets`` 一律为空，真正的目录扫描在 M1 接上。
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from . import __version__
from .models import ACTIVE, default_recipe

BASE_DIR = Path(__file__).parent

app = FastAPI(title="diyface", version=__version__)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def build_manifest() -> dict:
    """输出素材清单骨架。

    M1 会把 ``assets`` 换成扫描 ``assets/`` 目录得到的真实列表；
    在此之前保留空数组，让前端可以先按槽位渲染类目。
    """
    return {
        "schema": 1,
        "slots": [
            {
                "id": slot.id.value,
                "z": slot.z,
                "tintable": slot.tintable,
                "default_color": slot.default_color,
                "assets": [],
            }
            for slot in ACTIVE
        ],
    }


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    manifest = build_manifest()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "title": "DIY 头像生成器",
            "slots": manifest["slots"],
            "version": __version__,
        },
    )


@app.get("/api/manifest")
def api_manifest() -> dict:
    return build_manifest()


@app.get("/api/recipe/default")
def api_default_recipe() -> dict:
    return default_recipe().model_dump(mode="json")


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "version": __version__, "slots": len(ACTIVE)}
