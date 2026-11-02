"""测试公共装置。

提供两类夹具：
* ``fake_request``：模板渲染测试用的最小 Request；
* ``workdir``：干净的临时目录，测试结束即删除。
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from starlette.requests import Request

from diyface.app import app
from tests.helpers import TMP_ROOT


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


@pytest.fixture
def workdir() -> Iterator[Path]:
    """干净的临时目录，测试结束即删除。"""
    shutil.rmtree(TMP_ROOT, ignore_errors=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        yield TMP_ROOT
    finally:
        shutil.rmtree(TMP_ROOT, ignore_errors=True)
