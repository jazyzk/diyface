"""最小的 ASGI 测试客户端。

环境里没有 httpx 时，``starlette.testclient`` 用不了；这里直接按 ASGI 协议
发一次请求，够验证状态码、响应头与响应体，且不引入额外依赖。

注意 ``receive``：第一次请求体返回之后不能立刻给 ``http.disconnect``，
否则 ``FileResponse``（静态文件）会以为客户端已断开，一个字节都不发。
这里等到响应体结束时再返回断开信号。
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Response:
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""

    @property
    def json(self) -> Any:
        return json.loads(self.body)


def call(
    app: Any,
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    """同步调用一次 ASGI 应用，返回状态码、响应头与响应体。"""
    payload = b"" if json_body is None else json.dumps(json_body).encode("utf-8")

    raw_headers = [
        (b"host", b"testserver"),
        (b"content-type", b"application/json"),
        (b"content-length", str(len(payload)).encode()),
    ]
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode(), value.encode()))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": raw_headers,
        "client": ("testclient", 12345),
        "server": ("testserver", 80),
    }

    async def run() -> list[dict]:
        request_sent = False
        finished = asyncio.Event()
        messages: list[dict] = []

        async def receive() -> dict:
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {"type": "http.request", "body": payload, "more_body": False}
            await finished.wait()
            return {"type": "http.disconnect"}

        async def send(message: dict) -> None:
            messages.append(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                finished.set()

        await app(scope, receive, send)
        return messages

    messages = asyncio.run(run())

    status = 500
    out_headers: dict[str, str] = {}
    body = b""
    for message in messages:
        if message["type"] == "http.response.start":
            status = message["status"]
            out_headers = {
                key.decode().lower(): value.decode() for key, value in message.get("headers", [])
            }
        elif message["type"] == "http.response.body":
            body += message.get("body", b"")

    return Response(status=status, headers=out_headers, body=body)
