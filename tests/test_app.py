"""M0 冒烟测试：应用能装配、页面能渲染、接口返回约定结构。"""

from __future__ import annotations

import pytest

from diyface import __version__
from diyface.app import api_default_recipe, api_manifest, app, healthz, index
from diyface.models import ACTIVE, SLOTS


def test_app_exposes_expected_routes() -> None:
    paths = {route.path for route in app.routes}
    assert {"/", "/api/manifest", "/api/recipe/default", "/healthz"} <= paths


def test_manifest_lists_only_active_slots_in_z_order() -> None:
    data = api_manifest()

    assert data["schema"] == 1
    ids = [slot["id"] for slot in data["slots"]]
    z_values = [slot["z"] for slot in data["slots"]]

    assert len(ids) == len(ACTIVE) == 8
    assert z_values == sorted(z_values), "清单必须按 z 升序"
    assert "cheeks" not in ids and "brows" not in ids, "预留槽位不应出现在清单里"
    for slot in data["slots"]:
        assert slot["assets"] == [], "M0 阶段素材列表应为空"


def test_healthz_reports_version_and_slot_count() -> None:
    data = healthz()

    assert data == {"ok": True, "version": __version__, "slots": len(ACTIVE)}


def test_default_recipe_covers_all_twelve_slots() -> None:
    data = api_default_recipe()

    assert set(data["slots"]) == {slot.id.value for slot in SLOTS}
    assert all(value is None for value in data["slots"].values())
    assert len(data["colors"]) == 8


def test_index_renders_page_with_slot_list(fake_request) -> None:
    response = index(fake_request)
    body = response.body.decode("utf-8")

    assert response.status_code == 200
    assert "DIY 头像生成器" in body
    assert "/static/style.css" in body
    for slot in ACTIVE:
        assert slot.id.value in body


@pytest.mark.parametrize("path", ["/", "/api/manifest", "/healthz"])
def test_routes_are_registered_as_get(path: str) -> None:
    methods = {
        method
        for route in app.routes
        if getattr(route, "path", None) == path
        for method in getattr(route, "methods", set())
    }
    assert "GET" in methods
