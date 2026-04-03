"""
图表描述解析器 - 将自然语言转为图表数据
"""
import re
from typing import Dict, Any, List, Tuple


def parse_diagram_description(diagram_type: str, description: str) -> Dict[str, Any]:
    """根据图表类型和描述，解析生成结构化数据"""

    if diagram_type == "er":
        return _parse_er(description)
    elif diagram_type == "flowchart":
        return _parse_flowchart(description)
    elif diagram_type == "sequence":
        return _parse_sequence(description)
    else:
        return {"title": "Unknown Diagram", "data": description}


def _parse_er(description: str) -> Dict[str, Any]:
    """解析 ER 图描述"""
    data = {"title": "ER Diagram", "entities": [], "relationships": []}

    lines = description.strip().split("\n")

    # 提取标题
    for line in lines[:3]:
        if any(k in line for k in ["标题", "title", "名称", "name"]):
            m = re.search(r'[:：]\s*(.+)', line)
            if m:
                data["title"] = m.group(1).strip()

    current_entity = None
    in_relationships = False

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # 跳过标题行
        if any(k in line for k in ["标题", "title", "名称", "name"]) and ":" in line:
            m = re.search(r'[:：]\s*(.+)', line)
            if m:
                val = m.group(1).strip()
                if val not in ["ER Diagram", "ER图", "ER"]:
                    data["title"] = val
            continue

        # 实体: 读者(学号(pk), 姓名, 年龄)
        # 或 实体: 读者 属性: 学号(pk), 姓名
        entity_match = re.match(r'^实体[:：]\s*(.+)$', line)
        if entity_match:
            if current_entity:
                data["entities"].append(current_entity)
            content = entity_match.group(1).strip()

            # 解析 实体名(属性列表) 格式
            paren_match = re.match(r'(.+?)\s*\((.+)\)\s*$', content)
            if paren_match:
                entity_name = paren_match.group(1).strip()
                attrs_str = paren_match.group(2)
                current_entity = {"name": entity_name, "attributes": []}
                for attr_raw in _split_attrs(attrs_str):
                    attr_name, attr_type = _parse_attribute(attr_raw)
                    current_entity["attributes"].append({"name": attr_name, "type": attr_type})
            else:
                # 只有实体名，等待下一行的属性
                current_entity = {"name": content, "attributes": []}
            in_relationships = False
            continue

        # 属性行: 属性: 学号(pk), 姓名
        # 或直接 PK: 学号 / FK: 学号 / 属性: 学号
        attr_line_match = re.match(r'^(PK|主键|FK|外键|属性|字段)[:：]\s*(.+)', line)
        if attr_line_match and current_entity:
            key_type = attr_line_match.group(1)
            attrs_str = attr_line_match.group(2)
            if key_type in ["PK", "主键"]:
                for attr_raw in _split_attrs(attrs_str):
                    attr_name, _ = _parse_attribute(attr_raw)
                    current_entity["attributes"].append({"name": attr_name, "type": "pk"})
            elif key_type in ["FK", "外键"]:
                for attr_raw in _split_attrs(attrs_str):
                    attr_name, _ = _parse_attribute(attr_raw)
                    current_entity["attributes"].append({"name": attr_name, "type": "fk"})
            else:
                for attr_raw in _split_attrs(attrs_str):
                    attr_name, attr_type = _parse_attribute(attr_raw)
                    current_entity["attributes"].append({"name": attr_name, "type": attr_type})
            continue

        # 关系: 选修(学生, 课程, N:M)
        rel_match = re.match(r'^(关系|relationship|联系)[:：]\s*(.+)$', line)
        if rel_match:
            if current_entity:
                data["entities"].append(current_entity)
                current_entity = None

            content = rel_match.group(2).strip()
            # 解析 关系名(实体1, 实体2, 基数) 格式
            paren_match = re.match(r'(.+?)\s*\((.+)\)\s*$', content)
            if paren_match:
                rel_name = paren_match.group(1).strip()
                rest = paren_match.group(2)
                parts = _split_attrs(rest)
                cardinality = ""
                entities_in = []
                rel_attrs = []
                for part in parts:
                    part = part.strip()
                    if re.match(r'^\d+[:NnMm:]+|\d+:\d+|[NnMm]:[NnMm]|[NnMm]$', part):
                        cardinality = part
                    elif part.lower() not in ["pk", "fk", "normal"]:
                        entities_in.append(part)
                    else:
                        attr_name, attr_type = _parse_attribute(part)
                        rel_attrs.append({"name": attr_name, "type": attr_type})

                data["relationships"].append({
                    "name": rel_name,
                    "entities": entities_in,
                    "cardinality": cardinality,
                    "attributes": rel_attrs
                })
            in_relationships = True
            continue

    if current_entity:
        data["entities"].append(current_entity)

    return data


