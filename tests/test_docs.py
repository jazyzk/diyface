"""文档结构校验（docs/*.md）。

按 AGENTS.md 第 2 条，纯文档改动也要有可执行的验证。这里只用标准库
``unittest``，不引入第三方依赖：

    python -m unittest discover -s tests -v

通用检查（每个文档都跑）：
文件存在且为合法 UTF-8 / 纯 LF、唯一 H1、关键章节齐全、代码围栏成对、
表格列数一致且有对齐行、标题不跳级、无占位标记。

专项检查：
* PLAN.md —— 12 个槽位全覆盖、z 序表 12 行、素材预算合计 43；
* COLLABORATION.md —— 6 人分工覆盖主要模块、交付数量与预算一致。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PLAN = DOCS / "PLAN.md"
COLLAB = DOCS / "COLLABORATION.md"
ONBOARDING = DOCS / "ONBOARDING.md"
BRIEF = DOCS / "AGENT-BRIEF.md"
WEEK = DOCS / "WEEK-01.md"

#: 周计划必须具备的二级标题。
WEEK_SECTIONS = (
    "一周总览",
    "P1 素材与美术",
    "P2 渲染内核",
    "P3 前端体验",
    "P4 后端与数据",
    "P5 视觉与训练",
    "P6 质量与交付",
    "周五验收",
    "卡住了怎么办",
)

#: 新人上手文档必须具备的二级标题。
ONBOARDING_SECTIONS = (
    "加入仓库",
    "配好环境",
    "第一次提交",
    "六个人分别怎么干",
    "每周节奏",
    "交付与验收",
    "速查",
)

#: 计划书必须具备的二级标题（子串匹配，允许标题里带编号）。
PLAN_SECTIONS = (
    "摘要",
    "对标产品拆解",
    "目标与非目标",
    "技术选型",
    "系统架构",
    "数据模型",
    "素材规范",
    "渲染管线",
    "API 契约",
    "前端方案",
    "测试与质量门禁",
    "里程碑",
    "仓库结构",
    "风险登记表",
    "验收清单",
    "待确认决策",
)

#: 协作文档必须具备的二级标题。
COLLAB_SECTIONS = (
    "现状与卡点",
    "一次性建仓",
    "授权方式",
    "仓库设置",
    "6 人分工",
    "分支与提交",
    "二进制素材",
    "日常节奏",
    "常见坑",
    "第一周检查表",
)

#: 10 个槽位 id，必须与 models.py 中的 SlotId 保持一致。
SLOT_IDS = (
    "skin",
    "clothes",
    "hair_back",
    "hair",
    "eyes",
    "brows",
    "mouth",
    "glasses",
    "hat",
    "extra",
)

PLACEHOLDER_PATTERN = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b|待补|待定方案")


def read_text(path: Path) -> str:
    """读取文档；缺失或非 UTF-8 时给出可读的失败信息。"""
    if not path.is_file():
        raise AssertionError(f"文档不存在：{path}")
    return path.read_bytes().decode("utf-8")


def unfenced_lines(text: str) -> list[str]:
    """剔除代码围栏内的行，避免把代码注释里的 # 当成标题。"""
    kept: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            kept.append(line)
    return kept


def table_blocks(text: str) -> list[list[str]]:
    """把连续的表格行切成块（忽略代码围栏内的内容）。"""
    blocks: list[list[str]] = []
    current: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            current = []
            continue
        if in_fence:
            continue
        if line.lstrip().startswith("|"):
            current.append(line.strip())
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


def cell_count(row: str) -> int:
    """统计一行表格的竖线数量（行首行尾各一个，故列数 = 竖线数 - 1）。"""
    return row.count("|")


def header_cells(block: list[str]) -> list[str]:
    """取出表头各单元格文本，用于精确定位某张表。"""
    return [cell.strip() for cell in block[0].strip("|").split("|")]


def body_rows(block: list[str]) -> list[list[str]]:
    """取出表格的数据行（跳过表头与对齐行），每行拆成单元格列表。"""
    return [[cell.strip() for cell in row.strip("|").split("|")] for row in block[2:]]


