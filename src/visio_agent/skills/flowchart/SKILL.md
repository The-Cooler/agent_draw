---
name: flowchart
description: "用户要画流程图时：按模板1/2整理 nodes，ReAct 检查后再校验与绘制"
---

# 流程图（模板 1 / 模板 2）

结构说明见仓库根目录 **`流程图模板说明.md`**（虚拟路径 **`/流程图模板说明.md`**）。

## 硬性规则

1. **`data.template`**：`1` 或 `2`。
2. **`data.nodes`**：顺序与条数**固定**，每项为 `{ "role", "text" }`。
3. **`text`**：每条 **≤5 个字**；过长须删减，过短可在**符合该槽语义**下补充。
4. **槽位与图形一致（禁止混填）**  
   - **`input`**：仅模板 1 的**输入**平行四边形 → 只填「输入类」短文案，**不要**填判断句。  
   - **`decision`**：条件判断平行四边形 → 只填判断类（如「是否×」），**不要**填到 **`process`** 矩形里，也**不要**把输入内容塞到判断形里。  
   - **`process`**：矩形处理步骤 → 只填处理动作短句，**不要**填菱形内容。  
   - **`start` / `end`**：圆角开始/结束。

## ReAct（建议）

1. 根据用户话选定模板 1 或 2，起草 `nodes`（`role` 必须与下表顺序**逐格一致**）。
2. 调用 **`check_flowchart_nodes`**（`template` + `nodes`）→ 若 `ok` 为 false，按 `errors` 改文案或 `role`，再测。
3. 拼顶层 JSON，`validate_diagram_request` 直至 `valid`。
4. 调用 **`flowchart_draw`**：`project_root`、`user`、`title`、`template`、`nodes`。

## 模板 1 — `nodes` 的 `role` 顺序（共 8 项）

`start` → `input` → `process` → `process` → `decision` → `process` → `process` → `end`

## 模板 2 — `role` 顺序（共 7 项）

`start` → `decision` → `process` → `decision` → `process` → `process` → `end`

## `flowchart_draw` 参数

与校验通过的 `data` 对齐：**`project_root`**（用户消息中的项目根）、**`user`**、**`title`**、**`template`**、**`nodes`**。保存：`{project_root}/data/{user}/flowchart/{title}.vsdx`。

## Visio 模板文件

在 `skills/flowchart/template/` 放置 **`template_1.vsdx`**、**`template_2.vsdx`**。

**占位符**

每个节点形状里的文字 **只能是纯数字** `1`…`N`（模板 1：`N=8`；模板 2：`N=7`），仅用于**对齐槽位**；绘制完成后该处**只保留** `nodes[i].text`，**不再**出现占位数字或「序号.」前缀。未识别到占位则**不**生成成品文件。
