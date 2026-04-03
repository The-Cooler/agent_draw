## 陈氏ER图标准模板代码

### 完整XML模板（10个属性）

```xml
 <mxCell id="2" parent="1" style="shape=rectangle;whiteSpace=wrap;html=1;strokeWidth=1;fontSize=14;fontStyle=0;fontColor=#000000;fillColor=#ffffff" value="用户" vertex="1">
          <mxGeometry height="60" width="100" x="360" y="250" as="geometry" />
        </mxCell>
        <mxCell id="3" parent="1" style="ellipse;whiteSpace=wrap;html=1;strokeWidth=1;fontSize=14;fontStyle=4;fontColor=#000000;fillColor=#ffffff" value="用户ID" vertex="1">
          <mxGeometry height="50" width="100" x="360" y="127" as="geometry" />
        </mxCell>
        <mxCell id="4" parent="1" style="ellipse;whiteSpace=wrap;html=1;strokeWidth=1;fontSize=14;fontStyle=0;fontColor=#000000;fillColor=#ffffff" value="用户名" vertex="1">
          <mxGeometry height="50" width="100" x="482" y="155" as="geometry" />
        </mxCell>
        <mxCell id="5" parent="1" style="ellipse;whiteSpace=wrap;html=1;strokeWidth=1;fontSize=14;fontStyle=0;fontColor=#000000;fillColor=#ffffff" value="密码" vertex="1">
          <mxGeometry height="50" width="100" x="539" y="225" as="geometry" />
        </mxCell>
        <mxCell id="6" parent="1" style="ellipse;whiteSpace=wrap;html=1;strokeWidth=1;fontSize=14;fontStyle=0;fontColor=#000000;fillColor=#ffffff" value="真实姓名" vertex="1">
          <mxGeometry height="50" width="100" x="533" y="301" as="geometry" />
        </mxCell>
        <mxCell id="7" parent="1" style="ellipse;whiteSpace=wrap;html=1;strokeWidth=1;fontSize=14;fontStyle=0;fontColor=#000000;fillColor=#ffffff" value="手机号" vertex="1">
          <mxGeometry height="50" width="100" x="465" y="357" as="geometry" />
        </mxCell>
        <mxCell id="8" parent="1" style="ellipse;whiteSpace=wrap;html=1;strokeWidth=1;fontSize=14;fontStyle=0;fontColor=#000000;fillColor=#ffffff" value="邮箱" vertex="1">
          <mxGeometry height="50" width="100" x="360" y="378" as="geometry" />
        </mxCell>
        <mxCell id="9" parent="1" style="ellipse;whiteSpace=wrap;html=1;strokeWidth=1;fontSize=14;fontStyle=0;fontColor=#000000;fillColor=#ffffff" value="角色类型" vertex="1">
          <mxGeometry height="50" width="100" x="245" y="357" as="geometry" />
        </mxCell>
        <mxCell id="10" parent="1" style="ellipse;whiteSpace=wrap;html=1;strokeWidth=1;fontSize=14;fontStyle=0;fontColor=#000000;fillColor=#ffffff" value="注册时间" vertex="1">
          <mxGeometry height="50" width="100" x="185" y="301" as="geometry" />
        </mxCell>
        <mxCell id="11" parent="1" style="ellipse;whiteSpace=wrap;html=1;strokeWidth=1;fontSize=14;fontStyle=0;fontColor=#000000;fillColor=#ffffff" value="最后登录时间" vertex="1">
          <mxGeometry height="50" width="100" x="181" y="227" as="geometry" />
        </mxCell>
        <mxCell id="12" parent="1" style="ellipse;whiteSpace=wrap;html=1;strokeWidth=1;fontSize=14;fontStyle=0;fontColor=#000000;fillColor=#ffffff" value="用户状态" vertex="1">
          <mxGeometry height="50" width="100" x="238" y="163" as="geometry" />
        </mxCell>
        <mxCell id="13" edge="1" parent="1" source="3" style="edgeStyle=none;html=1;endArrow=none;strokeWidth=1;fontColor=#000000" target="2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="14" edge="1" parent="1" source="4" style="edgeStyle=none;html=1;endArrow=none;strokeWidth=1;fontColor=#000000" target="2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="15" edge="1" parent="1" source="5" style="edgeStyle=none;html=1;endArrow=none;strokeWidth=1;fontColor=#000000" target="2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="16" edge="1" parent="1" source="6" style="edgeStyle=none;html=1;endArrow=none;strokeWidth=1;fontColor=#000000" target="2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="17" edge="1" parent="1" source="7" style="edgeStyle=none;html=1;endArrow=none;strokeWidth=1;fontColor=#000000" target="2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="18" edge="1" parent="1" source="8" style="edgeStyle=none;html=1;endArrow=none;strokeWidth=1;fontColor=#000000" target="2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="19" edge="1" parent="1" source="9" style="edgeStyle=none;html=1;endArrow=none;strokeWidth=1;fontColor=#000000" target="2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="20" edge="1" parent="1" source="10" style="edgeStyle=none;html=1;endArrow=none;strokeWidth=1;fontColor=#000000" target="2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="21" edge="1" parent="1" source="11" style="edgeStyle=none;html=1;endArrow=none;strokeWidth=1;fontColor=#000000" target="2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="22" edge="1" parent="1" source="12" style="edgeStyle=none;html=1;endArrow=none;strokeWidth=1;fontColor=#000000" target="2">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
```

---

### 替换规则

| 占位符 | 替换内容 | 对应cell_id |
|--------|----------|-------------|
| `[实体名]` | 实体名称 | id="2" |
| `[主键属性]` | 主键属性名（带下划线） | id="3" |
| `[属性2]`~`[属性10]` | 其余属性名 | id="4"~id="12" |

### 删除多余属性方法
若新实体属性少于10个，**删除对应的属性椭圆和连接线**：
- 删除属性：删除对应 id 的 mxCell（如 id="12"）
- 删除连线：删除对应 id 的 mxCell（如 id="22"）

**示例**：若只有6个属性，删除 id="9"~"12"（属性）和 id="19"~"22"（连线）

---

### 提示词模板

```
绘制陈氏ER图，使用标准模板：
- 实体：[实体名称]
- 主键：[主键属性]（加下划线）
- 属性：[属性1]、[属性2]、[属性3]...

按模板布局，多余属性直接删除对应cell_id。
样式：线宽1pt，字体14pt，黑白配色，主键fontStyle=4。

填充顺序：
位置顺序：主键 → 左1 → 右1 → 左2 → 右2 → 左3 → 右3 → 左4 → 右4 → 正下
对应id：  3  → 12 →  4 → 11 →  5 → 10 →  6 →  9 →  7 →  8
```