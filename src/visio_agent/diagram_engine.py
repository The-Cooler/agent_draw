"""
陈氏 ER 图 / 流程图 / 时序图 绘制引擎
"""
from .visio_controller import VisioController
from typing import List, Dict, Any, Tuple


class ChenERDiagram:
    """陈氏 ER 图绘制器"""

    ENTITY_FILL = "RGB(220, 230, 241)"
    ENTITY_LINE = "RGB(46, 117, 182)"
    ATTR_FILL = "RGB(255, 245, 238)"
    ATTR_LINE = "RGB(218, 112, 70)"
    REL_FILL = "RGB(255, 242, 204)"
    REL_LINE = "RGB(192, 80, 77)"
    PK_FILL = "RGB(226, 239, 255)"

    def __init__(self, visio_ctrl: VisioController):
        self.v = visio_ctrl

    def draw(self, data: Dict[str, Any], title: str = "Chen ER Diagram"):
        """绘制完整的陈氏 ER 图"""
        self.v.new_document()
        self.v.page_setup(width=16.5, height=11.7, orientation="landscape")
        self.v.set_grid_size(0.25, 0.25)

        if title:
            self._draw_title(title)

        entities = data.get("entities", [])
        relationships = data.get("relationships", [])

        import math
        n_entities = len(entities)
        cols = max(1, math.ceil(math.sqrt(n_entities)))
        start_x, start_y = 1.5, 2.5
        spacing_x, spacing_y = 4.0, 3.5

        # 绘制实体
        for i, entity in enumerate(entities):
            col = i % cols
            row = i // cols
            ex = start_x + col * spacing_x * 1.8
            ey = start_y + row * spacing_y * 1.5
            self._draw_entity(entity, ex, ey)

        # 绘制关系
        rel_start_x = start_x + cols * spacing_x * 1.5 + 1.5
        for i, rel in enumerate(relationships):
            ry = start_y + i * 3.0
            self._draw_relationship(rel, rel_start_x, ry)

    def _draw_title(self, title: str):
        """绘制标题"""
        try:
            shape = self.v.add_rectangle(0.5, 0.3, 15.0, 0.6, text=title)
            if shape:
                shape.Text = title
                shape.get_Cells("CharSize").FormulaU = "24 pt"
                shape.get_Cells("Font").FormulaU = "Arial"
                shape.Line.NoShow = True
                shape.Fill.NoShow = True
        except Exception as e:
            print(f"绘制标题失败: {e}")

    def _draw_entity(self, entity: Dict, x: float, y: float):
        """绘制单个实体（陈氏双矩形风格）"""
        name = entity["name"]
        attrs = entity.get("attributes", [])
        ew, eh = 2.0, 0.7

        # 外框
        outer = self.v.add_rectangle(
            x - ew/2, y - eh/2, ew, eh,
            text=name,
            fill=self.ENTITY_FILL,
            line=self.ENTITY_LINE
        )

        # 内框（双线效果）
        inner = self.v.add_rectangle(
            x - ew/2 + 0.08, y - eh/2 + 0.08,
            ew - 0.16, eh - 0.16,
            fill="RGB(255,255,255)",
            line=self.ENTITY_LINE
        )
        if inner:
            try:
                inner.Line.Weight = 0.75
                inner.Fill.ForeColor.RGB = self.v._parse_color("RGB(255,255,255)")
                if outer:
                    self.v.bring_to_front(outer)
            except Exception as e:
                print(f"设置内框样式失败: {e}")

        # 属性
        attr_y = y + eh/2 + 0.15
        attr_h = 0.35
        attr_w = 1.8

        pk_attrs = [a for a in attrs if a.get("type") == "pk"]
        other_attrs = [a for a in attrs if a.get("type") != "pk"]
        ordered_attrs = pk_attrs + other_attrs

        for j, attr in enumerate(ordered_attrs):
            ay = attr_y + j * (attr_h + 0.1)
            fill = self.PK_FILL if attr.get("type") == "pk" else self.ATTR_FILL
            ellipse = self.v.add_ellipse(
                x - ew/2, ay, attr_w, attr_h,
                text=self._format_attr(attr),
                fill=fill,
                line=self.ATTR_LINE
            )
            if ellipse:
                self.v.add_line(x, y + eh/2, x - ew/2 + attr_w/2, ay + attr_h/2)

    def _format_attr(self, attr: Dict) -> str:
        name = attr["name"]
        t = attr.get("type", "normal")
        if t == "pk":
            return f"*{name}*"
        elif t == "fk":
            return f"/{name}/"
        return name

    def _draw_relationship(self, rel: Dict, x: float, y: float):
        """绘制关系（菱形）"""
        name = rel.get("name", "")
        cardinality = rel.get("cardinality", "")
        attrs = rel.get("attributes", [])
        rw, rh = 1.8, 1.0

        label = f"{name}\n({cardinality})" if cardinality else name
        diamond = self.v.add_diamond(x - rw/2, y - rh/2, rw, rh,
                                     text=label,
                                     fill=self.REL_FILL,
                                     line=self.REL_LINE)

        # 关系属性
        if attrs:
            attr_y = y + rh/2 + 0.1
            for j, attr in enumerate(attrs):
                ay = attr_y + j * 0.45
                self.v.add_ellipse(
                    x - 0.9, ay, 1.8, 0.35,
                    text=self._format_attr(attr),
                    fill=self.ATTR_FILL,
                    line=self.ATTR_LINE
                )


