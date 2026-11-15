"""生成《DIY 头像生成器 —— 实验任务书》.docx。

用 python-docx 直接构建，结构对标参考实验案例：
    1 实验介绍 → 2 系统设计 → 3 系统实现 → 4 效果展示与验收 → 5 总结与思考 → 附录

运行（使用自带 python-docx 的运行时）：
    python scripts/build_taskbook.py
产物：
    docs/DIY头像生成器-实验任务书.docx
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "DIY头像生成器-实验任务书.docx"

SONG = "宋体"
HEI = "黑体"
MONO = "Consolas"
LATIN = "Times New Roman"

PAGE_WIDTH_CM = 21.0
MARGIN_LR_CM = 3.18
USABLE_CM = PAGE_WIDTH_CM - 2 * MARGIN_LR_CM

# 参考文档的字体尺度：小四正文、三号一级标题、四号二级标题、五号图表题注
BODY_PT = 12
H1_PT, H2_PT, H3_PT = 16, 14, 12
CAPTION_PT = 10.5
CODE_PT = 9


# --------------------------------------------------------------------------- #
# 基础排版工具
# --------------------------------------------------------------------------- #
def set_run_font(run, latin: str, eastasia: str, size: float, bold: bool = False) -> None:
    run.font.name = latin
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), latin)
    rfonts.set(qn("w:hAnsi"), latin)
    rfonts.set(qn("w:eastAsia"), eastasia)


def style_font(style, latin: str, eastasia: str, size: float, bold: bool = False) -> None:
    style.font.name = latin
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), latin)
    rfonts.set(qn("w:eastAsia"), eastasia)


def shade_cell(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def table_borders(table, color: str = "BFBFBF", size: int = 4) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tbl_pr.append(borders)


def cell_margins(table, top: int = 40, bottom: int = 40, left: int = 80, right: int = 80) -> None:
    tbl_pr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for edge, value in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(value))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tbl_pr.append(mar)


def add_field(paragraph, instruction: str, placeholder: str = "") -> None:
    """插入域代码（PAGE / NUMPAGES / TOC）。"""
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = placeholder
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, separate, text, end):
        run._r.append(el)


# --------------------------------------------------------------------------- #
# 文档级设置
# --------------------------------------------------------------------------- #
def build_document() -> Document:
    doc = Document()

    section = doc.sections[0]
    section.page_width = Cm(PAGE_WIDTH_CM)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(MARGIN_LR_CM)
    section.right_margin = Cm(MARGIN_LR_CM)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.5)

    normal = doc.styles["Normal"]
    style_font(normal, LATIN, SONG, BODY_PT)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)

    for level, size, before, after in ((1, H1_PT, 18, 8), (2, H2_PT, 12, 6), (3, H3_PT, 10, 4)):
        style = doc.styles[f"Heading {level}"]
        style_font(style, LATIN, HEI, size, bold=True)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.line_spacing = 1.3
        style.paragraph_format.keep_with_next = True

    add_header(section)
    add_footer(section)
    return doc


def add_header(section) -> None:
    paragraph = section.header.paragraphs[0]
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        Cm(USABLE_CM / 2), WD_TAB_ALIGNMENT.CENTER
    )
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        Cm(USABLE_CM), WD_TAB_ALIGNMENT.RIGHT
    )
    for text in ("Python 程序设计", "\t实验任务书", "\tDIY 头像生成器"):
        set_run_font(paragraph.add_run(text), LATIN, SONG, 9)

    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "808080")
    p_bdr.append(bottom)
    p_pr.append(p_bdr)


def add_footer(section) -> None:
    paragraph = section.footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(paragraph.add_run("第 "), LATIN, SONG, 9)
    add_field(paragraph, "PAGE", "1")
    set_run_font(paragraph.add_run(" 页 / 共 "), LATIN, SONG, 9)
    add_field(paragraph, "NUMPAGES", "1")
    set_run_font(paragraph.add_run(" 页"), LATIN, SONG, 9)


# --------------------------------------------------------------------------- #
# 内容构件
# --------------------------------------------------------------------------- #
def h(doc: Document, level: int, text: str):
    paragraph = doc.add_heading(text, level=level)
    for run in paragraph.runs:
        set_run_font(run, LATIN, HEI, {1: H1_PT, 2: H2_PT, 3: H3_PT}[level], bold=True)
    return paragraph


def body(doc: Document, text: str, indent: bool = True, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    paragraph = doc.add_paragraph()
    paragraph.alignment = align
    paragraph.paragraph_format.line_spacing = 1.5
    if indent:
        paragraph.paragraph_format.first_line_indent = Pt(BODY_PT * 2)
    set_run_font(paragraph.add_run(text), LATIN, SONG, BODY_PT)
    return paragraph


def rich(doc: Document, parts: list[tuple[str, bool]]):
    """parts: (文本, 是否加粗)；用于「字段名：说明」这类混排段落。"""
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.first_line_indent = Pt(BODY_PT * 2)
    for text, bold in parts:
        set_run_font(paragraph.add_run(text), LATIN, SONG, BODY_PT, bold=bold)
    return paragraph


def bullet(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.left_indent = Cm(0.74)
    set_run_font(paragraph.add_run(text), LATIN, SONG, BODY_PT)


def numbered(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph(style="List Number")
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.left_indent = Cm(0.74)
    set_run_font(paragraph.add_run(text), LATIN, SONG, BODY_PT)


def caption(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(9)
    set_run_font(paragraph.add_run(text), LATIN, SONG, CAPTION_PT)


def code_block(doc: Document, code: str, lang: str = "") -> None:
    """代码置灰框：1×1 表格 + 等宽字体，视觉上贴近参考文档的方框代码。"""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Cm(USABLE_CM)
    table_borders(table, color="A6A6A6", size=4)
    cell_margins(table, top=60, bottom=60, left=120, right=120)
    cell = table.cell(0, 0)
    cell.width = Cm(USABLE_CM)
    shade_cell(cell, "F7F7F7")

    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.line_spacing = 1.1
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    for index, line in enumerate(code.rstrip("\n").split("\n")):
        if index:
            paragraph.add_run().add_break()
        set_run_font(paragraph.add_run(line if line else " "), MONO, MONO, CODE_PT)

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(6)
    spacer.paragraph_format.line_spacing = 1.0


def cell_borders(cell, color: str = "A6A6A6", size: int = 6) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tc_pr.append(borders)


def box_diagram(doc: Document, blocks: list[tuple[str, str]], cap: str) -> None:
    """层叠结构图：用单元格画方框，比 ASCII 图在 Word 里稳定（中文不会错位）。"""
    table = doc.add_table(rows=0, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Cm(USABLE_CM)
    cell_margins(table, top=60, bottom=60, left=120, right=120)

    for kind, text in blocks:
        cell = table.add_row().cells[0]
        cell.width = Cm(USABLE_CM)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.line_spacing = 1.2
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(0)
        if kind == "box":
            shade_cell(cell, "F2F2F2")
            cell_borders(cell)
            set_run_font(paragraph.add_run(text), LATIN, HEI, 10, bold=True)
        else:
            set_run_font(paragraph.add_run(text), LATIN, SONG, 9)

    caption(doc, cap)


def data_table(doc: Document, header: list[str], rows: list[list[str]], cap: str, widths=None) -> None:
    caption(doc, cap)
    table = doc.add_table(rows=1, cols=len(header))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table_borders(table)
    cell_margins(table)

    if widths is None:
        widths = [USABLE_CM / len(header)] * len(header)
    total = sum(widths)
    if total > USABLE_CM + 0.01:
        raise ValueError(f"{cap} 列宽合计 {total:.2f}cm 超出可用宽度 {USABLE_CM:.2f}cm")

    for index, text in enumerate(header):
        cell = table.rows[0].cells[index]
        cell.width = Cm(widths[index])
        shade_cell(cell, "EDEDED")
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.line_spacing = 1.15
        set_run_font(paragraph.add_run(text), LATIN, HEI, 9.5, bold=True)

    for row in rows:
        cells = table.add_row().cells
        for index, text in enumerate(row):
            cells[index].width = Cm(widths[index])
            paragraph = cells[index].paragraphs[0]
            paragraph.paragraph_format.line_spacing = 1.15
            paragraph.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER if index == 0 and len(text) <= 8
                else WD_ALIGN_PARAGRAPH.LEFT
            )
            set_run_font(paragraph.add_run(text), LATIN, SONG, 9.5)

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(6)
    spacer.paragraph_format.line_spacing = 1.0


def add_toc(doc: Document) -> None:
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(6)
    title.paragraph_format.space_after = Pt(18)
    set_run_font(title.add_run("目　　录"), LATIN, HEI, 18, bold=True)

    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.5
    add_field(paragraph, 'TOC \\o "1-3" \\h \\z \\u', "（在 Word 中右键选择「更新域」生成目录）")


# --------------------------------------------------------------------------- #
# 正文
# --------------------------------------------------------------------------- #
def add_cover(doc: Document) -> None:
    for _ in range(3):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(title.add_run("《Python 程序设计》实验任务书"), LATIN, HEI, 24, bold=True)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_before = Pt(16)
    set_run_font(
        subtitle.add_run("—— 分层 DIY 头像生成器（FastAPI + Pillow）"), LATIN, HEI, 15
    )

    for _ in range(5):
        doc.add_paragraph()

    info = table_no_caption(
        doc,
        [
            ("课程名称", "Python 程序设计"),
            ("实验名称", "分层 DIY 头像生成器"),
            ("团队规模", "6 人"),
            ("项目代号", "diyface"),
            ("小组成员", "　"),
            ("指导教师", "　"),
            ("完成日期", "　　　年　　月　　日"),
        ],
        widths=[4.0, 8.0],
        border_color="FFFFFF",
    )
    for row in info.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.line_spacing = 1.8

    doc.add_page_break()


def table_no_caption(doc, pairs, widths, border_color="BFBFBF"):
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table_borders(table, color=border_color)
    cell_margins(table, top=60, bottom=60, left=120, right=120)
    for key, value in pairs:
        cells = table.add_row().cells
        cells[0].width = Cm(widths[0])
        cells[1].width = Cm(widths[1])
        for index, text in enumerate((key, value)):
            paragraph = cells[index].paragraphs[0]
            set_run_font(paragraph.add_run(text), LATIN, SONG, 12, bold=index == 0)
    return table


def add_intro(doc: Document) -> None:
    h(doc, 1, "1  实验介绍")

    h(doc, 2, "1.1  实验目的")
    body(
        doc,
        "社交平台、论坛与即时通讯软件都要求一张头像。用设计软件手工绘制门槛高、难以批量，"
        "而「分层素材 + 参数化合成」把头像拆成脸型、发型、眼睛、嘴、配饰等可替换的图层，"
        "用户只需点选与取色，就能组合出属于自己的形象。本实验以 Python 为主实现这一思路。",
    )
    body(
        doc,
        "实验要求设计并实现一个分层头像生成器：服务端用 FastAPI 提供接口，用 Pillow 完成图层合成、"
        "颜色映射与多尺寸导出；浏览器端提供类目切换、实时预览、一键随机与下载。"
        "系统对外只暴露一份「配方」（JSON），同一份配方必须能稳定复现同一张头像，"
        "并支持编码进链接分享。",
    )
    body(
        doc,
        "通过本实验，应达到以下四个目标：",
    )
    bullet(doc, "掌握用 Pillow 处理多图层 RGBA 图像：通道拆分、alpha 合成、颜色相乘、高质量缩放。")
    bullet(doc, "掌握用 Pydantic 描述业务数据结构，并把「配方」与「素材清单」分离为数据与资源两层。")
    bullet(doc, "掌握 FastAPI 的基本用法：请求校验、二进制响应、ETag 与缓存、静态资源托管。")
    bullet(doc, "掌握以测试保障重构的习惯：单元测试、接口契约测试、渲染快照测试与素材完整性校验。")

    body(
        doc,
        "本实验与课程知识点的对应关系如表 1 所示，建议在动手前先通读一遍，明确每个模块要用到哪些语法。",
    )
    data_table(
        doc,
        ["课程知识点", "在本实验中的落点", "难度"],
        [
            ["字典与列表", "配方 slots / colors 映射、素材清单遍历", "基础"],
            ["函数与模块", "渲染、着色、编目各自独立成模块", "基础"],
            ["类与数据建模", "Pydantic 模型约束字段与取值范围", "中等"],
            ["文件与目录操作", "扫描 assets/ 生成清单、批量校验素材", "中等"],
            ["异常处理", "素材缺失、配方非法时降级为默认脸", "中等"],
            ["图像处理", "Pillow 图层合成、蒙版、缩放与编码", "进阶"],
            ["Web 接口", "FastAPI 路由、JSON 出入参、二进制响应", "中等"],
            ["测试与 CI", "单元测试、快照回归、GitHub Actions", "进阶"],
        ],
        "表 1  实验涉及的知识点",
        widths=[3.6, 8.0, 2.4],
    )

    h(doc, 2, "1.2  实验环境")
    body(doc, "本实验为纯 Python 技术栈，不依赖前端构建工具，环境准备成本较低。")
    data_table(
        doc,
        ["项目", "要求 / 版本", "说明"],
        [
            ["操作系统", "Windows 10+ 或 macOS 12+", "路径与文件名统一使用小写英文"],
            ["Python", "3.11 及以上", "本实验在 3.12 上开发；需支持 dict[str, int] 等新语法"],
            ["编辑器", "Visual Studio Code", "需安装 Python 与 Pylance 扩展"],
            ["Web 框架", "FastAPI + Uvicorn", "提供 JSON 接口与静态资源"],
            ["图像库", "Pillow 12", "RGBA 合成、颜色运算、PNG 编码"],
            ["模板引擎", "Jinja2", "服务端渲染首屏，减少一次往返"],
            ["测试工具", "pytest + pytest-cov", "单元、契约、快照与覆盖率"],
            ["版本控制", "Git + GitHub", "6 人协作、Pull Request 评审"],
            ["浏览器", "Chrome / Edge / Safari 最新版", "需支持 fetch 与 CSS aspect-ratio"],
        ],
        "表 2  实验环境与依赖",
        widths=[3.2, 5.8, 5.0],
    )

    h(doc, 2, "1.3  实验流程")
    body(
        doc,
        "实验按「先骨架、后内核、再界面、最后打磨」的顺序推进，每一步都以测试通过作为完成标志。"
        "六个阶段及其产出如表 3 所示，团队可按此表安排每周工作。",
    )
    data_table(
        doc,
        ["阶段", "主要工作", "产出物", "时长"],
        [
            ["M0 骨架", "建仓库、装依赖、起一个空页面、配 CI", "可运行的项目骨架", "0.5 天"],
            ["M1 渲染内核", "配方模型、合成管线、素材编目、命令行出图", "能生成 PNG 的渲染器", "2 天"],
            ["M2 素材管线", "素材规范、校验脚本、首批 5 类 30 张素材", "合规素材与清单", "1.5 天"],
            ["M3 界面联调", "三栏布局、素材格、取色、随机、下载、分享", "可用的单页产品", "2.5 天"],
            ["M4 补齐素材", "帽子、衣服、配饰共 13 张，随机兼容规则", "8 类 43 张完整素材", "1 天"],
            ["M5 打磨", "缓存、压缩、分享图、中英双语、容器化", "可部署版本", "1.5 天"],
        ],
        "表 3  实验阶段与产出",
        widths=[2.8, 6.2, 3.8, 1.6],
    )

    h(doc, 2, "1.4  实验范围与交付物")
    body(
        doc,
        "为控制工作量，本实验明确不做以下内容：用户账号与云端相册、AI 文生图或真人换脸、"
        "上传自有素材、付费与水印体系、原生 App 与小程序。评分只覆盖下列交付物。",
    )
    data_table(
        doc,
        ["交付物", "形式", "要求"],
        [
            ["源代码", "Git 仓库", "模块划分清晰，函数职责单一，无大段复制粘贴"],
            ["分层素材", "assets/ 目录", "43 张 1024×1024 PNG，尺寸与对齐完全一致"],
            ["测试用例", "tests/ 目录", "单元 + 契约 + 快照，全部通过"],
            ["运行说明", "README.md", "三步内能在同学机器上跑起来"],
            ["实验报告", "本文档 + 截图", "补全第 4、5 章的结果与反思"],
        ],
        "表 4  交付物清单",
        widths=[3.2, 3.6, 7.2],
    )


def add_design(doc: Document) -> None:
    h(doc, 1, "2  系统设计")

    h(doc, 2, "2.1  总体结构")
    body(
        doc,
        "本系统沿用经典的模型-视图-控制器（MVC）思想，并在此基础上做了适合 Web 的切分："
        "模型负责配方与素材清单的数据结构与校验；视图由服务端模板与浏览器页面共同承担；"
        "控制器即 FastAPI 的路由与渲染管线，负责接收参数、调用模型、产出图像。"
        "与桌面程序不同的是，这里的「视图」还多了一层由 Pillow 生成的位图——"
        "图像本身就是对模型的一次渲染结果。",
    )
    body(
        doc,
        "整个系统只有一条数据主线：浏览器持有一份约 300 字节的配方，"
        "每次改动画出请求，服务端把它合成成图像返回。因为图像永远可从配方重建，"
        "所以服务端不需要保存用户作品，也天然获得「分享即复现」的能力。",
    )
    box_diagram(
        doc,
        [
            ("box", "浏览器｜类目导航 · 预览画布 · 颜色与操作"),
            ("arrow", "↓  recipe（JSON）        ↑  PNG（256 / 1024）"),
            ("box", "FastAPI 接口层｜/api/manifest · /api/render · /api/random · /healthz"),
            ("arrow", "↓"),
            ("box", "渲染核｜catalog.py · render.py · palettes.py · randomizer.py"),
            ("arrow", "↓"),
            ("box", "素材库｜assets/ 43 张 1024×1024 分层 PNG"),
        ],
        "图 1  系统总体结构",
    )
    data_table(
        doc,
        ["分层", "对应实现", "职责"],
        [
            ["视图", "templates/index.html、static/", "展示类目、预览、颜色与操作按钮"],
            ["控制器", "app.py 路由", "校验请求、调用渲染、设置缓存头"],
            ["模型", "models.py、catalog.py", "配方结构、素材清单、z 序与默认值"],
            ["渲染核", "render.py、palettes.py", "图层合成、颜色映射、多尺寸导出"],
            ["资源", "assets/", "43 张 1024×1024 分层 PNG 与缩略图"],
        ],
        "表 5  分层职责",
        widths=[2.4, 5.4, 6.6],
    )

    h(doc, 2, "2.2  数据结构设计")
    body(
        doc,
        "系统有两类数据：一类是用户可变的「配方」，一类是系统只读的「素材清单」。"
        "前者决定画什么，后者决定能画什么，二者分离是后续扩展素材的关键。",
    )

    h(doc, 3, "2.2.1  配方（Recipe）")
    body(
        doc,
        "配方记录每个槽位选了哪张素材、用了什么颜色。槽位固定为 12 个，"
        "v1 启用 8 个（脸型、刘海、眼睛、嘴、眼镜、帽子、衣服、配饰），其余 4 个只保留枚举值。"
        "槽位名与素材 id 都必须是字符串，颜色统一为 #RRGGBB，未知字段一律拒绝，避免脏数据进入渲染。",
    )
    code_block(
        doc,
        """from pydantic import BaseModel, ConfigDict, Field