class MarkdownDocChecks:
    """通用 Markdown 体检；子类提供 PATH / REQUIRED_SECTIONS / MIN_BYTES。"""

    PATH: Path
    REQUIRED_SECTIONS: tuple[str, ...] = ()
    MIN_BYTES: int = 1200

    def setUp(self) -> None:
        self.path = self.PATH
        self.text = read_text(self.path)
        self.lines = self.text.splitlines()
        self.heading_lines = unfenced_lines(self.text)

    def test_file_exists_and_is_utf8(self) -> None:
        raw = self.path.read_bytes()
        self.assertGreater(len(raw), self.MIN_BYTES, f"{self.path.name} 内容过短，疑似被截断")
        self.assertNotIn(b"\r\n", raw, "应为 LF 换行，避免 Windows 下 diff 噪声")
        self.assertTrue(raw.decode("utf-8"), "应为合法 UTF-8")

    def test_has_exactly_one_h1(self) -> None:
        h1 = [line for line in self.heading_lines if line.startswith("# ")]
        self.assertEqual(len(h1), 1, f"应只有一个 H1，实际 {len(h1)} 个：{h1[:3]}")

    def test_required_sections_present(self) -> None:
        h2 = [line[3:].strip() for line in self.heading_lines if line.startswith("## ")]
        joined = "\n".join(h2)
        missing = [name for name in self.REQUIRED_SECTIONS if name not in joined]
        self.assertEqual(missing, [], f"{self.path.name} 缺少章节：{missing}")

    def test_code_fences_balanced(self) -> None:
        fences = [line for line in self.lines if line.lstrip().startswith("```")]
        self.assertEqual(len(fences) % 2, 0, "代码围栏未成对闭合")

    def test_tables_have_consistent_columns(self) -> None:
        for block in table_blocks(self.text):
            widths = {cell_count(row) for row in block}
            self.assertEqual(
                len(widths),
                1,
                f"表格列数不一致（{sorted(widths)}），起始行：{block[0][:60]}",
            )

    def test_every_table_has_alignment_row(self) -> None:
        for block in table_blocks(self.text):
            self.assertGreaterEqual(len(block), 2, f"表格只有表头：{block[0][:60]}")
            self.assertRegex(
                block[1], r"^\|[\s:\-|]+\|$", f"第二行缺少对齐行：{block[0][:60]}"
            )

    def test_no_placeholder_markers(self) -> None:
        hits = PLACEHOLDER_PATTERN.findall(self.text)
        self.assertEqual(hits, [], f"存在未清理的占位标记：{hits}")

    def test_headings_have_no_skipped_levels(self) -> None:
        """标题层级不许跳级（H1→H3），保证大纲可折叠。"""
        previous = 0
        for line in self.heading_lines:
            match = re.match(r"^(#{1,6})\s+\S", line)
            if not match:
                continue
            level = len(match.group(1))
            self.assertLessEqual(level, previous + 1, f"标题跳级：{line[:40]}")
            previous = level


class TestPlanDocument(MarkdownDocChecks, unittest.TestCase):
    PATH = PLAN
    REQUIRED_SECTIONS = PLAN_SECTIONS
    MIN_BYTES = 3000

    def test_all_slot_ids_documented(self) -> None:
        missing = [
            slot for slot in SLOT_IDS if f"`{slot}`" not in self.text and slot not in self.text
        ]
        self.assertEqual(missing, [], f"计划书未覆盖槽位：{missing}")

        # z 序表必须正好 12 行数据行，避免漏加/多加槽位。
        z_tables = [b for b in table_blocks(self.text) if "槽位" in b[0] and "说明" in b[0]]
        self.assertEqual(len(z_tables), 1, "应存在唯一的 z 序表")
        self.assertEqual(len(z_tables[0]) - 2, len(SLOT_IDS), "z 序表数据行数应等于 10")

    def test_asset_budget_matches_total(self) -> None:
        """§2.3 预算表逐槽位数量之和应等于声明的总数，改预算时不许漏改合计。"""
        budget_tables = [
            block
            for block in table_blocks(self.text)
            if header_cells(block) == ["槽位", "数量", "内容"]
        ]
        self.assertEqual(len(budget_tables), 1, "应存在唯一的素材预算表（槽位/数量/内容）")

        per_slot: dict[str, int] = {}
        declared_total: int | None = None
        for cells in body_rows(budget_tables[0]):
            if cells[0] in SLOT_IDS:
                per_slot[cells[0]] = int(cells[1])
            elif cells[0] == "合计":
                declared_total = int(cells[1])

        self.assertEqual(len(per_slot), 10, "预算表应覆盖全部 10 个槽位")
        self.assertEqual(sum(per_slot.values()), 54, "预算表各槽位之和应为 54")
        self.assertEqual(declared_total, 54, "合计行应写 54，与逐项之和一致")