class FlowchartDiagram:
    """标准流程图绘制器"""

    START_END_FILL = "RGB(83, 147, 72)"
    START_END_LINE = "RGB(56, 96, 49)"
    PROCESS_FILL = "RGB(221, 217, 195)"
    PROCESS_LINE = "RGB(148, 138, 84)"
    DECISION_FILL = "RGB(255, 242, 204)"
    DECISION_LINE = "RGB(192, 80, 77)"
    IO_FILL = "RGB(226, 239, 255)"
    IO_LINE = "RGB(31, 73, 125)"
    ARROW_COLOR = "RGB(89, 89, 89)"

    def __init__(self, visio_ctrl: VisioController):
        self.v = visio_ctrl

    def draw(self, data: Dict[str, Any], title: str = "Flowchart"):
        """绘制流程图"""
        self.v.new_document()
        self.v.page_setup(width=11.0, height=8.5, orientation="portrait")
        self.v.set_grid_size(0.25, 0.25)

        if title:
            self._draw_title(title)

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        layout = self._auto_layout(nodes, edges)
        shape_map = {}

        for node_id, (x, y) in layout.items():
            node = next((n for n in nodes if n["id"] == node_id), None)
            if not node:
                continue
            shape = self._draw_node(node, x, y)
            if shape:
                shape_map[node_id] = shape

        for edge in edges:
            frm, to = edge.get("from"), edge.get("to")
            if frm in shape_map and to in shape_map:
                self._draw_edge(shape_map[frm], shape_map[to], edge.get("label", ""))

    def _draw_title(self, title: str):
        try:
            shape = self.v.add_rectangle(0.5, 0.3, 10.0, 0.5, text=title)
            if shape:
                shape.get_Cells("CharSize").FormulaU = "22 pt"
                shape.get_Cells("Font").FormulaU = "Arial"
                shape.Line.NoShow = True
                shape.Fill.NoShow = True
        except Exception as e:
            print(f"绘制标题失败: {e}")

    def _draw_node(self, node: Dict, x: float, y: float):
        ntype = node.get("type", "process")
        label = node.get("label", node.get("id", ""))
        w, h = 2.2, 0.9

        if ntype == "terminal":
            shape = self.v.add_stadium(x - w/2, y - h/2, w, h, text=label,
                                        fill=self.START_END_FILL,
                                        line=self.START_END_LINE)
        elif ntype == "decision":
            shape = self.v.add_diamond(x - w/2, y - h/2, w, h, text=label,
                                        fill=self.DECISION_FILL,
                                        line=self.DECISION_LINE)
        elif ntype == "io":
            shape = self.v.add_parallelogram(x - w/2, y - h/2, w, h, text=label,
                                               fill=self.IO_FILL,
                                               line=self.IO_LINE)
        else:
            shape = self.v.add_rectangle(x - w/2, y - h/2, w, h, text=label,
                                          fill=self.PROCESS_FILL,
                                          line=self.PROCESS_LINE)
        return shape

    def _draw_edge(self, from_shape, to_shape, label: str = ""):
        try:
            from_x = from_shape.get_Cells("PinX").ResultIU
            from_y = from_shape.get_Cells("PinY").ResultIU
            to_x = to_shape.get_Cells("PinX").ResultIU
            to_y = to_shape.get_Cells("PinY").ResultIU

            line = self.v.add_line(from_x, from_y, to_x, to_y)
            if line:
                line.Line.Color.RGB = self.v._parse_color(self.ARROW_COLOR)
                line.Line.Weight = 1.5
                line.EndArrow = 2

            if label:
                mid_x = (from_x + to_x) / 2
                mid_y = (from_y + to_y) / 2
                ls = self.v.add_rectangle(mid_x - 0.5, mid_y - 0.15, 1.0, 0.3, text=label)
                if ls:
                    ls.Line.NoShow = True
                    ls.Fill.NoShow = True
                    ls.get_Cells("CharSize").FormulaU = "10 pt"
        except Exception as e:
            print(f"绘制连线失败: {e}")

    def _auto_layout(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Tuple[float, float]]:
        if not nodes:
            return {}
        from collections import defaultdict
        import math

        levels: Dict[str, int] = {}
        visited: set = set()

        def assign(nid: str, lvl: int):
            if nid in visited and lvl <= levels.get(nid, 999):
                return
            levels[nid] = lvl
            visited.add(nid)
            for edge in edges:
                if edge.get("from") == nid:
                    assign(edge.get("to"), lvl + 1)

        terminals = [n["id"] for n in nodes if n.get("type") == "terminal"]
        if terminals:
            for tid in terminals:
                assign(tid, 0)

        for node in nodes:
            if node["id"] not in visited:
                assign(node["id"], 0)

        groups = defaultdict(list)
        for nid, lvl in levels.items():
            groups[lvl].append(nid)

        max_lvl = max(groups.keys()) if groups else 0
        layout = {}
        start_x, start_y = 5.5, 1.5
        dy = 1.4

        for lvl in range(max_lvl + 1):
            items = groups.get(lvl, [])
            if not items:
                continue
            n_at = len(items)
            total_h = (n_at - 1) * dy
            y0 = start_y + (max_lvl - lvl) * 2.5 - total_h / 2
            for j, nid in enumerate(sorted(items)):
                layout[nid] = (start_x + lvl * 2.8, y0 + j * dy)
        return layout


