"""启动开发/演示服务：监听所有网卡，并打印可访问的地址。

    python scripts/serve.py            # 默认 8000 端口
    python scripts/serve.py --port 8123
    python scripts/serve.py --tunnel   # 额外提示如何开公网隧道
"""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def local_ips() -> list[str]:
    """拿到本机所有 IPv4，过滤掉回环与明显是虚拟网卡的地址。"""
    ips: list[str] = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip.startswith("127.") or ip.startswith("169.254."):
                continue
            if ip not in ips:
                ips.append(ip)
    except OSError:
        pass
    return ips


def main() -> int:
    parser = argparse.ArgumentParser(description="启动 diyface 服务")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--tunnel", action="store_true", help="打印公网隧道提示")
    args = parser.parse_args()

    from diyface.app import app  # noqa: PLC0415

    print(f"本机：   http://127.0.0.1:{args.port}")
    for ip in local_ips():
        print(f"局域网： http://{ip}:{args.port}")
    if args.tunnel:
        print()
        print("公网（任选一种，需在另一窗口执行）：")
        print("  cloudflared tunnel --url http://127.0.0.1:%d" % args.port)
        print("  ssh -R 80:localhost:%d nokey@localhost.run" % args.port)

    app.run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
