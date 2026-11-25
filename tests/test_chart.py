"""图纸识别的测试：网格检测、切格、图案聚类。"""

from __future__ import annotations

from PIL import Image, ImageDraw

from diyface.chart import cluster_cells, detect_grid, extract_cells

COLS, ROWS = 20, 16
LEFT, TOP, CW, CH = 12, 12, 18, 18


def make_chart(with_text: bool = True) -> Image.Image:
    image = Image.new("RGB", (COLS * CW + 40, ROWS * CH + 40), "white")
    draw = ImageDraw.Draw(image)
    for col in range(COLS + 1):
        x = LEFT + col * CW
        draw.line((x, TOP, x, TOP + ROWS * CH), fill="#333")
    for row in range(ROWS + 1):
        y = TOP + row * CH
        draw.line((LEFT, y, LEFT + COLS * CW, y), fill="#333")
    if with_text:
        for row in range(4):
            for col in range(4):
                label = "H2" if (row + col) % 2 == 0 else "H7"
                draw.text((LEFT + col * CW + 3, TOP + row * CH + 5), label, fill="black")
    return image


def test_detects_grid_size() -> None:
    grid = detect_grid(make_chart(with_text=False))

    assert grid is not None
    assert (grid.cols, grid.rows) == (COLS, ROWS)


def test_returns_none_without_lines() -> None:
    assert detect_grid(Image.new("RGB", (200, 200), "white")) is None


def test_extract_cells_matches_grid() -> None:
    grid = detect_grid(make_chart(with_text=False))
    assert grid is not None

    cells = extract_cells(make_chart(with_text=False), grid)

    assert len(cells) == grid.rows
    assert len(cells[0]) == grid.cols


def test_clusters_separate_empty_and_text() -> None:
    grid = detect_grid(make_chart())
    assert grid is not None

    clusters = cluster_cells(extract_cells(make_chart(), grid))

    assert len(clusters) >= 2, "空白格与带文字的格应当分开"
    assert clusters[0]["count"] > max(cluster["count"] for cluster in clusters[1:])
    assert all(cluster["preview"] for cluster in clusters)


def test_cluster_cells_are_unique_positions() -> None:
    grid = detect_grid(make_chart())
    assert grid is not None

    clusters = cluster_cells(extract_cells(make_chart(), grid))
    positions = [tuple(cell) for cluster in clusters for cell in cluster["cells"]]

    assert len(positions) == len(set(positions))
    assert len(positions) == grid.rows * grid.cols
