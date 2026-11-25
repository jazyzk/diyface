"""可选的 OCR：识别图纸格子里的色号文字。

依赖（用户自行安装，不装也能用）：

* Tesseract-OCR（Windows 安装包）—— 提供 ``tesseract.exe``
* ``pytesseract``（纯 Python 包）

装好后本项目会自动启用：图纸导入时给每类图案预填色号，
识别不准时用户仍可在下拉框里改。
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from PIL import Image

from .mard import MARD_ALL

WHITELIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
CODE_PATTERN = re.compile(r"^[A-Z]{1,2}[0-9]{1,2}$")

#: OCR 常见混淆：把识别结果替换成更像色号的形式
CONFUSIONS = str.maketrans({"O": "0", "I": "1", "S": "5", "B": "8", "Z": "2", "G": "6"})


#: Windows 安装包的默认位置（装完不重启也能用）
DEFAULT_PATHS = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)


def _tesseract_path() -> str | None:
    env = os.environ.get("TESSERACT_CMD")
    if env and Path(env).is_file():
        return env
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in DEFAULT_PATHS:
        if Path(candidate).is_file():
            return candidate
    return None


def available() -> bool:
    """OCR 是否可用：有 tesseract 可执行文件 + pytesseract 包。"""
    if _tesseract_path() is None:
        return False
    try:
        import pytesseract
    except Exception:
        return False
    pytesseract.pytesseract.tesseract_cmd = _tesseract_path()
    return True


def _prepare(cell: Image.Image) -> Image.Image:
    """放大 + 转灰度 + 二值化，小字号识别率更高。"""
    image = cell.convert("L")
    image = image.resize((image.width * 5, image.height * 5), Image.LANCZOS)
    return image.point(lambda value: 0 if value < 165 else 255)


def read_code(cell: Image.Image) -> str | None:
    """识别一个格子里的色号；识别失败或不是色号时返回 None。"""
    if not available():
        return None
    import pytesseract

    text = pytesseract.image_to_string(
        _prepare(cell),
        config="--psm 7 -c tessedit_char_whitelist=" + WHITELIST,
    )
    token = re.sub(r"\s+", "", text).upper()
    if not token:
        return None
    if token in MARD_ALL:
        return token
    fixed = token.translate(CONFUSIONS)
    if fixed in MARD_ALL:
        return fixed
    if CODE_PATTERN.match(fixed) and fixed in MARD_ALL:
        return fixed
    return None


def vote_codes(cells: list[Image.Image]) -> str | None:
    """对同一类图案的多个样本做投票，降低单次识别误差。"""
    from collections import Counter

    votes: Counter[str] = Counter()
    for cell in cells[:5]:
        code = read_code(cell)
        if code:
            votes[code] += 1
    if not votes:
        return None
    return votes.most_common(1)[0][0]
