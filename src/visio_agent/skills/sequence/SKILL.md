---
name: sequence-diagram
description: "Use this skill when the user asks to draw a sequence diagram, UML timing diagram, or interaction diagram"
allowed-tools: ["draw_sequence_diagram"]
---

# Sequence Diagram Skill

## Overview

This skill helps generate UML sequence diagrams from natural language descriptions.

## Data Format

The draw_sequence_diagram tool expects the following JSON structure:

```json
{
  "title": "图表标题",
  "participants": ["参与者1", "参与者2", "参与者3"],
  "interactions": [
    {
      "from": "发送者",
      "to": "接收者",
      "message": "消息内容",
      "type": "sync|return|self"
    }
  ]
}
```

## Interaction Types

- **sync**: Synchronous call (solid arrow) - standard method call
- **return**: Return value (dashed arrow) - response message
- **self**: Self-call (box on lifeline) - method calling itself

## Workflow

1. Parse the user's description to identify all participants
2. Extract interactions between participants
3. Classify each interaction as sync, return, or self
4. Generate the complete JSON structure
5. Call draw_sequence_diagram with the data
