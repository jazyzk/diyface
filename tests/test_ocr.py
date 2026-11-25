"""OCR 测试：不依赖真实 tesseract，用 monkeypatch 模拟识别结果。"""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

from diyface import ocr


def test_available_reports_bool() -> None:
    assert isinstance(ocr.available(), bool)


def test_normalise_accepts_known_code() -> None:
    assert ocr.normalise("H2") == "H2"
    assert ocr.normalise(" e15 ") == "E15"


def test_normalise_rejects_garbage() -> None:
    assert ocr.normalise("") is None
    assert ocr.normalise("###") is None
    assert ocr.normalise("NOTACODE") is None


def test_read_code_without_engine_returns_none(monkeypatch) -> None:
    monkeypatch.setattr(ocr, "available", lambda: False)

    assert ocr.read_code(Image.new("L", (10, 10), "white")) is None


def test_read_code_uses_engine_output(monkeypatch) -> None:
    monkeypatch.setattr(ocr, "available", lambda: True)
    monkeypatch.setattr(ocr, "_run_tesseract", lambda cell: "H2\n")

    assert ocr.read_code(Image.new("L", (10, 10), "white")) == "H2"


def test_vote_codes_picks_majority(monkeypatch) -> None:
    calls = iter(["H2", None, "H2", "H7"])
    monkeypatch.setattr(ocr, "read_code", lambda cell: next(calls))

    assert ocr.vote_codes([Image.new("L", (8, 8))] * 4) == "H2"


def test_vote_codes_returns_none_when_nothing_recognised(monkeypatch) -> None:
    monkeypatch.setattr(ocr, "read_code", lambda cell: None)

    assert ocr.vote_codes([Image.new("L", (8, 8))] * 3) is None


def _grid_image() -> BytesIO:
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
    return buffer


def test_chart_route_reports_ocr_flag() -> None:
    from diyface.app import app

    response = app.test_client().post(
        "/api/pixel/chart",
        data={"image": (_grid_image(), "chart.png")},
        content_type="multipart/form-data",
    )

    body = response.get_json()
    assert response.status_code == 200
    assert body["ocr"] in (True, False)
    assert all("suggestion" in cluster for cluster in body["clusters"])


def test_chart_route_uses_suggestions_when_engine_available(monkeypatch) -> None:
    from diyface import app as app_module

    monkeypatch.setattr(app_module, "ocr_available", lambda: True)
    monkeypatch.setattr(app_module, "vote_codes", lambda cells: "H2")

    response = app_module.app.test_client().post(
        "/api/pixel/chart",
        data={"image": (_grid_image(), "chart.png")},
        content_type="multipart/form-data",
    )

    body = response.get_json()
    assert body["ocr"] is True
    assert any(cluster["suggestion"] == "H2" for cluster in body["clusters"])
