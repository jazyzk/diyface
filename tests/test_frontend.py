"""前端静态契约测试。

B 的 UI 由原生 ES 模块 + CSS 实现，仓库里没有 Node/浏览器测试链。这里用
HTTP 请求验证「服务端发出去的东西」：页面骨架、内联清单、脚本与样式是否
真的可达，以及去抖 / 序号 / 持久化 / 分享这些关键行为没有被后续改动弄丢。

真正的交互（375px 无横向滚动、连点 10 次显示最后一张）留给联调日的
浏览器手测，这里守住不会随 CI 环境变化的静态底线。
"""

from __future__ import annotations

import json
import re

from diyface.app import app
from tests import http_client

MANIFEST_SCRIPT = re.compile(
    r'<script type="application/json" id="manifest-data">(.*?)</script>',
    re.DOTALL,
)


def test_index_page_ships_three_column_ui() -> None:
    response = http_client.call(app, "GET", "/")

    assert response.status == 200
    body = response.body.decode("utf-8")
    for token in (
        'class="layout"',
        'id="categories"',
        'id="assets"',
        'id="preview"',
        'id="color"',
        'id="random"',
        'id="share"',
        'data-size="256"',
        'data-size="1024"',
        'alt="头像预览"',
        'href="/static/style.css"',
        'src="/static/app.js"',
    ):
        assert token in body, f"首页缺少前端契约元素：{token}"


def test_index_inlines_manifest_that_matches_api() -> None:
    page = http_client.call(app, "GET", "/").body.decode("utf-8")
    match = MANIFEST_SCRIPT.search(page)

    assert match, "首页应内联 #manifest-data，避免首屏再请求一次清单"
    inline = json.loads(match.group(1))
    api = http_client.call(app, "GET", "/api/manifest").json

    assert inline == api
    assert inline["schema"] == 1
    ids = [slot["id"] for slot in inline["slots"]]
    assert {"skin", "hair", "eyes"} <= set(ids)
    assert [slot["z"] for slot in inline["slots"]] == sorted(slot["z"] for slot in inline["slots"])
    assert inline["default_recipe"]["slots"]["skin"] == "skin_base"


def test_index_manifest_does_not_break_out_of_script_tag() -> None:
    page = http_client.call(app, "GET", "/").body.decode("utf-8")
    match = MANIFEST_SCRIPT.search(page)

    assert match
    assert "</script" not in match.group(1), "内联 JSON 必须安全转义，不能提前闭合脚本标签"


def test_index_has_noscript_fallback() -> None:
    body = http_client.call(app, "GET", "/").body.decode("utf-8")

    assert "<noscript>" in body
    assert "交互需要启用 JavaScript" in body
    assert "脸型" in body and "前发" in body and "眼睛" in body


def test_app_js_is_served_and_keeps_core_interactions() -> None:
    response = http_client.call(app, "GET", "/static/app.js")

    assert response.status == 200
    assert "javascript" in response.headers["content-type"]
    source = response.body.decode("utf-8")

    for token in (
        "setTimeout",
        "clearTimeout",
        "AbortController",
        "state.seq",
        "localStorage",
        "encodeRecipe",
        "decodeRecipe",
        "navigator.clipboard",
        "describeError",
        "aria-pressed",
        "/api/render",
        "/api/random",
        'document.addEventListener("keydown"',
    ):
        assert token in source, f"app.js 缺少关键实现：{token}"

    assert source.count("addEventListener") >= 8, "素材、类目、取色、按钮都应绑定事件"


def test_style_css_is_served_and_responsive() -> None:
    response = http_client.call(app, "GET", "/static/style.css")

    assert response.status == 200
    assert "text/css" in response.headers["content-type"]
    css = response.body.decode("utf-8")

    assert "grid-template-columns: 280px minmax(0, 1fr) 240px" in css
    assert "@media (max-width: 960px)" in css
    assert "@media (max-width: 480px)" in css
    assert "min-height: 44px" in css, "触控目标至少 44px"
    assert "aspect-ratio: 1 / 1" in css, "预览容器必须严格 1:1"
    assert ":focus-visible" in css, "键盘焦点必须有可见样式"


def test_static_files_are_utf8() -> None:
    for path in ("/static/app.js", "/static/style.css"):
        response = http_client.call(app, "GET", path)
        response.body.decode("utf-8")
