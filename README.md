# Visio Agent

AI 驱动的 Visio 图表绘制工具。

## 外部接口（全局 JSON）

外部系统与 Agent 交互时，使用统一顶层结构；**`type` 决定 `data` 的对象结构**。由 Agent 根据 `type` 选择对应工具（如 `er_draw`、`sequence_draw`、`flowchart_draw`），应用代码侧无需再写类型路由表。

```json
{
  "user": "用户名",
  "type": "er",
  "data": {}
}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| user | string | 输出位于 `{项目根目录}/data/{user}/` 下，按图表类型分子目录：`er/`、`sequence/`、`flowchart/` |
| type | string | `er` \| `sequence` \| `flowchart` |
| data | object | 随 `type` 变化，见下表 |

### 各 type 的 data 结构

**`type: "er"`**（已实现）

```json
{
  "entity": "学生",
  "attributes": [
    {"name": "学号", "type": "pk"},
    {"name": "姓名", "type": "normal"}
  ]
}
```

属性 `type` 取值：`pk`（主键）、`fk`、`normal`。主键会排在第一位。

**`type: "sequence"`**（占位，工具返回未实现）

```json
{
  "title": "根据内容提炼出标题",
  "participant": "用户",
  "messages": [{"from": "用户", "to": "系统", "text": "登录"}]
}
```

**`type: "flowchart"`**（占位，工具返回未实现）

```json
{
  "title": "根据内容提炼标题",
  "steps": [{"id": "1", "label": "开始"}],
  "edges": [{"from": "1", "to": "2"}]
}
```

**输出路径（约定）**：ER 图为 `{项目根目录}/data/{user}/er/{entity}.vsdx`；时序图为 `{项目根目录}/data/{user}/sequence/`；流程图为 `{项目根目录}/data/{user}/flowchart/`（后两者在工具实现后写入文件）。

详细约定见 [`src/visio_agent/skills/diagram_protocol/SKILL.md`](src/visio_agent/skills/diagram_protocol/SKILL.md)。

### 示例用法

配置 `.env` 中的 `MODEL`、`API_KEY`、`API_BASE` 后，运行项目根目录下的 [`examples.py`](examples.py)：将上述 JSON 作为用户消息的一部分交给 Agent，并在消息中提供**项目根目录**的绝对路径（与 `examples.py` 中写法一致）。

### ER 模板规则

| 属性数量 | 使用模板 |
|----------|----------|
| 奇数 | `src/visio_agent/skills/er/template/ER_odd.vsdx` |
| 偶数 | `src/visio_agent/skills/er/template/ER_even.vsdx` |

- 属性超过模板容量时，超出部分舍弃
- 模板第 1 个属性位置固定为主键

### 返回值（工具）

```json
{
  "success": true,
  "message": "已保存: /path/to/学生.vsdx"
}
```

失败时 `success` 为 `false`，`message` 为原因说明。
