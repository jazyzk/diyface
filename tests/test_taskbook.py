"""任务书 DOCX 的结构校验。

只有安装了 python-docx 的解释器才会执行（未安装则整体跳过），
因此既能在系统 Python 下跑通，也能在带依赖的运行时下做完整校验。

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
import zipfile
from pathlib import Path

try:
    import docx  # type: ignore[import-not-found]
    from docx.shared import Cm
except ImportError:  # pragma: no cover - 取决于运行环境
    docx = None

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs" / "DIY头像生成器-实验任务书.docx"

#: 任务书必备的一级标题（子串匹配，允许带编号）。
REQUIRED_H1 = (
    "实验介绍",
    "系统设计",
    "系统实现",
    "效果展示",
    "总结与思考",
    "附录 A",
    "附录 B",
    "附录 C",
)

#: 任务书必备的关键小节，确保内容没有缩水。
REQUIRED_TOPICS = (
    "实验目的",
    "实验环境",
    "总体结构",
    "数据结构设计",
    "接口设计",
    "界面设计",
    "模块划分",
    "分层渲染",
    "颜色映射",
    "测试与质量门禁",
    "验收测试",
    "评分参考",
)

PLACEHOLDER_MARKERS = ("TODO", "FIXME", "XXX", "待补")


@unittest.skipUnless(docx is not None, "未安装 python-docx，跳过 DOCX 校验")
class TestTaskbook(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not DOCX.is_file():
            raise AssertionError(f"任务书不存在：{DOCX}（先运行 scripts/build_taskbook.py）")
        cls.doc = docx.Document(str(DOCX))
        cls.headings = [
            (p.style.name, p.text.strip())
            for p in cls.doc.paragraphs
            if p.style.name.startswith("Heading")
        ]
        cls.all_text = "\n".join(p.text for p in cls.doc.paragraphs)
        for table in cls.doc.tables:
            for row in table.rows:
                cls.all_text += "\n" + "\n".join(cell.text for cell in row.cells)

    def test_file_size_is_reasonable(self) -> None:
        size = DOCX.stat().st_size
        self.assertGreater(size, 30_000, f"文件仅 {size} 字节，疑似内容缺失")

    def test_required_h1_present(self) -> None:
        h1 = [text for style, text in self.headings if style == "Heading 1"]
        joined = "\n".join(h1)
        missing = [name for name in REQUIRED_H1 if name not in joined]
        self.assertEqual(missing, [], f"缺少一级标题：{missing}")

    def test_section_hierarchy_is_deep_enough(self) -> None:
        levels = [style for style, _ in self.headings]
        self.assertGreaterEqual(levels.count("Heading 1"), 8, "一级标题数量不足")
        self.assertGreaterEqual(levels.count("Heading 2"), 20, "二级标题数量不足")
        self.assertGreaterEqual(levels.count("Heading 3"), 4, "三级标题数量不足")

    def test_required_topics_covered(self) -> None:
        missing = [topic for topic in REQUIRED_TOPICS if topic not in self.all_text]
        self.assertEqual(missing, [], f"任务书缺少主题：{missing}")

    def test_has_enough_tables_and_captions(self) -> None:
        self.assertGreaterEqual(len(self.doc.tables), 18, "表格数量不足（应含代码框与数据表）")
        captions = [p for p in self.doc.paragraphs if p.text.strip().startswith("表 ")]
        self.assertGreaterEqual(len(captions), 15, "表题数量不足")

    def test_code_blocks_use_monospace(self) -> None:
        mono = 0
        for table in self.doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if paragraph.runs and paragraph.runs[0].font.name == "Consolas":
                            mono += 1
        self.assertGreaterEqual(mono, 10, "代码框数量不足或未使用等宽字体")

    def test_table_widths_fit_page(self) -> None:
        usable = Cm(14.64)
        for index, table in enumerate(self.doc.tables, start=1):
            widths = [column.width for column in table.columns]
            if any(width is None for width in widths):
                continue
            total = sum(widths, Cm(0))
            self.assertLessEqual(total, usable + Cm(0.1), f"第 {index} 张表超出页面宽度")

    def test_header_and_footer(self) -> None:
        section = self.doc.sections[0]
        header = section.header.paragraphs[0].text
        for token in ("Python 程序设计", "实验任务书", "DIY 头像生成器"):
            self.assertIn(token, header)
        self.assertTrue(section.footer.paragraphs[0].text.strip(), "页脚缺少内容")

    def test_toc_field_is_present(self) -> None:
        with zipfile.ZipFile(DOCX) as package:
            xml = package.read("word/document.xml").decode("utf-8")
        self.assertIn("TOC", xml, "缺少目录域，用户无法一键生成目录")

    def test_no_placeholder_markers(self) -> None:
        hits = [marker for marker in PLACEHOLDER_MARKERS if marker in self.all_text]
        self.assertEqual(hits, [], f"存在未清理的占位标记：{hits}")

    def test_key_numbers_match_plan(self) -> None:
        """任务书里的关键数字必须与 PLAN 一致，避免两处说法打架。"""
        for token in ("43 张", "8 个", "256", "1024", "6 人"):
            self.assertIn(token, self.all_text, f"缺少关键数字：{token}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