class AvatarRecipe(BaseModel):
    version: int = 1
    slots: dict[str, str | None] = Field(default_factory=dict)   # 槽位 -> 素材 id
    colors: dict[str, str] = Field(default_factory=dict)         # 槽位 -> #RRGGBB
    seed: int | None = None                                      # 随机来源，可复现

    model_config = ConfigDict(extra="forbid")   # 多余字段直接 422""",
    )

    h(doc, 3, "2.2.2  素材清单（manifest）")
    body(
        doc,
        "素材清单由程序扫描 assets/ 目录自动生成，不手工维护。"
        "它记录每个槽位的显示名、图层顺序、是否可着色、默认颜色与素材列表，"
        "前端据此渲染界面，渲染器据此决定叠放顺序，二者共用同一份事实来源。",
    )
    code_block(
        doc,
        """{
  "schema": 1,
  "slots": [
    {
      "id": "hair", "label": {"zh": "发型", "en": "Bangs"}, "z": 30,
      "tintable": true, "default_color": "#3b2b23",
      "assets": [{"id": "hair_straight_01", "file": "04_hair/hair_straight_01.png"}]
    }
  ]
}""",
    )

    h(doc, 3, "2.2.3  素材规范")
    body(
        doc,
        "对齐是这一类项目最容易返工的地方：只要有一张图层偏了 3 像素，合成后就会「浮空」。"
        "因此把规范写成脚本可校验的硬性条件，任何一张不合规的图都进不了仓库。",
    )
    data_table(
        doc,
        ["项目", "要求"],
        [
            ["画布", "1024×1024，PNG，RGBA，透明背景"],
            ["对齐", "共用坐标系：脸中心 (512, 448)，头顶基线 y=256"],
            ["命名", "槽位_形状_序号.png，只允许小写字母、数字与下划线"],
            ["着色", "可着色素材另附同名 _tint.png 蒙版（白=上色，黑=保留原色）"],
            ["描边", "描边烘焙进图层或单独成层，不依赖缩放保边"],
            ["体积", "单张 1024 图层小于 120 KB，256 缩略图小于 18 KB"],
        ],
        "表 6  素材规范",
        widths=[3.0, 11.6],
    )

    h(doc, 3, "2.2.4  图层顺序")
    body(
        doc,
        "图层顺序（z 序）决定遮挡关系，只在一处定义，渲染器与前端共用。"
        "数值越大越靠上：帽子压住所有头发，眼镜压住五官，衣服压在脖子底部。",
    )
    data_table(
        doc,
        ["z", "槽位", "说明", "v1"],
        [
            ["10", "skin", "脸型底", "启用"],
            ["20", "cheeks", "腮红与皱纹", "预留"],
            ["30", "hair", "刘海", "启用"],
            ["40", "side_hair", "鬓发", "预留"],
            ["50", "brows", "眉与睫毛", "预留"],
            ["60", "eyes", "眼睛", "启用"],
            ["70", "nose", "鼻子", "预留"],
            ["80", "mouth", "嘴", "启用"],
            ["90", "glasses", "眼镜", "启用"],
            ["100", "clothes", "衣领", "启用"],
            ["110", "hat", "帽子", "启用"],
            ["120", "extra", "耳饰与贴纸", "启用"],
        ],
        "表 7  槽位与图层顺序",
        widths=[1.6, 3.4, 7.4, 2.2],
    )

    h(doc, 2, "2.3  接口设计")
    body(
        doc,
        "接口只做三件事：下发清单、按配方出图、生成合法随机配方。"
        "所有出图请求都带 ETag，浏览器命中缓存时直接返回 304，避免重复合成。",
    )
    data_table(
        doc,
        ["方法", "路径", "入参", "出参", "说明"],
        [
            ["GET", "/", "—", "HTML", "首屏，内联清单"],
            ["GET", "/api/manifest", "—", "JSON", "素材清单，可缓存 5 分钟"],
            ["POST", "/api/render", "recipe, size", "image/png", "size 取 256 或 1024"],
            ["POST", "/api/random", "constraints", "recipe", "返回合法组合"],
            ["GET", "/healthz", "—", "JSON", "版本与素材哈希"],
        ],
        "表 8  接口一览",
        widths=[1.4, 3.4, 2.6, 2.4, 4.6],
    )
    body(
        doc,
        "错误响应统一为如下结构，前端据此定位到具体字段，而不是只弹一句「出错了」。",
    )
    code_block(
        doc,
        """{ "error": { "code": "UNKNOWN_ASSET", "message": "素材不存在", "field": "slots.hat" } }""",
    )

    h(doc, 2, "2.4  界面设计")
    body(
        doc,
        "界面采用「左选择、中预览、右调色」的三栏结构，移动端降级为上下结构："
        "预览固定在顶部，类目变底部横向标签，颜色放进抽屉。"
        "预览区严格保持 1:1，避免头像在不同屏幕上被拉变形。",
    )
    data_table(
        doc,
        ["区域", "内容", "说明"],
        [
            [
                "类目栏",
                "脸型、发型、眼睛、嘴、眼镜、帽子、衣服、配饰（8 个启用槽位）",
                "点击切换右侧素材格",
            ],
            [
                "预览画布",
                "1:1 实时渲染，空槽位保持透明",
                "严格正方形，避免拉伸变形",
            ],
            [
                "操作栏",
                "取色器与预设色板；随机、下载 256、下载 1024、复制分享链接",
                "移动端收进底部抽屉",
            ],
            [
                "素材格",
                "当前槽位的全部素材缩略图，含「无」选项",
                "懒加载，触控目标不小于 44 像素",
            ],
        ],
        "图 2  主界面布局示意",
        widths=[2.4, 8.4, 3.6],
    )
    data_table(
        doc,
        ["交互", "预期行为"],
        [
            ["点类目", "切换右侧素材格，懒加载缩略图"],
            ["点素材", "立即应用；点「无」置空该槽位"],
            ["拖颜色", "实时预览，请求去抖 120 毫秒"],
            ["点随机", "生成合法组合，300 毫秒内可连点"],
            ["点下载", "导出 256 或 1024 的透明 PNG"],
            ["点分享", "复制带配方的链接，打开即复现"],
        ],
        "表 9  主要交互",
        widths=[3.0, 11.6],
    )

    h(doc, 2, "2.5  模块划分与人员分工")
    body(
        doc,
        "六人团队按「代码、素材、质量」三条线分工，每人负责的目录互不重叠，"
        "这样既减少冲突，也便于用 CODEOWNERS 指定评审人。",
    )
    data_table(
        doc,
        ["角色", "负责模块", "主要任务"],
        [
            ["A 渲染内核", "render.py、palettes.py、models.py", "合成管线、颜色映射、单元测试"],
            ["B 前端交互", "templates/、static/", "布局、素材格、取色、导出与分享"],
            ["C 接口与部署", "app.py、cache.py、randomizer.py", "路由、缓存、随机规则、CI 与上线"],
            ["D 素材·头部", "04_hair、05_eyes、10_hat", "21 张素材的绘制与对齐"],
            ["E 素材·面部服饰", "01_skin、07_mouth、08_glasses 等", "22 张素材的绘制与对齐"],
            ["F 质量与文档", "tests/、docs/、scripts/", "测试体系、素材校验、进度同步"],
        ],
        "表 10  六人分工",
        widths=[3.2, 6.0, 5.4],
    )


