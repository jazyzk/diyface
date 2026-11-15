"""薄薄一层测试客户端封装。

用 Flask 自带的 test_client，包成「状态码 + 响应头 + 响应体」的小对象，
让测试读起来和真实 HTTP 请求一致。
"""

from __future__ import annotations

import json as jsonlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Response:
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""

    @property
    def json(self) -> Any:
        return jsonlib.loads(self.body)


def call(
    app: Any,
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    """对 Flask 应用发一次请求。"""
    client = app.test_client()
    response = client.open(path, method=method.upper(), json=json_body, headers=headers or {})
    return Response(
        status=response.status_code,
        headers={key.lower(): value for key, value in response.headers.items()},
        body=response.data,
    )
