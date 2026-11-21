"""部署相关文件的测试：保证「一条命令能跑起来」的承诺不落空。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_render_blueprint_starts_app_on_injected_port() -> None:
    text = (ROOT / "render.yaml").read_text(encoding="utf-8")

    assert "diyface.app:app" in text
    assert "$PORT" in text, "云平台会注入端口，必须用它"
    assert "/healthz" in text, "健康检查路径要和接口一致"


def test_dockerfile_uses_wsgi_server() -> None:
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "waitress-serve" in text
    assert "diyface.app:app" in text
    assert "EXPOSE 8000" in text


def test_assets_dir_can_be_overridden(tmp_path, monkeypatch) -> None:
    """装进 site-packages 后要靠环境变量找到 assets，否则部署后 404。"""
    from diyface import app as app_module

    monkeypatch.setenv("DIYFACE_ASSETS", str(tmp_path))
    assert app_module._resolve_assets() == tmp_path


def test_serve_script_prints_lan_addresses() -> None:
    text = (ROOT / "scripts" / "serve.py").read_text(encoding="utf-8")

    assert "0.0.0.0" in text, "默认要监听所有网卡，否则别人连不上"
    assert "local_ips" in text
    assert "--tunnel" in text


def test_deploy_doc_covers_three_routes() -> None:
    text = (ROOT / "docs" / "DEPLOY.md").read_text(encoding="utf-8")

    for token in ("Render", "cloudflared", "waitress", "healthz"):
        assert token in text, f"部署文档缺少：{token}"
