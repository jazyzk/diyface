"""测试公共装置。

M0 不需要真实素材：所有测试直接调用路由函数或模型，等 M1 引入渲染管线后，
再在这里补 ``fake_assets``（临时目录 + 占位 PNG）供渲染测试使用。
"""

from __future__ import annotations

import pytest
from starlette.requests import Request

from diyface.app import app


@pytest.fixture
def fake_request() -> Request:
    """最小可用的 Request，供模板渲染测试使用。"""
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "app": app,
        }
    )
