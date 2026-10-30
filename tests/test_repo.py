"""仓库配置的护栏。

这些文件不参与业务逻辑，但缺一个就会让六人协作出问题：换行混乱、红着提交、
新人 clone 后跑不起来。测试它们比写在文档里更可靠。
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pre_commit_hook_runs_tests_and_blocks_failures() -> None:
    hook = ROOT / ".githooks" / "pre-commit"

    assert hook.is_file(), "缺少本地提交门禁 .githooks/pre-commit"

    text = hook.read_text(encoding="utf-8")
    assert "pytest" in text, "钩子必须真的跑测试"
    assert "exit 1" in text, "测试失败时必须拒绝提交"


def test_gitattributes_unifies_line_endings_and_binaries() -> None:
    text = (ROOT / ".gitattributes").read_text(encoding="utf-8")

    assert "*.png binary" in text, "PNG 必须标记为二进制，否则会被当文本合并"
    assert "text=auto eol=lf" in text, "文本文件必须统一为 LF"


def test_ci_workflow_installs_project_then_runs_tests() -> None:
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "pip install -e" in text, "CI 应安装本项目（含 dev 依赖）"
    assert "pytest" in text, "CI 必须跑测试"


def test_pyproject_makes_tests_runnable_without_install() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'pythonpath = ["src"]' in text, "没有它，clone 后必须先 pip install 才能跑测试"


def test_collaboration_doc_uses_gitee_as_primary() -> None:
    text = (ROOT / "docs" / "COLLABORATION.md").read_text(encoding="utf-8")

    assert "gitee.com" in text
    assert "GitHub 保留为备份镜像" in text, "文档必须写清 GitHub 已降级为镜像"
