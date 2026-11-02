"""M1 接口的冒烟测试（直接调用路由函数，不经过 HTTP）。

端到端行为（状态码、响应头、304、错误结构）在 test_api.py 里测。
"""

from __future__ import annotations

import pytest

from diyface import __version__
from diyface.app import api_default_recipe, api_manifest, app, healthz, index
from diyface.models import ACTIVE, SLOTS


def test_app_exposes_expected_routes() -> None:
    paths = {route.path for route in app.routes}
    assert {"/", "/api/manifest", "/api/render", "/api/recipe/default", "/healthz"} <= paths


def test_manifest_lists_only_slots_that_have_assets() -> None:
    data = api_manifest()

    ids = [slot["id"] for slot in data["slots"]]
    z_values = [slot["z"] for slot in data["slots"]]

    assert data["schema"] == 1
    assert z_values == sorted(z_values), "清单必须按 z 升序"
    assert set(ids) <= {slot.id.value for slot in ACTIVE}
    assert ids == ["skin", "bangs", "eyes"], "当前仓库里只有这三个槽位有素材"
    for slot in data["slots"]:
        assert slot["assets"], "既然出现在清单里，就必须至少有一个素材"
        assert set(slot["assets"][0]) == {"id", "file"}


def test_manifest_carries_default_recipe() -> None:
    recipe = api_manifest()["default_recipe"]

    assert len(recipe["slots"]) == len(SLOTS) == 12
    assert recipe["slots"]["skin"] == "skin_base"
    assert recipe["colors"]["bangs"] == "#3B2B23"


def test_default_recipe_endpoint_picks_first_asset() -> None:
    data = api_default_recipe()

    assert data["slots"]["skin"] == "skin_base"
    assert data["slots"]["bangs"] == "bangs_straight_01"
    assert data["slots"]["mouth"] is None, "没有素材的槽位保持为空"


def test_healthz_reports_counts() -> None:
    data = healthz()

    assert data["ok"] is True
    assert data["version"] == __version__
    assert data["slots"] == 3
    assert data["assets"] == 3


def test_index_renders_page_with_slot_list(fake_request) -> None:
    response = index(fake_request)
    body = response.body.decode("utf-8")

    assert response.status_code == 200
    assert "DIY 头像生成器" in body
    assert "/static/style.css" in body
    for slot_id in ("skin", "bangs", "eyes"):
        assert slot_id in body


@pytest.mark.parametrize("path", ["/", "/api/manifest", "/healthz"])
def test_routes_are_registered_as_get(path: str) -> None:
    methods = {
        method
        for route in app.routes
        if getattr(route, "path", None) == path
        for method in getattr(route, "methods", set())
    }
    assert "GET" in methods
