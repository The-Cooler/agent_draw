"""
时序图工具：固定四泳道（用户、前端、后端、数据库），单程 7 条消息、双程 13 条。

模板（须自备）：
  skills/sequence/template/one_way.vsdx   — 占位文案形如 "1. 消息1" … "7. 消息7"
  skills/sequence/template/double_way.vsdx — 占位至 "13. 消息13"

输出路径（代码内固定）：
  {project_root}/data/{user}/sequence/{title}.vsdx
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
import pythoncom
import win32com.client
from langchain_core.tools import tool

from .slots import validate_sequence_data


@tool
def sequence_draw(
    project_root: str,
    user: str,
    title: str,
    trip: str,
    messages: list,
) -> dict:
    """
    绘制时序图；保存路径固定为 project_root/data/user/sequence/title.vsdx。

    Args:
        project_root: 项目根目录绝对路径（与用户消息一致）
        user: 顶层请求中的 user
        title: 图标题（文件名主体，与校验通过的 data.title 一致）
        trip: "one_way" 或 "double_way"
        messages: 与校验通过的 data.messages 一致（每条含 from、to、text）

    Returns:
        {"success": bool, "message": str}
    """
    data = {
        "title": title,
        "trip": trip,
        "messages": messages,
    }
    verr = validate_sequence_data(data)
    if verr:
        return {"success": False, "message": "; ".join(verr)}

    skills_dir = os.path.dirname(__file__)
    template_dir = os.path.join(skills_dir, "template")
    if trip == "one_way":
        template_name = "one_way.vsdx"
    else:
        template_name = "double_way.vsdx"
    template_path = os.path.join(template_dir, template_name)

    if not os.path.exists(template_path):
        return {
            "success": False,
            "message": f"模板不存在: {template_path}（请放置 {template_name}）",
        }

    root = os.path.abspath(project_root.strip())
    usr = user.strip()
    ttl = title.strip()
    out_dir = os.path.join(root, "data", usr, "sequence")
    abs_output = str(Path(out_dir) / f"{ttl}.vsdx")

    lines: list[str] = []
    for i, m in enumerate(messages):
        if not isinstance(m, dict):
            continue
        raw = m.get("text", "")
        text = raw.strip() if isinstance(raw, str) else ""
        lines.append(f"{i + 1}. {text}")

    pythoncom.CoInitialize()
    try:
        os.makedirs(out_dir, exist_ok=True)
        shutil.copy2(template_path, abs_output)

        visio = win32com.client.Dispatch("Visio.Application")
        visio.Visible = False
        doc = visio.Documents.Open(abs_output)
        page = doc.Pages.ItemU(1)

        pat = re.compile(r"^(\d+)\.\s*消息\d+$")
        for i in range(1, page.Shapes.Count + 1):
            shape = page.Shapes.ItemU(i)
            try:
                original = shape.Text or ""
            except Exception:
                continue
            m = pat.match(original.strip())
            if not m:
                continue
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(lines):
                shape.Text = lines[idx]

        doc.Save()
        doc.Close()
        visio.Quit()

        return {"success": True, "message": f"已保存: {abs_output}"}

    except Exception as e:
        try:
            visio.Quit()
        except Exception:
            pass
        return {"success": False, "message": f"失败: {e}"}

    finally:
        pythoncom.CoUninitialize()