def add_impl(doc: Document) -> None:
    h(doc, 1, "3  系统实现")

    h(doc, 2, "3.1  环境搭建与项目骨架")
    body(
        doc,
        "先建虚拟环境并安装依赖。建议把依赖写进 pyproject.toml 并锁定版本，"
        "尤其是 Pillow：不同版本的重采样实现差异会让快照测试集体失败。",
    )
    code_block(
        doc,
        """python -m venv .venv
.venv\\Scripts\\activate            # macOS: source .venv/bin/activate
pip install fastapi uvicorn jinja2 pillow pydantic pytest pytest-cov""",
    )
    body(doc, "项目目录按职责划分，便于多人并行：")
    code_block(
        doc,
        """diyface/
├─ src/diyface/
│  ├─ app.py         FastAPI 入口
│  ├─ models.py      配方与槽位
│  ├─ catalog.py     素材编目
│  ├─ render.py      合成管线
│  ├─ palettes.py    颜色映射
│  ├─ randomizer.py  随机规则
│  ├─ templates/     页面模板
│  └─ static/        脚本与样式
├─ assets/           43 张分层素材
├─ tests/            单元、契约、快照
└─ scripts/          校验与缩略图构建""",
    )

    h(doc, 2, "3.2  素材编目模块")
    body(
        doc,
        "编目模块把「目录里有什么」变成「系统知道什么」。它扫描每个槽位目录，"
        "收集文件名、生成素材 id、写入清单，并顺带校验命名规范与尺寸。"
        "文件系统就是唯一事实来源，新增素材不需要改任何代码。",
    )
    code_block(
        doc,
        """from pathlib import Path
from PIL import Image

def scan_slot(root: Path, slot: str) -> list[dict]:
    folder = root / slot
    assets = []
    for path in sorted(folder.glob("*.png")):
        if path.name.startswith("_"):          # 跳过 tint 蒙版与缩略图
            continue
        with Image.open(path) as img:
            if img.size != (1024, 1024) or img.mode != "RGBA":
                raise ValueError(f"{path} 不符合规范: {img.size} {img.mode}")
        assets.append({"id": path.stem, "file": f"{slot}/{path.name}"})
    return assets""",
    )

    h(doc, 2, "3.3  分层渲染模块")
    body(
        doc,
        "渲染是整个系统的核心，只有四步：按 z 序取层、按颜色着色、逐层 alpha 合成、按尺寸缩放编码。"
        "每一步都写成纯函数，输入配方、输出图像，不读全局变量，因而可以脱离 Web 直接测试。",
    )
    code_block(
        doc,
        """import io
from PIL import Image

def render(recipe: AvatarRecipe, size: int = 256) -> bytes:
    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    for slot in SLOTS_BY_Z:                       # 已按 z 升序排好
        asset_id = recipe.slots.get(slot.id)
        if not asset_id:
            continue                              # 空槽位不画
        layer = load_layer(slot.id, asset_id)
        if slot.tintable:
            layer = tint(layer, recipe.colors.get(slot.id, slot.default_color))
        canvas = Image.alpha_composite(canvas, layer)

    out = canvas if size == 1024 else canvas.resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=True)
    return buf.getvalue()""",
    )
    body(
        doc,
        "缩放必须用 LANCZOS：双线性在 256 尺寸下会让描边发虚，最近邻则出现锯齿。"
        "合成必须用 alpha_composite 而不是 paste：前者按 alpha 权重叠加，后者会硬覆盖下层像素。",
    )
    data_table(
        doc,
        ["场景", "目标耗时（中位）", "目标耗时（95 分位）"],
        [
            ["256 预览（缓存未命中）", "60 毫秒", "150 毫秒"],
            ["256 预览（命中缓存）", "3 毫秒", "10 毫秒"],
            ["1024 导出", "200 毫秒", "400 毫秒"],
        ],
        "表 11  渲染性能预算",
        widths=[6.4, 4.1, 4.1],
    )

    h(doc, 2, "3.4  颜色映射模块")
    body(
        doc,
        "着色不能简单地整层染色，否则明暗关系会丢。做法是把素材当作「灰度底」，"
        "与目标颜色做相乘（multiply）：白色区域完整呈现目标色，黑色描边保持黑色，"
        "中间的明暗自然保留。可着色区域再乘一张 tint 蒙版，保护眼睛高光等不该变色的部分。",
    )
    code_block(
        doc,
        """from PIL import Image, ImageChops

def tint(layer: Image.Image, color: str) -> Image.Image:
    rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    solid = Image.new("RGB", layer.size, rgb)
    tinted = ImageChops.multiply(layer.convert("RGB"), solid)
    tinted.putalpha(layer.getchannel("A"))        # 只改颜色，不动透明度
    mask = load_tint_mask(layer)                  # 可选：白=上色，黑=保留
    return Image.composite(tinted, layer, mask) if mask else tinted""",
    )

    h(doc, 2, "3.5  Web 接口模块")
    body(
        doc,
        "接口层只做三件事：校验参数、调用渲染、设置缓存头。把「怎么画」留在渲染核里，"
        "接口就变得很薄，测试也只需要验证状态码与响应类型。",
    )
    code_block(
        doc,
        """import hashlib
from fastapi import FastAPI, Request, Response

app = FastAPI()

@app.post("/api/render")
def api_render(payload: RenderRequest, request: Request) -> Response:
    png = render(payload.recipe, payload.size)
    etag = '"' + hashlib.sha1(png).hexdigest()[:16] + '"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)          # 浏览器已有这张图
    return Response(png, media_type="image/png",
                    headers={"ETag": etag, "Cache-Control": "public, max-age=86400"})""",
    )

    h(doc, 2, "3.6  前端交互实现")
    body(
        doc,
        "前端不发散：所有状态压在一个 recipe 对象里，任何改动都走同一个刷新函数。"
        "拖动取色器会产生大量请求，因此需要去抖；网络返回顺序不保证，因此需要序号丢弃过期响应。"
        "这两个细节决定了「拖动是否跟手」和「快速连点是否闪回旧图」。",
    )
    code_block(
        doc,
        """let timer = null, seq = 0;

function schedulePreview() {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    const mine = ++seq;                        // 本次请求的序号
    const res = await fetch("/api/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipe: state.recipe, size: 256 }),
    });
    if (mine !== seq) return;                  // 已有更新的请求，丢弃
    preview.src = URL.createObjectURL(await res.blob());
  }, 120);                                     // 去抖 120 毫秒
}""",
    )

    h(doc, 2, "3.7  测试与质量门禁")
    body(
        doc,
        "本实验要求「每改一处代码，都要有对应测试」。测试分四层，越靠下越慢，"
        "提交前只跑快测，合并前跑全量。渲染结果用快照比对：同一配方生成的图与基准图的"
        "均方根误差小于 1% 才算通过，超过阈值时输出差异图便于定位。",
    )
    data_table(
        doc,
        ["层次", "测试对象", "关注点"],
        [
            ["单元测试", "models、palettes、randomizer", "默认值、非法输入、颜色换算、随机分布"],
            ["契约测试", "FastAPI 各端点", "状态码、ETag 与 304、错误结构"],
            ["快照测试", "render 输出", "固定配方出图与基准的一致度"],
            ["素材校验", "assets/ 全量", "尺寸、模式、命名、体积、tint 配对"],
        ],
        "表 12  测试分层",
        widths=[3.0, 5.6, 6.0],
    )
    code_block(
        doc,
        """def test_empty_slot_stays_transparent():
    recipe = default_recipe() | {"slots": {"hat": None}}
    img = Image.open(io.BytesIO(render(recipe, 256)))
    assert img.getpixel((8, 8))[3] == 0          # 角落必须完全透明""",
    )
    code_block(
        doc,
        """pytest -q --cov=src/diyface --cov-fail-under=85
python -m diyface verify --all          # 素材合规
python -m diyface build-thumbs --check  # 缩略图是否过期""",
    )

    h(doc, 2, "3.8  运行与部署")
    body(
        doc,
        "本地开发一条命令即可：uvicorn 启动后访问 http://127.0.0.1:8000 。"
        "部署时用 Docker 把依赖与素材一起打包，镜像约 200 MB；"
        "若访问量上升，可在前面加一层 CDN 缓存 /api/render 的 GET 分享链接。",
    )
    code_block(
        doc,
        """uvicorn diyface.app:app --reload --port 8000""",
    )


