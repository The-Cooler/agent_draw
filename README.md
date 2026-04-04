# Visio Agent

Deep Agent + Visio（Windows）。**接口与硬规则**见下文；**Agent 操作步骤**见 `src/visio_agent/skills/**/SKILL.md`；**校验实现源码**见 [`validate_tool.py`](src/visio_agent/skills/diagram_protocol/validate_tool.py)（与本文不一致时以源码为准）。

---

## 运行

1. `.env`：`MODEL`、`API_KEY`、`API_BASE`
2. `uv run python examples.py "<一句自然语言>"`（无参数会提示用法并退出）

### 编程调用（自然语言 + 流式）

`DiagramAgentRunner`（[`diagram_runner.py`](src/visio_agent/diagram_runner.py)）会在用户消息中写明**项目根目录**，要求 Agent 调用 `er_draw` 时传入相同的 `project_root`，并对 Agent 使用 `stream_mode=["messages","updates"]`。`print_stream_events` **默认不打印** `[updates]`，仅输出助手正文；调试工具回包时可传 `print_updates=True`。

```python
import sys
sys.path.insert(0, "src")
from visio_agent import DiagramAgentRunner, print_stream_events

runner = DiagramAgentRunner(project_root=r"E:\Desktop\langchain_draw")
print_stream_events(runner, "<你的自然语言需求>")
# 或: for mode, payload in runner.stream("……"): ...
```

`er_draw` **不接受**输出路径参数；保存位置在代码里固定为 `{项目根}/data/{user}/er/{entity}.vsdx`，避免模型自拟路径。

---

## 顶层请求 JSON（外部 / Agent 整理后的统一形状）

校验工具入参为 **整段对象的 JSON 字符串**（`json.dumps`）。

```json
{
  "user": "非空字符串",
  "type": "er | sequence | flowchart",
  "data": {}
}
```

| 字段 | 说明 |
|------|------|
| `user` | 输出目录里的用户子文件夹名 |
| `type` | 决定 `data` 结构与后续绘图工具 |
| `data` | 随 `type` 变化，见下三节 |

---

## 保存路径（约定）

`{项目根}` 为运行环境约定的工程根目录（如 `examples.py` 所在目录）。**ER** 由 `er_draw` 拼接；**sequence** 由 `sequence_draw` 拼接；flowchart 仍为占位。

| `type` | 文件路径 |
|--------|----------|
| `er` | `{项目根}/data/{user}/er/{entity}.vsdx` |
| `sequence` | `{项目根}/data/{user}/sequence/{title}.vsdx` |
| `flowchart` | `{项目根}/data/{user}/flowchart/{title}.vsdx` |

---

## `validate_diagram_request`（工具）

- **入参**：`json_text` — 上述顶层对象的 **JSON 字符串**。
- **返回**：
  - `valid`（bool）
  - `errors`（字符串列表）
  - `parsed`（解析成功时的对象；根非对象或解析失败时为 `null`）
  - `hint`（短提示）

`type` 为 `er` / `sequence` / `flowchart` 时，对 `data` 的字段校验逻辑见 `validate_tool.py` 内 `_validate_*`。

---

## `type: "er"` — `data` 与 `er_draw`

### 校验（`data`）

| 字段 | 规则 |
|------|------|
| `entity` | 非空字符串，且须含至少一个 CJK（中日韩统一表意文字 `\u4e00-\u9fff`） |
| `attributes` | 非空数组，**至多 10 条**（与模板属性位数一致）；每项为对象，须含非空字符串 `name` |
| `name` 语言 | 须含 CJK；**例外**：`name` 去空白后大小写不敏感等于 `id` 时可非中文 |
| `type`（每项可选） | **仅** `"pk"` 表示主键；**至多一个** `pk`。其余取值或省略均不作 fk/normal 等区分，校验不限制 |

### `er_draw`（入参）

| 参数 | 说明 |
|------|------|
| `project_root` | 项目根目录绝对路径，须与用户消息 / `DiagramAgentRunner` 给出的根目录一致 |
| `user` | 与通过校验的顶层 `user` 一致 |
| `entity` | 与通过校验的 `data.entity` 一致 |
| `attributes` | 与通过校验的 `data.attributes` 一致 |

### `er_draw`（行为）

1. `type == "pk"` 的项排第一，其余保持**传入顺序**。
2. 合法请求下属性恒为 **1～10 条**；`er_draw` 内仍按模板最多 10 格写入（与校验上限一致）。
3. **奇/偶模板**按 **`len(attributes)`** 选 `ER_odd.vsdx` / `ER_even.vsdx`。
4. 写入图形的文字与每项 **`name` 完全一致**，不改写、不翻译。

### `er_draw`（返回）

```json
{ "success": true, "message": "已保存: <路径>" }
```

失败时 `success` 为 `false`，`message` 为原因。

---

## `type: "sequence"` — `data` 与 `sequence_draw`

固定四泳道：**用户 / 前端 / 后端 / 数据库**。`trip` 为 `one_way` 时 **7** 条消息，`double_way` 时 **13** 条；每条 `from`、`to` 须与 [`slots.py`](src/visio_agent/skills/sequence/slots.py) 中序号一致；`text` 非空且 **≤8 字**。

| 字段 | 说明 |
|------|------|
| `title` | 安全文件名主体 |
| `trip` | `one_way` \| `double_way` |
| `messages` | 与 `trip` 长度一致；每项 `{from, to, text}` |

### `sequence_draw`（入参）

| 参数 | 说明 |
|------|------|
| `project_root` | 同 `er_draw` |
| `user` | 顶层 `user` |
| `title` | `data.title` |
| `trip` | `data.trip` |
| `messages` | `data.messages` |

须在 `skills/sequence/template/` 下提供 `one_way.vsdx` / `double_way.vsdx`（消息占位形如 `1. 消息1` …）。详见 `sequence/SKILL.md`。

---

## `type: "flowchart"` — `data`（当前无真绘图）

校验要求（摘要）：`title` 同 sequence；`steps` 非空，项含非空 `id`、`label`；`edges` 为数组，项含非空 `from`、`to`。

工具 **`flowchart_draw`** 仍为占位，**不会生成 vsdx**。

---

## 相关路径

| 用途 | 路径 |
|------|------|
| Agent 与工具注册 | `src/visio_agent/agent.py` |
| 校验实现 | `src/visio_agent/skills/diagram_protocol/validate_tool.py` |
| ER 绘图 | `src/visio_agent/skills/er/tools.py` |
| 测试入口 | `examples.py` |