class SequenceDiagram:
    """UML 时序图绘制器"""

    PARTICIPANT_FILL = "RGB(220, 230, 241)"
    PARTICIPANT_LINE = "RGB(46, 117, 182)"
    SELF_CALL_FILL = "RGB(255, 242, 204)"
    RETURN_COLOR = "RGB(148, 138, 84)"

    def __init__(self, visio_ctrl: VisioController):
        self.v = visio_ctrl

    def draw(self, data: Dict[str, Any], title: str = "Sequence Diagram"):
        """绘制时序图"""
        self.v.new_document()
        self.v.page_setup(width=13.5, height=8.5, orientation="landscape")
        self.v.set_grid_size(0.25, 0.25)

        if title:
            self._draw_title(title)

        participants = data.get("participants", [])
        interactions = data.get("interactions", [])

        px_start, px_spacing = 2.0, 2.8
        y_start, y_spacing = 1.5, 0.65

        px_map: Dict[str, float] = {p: px_start + i * px_spacing for i, p in enumerate(participants)}

        for p, px in px_map.items():
            self._draw_participant(px, y_start, p)

        page_h = self.v.get_page_height()
        for p, px in px_map.items():
            self._draw_lifeline(px, y_start + 0.6, page_h - 1.0)

        y_cur = y_start + 0.75
        for interaction in interactions:
            frm = interaction.get("from", "")
            to = interaction.get("to", "")
            msg = interaction.get("message", "")
            itype = interaction.get("type", "sync")

            if frm not in px_map or to not in px_map:
                continue

            fx, tx = px_map[frm], px_map[to]
            if itype == "self":
                self._draw_self_call(fx, y_cur, msg)
            elif itype == "return":
                self._draw_message(fx, tx, y_cur, msg, dashed=True)
            else:
                self._draw_message(fx, tx, y_cur, msg, dashed=False)
            y_cur += y_spacing

    def _draw_title(self, title: str):
        try:
            shape = self.v.add_rectangle(0.5, 0.2, 12.0, 0.5, text=title)
            if shape:
                shape.get_Cells("CharSize").FormulaU = "22 pt"
                shape.get_Cells("Font").FormulaU = "Arial"
                shape.Line.NoShow = True
                shape.Fill.NoShow = True
        except Exception as e:
            print(f"绘制标题失败: {e}")

    def _draw_participant(self, x: float, y: float, name: str):
        shape = self.v.add_rectangle(x - 0.9, y, 1.8, 0.6, text=name,
                                      fill=self.PARTICIPANT_FILL,
                                      line=self.PARTICIPANT_LINE)
        if shape:
            try:
                shape.Line.Weight = 1.5
            except Exception as e:
                print(f"设置参与者样式失败: {e}")

    def _draw_lifeline(self, x: float, y_start: float, y_end: float):
        line = self.v.add_line(x, y_start, x, y_end)
        if line:
            try:
                line.Line.Color.RGB = self.v._parse_color("RGB(46, 117, 182)")
                line.Line.Weight = 1.0
            except Exception as e:
                print(f"设置生命线样式失败: {e}")

    def _draw_message(self, x1: float, x2: float, y: float,
                      msg: str, dashed: bool = False):
        line = self.v.add_line(x1, y, x2, y)
        if line:
            try:
                if dashed:
                    line.Line.Pattern = 5
                    line.Line.Color.RGB = self.v._parse_color(self.RETURN_COLOR)
                else:
                    line.EndArrow = 2
                    line.Line.Color.RGB = self.v._parse_color("RGB(89, 89, 89)")
                line.Line.Weight = 1.2
            except Exception as e:
                print(f"设置消息线样式失败: {e}")

        mid_x = (x1 + x2) / 2
        ls = self.v.add_rectangle(mid_x - 1.5, y - 0.22, 3.0, 0.28, text=msg)
        if ls:
            try:
                ls.Line.NoShow = True
                ls.Fill.NoShow = True
                ls.get_Cells("CharSize").FormulaU = "9 pt"
            except Exception as e:
                print(f"设置消息标签样式失败: {e}")

    def _draw_self_call(self, x: float, y: float, msg: str):
        box = self.v.add_rectangle(x - 0.15, y, 0.3, 0.5,
                                    fill=self.SELF_CALL_FILL,
                                    line=self.PARTICIPANT_LINE)
        if box:
            try:
                box.Line.Weight = 1.0
            except Exception as e:
                print(f"设置自调用框样式失败: {e}")
        ls = self.v.add_rectangle(x + 0.3, y + 0.05, 3.0, 0.28, text=f"self: {msg}")
        if ls:
            try:
                ls.Line.NoShow = True
                ls.Fill.NoShow = True
                ls.get_Cells("CharSize").FormulaU = "9 pt"
            except Exception as e:
                print(f"设置自调用标签样式失败: {e}")


class DiagramEngine:
    """统一绘图引擎"""

    def __init__(self, visio_ctrl: VisioController):
        self.v = visio_ctrl
        self.engines = {
            "er": ChenERDiagram(visio_ctrl),
            "flowchart": FlowchartDiagram(visio_ctrl),
            "sequence": SequenceDiagram(visio_ctrl),
        }

    def draw(self, diagram_type: str, data: Dict[str, Any],
             output_path: str, title: str = "") -> bool:
        """绘制并保存图表"""
        engine = self.engines.get(diagram_type)
        if not engine:
            print(f"不支持的图表类型: {diagram_type}")
            return False
        try:
            engine.draw(data, title=title or data.get("title", ""))
            self.v.save(output_path)
            print(f"图表已保存: {output_path}")
            return True
        except Exception as e:
            print(f"绘制失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def draw_from_text(self, diagram_type: str, description: str,
                       output_path: str) -> bool:
        """从自然语言描述绘制图表（本地解析）"""
        from .parser import parse_diagram_description
        data = parse_diagram_description(diagram_type, description)
        return self.draw(diagram_type, data, output_path,
                         title=data.get("title", ""))
