"""
流程图：按模板 1/2 填充 Visio。

占位：节点形状 Text 仅为数字 `1`…`N`（N=模板槽位数；模板1为8，模板2为7）。
先做空白/全角数字规范化后再解析。

输出：{project_root}/data/{user}/flowchart/{title}.vsdx
"""

from __future__ import annotations

import os
from typing import Any
import re
import shutil
from pathlib import Path

import pythoncom
import win32com.client
from langchain_core.tools import tool

from .spec import normalize_flowchart_template, validate_flowchart_content

_TITLE_FORBIDDEN = frozenset('<>:"/\\|?*')

# 全角数字 → 半角，便于识别 Visio 里常见的「１」「２」
_FW_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


def _normalize_placeholder_raw(text: str) -> str:
    """去掉空白/零宽字符，全角数字转半角。"""
    s = (text or "").strip().translate(_FW_DIGITS)
    return re.sub(r"[\s\u200b\u00a0\r\n\t]+", "", s)


def _iter_visio_shapes(container: Any) -> Any:
    """深度优先遍历 Page 或组合内的所有 Shape。"""
    try:
        count = int(container.Shapes.Count)
    except Exception:
        return
    for i in range(1, count + 1):
        try:
            sh = container.Shapes.ItemU(i)
        except Exception:
            continue
        yield sh
        try:
            sub = int(sh.Shapes.Count)
        except Exception:
            sub = 0
        if sub > 0:
            yield from _iter_visio_shapes(sh)


def _parse_flowchart_placeholder_index(text: str, max_slot: int) -> int | None:
    """占位序号 1..max_slot：规范化后整段须为十进制数字。"""
    compact = _normalize_placeholder_raw(text)
    if not compact or not re.fullmatch(r"\d+", compact):
        return None
    v = int(compact)
    if 1 <= v <= max_slot:
        return v
    return None


def _validate_flowchart_title(title: str) -> list[str]:
    errs: list[str] = []
    if not title or not isinstance(title, str) or not title.strip():
        errs.append("flowchart: title 必须为非空字符串（用作文件名）")
        return errs
    t = title.strip()
    if any(c in _TITLE_FORBIDDEN or ord(c) < 32 for c in t):
        errs.append(
            "flowchart: title 含非法文件名字符（不含 \\ / : * ? \" < > | 等）"
        )
    return errs


@tool
def check_flowchart_nodes(template: int, nodes: list) -> dict:
    """
    ReAct 用：检查 nodes 是否满足对应模板的槽位数、role 顺序、每条文案 ≤5 字。
    不含文件名；提交前仍须对完整顶层 JSON 调用 validate_diagram_request。

    Args:
        template: 1 或 2
        nodes: 与 data.nodes 相同，每项含 role、text

    Returns:
        {"ok": bool, "errors": list[str]}
    """
    errs = validate_flowchart_content({"template": template, "nodes": nodes})
    return {"ok": len(errs) == 0, "errors": errs}


@tool
def flowchart_draw(
    project_root: str,
    user: str,
    title: str,
    template: int,
    nodes: list,
) -> dict:
    """
    绘制流程图；保存路径固定为 project_root/data/user/flowchart/title.vsdx。

    Args:
        project_root: 项目根目录绝对路径
        user: 顶层 user
        title: data.title
        template: 1 或 2
        nodes: data.nodes（已通过校验）
    """
    terr = _validate_flowchart_title(title)
    cerr = validate_flowchart_content({"template": template, "nodes": nodes})
    if terr or cerr:
        parts = terr + cerr
        return {"success": False, "message": "; ".join(parts)}

    skills_dir = os.path.dirname(__file__)
    template_dir = os.path.join(skills_dir, "template")
    ti = normalize_flowchart_template(template)
    if ti is None:
        return {"success": False, "message": 'flowchart: template 须为 1 或 2'}
    name = "template_1.vsdx" if ti == 1 else "template_2.vsdx"
    template_path = os.path.join(template_dir, name)
    if not os.path.exists(template_path):
        return {
            "success": False,
            "message": f"模板不存在: {template_path}（请放置 {name}）",
        }

    root = os.path.abspath(project_root.strip())
    usr = user.strip()
    ttl = title.strip()
    out_dir = os.path.join(root, "data", usr, "flowchart")
    abs_output = str(Path(out_dir) / f"{ttl}.vsdx")

    lines: list[str] = []
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            lines.append("")
            continue
        raw = node.get("text", "")
        text = raw.strip() if isinstance(raw, str) else ""
        # 占位用模板里纯数字 1..N 定位；写入 Visio 只放文案，不再带「序号.」前缀
        lines.append(text)

    max_slot = len(lines)
    pythoncom.CoInitialize()
    try:
        os.makedirs(out_dir, exist_ok=True)
        shutil.copy2(template_path, abs_output)

        visio = win32com.client.Dispatch("Visio.Application")
        visio.Visible = False
        doc = visio.Documents.Open(abs_output)
        page = doc.Pages.ItemU(1)

        indexed: list[tuple[int, Any]] = []
        for shape in _iter_visio_shapes(page):
            try:
                raw = shape.Text or ""
            except Exception:
                continue
            idx = _parse_flowchart_placeholder_index(raw, max_slot)
            if idx is None:
                continue
            indexed.append((idx, shape))

        replaced = 0
        for idx, shape in indexed:
            pos = idx - 1
            if not (0 <= pos < len(lines)):
                continue
            try:
                shape.Text = lines[pos]
                replaced += 1
            except Exception:
                pass

        if replaced == 0:
            try:
                doc.Close(2)
            except Exception:
                try:
                    doc.Close()
                except Exception:
                    pass
            try:
                visio.Quit()
            except Exception:
                pass
            try:
                os.remove(abs_output)
            except OSError:
                pass
            return {
                "success": False,
                "message": (
                    f"未替换任何文本：未找到占位（形状 Text 须为 1～{max_slot} 的纯数字，"
                    f"可在组合内子形状上）。已取消生成输出文件。"
                ),
            }

        doc.Save()
        doc.Close()
        visio.Quit()
        msg = f"已保存: {abs_output}（已替换 {replaced}/{max_slot} 处节点文案）"
        if replaced < max_slot:
            msg += "；仍有序号未匹配到形状，请检查模板是否缺占位或与序号不一致。"
        return {"success": True, "message": msg}
    except Exception as e:
        try:
            visio.Quit()
        except Exception:
            pass
        return {"success": False, "message": f"失败: {e}"}
    finally:
        pythoncom.CoUninitialize()
