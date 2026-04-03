---
name: flowchart
description: "Use this skill when the user asks to draw a flowchart, process flow, or workflow diagram"
allowed-tools: ["draw_flowchart"]
---

# Flowchart Skill

## Overview

This skill helps generate standard ISO 5807 flowcharts from natural language descriptions.

## Data Format

The draw_flowchart tool expects the following JSON structure:

```json
{
  "title": "图表标题",
  "nodes": [
    {"id": "唯一ID", "type": "terminal|process|decision|io", "label": "显示文本"}
  ],
  "edges": [
    {"from": "节点ID", "to": "节点ID", "label": "分支标签(可选)"}
  ]
}
```

## Node Types

- **terminal**: Start/End points (rounded rectangle, green) - use for "开始", "结束", "start", "end"
- **process**: Processing steps (rectangle, beige) - default for regular steps
- **decision**: Decision points (diamond, yellow) - use for "判断", "是否", "?"
- **io**: Input/Output (parallelogram, blue) - use for "输入", "输出", "display"

## Workflow

1. Parse the user's description to identify all steps
2. Classify each step as terminal, process, decision, or io
3. Determine the flow order between nodes
4. Generate edges connecting the nodes
5. Call draw_flowchart with the data