class TestCollaborationDocument(MarkdownDocChecks, unittest.TestCase):
    PATH = COLLAB
    REQUIRED_SECTIONS = COLLAB_SECTIONS
    MIN_BYTES = 2500

    def test_six_person_division_covers_modules(self) -> None:
        """分工表必须恰好 6 个角色，且覆盖代码、素材、测试三类路径。"""
        role_tables = [
            block
            for block in table_blocks(self.text)
            if header_cells(block) == ["角色", "负责路径", "主战场", "交付物"]
        ]
        self.assertEqual(len(role_tables), 1, "应存在唯一的 6 人分工表")
        roles = body_rows(role_tables[0])
        self.assertEqual(len(roles), 6, f"分工表应恰好 6 个角色，实际 {len(roles)}")

        for module in ("src/diyface/", "assets/", "tests/"):
            self.assertIn(module, self.text, f"分工未覆盖模块：{module}")

    def test_asset_ownership_matches_budget(self) -> None:
        """素材总量应与 PLAN 的预算一致（当前 54 张）。"""
        self.assertIn("54 张", self.text, "素材总量应为 54 张")

    def test_auth_options_documented(self) -> None:
        """三种授权方式都要给出可执行步骤，避免队友照着卡住。"""
        for token in ("ssh-keygen", "私人令牌", "gitee.com"):
            self.assertIn(token, self.text, f"授权方式缺少关键步骤：{token}")


class TestOnboardingDocument(MarkdownDocChecks, unittest.TestCase):
    PATH = ONBOARDING
    REQUIRED_SECTIONS = ONBOARDING_SECTIONS
    MIN_BYTES = 3000

    def test_six_roles_have_weekly_goals(self) -> None:
        """每个角色都要有「本周目标」，否则新人不知道从哪下手。"""
        for index in range(1, 7):
            heading = f"### 4.{index} P{index}"
            start = self.text.find(heading)
            self.assertGreaterEqual(start, 0, f"缺少角色 P{index} 的小节")
            window = self.text[start : start + 1200]
            self.assertIn("本周目标", window, f"角色 P{index} 没有写本周目标")

    def test_environment_steps_are_runnable(self) -> None:
        """环境配置必须给出可直接复制的命令。"""
        for token in (
            "git clone https://gitee.com/chords-of-fate/diyface.git",
            "python -m venv .venv",
            "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple",
            "git config core.hooksPath .githooks",
            "python -m pytest",
        ):
            self.assertIn(token, self.text, f"环境配置缺少命令：{token}")

    def test_first_pr_walkthrough_is_complete(self) -> None:
        """练手 PR 必须覆盖分支、提交、推送、合并四步。"""
        for token in ("git switch -c", "git commit", "git push -u", "Squash"):
            self.assertIn(token, self.text, f"练手 PR 缺少步骤：{token}")

    def test_baseline_test_count_is_stated(self) -> None:
        self.assertRegex(self.text, r"\d+ passed, 11 skipped")

    def test_acceptance_table_covers_all_milestones(self) -> None:
        for milestone in ("M1", "M2", "M3"):
            self.assertIn(f"| {milestone} |", self.text, f"验收表缺少 {milestone}")

    def test_each_role_has_actionable_steps(self) -> None:
        """每个角色至少 5 条可执行步骤。"""
        for index in range(1, 7):
            start = self.text.find(f"### 4.{index} P{index}")
            self.assertGreaterEqual(start, 0, f"缺少角色 P{index} 的小节")
            end = self.text.find("\n### ", start + 4)
            section = self.text[start : end if end > 0 else len(self.text)]
            steps = re.findall(r"(?m)^\d+\. ", section)
            self.assertGreaterEqual(len(steps), 5, f"P{index} 的步骤不足 5 条")


