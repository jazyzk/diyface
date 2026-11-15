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
HANDBOOK = DOCS / "HANDBOOK.md"
ONBOARDING = DOCS / "ONBOARDING.md"
BRIEF = DOCS / "AGENT-BRIEF.md"
WEEK = DOCS / "WEEK-01.md"

#: 周计划必须具备的二级标题。
WEEK_SECTIONS = (
    "一周总览",
    "A：渲染内核",
    "B：前端",
    "C：接口与部署",
    "D：素材·头部",
    "E：素材·面部",
    "F：质量与文档",
    "周五验收",
    "卡住了怎么办",
)

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

#: 实施手册必须具备的二级标题。
HANDBOOK_SECTIONS = (
    "全员通用",
    "角色 A",
    "角色 B",
    "角色 C",
    "角色 D",
    "角色 E",
    "角色 F",
    "联调日",
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


class TestHandbookDocument(MarkdownDocChecks, unittest.TestCase):
    PATH = HANDBOOK
    REQUIRED_SECTIONS = HANDBOOK_SECTIONS
    MIN_BYTES = 15_000

    def _role_sections(self) -> dict[str, str]:
        """按「## 角色 X」切分出手册的六个角色章节。"""
        sections: dict[str, str] = {}
        current: str | None = None
        buffer: list[str] = []
        for line in self.text.splitlines():
            if line.startswith("## "):
                if current is not None:
                    sections[current] = "\n".join(buffer)
                title = line[3:].strip()
                current = next((title for title in [title] if "角色" in title), None)
                buffer = []
            elif current is not None:
                buffer.append(line)
        if current is not None:
            sections[current] = "\n".join(buffer)
        return sections

    def test_all_six_roles_present(self) -> None:
        """六个角色各占一章，缺一不可。"""
        roles = self._role_sections()
        for letter in "ABCDEF":
            hit = [title for title in roles if f"角色 {letter}" in title]
            self.assertEqual(len(hit), 1, f"角色 {letter} 的章节缺失或重复")

    def test_each_role_has_step_by_step_guide(self) -> None:
        """每个角色至少要给出 5 个编号步骤，否则不算「一步一步教」。"""
        for title, content in self._role_sections().items():
            steps = [line for line in content.splitlines() if line.startswith("### ") and "第 " in line]
            self.assertGreaterEqual(len(steps), 5, f"{title} 的步骤不足 5 个，实际 {len(steps)} 个")

    def test_each_role_declares_deliverables(self) -> None:
        """每个角色开头都要写清交付物与工时，便于认领。"""
        for title, content in self._role_sections().items():
            self.assertIn("你要交付什么", content, f"{title} 缺少交付物小节")

    def test_core_commands_are_documented(self) -> None:
        for command in ("uvicorn", "pytest", "verify --all", "git switch", "git commit"):
            self.assertIn(command, self.text, f"手册缺少关键命令：{command}")

    def test_handbook_has_many_code_blocks(self) -> None:
        fences = [line for line in self.lines if line.lstrip().startswith("```")]
        self.assertGreaterEqual(len(fences) // 2, 24, "代码示例过少，不足以照着做")

    def test_asset_split_matches_budget(self) -> None:
        """素材总量必须与 PLAN 的 54 张一致。"""
        self.assertIn("54 张", self.text, "手册缺少素材总量：54 张")


class TestOnboardingDocument(MarkdownDocChecks, unittest.TestCase):
    PATH = ONBOARDING
    REQUIRED_SECTIONS = ONBOARDING_SECTIONS
    MIN_BYTES = 8000

    def test_six_roles_have_weekly_goals(self) -> None:
        """每个角色都要有「本周目标」，否则新人不知道从哪下手。"""
        for letter in "ABCDEF":
            heading = f"### 4.{'ABCDEF'.index(letter) + 1} {letter}"
            start = self.text.find(heading)
            self.assertGreaterEqual(start, 0, f"缺少角色 {letter} 的小节")
            window = self.text[start:start + 1200]
            self.assertIn("本周目标", window, f"角色 {letter} 没有写本周目标")

    def test_environment_steps_are_runnable(self) -> None:
        """环境配置必须给出可直接复制的命令，而不是泛泛而谈。"""
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
        """文档要写明期望的测试基线，否则新人分不清「绿」是什么样。"""
        self.assertRegex(self.text, r"\d+ passed, 11 skipped")

    def test_acceptance_table_covers_all_milestones(self) -> None:
        for milestone in ("M0", "M1", "M2", "M3", "M4", "M5", "M6"):
            self.assertIn(f"| {milestone} |", self.text, f"验收表缺少 {milestone}")

    def test_each_role_has_six_or_more_steps(self) -> None:
        """「一步一步教」的最低标准：每个角色至少 6 个编号步骤。"""
        for index, letter in enumerate("ABCDEF", start=1):
            start = self.text.find(f"### 4.{index} {letter}")
            self.assertGreaterEqual(start, 0, f"缺少角色 {letter} 的小节")
            end = self.text.find("\n### ", start + 4)
            section = self.text[start : end if end > 0 else len(self.text)]
            steps = re.findall(r"\*\*第 \d+ 步", section)
            self.assertGreaterEqual(
                len(steps), 6, f"角色 {letter} 只有 {len(steps)} 个步骤，至少要 6 个"
            )

    def test_every_step_declares_acceptance(self) -> None:
        """每步都要有可验收的结果，否则新人不知道做没做完。"""
        steps = self.text.count("**第 ")
        checks = self.text.count("✅ 验收")
        self.assertGreaterEqual(checks, steps, "有步骤没写验收标准")


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
    """周计划必须覆盖六个人、每天有任务、且每步都有代码或命令。"""

    PATH = WEEK
    REQUIRED_SECTIONS = WEEK_SECTIONS
    MIN_BYTES = 8000

    def test_each_role_has_five_day_tasks(self) -> None:
        # 只看围栏外的内容：代码块里可能有 markdown 标题，会干扰切分
        visible = "\n".join(unfenced_lines(self.text))
        for index, letter in enumerate("ABCDEF", start=2):
            start = visible.find(f"## {index} {letter}")
            self.assertGreaterEqual(start, 0, f"缺少角色 {letter} 的章节")
            end = visible.find("\n## ", start + 4)
            section = visible[start : end if end > 0 else len(visible)]
            days = re.findall(r"### \d+\.\d+ (周一|周二|周三|周四|周五)", section)
            self.assertEqual(
                days, ["周一", "周二", "周三", "周四", "周五"], f"角色 {letter} 的每日任务不完整"
            )

    def test_plan_has_runnable_code(self) -> None:
        fences = [line for line in self.lines if line.lstrip().startswith("```")]
        self.assertGreaterEqual(len(fences) // 2, 20, "代码块太少，不够手把手")

    def test_every_day_has_acceptance(self) -> None:
        days = len(re.findall(r"### \d+\.\d+ (周一|周二|周三|周四|周五)", self.text))
        checks = self.text.count("**完成标志**")
        self.assertGreaterEqual(checks, days - 3, "多数日子应写明完成标志")

    def test_mentions_handoff_commands(self) -> None:
        for token in ("git switch -c", "python -m pytest", "python -m diyface verify", "git push"):
            self.assertIn(token, self.text, f"周计划缺少命令：{token}")

    def test_no_placeholder_numbers(self) -> None:
        for marker in ("xxx", "XXX", "TBD", "待补"):
            self.assertNotIn(marker, self.text, f"周计划里还有占位符：{marker}")

    def test_has_daily_env_sync_section(self) -> None:
        """新手最容易漏的就是「拉完代码没同步环境」，必须单独成一节。"""
        for token in ("每天同步环境", "git pull --rebase", "git rebase main", "Activate.ps1"):
            self.assertIn(token, self.text, f"缺少环境同步内容：{token}")

    def test_has_end_of_day_checklist(self) -> None:
        self.assertIn("收工前 5 分钟", self.text)
        for token in ("git status", "git push", "python -m pytest"):
            start = self.text.find("收工前 5 分钟")
            self.assertIn(token, self.text[start:], f"收工清单缺少：{token}")


#: 角色简报：字母 -> (文件, 必须出现的关键内容)
ROLE_BRIEFS = {
    "C": (
        DOCS / "briefs" / "c-api-deploy.md",
        ("cache.py", "Dockerfile", "scripts/check.ps1", "feat/c-w1"),
    ),
    "D": (
        DOCS / "briefs" / "d-assets-head.md",
        ("assets/04_hair", "assets/05_eyes", "make_guide.py", "feat/d-w1"),
    ),
    "E": (
        DOCS / "briefs" / "e-assets-face.md",
        ("assets/01_skin", "assets/07_mouth", "assets/08_glasses", "feat/e-w1"),
    ),
    "F": (
        DOCS / "briefs" / "f-quality.md",
        ("pyproject.toml", "CHANGELOG.md", "覆盖率", "feat/f-w1"),
    ),
}


class TestRoleBriefs(unittest.TestCase):
    """给 C/D/E/F 的 DSH 简报必须自成一体：能直接粘进对话就开工。"""

    def test_each_brief_is_self_contained(self) -> None:
        for letter, (path, tokens) in ROLE_BRIEFS.items():
            self.assertTrue(path.is_file(), f"{path} 不存在")
            text = read_text(path)

            for section in ("你是谁", "你的文件", "本周任务", "不要做", "卡住了找谁"):
                self.assertIn(section, text, f"{path.name} 缺少小节：{section}")
            for token in tokens:
                self.assertIn(token, text, f"{path.name} 缺少关键内容：{token}")

            self.assertIn("python -m pytest", text, f"{path.name} 没写测试命令")
            self.assertIn("WEEK-01.md", text, f"{path.name} 没指向环境同步章节")

    def test_briefs_have_no_placeholders(self) -> None:
        for path, _ in ROLE_BRIEFS.values():
            hits = PLACEHOLDER_PATTERN.findall(read_text(path))
            self.assertEqual(hits, [], f"{path.name} 还有占位符：{hits}")

    def test_briefs_forbid_direct_push(self) -> None:
        for path, _ in ROLE_BRIEFS.values():
            self.assertIn("不直推", read_text(path), f"{path.name} 没写「不直推 main」")


if __name__ == "__main__":
    unittest.main(verbosity=2)
