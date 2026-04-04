"""
validate_diagram_request：能通过校验的 JSON 形状以本文件实现为准。

ER（type=er）：实体名与各属性 name 须含中文，属性名仅为 ID/id 时可非中文；attributes 至多 10 条（与模板一致）；详见 _validate_er。

保存路径约定：
  ER:        由 er_draw 在代码内拼接为 {project_root}/data/{user}/er/{entity}.vsdx
  sequence:  由 sequence_draw 在代码内拼接为 {project_root}/data/{user}/sequence/{title}.vsdx
  flowchart:  由 flowchart_draw 在代码内拼接为 {project_root}/data/{user}/flowchart/{title}.vsdx
"""

import json
import re
from typing import Any

from langchain_core.tools import tool

from ..er.tools import ER_TEMPLATE_ATTR_SLOTS

_ALLOWED_TYPES = frozenset({"er", "sequence", "flowchart"})
# ER：仅识别 type 是否为 "pk"（主键）；其余 type 不参与校验、不区分 fk/normal
# ER：实体名与属性显示名须含中文；属性名仅为 ID/id（大小写不敏感）时可不含中文
_CJK_IN_NAME = re.compile(r"[\u4e00-\u9fff]")


def _er_label_has_cjk(s: str) -> bool:
    return bool(_CJK_IN_NAME.search(s))


def _er_attr_name_is_id_exempt(name: str) -> bool:
    return name.strip().casefold() == "id"


# sequence/flowchart 的 data.title 作文件名
_TITLE_FORBIDDEN = frozenset('<>:"/\\|?*')


def _validate_title_filename(title: Any, type_label: str) -> list[str]:
    """sequence / flowchart 的 data.title：必填，且须可作文件名主体。"""
    errs: list[str] = []
    if not title or not isinstance(title, str) or not title.strip():
        errs.append(
            f"{type_label}: data.title 必须为非空字符串（用作保存文件名）"
        )
        return errs
    t = title.strip()
    bad = [c for c in t if c in _TITLE_FORBIDDEN or ord(c) < 32]
    if bad:
        errs.append(
            f"{type_label}: data.title 含非法文件名字符，请改为安全文件名（不含 \\ / : * ? \" < > | 等）"
        )
    return errs


def _validate_er(data: Any) -> list[str]:
    """校验 type=er 时的 data；返回问题列表（空列表表示本段无问题）。"""
    errs: list[str] = []
    if not isinstance(data, dict):
        errs.append("data 必须是对象")
        return errs
    entity = data.get("entity")
    if not entity or not isinstance(entity, str) or not entity.strip():
        errs.append("er: data.entity 必须为非空字符串")
    elif not _er_label_has_cjk(entity.strip()):
        errs.append("er: data.entity 须使用中文（须含中日韩统一表意文字）")
    attrs = data.get("attributes")
    if not isinstance(attrs, list):
        errs.append("er: data.attributes 必须为数组")
        return errs
    if len(attrs) == 0:
        errs.append("er: data.attributes 至少包含一个属性")
    elif len(attrs) > ER_TEMPLATE_ATTR_SLOTS:
        errs.append(
            f"er: data.attributes 至多 {ER_TEMPLATE_ATTR_SLOTS} 条（与模板属性位数量一致）"
        )
    pk_count = 0
    for i, a in enumerate(attrs):
        if not isinstance(a, dict):
            errs.append(f"er: attributes[{i}] 必须是对象")
            continue
        name = a.get("name")
        if not name or not isinstance(name, str):
            errs.append(f"er: attributes[{i}].name 必须为非空字符串")
        elif isinstance(name, str) and name.strip():
            if not _er_attr_name_is_id_exempt(name) and not _er_label_has_cjk(name.strip()):
                errs.append(
                    f"er: attributes[{i}].name 须使用中文（属性名仅为 ID/id 时可非中文）"
                )
        t = a.get("type")
        if t == "pk":
            pk_count += 1
    if pk_count > 1:
        errs.append("er: 至多一个属性的 type 可为 pk（主键）")
    return errs


def _validate_sequence(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["data 必须是对象"]
    from ..sequence.slots import validate_sequence_data

    return validate_sequence_data(data)


def _validate_flowchart(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["data 必须是对象"]
    from ..flowchart.spec import validate_flowchart_content

    errs = _validate_title_filename(data.get("title"), "flowchart")
    errs.extend(validate_flowchart_content(data))
    return errs


@tool
def validate_diagram_request(json_text: str) -> dict:
    """
    校验顶层绘图 JSON 字符串。规则见本模块源码。

    返回：valid、errors、parsed、hint。valid 为 true 后再调用 er_draw / sequence_draw / flowchart_draw。流程图可先用 check_flowchart_nodes 预检 nodes。
    """
    errors: list[str] = []
    try:
        obj = json.loads(json_text)
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "errors": [f"JSON 解析失败: {e}"],
            "parsed": None,
            "hint": "请输出合法 JSON 字符串后重试。",
        }

    if not isinstance(obj, dict):
        return {
            "valid": False,
            "errors": ["根节点必须是 JSON 对象"],
            "parsed": None,
            "hint": "根节点必须是对象。",
        }

    user = obj.get("user")
    if not user or not isinstance(user, str) or not user.strip():
        errors.append("user 必须为非空字符串")

    dtype = obj.get("type")
    if dtype not in _ALLOWED_TYPES:
        errors.append(
            f'type 必须是 "er"、"sequence"、"flowchart" 之一，当前: {dtype!r}'
        )

    data = obj.get("data")
    if not isinstance(data, dict):
        errors.append("data 必须是对象")
        data = {}

    if dtype == "er":
        errors.extend(_validate_er(data))
    elif dtype == "sequence":
        errors.extend(_validate_sequence(data))
    elif dtype == "flowchart":
        errors.extend(_validate_flowchart(data))

    valid = len(errors) == 0
    return {
        "valid": valid,
        "errors": errors,
        "parsed": obj,
        "hint": (
            "规范校验已通过：按 type 调用唯一对应绘图工具，并遵守路径约定。"
            if valid
            else "请根据 errors 修正 JSON 后再次调用 validate_diagram_request，直至 valid 为 true。"
        ),
    }
