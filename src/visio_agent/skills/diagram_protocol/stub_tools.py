"""
流程图占位工具：保留协议与 Agent 路由闭环；时序图见 skills.sequence.tools。
"""

from langchain_core.tools import tool


@tool
def flowchart_draw(user: str, data: dict) -> dict:
    """
    流程图绘制（占位）。参数与 diagram_protocol 技能中 type=flowchart 的 data 约定一致。

    Args:
        user: 顶层 JSON 的 user 字段
        data: type=flowchart 时的 data 对象

    Returns:
        {"success": bool, "message": str}
    """
    return {
        "success": False,
        "message": "流程图绘制尚未实现（占位工具）。",
    }
