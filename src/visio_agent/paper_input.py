"""
从项目根下 ``input/<用户>/`` 读取论文 .docx，抽取 3.2.1 与第四章，供论文批量画图模式使用。
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from .diagram_runner import DiagramAgentRunner


def input_root(project_root: str) -> Path:
    return Path(project_root).resolve() / "input"


def list_input_users(project_root: str) -> list[str]:
    """``input`` 下的一级子目录名（每人一个文件夹）。"""
    root = input_root(project_root)
    if not root.is_dir():
        return []
    names: list[str] = []
    for p in sorted(root.iterdir()):
        if p.is_dir() and not p.name.startswith("."):
            names.append(p.name)
    return names


def pick_user_interactive(users: list[str]) -> str | None:
    if not users:
        print("input 目录下没有用户子文件夹。", file=sys.stderr)
        return None
    print("可选用户（input 下子目录）：")
    for i, u in enumerate(users, 1):
        print(f"  {i}. {u}")
    try:
        raw = input("请输入序号: ").strip()
    except EOFError:
        return None
    if not raw.isdigit():
        print("请输入数字序号。", file=sys.stderr)
        return None
    n = int(raw)
    if n < 1 or n > len(users):
        print("序号超出范围。", file=sys.stderr)
        return None
    return users[n - 1]


def resolve_user_docx(project_root: str, user: str) -> Path | None:
    """优先 ``<用户>/<用户>.docx``，否则该目录下第一个 .docx。"""
    d = input_root(project_root) / user
    if not d.is_dir():
        return None
    preferred = d / f"{user}.docx"
    if preferred.is_file():
        return preferred
    docxs = sorted(d.glob("*.docx"))
    if docxs:
        return docxs[0]
    return None


def document_body_lines(doc: Document) -> list[str]:
    """按文档顺序遍历段落与表格行（与 Word 中顺序大致一致）。"""
    out: list[str] = []
    for el in doc.element.body:
        if el.tag == qn("w:p"):
            p = Paragraph(el, doc)
            t = p.text.strip()
            if t:
                out.append(t)
        elif el.tag == qn("w:tbl"):
            tbl = Table(el, doc)
            for row in tbl.rows:
                parts = [c.text.strip() for c in row.cells if c.text.strip()]
                if parts:
                    out.append(" | ".join(parts))
    return out


def load_docx_lines(path: Path) -> list[str]:
    doc = Document(str(path))
    return document_body_lines(doc)


# 短于该长度视为只命中目录行或未取到正文，启用回退锚点
_MIN_SECTION_CHARS = 400


def _looks_like_toc_line(line: str) -> bool:
    """目录行常见：标题与页码之间为制表符，段尾为纯数字。"""
    s = line.strip()
    if "\t" not in s:
        return False
    tail = s.rsplit("\t", 1)[-1].strip()
    return tail.isdigit()


def _take_section(
    lines: list[str],
    start_i: int,
    is_end: Callable[[int], bool],
) -> str:
    chunk: list[str] = []
    for j in range(start_i, len(lines)):
        if j > start_i and is_end(j):
            break
        chunk.append(lines[j])
    return "\n".join(chunk)


def extract_section_321(lines: list[str]) -> str:
    """3.2.1 数据库概念设计：跳过目录，必要时用「数据库概念设计」标题定位正文。"""

    def is_end(j: int, start: int) -> bool:
        if j <= start:
            return False
        s = lines[j].strip()
        if re.match(r"^3\.2\.2\b", s) or re.match(r"^3\.2\.2\s", s):
            return True
        if re.match(r"^3\.3\b", s) or s.startswith("3.3"):
            return True
        if "第4章" in s or "第四章" in s or re.match(r"^第\s*4\s*章", s):
            return True
        if s.startswith("数据库表设计"):
            return True
        return False

    start_i: int | None = None
    for i, line in enumerate(lines):
        if _looks_like_toc_line(line):
            continue
        if "3.2.1" not in line:
            continue
        if "数据库" in line or "概念" in line or "概念设计" in line:
            start_i = i
            break
    if start_i is None:
        for i, line in enumerate(lines):
            if _looks_like_toc_line(line):
                continue
            if re.search(r"3\.2\.1", line):
                start_i = i
                break

    text = ""
    if start_i is not None:
        text = _take_section(lines, start_i, lambda j: is_end(j, start_i))

    if len(text.strip()) >= _MIN_SECTION_CHARS:
        return text

    start2: int | None = None
    for i, line in enumerate(lines):
        if _looks_like_toc_line(line):
            continue
        s = line.strip()
        if s == "数据库概念设计":
            start2 = i
            break
        if s.startswith("数据库概念设计") and len(s) <= 24:
            start2 = i
            break
    if start2 is None:
        return text

    text2 = _take_section(lines, start2, lambda j: is_end(j, start2))
    if len(text2.strip()) >= len(text.strip()):
        return text2
    return text


def extract_chapter4(lines: list[str]) -> str:
    """第四章：跳过目录；正文无「第4章」时用「系统详细设计与实现」等锚点；止于「系统测试」或第5章等。"""

    def is_end(j: int, start: int) -> bool:
        if j <= start:
            return False
        s = lines[j].strip()
        if "第5章" in s or "第五章" in s or re.match(r"^第\s*5\s*章", s):
            return True
        if s == "系统测试":
            return True
        if s.startswith("参考文献") or s.startswith("致谢"):
            return True
        if re.match(r"^附录\s*[A-Za-z0-9一二三四]", s):
            return True
        return False

    start_i: int | None = None
    for i, line in enumerate(lines):
        if _looks_like_toc_line(line):
            continue
        s = line.strip()
        if "第4章" in s or "第四章" in s or re.match(r"^第\s*4\s*章", s):
            start_i = i
            break
    if start_i is None:
        for i, line in enumerate(lines):
            if _looks_like_toc_line(line):
                continue
            s = line.strip()
            if len(s) < 100 and re.match(r"^4\s+[\u4e00-\u9fff]", s):
                start_i = i
                break

    text = ""
    if start_i is not None:
        text = _take_section(lines, start_i, lambda j: is_end(j, start_i))

    if len(text.strip()) >= _MIN_SECTION_CHARS:
        return text

    start2: int | None = None
    for i, line in enumerate(lines):
        if _looks_like_toc_line(line):
            continue
        s = line.strip()
        if s == "系统详细设计与实现":
            start2 = i
            break
        if s.startswith("系统详细设计与实现") and len(s) <= 32:
            start2 = i
            break
    if start2 is None:
        return text

    text2 = _take_section(lines, start2, lambda j: is_end(j, start2))
    if len(text2.strip()) >= len(text.strip()):
        return text2
    return text


def clip_text(text: str, max_chars: int, label: str) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return (
        text[:max_chars]
        + f"\n\n……【{label} 过长，已截断至约 {max_chars} 字符，请必要时拆分论文或提高上限】",
        True,
    )


def run_paper_mode(
    project_root: str,
    *,
    max_chars_per_section: int = 100_000,
) -> tuple[str, str, str, str, str] | None:
    """
    交互选用户、读 docx、抽取章节，返回
    (user, path_str, section_321, chapter4, agent_user_content)。
    失败返回 None。
    """
    users = list_input_users(project_root)
    uid = pick_user_interactive(users)
    if not uid:
        return None
    p = resolve_user_docx(project_root, uid)
    if p is None:
        print(f"未找到 {uid} 目录下的 .docx 文件。", file=sys.stderr)
        return None
    lines = load_docx_lines(p)
    s321 = extract_section_321(lines)
    ch4 = extract_chapter4(lines)
    if not s321.strip():
        print("警告：未定位到 3.2.1 数据库概念设计，ER 将缺少依据。", file=sys.stderr)
    if not ch4.strip():
        print("警告：未定位到第四章，时序图/流程图将缺少依据。", file=sys.stderr)
    s321, _ = clip_text(s321, max_chars_per_section, "3.2.1")
    ch4, _ = clip_text(ch4, max_chars_per_section, "第四章")
    content = DiagramAgentRunner.build_thesis_batch_content(
        project_root, uid, s321, ch4
    )
    return uid, str(p), s321, ch4, content
