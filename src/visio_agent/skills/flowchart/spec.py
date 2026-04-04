"""
流程图模板 1 / 2 的节点顺序与 role 约定（见仓库根目录《流程图模板说明.md》）。

模板1：开始 → 输入(平行四边形) → 处理×2 → 判断(平行四边形) → 处理×2 → 结束
模板2：开始 → 判断 → 处理 → 判断 → 处理×2 → 结束
"""

from __future__ import annotations

from typing import Any

FLOWCHART_TEXT_MAX_LEN = 5

# 与 Visio 模板占位顺序一致：第 i 个可替换形状对应 nodes[i]
TEMPLATE_1_ROLES: tuple[str, ...] = (
    "start",  # 圆角·开始
    "input",  # 平行四边形·输入（不可填判断文案）
    "process",  # 矩形·处理
    "process",
    "decision",  # 平行四边形·判断（不可填输入/处理文案）
    "process",
    "process",
    "end",  # 圆角·结束
)

TEMPLATE_2_ROLES: tuple[str, ...] = (
    "start",
    "decision",  # 第一次判断
    "process",
    "decision",  # 第二次判断
    "process",
    "process",
    "end",
)

ROLE_SHAPE_HINT: dict[str, str] = {
    "start": "圆角矩形·开始",
    "end": "圆角矩形·结束",
    "input": "平行四边形·输入",
    "process": "矩形·处理",
    "decision": "平行四边形·判断",
}


def roles_for_template(template: int) -> tuple[str, ...]:
    if template == 1:
        return TEMPLATE_1_ROLES
    if template == 2:
        return TEMPLATE_2_ROLES
    raise ValueError("template 须为 1 或 2")


def normalize_flowchart_template(template: Any) -> int | None:
    if template == 1 or template == "1":
        return 1
    if template == 2 or template == "2":
        return 2
    return None


def validate_flowchart_content(data: dict[str, Any]) -> list[str]:
    """
    校验 data 中的 template、nodes（不含 title）。
    要求每条 text 非空且长度 ≤ FLOWCHART_TEXT_MAX_LEN；nodes[i].role 须与模板第 i 个槽位一致。
    """
    errs: list[str] = []
    t_raw = data.get("template")
    t = normalize_flowchart_template(t_raw)
    if t is None:
        errs.append('flowchart: data.template 须为 1 或 2')
        return errs

    try:
        expected = roles_for_template(t)
    except ValueError as e:
        errs.append(f"flowchart: {e}")
        return errs

    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        errs.append("flowchart: data.nodes 必须为数组")
        return errs

    n_exp = len(expected)
    if len(nodes) != n_exp:
        errs.append(
            f"flowchart: 模板{t} 须恰好 {n_exp} 个节点，当前 {len(nodes)} 个"
        )
        return errs

    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errs.append(f"flowchart: nodes[{i}] 必须是对象")
            continue
        role = node.get("role")
        text = node.get("text")
        exp = expected[i]
        if not isinstance(role, str) or role.strip() != exp:
            hint = ROLE_SHAPE_HINT.get(exp, exp)
            errs.append(
                f"flowchart: nodes[{i}].role 须为 \"{exp}\"（{hint}），"
                f"不可与菱形判断/输入/矩形处理槽位混用；当前 {role!r}"
            )
        if not isinstance(text, str) or not text.strip():
            errs.append(f"flowchart: nodes[{i}].text 须为非空字符串")
        elif isinstance(text, str):
            ts = text.strip()
            if len(ts) > FLOWCHART_TEXT_MAX_LEN:
                errs.append(
                    f"flowchart: nodes[{i}].text 至多 {FLOWCHART_TEXT_MAX_LEN} 个字（当前 {len(ts)}），请删减"
                )

    return errs
