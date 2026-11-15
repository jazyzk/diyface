"""测试公共装置。

提供：
* ``workdir``：干净的临时目录，测试结束即删除；
* ``client``：Flask 测试客户端；
* ``--update-golden``：重建渲染快照基准。
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from diyface.app import app
from tests.helpers import TMP_ROOT


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="按当前素材重新生成 tests/fixtures/golden 下的快照基准",
    )


@pytest.fixture
def update_golden(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--update-golden"))


@pytest.fixture
def client():
    """Flask 测试客户端。"""
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def workdir() -> Iterator[Path]:
    """干净的临时目录，测试结束即删除。"""
    shutil.rmtree(TMP_ROOT, ignore_errors=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        yield TMP_ROOT
    finally:
        shutil.rmtree(TMP_ROOT, ignore_errors=True)
