"""OCR 相关测试：不依赖真实 tesseract，用 monkeypatch 模拟识别。"""

from __future__ import annotations

from PIL import Image

from diyface import ocr


def test_available_is_false_or_true() -> None:
    """只是调用不应报错；没装 tesseract 时返回 False。"""
    assert isinstance(ocr.available(), bool)


def test_read_code_returns_none_without_ocr(monkeypatch) -> None:
    monkeypatch.setattr(ocr, "available", lambda: False)

    assert ocr.read_code(Image.new("L", (10, 10), "white")) is None


def test_confusion_mapping_is_applied(monkeypatch) -> None:
    """装了 pytesseract 时，才验证混淆表；没装就跳过。"""
    import pytest

    pytest.importorskip("pytesseract")

    monkeypatch.setattr(ocr, "available", lambda: True)
    monkeypatch.setattr(ocr, "_prepare", lambda cell: cell)

    import pytesseract

    monkeypatch.setattr(pytesseract, "image_to_string", lambda *a, **k: "H 2")

    assert ocr.read_code(Image.new("L", (10, 10), "white")) == "H2"


def test_vote_codes_picks_majority(monkeypatch) -> None:
    calls = iter(["H2", None, "H2", "H7"])

    monkeypatch.setattr(ocr, "read_code", lambda cell: next(calls))

    assert ocr.vote_codes([Image.new("L", (8, 8))] * 4) == "H2"


def test_vote_codes_returns_none_when_nothing_recognised(monkeypatch) -> None:
    monkeypatch.setattr(ocr, "read_code", lambda cell: None)

    assert ocr.vote_codes([Image.new("L", (8, 8))] * 3) is None


def test_chart_route_without_ocr_has_no_suggestion() -> None:
    from io import BytesIO

    from PIL import ImageDraw

    from diyface.app import app

    image = Image.new("RGB", (240, 200), "white")
    draw = ImageDraw.Draw(image)
    for col in range(9):
        x = 10 + col * 25
        draw.line((x, 10, x, 185), fill="#333")
    for row in range(8):
        y = 10 + row * 25
        draw.line((10, y, 210, y), fill="#333")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    response = app.test_client().post(
        "/api/pixel/chart",
        data={"image": (buffer, "chart.png")},
        content_type="multipart/form-data",
    )

    body = response.get_json()
    assert response.status_code == 200
    assert body["ocr"] in (True, False)
    if not body["ocr"]:
        assert all(cluster["suggestion"] is None for cluster in body["clusters"])
