"""图片导入拼豆网格的测试。"""

from __future__ import annotations

from io import BytesIO

from PIL import Image

from diyface.app import app
from diyface.mard import HEXES
from diyface.pixel import decode, encode
from diyface.pixel_import import GRID, quantize, used_colors


def make_image(size: int, blocks: list[tuple[int, int, int, int]]) -> Image.Image:
    """按 2×2 色块画一张图，方便断言四个象限。"""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    half = size // 2
    for index, color in enumerate(blocks):
        left = 0 if index % 2 == 0 else half
        top = 0 if index < 2 else half
        image.paste(color, (left, top, left + half, top + half))
    return image


def test_exact_grid_keeps_colors() -> None:
    red = (213, 0, 0, 255)
    image = make_image(32, [red, red, red, red])

    cells = quantize(image)

    assert len(cells) == GRID * GRID
    assert len(set(cells)) == 1, "同一颜色应当映射到同一个色号"
    assert cells[0] >= 0


def test_transparent_pixels_become_empty() -> None:
    image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))

    cells = quantize(image)

    assert set(cells) == {-1}


def test_white_background_becomes_empty() -> None:
    image = Image.new("RGBA", (32, 32), (255, 255, 255, 255))

    cells = quantize(image)

    assert set(cells) == {-1}, "纯白照片底色不应全部变成 H2"


def test_large_photo_is_downscaled() -> None:
    image = make_image(
        256,
        [(255, 0, 0, 255), (0, 128, 255, 255), (255, 255, 0, 255), (0, 200, 0, 255)],
    )

    cells = quantize(image)

    assert len(cells) == GRID * GRID
    assert all(0 <= cell < len(HEXES) for cell in cells)
    assert used_colors(cells) >= 3, "四种明显不同的颜色至少要区分出三种"


def test_roundtrip_through_rle() -> None:
    image = make_image(32, [(10, 20, 30, 255)] * 4)

    cells = quantize(image)

    assert decode(encode(cells)) == cells


def test_api_rejects_missing_file() -> None:
    client = app.test_client()

    response = client.post("/api/pixel/import", data={}, content_type="multipart/form-data")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "INVALID_REQUEST"


def test_api_rejects_garbage_bytes() -> None:
    client = app.test_client()

    response = client.post(
        "/api/pixel/import",
        data={"image": (BytesIO(b"not an image"), "x.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 422


def test_api_returns_canvas() -> None:
    client = app.test_client()
    buffer = BytesIO()
    make_image(64, [(255, 0, 0, 255)] * 4).save(buffer, format="PNG")
    buffer.seek(0)

    response = client.post(
        "/api/pixel/import",
        data={"image": (buffer, "beads.png")},
        content_type="multipart/form-data",
    )

    body = response.get_json()
    assert response.status_code == 200
    assert body["size"] == 32
    assert len(body["palette"]) == 64
    assert decode(body["pixels"]), "返回的 RLE 必须能解回 1024 格"