def _parse_attribute(attr_str: str) -> Tuple[str, str]:
    """解析单个属性字符串，返回 (名称, 类型)
    处理格式: 学号(pk), 姓名(pk), 联系方式 等
    """
    attr_str = attr_str.strip()
    t = "normal"
    lower = attr_str.lower()

    # 检测类型
    if re.search(r'\(pk\)|\(PK\)', attr_str) or "pk" in lower or "主键" in lower or "主码" in lower:
        t = "pk"
    elif re.search(r'\(fk\)|\(FK\)', attr_str) or "fk" in lower or "外键" in lower or "外码" in lower:
        t = "fk"
    elif lower.startswith("*") and lower.count("*") >= 2:
        t = "pk"
    elif lower.startswith("*"):
        t = "fk"

    # 提取名称（去除类型标记）
    name = re.sub(r'\s*\(pk\)|\s*\(PK\)|\s*\(fk\)|\s*\(FK\)|\s*\*+', '', attr_str).strip()
    return name, t


def _split_attrs(s: str) -> List[str]:
    """分割属性列表"""
    # 支持：学号,姓名,年龄 或 学号、姓名、年龄
    parts = re.split(r'[,，、]', s)
    return [p.strip() for p in parts if p.strip()]


def _extract_cardinality(s: str) -> str:
    """提取基数"""
    m = re.search(r'\(([^)]+)\)', s)
    if m:
        return m.group(1).strip()
    # 常见模式
    if "多" in s or "N" in s.upper() or "M" in s.upper():
        if "一" in s or "1" in s:
            return "N:M"
        return "N"
    return ""


def _parse_flowchart(description: str) -> Dict[str, Any]:
    """解析流程图描述"""
    data = {"title": "Flowchart", "nodes": [], "edges": []}

    lines = description.strip().split("\n")
    node_map = {}
    node_counter = 0

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "标题" in line or "title" in line:
            if "标题" in line or "title" in line:
                m = re.search(r'[:：]\s*(.+)', line)
                if m:
                    data["title"] = m.group(1).strip()
            continue

        # 判断节点类型
        ntype = "process"
        if any(k in line for k in ["开始", "结束", "start", "end", "终止"]):
            ntype = "terminal"
        elif any(k in line for k in ["判断", "决策", "是否", "?", "decision"]):
            ntype = "decision"
        elif any(k in line for k in ["输入", "输出", "display", "print", "read", "show"]):
            ntype = "io"

        # 提取节点标签
        label = re.sub(r'^[#\-*\d\.、\s]+', '', line).strip()

        if not label:
            continue

        node_id = f"n{node_counter}"
        node_counter += 1

        node = {"id": node_id, "type": ntype, "label": label}
        data["nodes"].append(node)
        node_map[label] = node_id

    # 根据描述推断流程顺序
    _infer_flow_edges(data, lines, node_map)

    return data


def _infer_flow_edges(data: Dict, lines: List[str], node_map: Dict):
    """根据描述推断流程图的边"""
    # 简单的相邻节点连接
    nodes = data["nodes"]

    for i in range(len(nodes) - 1):
        from_node = nodes[i]
        to_node = nodes[i + 1]

        # 判断是否有分支
        label = from_node["label"]
        edge_label = ""

        if from_node["type"] == "decision":
            if "是" in label or "Y" in label.upper():
                edge_label = "是"
            elif "否" in label or "N" in label.upper():
                edge_label = "否"

        data["edges"].append({
            "from": from_node["id"],
            "to": to_node["id"],
            "label": edge_label
        })


def _parse_sequence(description: str) -> Dict[str, Any]:
    """解析时序图描述"""
    data = {"title": "Sequence Diagram", "participants": [], "interactions": []}

    lines = description.strip().split("\n")
    participants_set = set()
    interactions = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "标题" in line or "title" in line:
            m = re.search(r'[:：]\s*(.+)', line)
            if m:
                data["title"] = m.group(1).strip()
            continue

        # 参与者行
        if "参与者" in line or "participant" in line or "actor" in line:
            m = re.search(r'[:：]\s*(.+)', line)
            if m:
                names = re.split(r'[,，、\s]+', m.group(1).strip())
                for n in names:
                    if n:
                        participants_set.add(n.strip())
            continue

        # 消息行: "A -> B: 消息内容"
        arrow_match = re.match(r'(.+?)\s*(->|=>|→)\s*(.+?)\s*[:：]\s*(.+)', line)
        if arrow_match:
            frm = arrow_match.group(1).strip()
            arrow = arrow_match.group(2)
            to = arrow_match.group(3).strip()
            msg = arrow_match.group(4).strip()

            itype = "sync"
            if arrow in ["=>", "<<"] or "返回" in msg:
                itype = "return"
            if frm == to:
                itype = "self"

            participants_set.add(frm)
            participants_set.add(to)

            interactions.append({
                "from": frm,
                "to": to,
                "message": msg,
                "type": itype
            })
            continue

        # 中文格式 "A 向 B 发送消息"
        send_match = re.match(r'(.+?)\s+(向|给|->|->)\s*(.+?)\s*(发送|调用|请求)?\s*[:：]?\s*(.+)', line)
        if send_match:
            frm = send_match.group(1).strip()
            to = send_match.group(3).strip()
            msg = send_match.group(5).strip()

            itype = "sync"
            if "返回" in msg or "回" in msg:
                itype = "return"
            if frm == to:
                itype = "self"

            participants_set.add(frm)
            participants_set.add(to)

            interactions.append({
                "from": frm,
                "to": to,
                "message": msg,
                "type": itype
            })

    data["participants"] = list(participants_set)
    data["interactions"] = interactions

    return data