def add_result(doc: Document) -> None:
    h(doc, 1, "4  效果展示与验收")

    h(doc, 2, "4.1  预期效果")
    body(
        doc,
        "打开页面即出现一张默认头像：浅肤色脸型、直发、圆眼、微笑。"
        "左侧依次点选「发型—双马尾」「眼睛—星星眼」，中间预览在 150 毫秒内更新；"
        "把发色拖到 #C0392B，头发连同高光一起变红而描边保持黑色；"
        "点「随机」连续三次，每次都得到一张五官完整、没有穿模的脸；"
        "点「下载 1024」，得到一张四周透明、可直接用作头像的 PNG。",
    )
    body(
        doc,
        "由于本实验的分层素材为自绘，最终成品的风格应保持统一：圆角、粗描边、低饱和配色。"
        "若出现图层错位、颜色发灰或合成边缘发白，按第 5 章的排查表处理。",
    )

    h(doc, 2, "4.2  验收测试")
    body(doc, "验收按下表逐条执行，结果列在答辩前填好并附截图。")
    data_table(
        doc,
        ["序号", "验证内容", "预期结果", "实测"],
        [
            ["1", "切换 8 个启用槽位", "预览即时更新，无错位", "　"],
            ["2", "选中素材后置空", "对应图层消失，其余不变", "　"],
            ["3", "修改发色为红色", "头发变红，描边仍为黑色", "　"],
            ["4", "连续随机 10 次", "无穿模、无空白脸", "　"],
            ["5", "导出 1024 PNG", "尺寸正确、四角透明", "　"],
            ["6", "复制分享链接重开", "与分享前完全一致", "　"],
            ["7", "手机宽度 375 像素", "无横向滚动条，按钮可点", "　"],
        ],
        "表 13  验收用例",
        widths=[1.4, 5.4, 5.6, 2.2],
    )

    h(doc, 2, "4.3  性能与质量指标")
    data_table(
        doc,
        ["指标", "目标值", "测量方法"],
        [
            ["预览响应（95 分位）", "小于 150 毫秒", "浏览器网络面板统计 20 次"],
            ["导出响应", "小于 400 毫秒", "同上，size=1024"],
            ["测试覆盖率", "不低于 85%", "pytest-cov 报告"],
            ["首页性能分", "不低于 90", "Chrome Lighthouse"],
            ["素材合规率", "100%", "verify --all 全绿"],
        ],
        "表 14  质量指标",
        widths=[4.4, 4.8, 5.4],
    )

    h(doc, 2, "4.4  交付标准")
    body(doc, "满足以下全部条件方可提交：")
    bullet(doc, "8 个启用槽位可切换，4 个预留槽位不出现在界面上。")
    bullet(doc, "256 与 1024 两种尺寸均可导出透明 PNG。")
    bullet(doc, "分享链接可完整复现同一张脸，包括颜色。")
    bullet(doc, "全部测试通过，覆盖率达标，素材校验零错误。")
    bullet(doc, "README 中的启动命令在他人机器上可一次跑通。")


