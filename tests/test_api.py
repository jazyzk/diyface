"""接口的端到端测试（走 ASGI，不依赖 httpx）。

用 tests/http_client.py 直接发请求，覆盖状态码、响应头、响应体与错误结构。
"""

from __future__ import annotations

import pytest

from diyface.app import app
from diyface.models import SLOTS
from tests import http_client

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def recipe_payload(**overrides: str | None) -> dict:
    slots: dict[str, str | None] = {slot.id.value: None for slot in SLOTS}
    slots.update({"skin": "skin_base", "bangs": "bangs_straight_01", "eyes": "eyes_round_01"})
    slots.update(overrides)
    return {
        "version": 1,
        "slots": slots,
        "colors": {"skin": "#F2D5B8", "bangs": "#3B2B23"},
    }


def render(**kwargs):
    body = {"recipe": recipe_payload(**kwargs.pop("slots", {})), "size": 256}
    body.update(kwargs)
    return http_client.call(app, "POST", "/api/render", json_body=body)


def test_manifest_over_http() -> None:
    response = http_client.call(app, "GET", "/api/manifest")

    assert response.status == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json["schema"] == 1
    assert response.json["default_recipe"]["slots"]["skin"] == "skin_base"


def test_render_returns_png_with_etag() -> None:
    response = render()

    assert response.status == 200
    assert response.headers["content-type"] == "image/png"
    assert response.body.startswith(PNG_MAGIC)
    assert response.headers["etag"].startswith('"')
    assert "max-age" in response.headers["cache-control"]


def test_render_returns_304_when_etag_matches() -> None:
    first = render()
    etag = first.headers["etag"]

    second = http_client.call(
        app,
        "POST",
        "/api/render",
        json_body={"recipe": recipe_payload(), "size": 256},
        headers={"If-None-Match": etag},
    )

    assert second.status == 304
    assert second.body == b""


def test_render_rejects_bad_size() -> None:
    response = render(size=512)

    assert response.status == 422
    assert response.json["error"]["code"] == "BAD_SIZE"


def test_render_reports_unknown_asset() -> None:
    response = render(slots={"bangs": "bangs_not_exist"})

    assert response.status == 422
    assert response.json["error"]["code"] == "UNKNOWN_ASSET"
    assert "bangs" in response.json["error"]["message"]


def test_render_rejects_unknown_field() -> None:
    body = {"recipe": {**recipe_payload(), "extra": 1}, "size": 256}

    response = http_client.call(app, "POST", "/api/render", json_body=body)

    assert response.status == 422
    assert response.json["error"]["code"] == "INVALID_REQUEST"


def test_healthz_over_http() -> None:
    response = http_client.call(app, "GET", "/healthz")

    assert response.status == 200
    assert response.json["ok"] is True
    assert response.json["assets"] == 3


def test_static_asset_is_served() -> None:
    response = http_client.call(app, "GET", "/assets/02_bangs/bangs_straight_01.png")

    assert response.status == 200
    assert response.headers["content-type"] == "image/png"
    assert response.body.startswith(PNG_MAGIC)


def test_index_page_over_http() -> None:
    response = http_client.call(app, "GET", "/")

    assert response.status == 200
    assert "text/html" in response.headers["content-type"]
    assert "DIY 头像生成器" in response.body.decode("utf-8")


@pytest.mark.parametrize("size", [256, 1024])
def test_render_supports_both_sizes(size: int) -> None:
    response = render(size=size)

    assert response.status == 200
    assert response.body.startswith(PNG_MAGIC)


def test_random_returns_recipe_for_all_slots() -> None:
    response = http_client.call(app, "POST", "/api/random", json_body={})

    assert response.status == 200
    data = response.json
    assert len(data["slots"]) == len(SLOTS) == 12
    assert data["seed"] is not None


def test_random_is_reproducible_with_seed() -> None:
    first = http_client.call(app, "POST", "/api/random", json_body={"seed": 1234}).json
    second = http_client.call(app, "POST", "/api/random", json_body={"seed": 1234}).json

    assert first == second


def test_random_recipe_can_be_rendered() -> None:
    recipe = http_client.call(app, "POST", "/api/random", json_body={"seed": 7}).json

    response = http_client.call(app, "POST", "/api/render", json_body={"recipe": recipe, "size": 256})

    assert response.status == 200
    assert response.body.startswith(PNG_MAGIC)
