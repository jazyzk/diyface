"""接口冒烟测试：路由存在、清单结构、默认配方、健康检查。

端到端行为（状态码、响应头、304、错误结构）在 test_api.py 里测。
"""

from __future__ import annotations

import pytest

from diyface import __version__
from diyface.app import ASSETS_DIR, app
from diyface.catalog import index, scan
from diyface.models import ACTIVE, SLOTS


def test_expected_routes_are_registered() -> None:
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    for path in ("/", "/api/manifest", "/api/render", "/api/random", "/healthz"):
        assert path in rules
    assert "/assets/<path:filename>" in rules


def test_manifest_lists_only_slots_that_have_assets(client) -> None:
    data = client.get("/api/manifest").get_json()

    ids = [slot["id"] for slot in data["slots"]]
    z_values = [slot["z"] for slot in data["slots"]]

    assert data["schema"] == 1
    assert z_values == sorted(z_values), "清单必须按 z 升序"
    assert set(ids) <= {slot.id.value for slot in ACTIVE}
    assert {"skin", "hair", "eyes"} <= set(ids), "至少这几个槽位必须有素材"
    for slot in data["slots"]:
        assert slot["assets"], "既然出现在清单里，就必须至少有一个素材"
        assert set(slot["assets"][0]) == {"id", "file", "thumb", "style"}
        assert slot["label"]["zh"], "每个槽位都要有中文名，前端直接显示"


def test_manifest_carries_default_recipe(client) -> None:
    recipe = client.get("/api/manifest").get_json()["default_recipe"]

    assert len(recipe["slots"]) == len(SLOTS) == 10
    assert recipe["slots"]["skin"] == "skin_base"
    assert recipe["colors"]["hair"] == "#2B1B12"


def test_default_recipe_endpoint_picks_first_asset(client) -> None:
    data = client.get("/api/recipe/default").get_json()

    assert data["slots"]["skin"] == "skin_base"
    assert data["slots"]["hair"] == "hair_straight_01"
    assert data["slots"]["hat"] is None, "本期不做帽子"
    assert data["slots"]["glasses"] is None, "眼镜是配饰，默认不戴"


def test_healthz_reports_counts(client) -> None:
    data = client.get("/healthz").get_json()
    catalog = scan(ASSETS_DIR)

    assert data["ok"] is True
    assert data["version"] == __version__
    assert data["slots"] == len(catalog)
    assert data["assets"] == sum(len(assets) for assets in catalog.values())


def test_index_renders_page_with_slot_list(client) -> None:
    response = client.get("/")
    body = response.data.decode("utf-8")

    assert response.status_code == 200
    assert "DIY 头像生成器" in body
    assert "/static/style.css" in body
    for slot_id in ("skin", "hair", "eyes"):
        assert slot_id in body


@pytest.mark.parametrize("path", ["/", "/api/manifest", "/healthz"])
def test_get_routes_accept_get(client, path: str) -> None:
    assert client.get(path).status_code == 200


def test_default_asset_exists() -> None:
    """每个槽位声明的默认素材必须真的在目录里，否则首屏会退回「随便挑一张」。"""
    catalog = index(scan(ASSETS_DIR))

    for slot in SLOTS:
        if slot.id not in catalog:
            continue
        assert slot.default_asset, f"{slot.id} 没有声明默认素材"
        assert slot.default_asset in catalog[slot.id], f"{slot.id} 的默认素材不存在：{slot.default_asset}"
