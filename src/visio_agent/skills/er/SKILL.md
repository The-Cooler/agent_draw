---
name: er
description: "Use this skill when the user asks to draw an ER diagram, entity-relationship diagram, or Chen notation diagram"
allowed-tools: ["draw_er_diagram"]
---

# ER 图技能

## 概述

本技能帮助从自然语言描述生成 Chen 风格的 ER 图（实体-关系图）。

## 数据格式

draw_er_diagram 工具期望以下 JSON 结构：

```json
{
  "title": "图表标题",
  "entities": [
    {
      "name": "实体名",
      "attributes": [
        {"name": "属性名", "type": "pk|fk|normal"}
      ]
    }
  ],
  "relationships": [
    {
      "name": "关系名",
      "entities": ["实体A", "实体B"],
      "cardinality": "N:M",
      "attributes": []
    }
  ]
}
```

## Chen 符号规则

- **实体**：双边框矩形
- **属性**：椭圆形状，主键 (PK) 带下划线，外键 (FK) 斜体
- **关系**：菱形表示，标注基数 (1:1, 1:N, N:M, N:1)

## 属性类型

- `pk`：主键属性（带下划线）
- `fk`：外键属性（斜体）
- `normal`：普通属性

## 关系基数

- `1:1`：一对一
- `1:N`：一对多
- `N:1`：多对一
- `N:M`：多对多

## 工作流程

1. 解析用户描述，识别所有实体及其属性
2. 识别实体之间的关系
3. 确定每个关系的基数
4. **复制模板文件**：首先复制 `ER模板.vsdx` 作为基础
5. **按顺序替换实体和属性 (1,2,3,4...)**：对于每个找到的实体：
   - 如果实体已存在于模板中：保留
   - 如果实体缺失：添加
   - 如需替换实体名称
   - 按编号顺序 (1→2→3→4) 替换/更新属性
6. **删除多余属性**：如果模板有比需求更多的属性，删除多余部分
7. 生成完整的JSON结构
8. 调用 draw_er_diagram 工具

## 模板使用

- **模板文件**：`src/visio_agent/skills/er/ER模板.vsdx`
- 始终先复制模板再进行修改
- 属性按编号顺序排列 (1, 2, 3, 4...)
- 删除任何与实际属性不对应的多余属性形状