def add_conclusion(doc: Document) -> None:
    h(doc, 1, "5  总结与思考")

    h(doc, 2, "5.1  技术总结")
    body(
        doc,
        "本实验把「头像生成」拆成三件可独立验证的事：分层素材（数据）、合成管线（逻辑）、"
        "Web 接口（外壳）。一旦拆开，每部分都能单独测试，团队也能并行推进。"
        "最值得记住的结论是：图像处理里真正难的不是算法，而是坐标约定与图层秩序——"
        "把它们写进规范和脚本，比写更多代码更有用。",
    )

    h(doc, 2, "5.2  常见问题与排查")
    data_table(
        doc,
        ["现象", "可能原因", "处理办法"],
        [
            ["图层浮空或错位", "素材坐标系不一致", "统一 1024 画布，重跑 verify --all"],
            ["颜色发灰发暗", "整层相乘，缺少 tint 蒙版", "补蒙版并保留高光"],
            ["边缘发白", "用 paste 覆盖而非 alpha 合成", "改用 alpha_composite"],
            ["预览闪烁回旧图", "响应乱序", "请求加序号，丢弃过期结果"],
            ["快照测试集体失败", "Pillow 版本变化", "锁定版本后统一重刷基准"],
        ],
        "表 15  常见问题排查",
        widths=[4.4, 5.4, 4.8],
    )

    h(doc, 2, "5.3  可改进方向")
    body(
        doc,
        "若时间允许，可以从三个方向继续：其一，把 4 个预留槽位补齐，组合数会再上一个量级；"
        "其二，为素材增加「风格包」，让用户一键切换像素风与扁平风；"
        "其三，把渲染搬到浏览器（OffscreenCanvas），彻底消除网络往返，代价是逻辑要写两遍。",
    )

    h(doc, 2, "5.4  思考题")
    numbered(doc, "为什么图像的合成顺序不能用字典的插入顺序决定？如果让用户自由调整顺序，会破坏什么？")
    numbered(doc, "颜色相乘会把白色变成目标色，为什么黑色描边不受影响？若素材底色是灰而非白，会发生什么？")
    numbered(doc, "服务端每次重新合成与「把成品图存起来」，在 6 人协作与隐私保护上各有什么代价？")
    numbered(doc, "如果要新增「脸型变体」并让它影响五官位置，现有的 12 槽位设计还够用吗？")


