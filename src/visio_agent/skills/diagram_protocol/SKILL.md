---
name: diagram_protocol
description: "处理标准绘图 JSON 请求：根据 type 选择 er_draw、sequence_draw 或 flowchart_draw"
---

# 图表请求全局协议

## 顶层 JSON（必填）

```json
{
  "user": "用户名",
  "type": "er | sequence | flowchart",
  "data": {}
}
```

| 字段 | 说明 |
|------|------|
| user | 用于 `data/` 下的用户子目录，各类图表按 type 分目录保存（见各节路径约定） |
| type | 决定 `data` 的结构与应调用的工具 |
| data | 与 `type` 对应的对象，见下文 |

用户消息中会给出 **项目根目录** 的绝对路径，拼路径时必须使用该目录。

## 按 type 选择工具（路由规则）

| type | 工具 | data 结构 |
|------|------|-----------|
| er | `er_draw` | 见下节 |
| sequence | `sequence_draw` | 见下节（当前为占位，仍应调用以统一流程） |
| flowchart | `flowchart_draw` | 见下节（当前为占位） |

未知 `type`：不要调用绘图工具，向用户说明仅支持上述三种。

---

## type = `er`

**data 结构：**

```json
{
  "entity": "实体名称",
  "attributes": [
    {"name": "属性名", "type": "pk | fk | normal"}
  ]
}
```

**调用 `er_draw`：**

- `entity` ← `data.entity`
- `attributes` ← `data.attributes`（属性键名小写 `name`，不要用 `Name`）
- `output_path`：`{项目根目录}/data/{user}/er/{entity}.vsdx`（绝对路径；`er_draw` 会创建父目录）

---

## type = `sequence`（时序图）

**data 最小约定示例：**

```json
{
  "title": "可选标题",
  "participants": ["用户", "系统"],
  "messages": [
    {"from": "用户", "to": "系统", "text": "登录"}
  ]
}
```

调用 `sequence_draw(user=顶层user, data=data)`。输出目录约定：`{项目根目录}/data/{user}/sequence/`（实现后 `.vsdx` 等文件放于此；当前为占位，会返回未实现说明）。

---

## type = `flowchart`（流程图）

**data 最小约定示例：**

```json
{
  "title": "可选标题",
  "steps": [
    {"id": "1", "label": "开始"},
    {"id": "2", "label": "处理"}
  ],
  "edges": [
    {"from": "1", "to": "2"}
  ]
}
```

调用 `flowchart_draw(user=顶层user, data=data)`。输出目录约定：`{项目根目录}/data/{user}/flowchart/`（实现后文件放于此；当前为占位，会返回未实现说明）。

---

## 工作流小结

1. 解析用户消息中的 JSON 与项目根目录路径。
2. 读取 `type`，只调用对应的一个绘图工具。
3. 将工具返回的 `success` / `message` 如实反馈给用户。