#: 交接简报必须具备的二级标题。
BRIEF_SECTIONS = (
    "一句话",
    "硬约定",
    "现状快照",
    "怎么跑",
    "代码地图",
    "接口契约",
    "数据模型要点",
    "已经踩过的坑",
    "下一步",
    "PR 前的自检",
    "对 DSH 的行为要求",
)


class TestAgentBrief(MarkdownDocChecks, unittest.TestCase):
    """交接简报必须与代码保持一致，否则会误导接手的 DSH。"""

    PATH = BRIEF
    REQUIRED_SECTIONS = BRIEF_SECTIONS
    MIN_BYTES = 4000

    def test_lists_every_api_route(self) -> None:
        from diyface.app import app

        paths = {
            rule.rule
            for rule in app.url_map.iter_rules()
            if rule.rule.startswith(("/api", "/healthz"))
        }
        missing = [path for path in paths if path not in self.text]
        self.assertEqual(missing, [], f"简报漏掉了接口：{missing}")

    def test_lists_every_module(self) -> None:
        modules = sorted(
            path.name
            for path in (ROOT / "src" / "diyface").glob("*.py")
            if path.name != "__init__.py"
        )
        missing = [name for name in modules if name not in self.text]
        self.assertEqual(missing, [], f"简报的代码地图漏了模块：{missing}")

    def test_states_current_baseline(self) -> None:
        self.assertRegex(self.text, r"\d+ passed, 11 skipped")

    def test_contains_paste_ready_prompt(self) -> None:
        """末尾要给一段可以直接粘进对话的短版说明。"""
        start = self.text.find("30 秒版")
        self.assertGreaterEqual(start, 0, "缺少可直接粘贴的 30 秒版")
        excerpt = self.text[start:]
        for token in ("AGENTS", "pytest", "/api/render"):
            self.assertIn(token, excerpt, f"30 秒版缺关键信息：{token}")

    def test_forbids_skipping_failed_tests(self) -> None:
        """行为要求里必须明确禁止用跳过测试的方式「变绿」。"""
        self.assertIn("--no-verify", self.text)
        self.assertIn("跳过", self.text)


class TestWeekPlan(MarkdownDocChecks, unittest.TestCase):
    """周计划必须覆盖六个人、每天有任务，且能手把手照着做。"""

    PATH = WEEK
    REQUIRED_SECTIONS = WEEK_SECTIONS
    MIN_BYTES = 4000

    def test_each_role_has_seven_day_rows(self) -> None:
        visible = "\n".join(unfenced_lines(self.text))
        for index in range(1, 7):
            start = visible.find(f"## {index + 1} P{index}")
            self.assertGreaterEqual(start, 0, f"缺少角色 P{index} 的章节")
            end = visible.find("\n## ", start + 4)
            section = visible[start : end if end > 0 else len(visible)]
            days = re.findall(r"(?m)^\| (D[1-7]) \|", section)
            self.assertEqual(days, ["D1", "D2", "D3", "D4", "D5", "D6", "D7"], f"P{index} 的每日任务不完整")

    def test_plan_states_acceptance_for_every_day(self) -> None:
        """每张日表都要有「验收」列。"""
        self.assertGreaterEqual(self.text.count("| 天 | 任务 | 验收 |"), 6)

    def test_mentions_handoff_commands(self) -> None:
        for token in ("git switch -c", "python -m pytest", "python -m diyface verify", "git push"):
            self.assertIn(token, self.text, f"周计划缺少命令：{token}")

    def test_has_daily_env_sync_section(self) -> None:
        for token in ("每天同步环境", "git pull --rebase", "git rebase main", "Activate.ps1"):
            self.assertIn(token, self.text, f"缺少环境同步内容：{token}")

    def test_has_end_of_day_checklist(self) -> None:
        self.assertIn("收工前 5 分钟", self.text)
        start = self.text.find("收工前 5 分钟")
        for token in ("git status", "git push", "python -m pytest"):
            self.assertIn(token, self.text[start:], f"收工清单缺少：{token}")


#: 角色简报：字母 -> (文件, 必须出现的关键内容)