def add_appendix(doc: Document) -> None:
    h(doc, 1, "附录 A  团队分工与进度")
    data_table(
        doc,
        ["成员", "角色", "交付物", "关键节点"],
        [
            ["成员 1", "渲染内核", "render.py、palettes.py", "M1 前完成合成与着色"],
            ["成员 2", "前端交互", "页面与脚本", "M3 前完成单页可用"],
            ["成员 3", "接口与部署", "app.py、CI、镜像", "M0 搭骨架，M6 上线"],
            ["成员 4", "素材·头部", "发型、眼睛、帽子 21 张", "M2 交 15 张，M4 交 6 张"],
            ["成员 5", "素材·面部服饰", "脸型、嘴、眼镜、衣服 22 张", "M2 交 15 张，M4 交 7 张"],
            ["成员 6", "质量与文档", "测试、校验脚本、文档", "全程，每周五出质量报告"],
        ],
        "表 16  成员分工",
        widths=[2.2, 3.0, 5.2, 4.2],
    )

    h(doc, 2, "A.1  进度安排")
    data_table(
        doc,
        ["周次", "里程碑", "检查点"],
        [
            ["第 1 周", "M0 — M2", "仓库可用、能命令行出图、30 张素材合规"],
            ["第 2 周", "M3 — M4", "页面可用、43 张素材齐、随机不穿模"],
            ["第 3 周", "M5 — M6", "可部署、指标达标、文档与演示就绪"],
        ],
        "表 17  三周排期",
        widths=[2.4, 3.2, 9.0],
    )

    h(doc, 1, "附录 B  评分参考")
    data_table(
        doc,
        ["评分项", "权重", "评审要点"],
        [
            ["功能完整性", "30%", "8 个槽位、随机、导出、分享是否都能用"],
            ["代码质量", "20%", "模块划分、命名、注释、无重复逻辑"],
            ["测试与工程", "20%", "测试覆盖、CI、提交规范、协作痕迹"],
            ["素材与观感", "15%", "规格统一、风格一致、边缘干净"],
            ["文档与答辩", "15%", "报告完整、演示流畅、能回答思考题"],
        ],
        "表 18  评分细则",
        widths=[4.0, 2.4, 8.2],
    )

    h(doc, 1, "附录 C  提交说明")
    body(
        doc,
        "提交内容为一个 Git 仓库的压缩包或可访问链接，包含源代码、素材、测试与报告。"
        "仓库根目录需有 README.md，写明环境要求、启动命令与测试命令；"
        "报告正文使用本任务书的第 4、5 章，并附图 3 张：主界面、素材选择页、导出结果。",
    )
    body(
        doc,
        "演示建议控制在 5 分钟内：30 秒讲背景与分工，2 分钟现场操作（选素材、换色、随机、导出），"
        "1 分钟展示测试与 CI 截图，1 分钟讲遇到的问题与改进方向，最后 30 秒回答提问。",
    )


def main() -> None:
    doc = build_document()
    add_cover(doc)
    add_toc(doc)
    doc.add_page_break()

    add_intro(doc)
    add_design(doc)
    add_impl(doc)
    add_result(doc)
    add_conclusion(doc)
    add_appendix(doc)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    print(f"saved: {OUT}  ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
