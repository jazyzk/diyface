"""可选的 OCR：识别图纸格子里的色号文字。

依赖（用户自行安装，不装也能用）：

* Tesseract-OCR —— 提供 ``tesseract.exe``（可放在项目根目录、PATH 或默认安装位置）
* 语言数据 ``tessdata/``（便携版自带；项目路径含中文时会自动复制到英文缓存目录）

调用走子进程 stdout，避免受限环境里写不了临时输出文件的问题。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from .mard import MARD_ALL

WHITELIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
CODE_PATTERN = re.compile(r"^[A-Z]{1,2}[0-9]{1,2}$")

#: OCR 常见混淆：把识别结果替换成更像色号的形式
CONFUSIONS = str.maketrans({"O": "0", "I": "1", "S": "5", "Z": "2", "G": "6"})

PROJECT_ROOT = Path(__file__).resolve().parents[2]

#: 候选位置：项目目录（便携版）→ Windows 默认安装路径
DEFAULT_PATHS = (
    str(PROJECT_ROOT / "tesseract.exe"),
    str(PROJECT_ROOT / "tools" / "tesseract.exe"),
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


def _ascii_only(path: Path) -> bool:
    try:
        str(path).encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


def _cache_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "diyface"


def _tessdata() -> str | None:
    """语言数据目录；项目路径含中文时复制到纯英文缓存。"""
    for candidate in (PROJECT_ROOT / "tessdata", PROJECT_ROOT / "tools" / "tessdata"):
        if not candidate.is_dir():
            continue
        if _ascii_only(candidate):
            return str(candidate)
        cache = _cache_root() / "tessdata"
        cache.mkdir(parents=True, exist_ok=True)
        for item in candidate.rglob("*.traineddata"):
            target = cache / item.name
            if not target.exists() or target.stat().st_size != item.stat().st_size:
                shutil.copy2(item, target)
        return str(cache)
    return None


def available() -> bool:
    """OCR 是否可用：能找到 tesseract 和语言数据。"""
    return _tesseract_path() is not None and _tessdata() is not None


def _prepare(cell: Image.Image) -> Image.Image:
    """放大 + 灰度 + 二值化：小字号识别率更高。"""
    image = cell.convert("L")
    image = image.resize((image.width * 6, image.height * 6), Image.LANCZOS)
    return image.point(lambda value: 0 if value < 170 else 255)


def _run_tesseract(image: Image.Image) -> str | None:
    binary = _tesseract_path()
    data = _tessdata()
    if binary is None or data is None:
        return None

    workdir = _cache_root() / "tmp"
    workdir.mkdir(parents=True, exist_ok=True)
    path = workdir / "cell.png"
    _prepare(image).save(path)

    env = dict(os.environ)
    env["TESSDATA_PREFIX"] = data
    for psm in ("7", "8"):
        try:
            result = subprocess.run(
                [
                    binary,
                    str(path),
                    "stdout",
                    "--psm",
                    psm,
                    "-c",
                    f"tessedit_char_whitelist={WHITELIST}",
                ],
                capture_output=True,
                timeout=20,
                env=env,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode == 0:
            text = result.stdout.decode("utf-8", "replace")
            if normalise(text):
                return text
    return None


def normalise(text: str) -> str | None:
    """把 OCR 文本清洗成合法色号；不是色号返回 None。"""
    token = re.sub(r"[^A-Z0-9]", "", (text or "").upper())
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


def read_code(cell: Image.Image) -> str | None:
    """识别一个格子里的色号；失败返回 None。"""
    if not available():
        return None
    return normalise(_run_tesseract(cell) or "")


def vote_codes(cells: list[Image.Image]) -> str | None:
    """同一类图案取多个样本投票，降低单格误判。"""
    from collections import Counter

    votes: Counter[str] = Counter()
    for cell in cells[:5]:
        code = read_code(cell)
        if code:
            votes[code] += 1
    if not votes:
        return None
    return votes.most_common(1)[0][0]
