---
name: diagram_protocol
description: "用户要画图或交绘图 JSON 时：先校验再调对应绘图工具"
---

# 绘图请求（执行顺序）

1. 整理顶层 JSON：`user`、`type`（`er` | `sequence` | `flowchart`）、`data`。
2. `json.dumps` 后调用 **`validate_diagram_request`**。
3. 若 `valid` 为 false：按返回的 **`errors`** 改 JSON，再调用校验，直到为 true；不要跳过这一步去调绘图工具。
4. 若 `valid` 为 true：只调下面**一个**工具。
   - `er_draw`：`project_root`、`user`、`entity`、`attributes`；保存 `{项目根}/data/{user}/er/{entity}.vsdx`。
   - `sequence_draw`：`project_root`、`user`、`title`、`trip`、`messages`；保存 `{项目根}/data/{user}/sequence/{title}.vsdx`。
   - `flowchart_draw`：`project_root`、`user`、`title`、`template`（1 或 2）、`nodes`；保存 `{项目根}/data/{user}/flowchart/{title}.vsdx`。

流程图在整表校验前，可多次用 **`check_flowchart_nodes`**（仅 `template` + `nodes`）做 ReAct 自检。

| type | 工具 |
|------|------|
| er | `er_draw` |
| sequence | `sequence_draw` |
| flowchart | `flowchart_draw` |

5. 把绘图工具返回的 `success`、`message` 回复用户。

`type` 为 `er` / `sequence` / `flowchart` 时，字段与流程见对应技能。
