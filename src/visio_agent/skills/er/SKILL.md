---
name: er
description: "当用户要画 ER 图、实体-关系图时启用：先通过校验再调 er_draw"
---

# ER 图

## 与 diagram_protocol 的衔接

若本任务带顶层 JSON：须 **`validate_diagram_request` 返回 valid** 后再调 **`er_draw`**。

## 从用户话里抽 entity / attributes

列表或单行里出现实体名、属性列表时，映射到 `data.entity` 与 `data.attributes`（每项必有 `name`；`type` 仅在为 **`pk`** 时表示主键，其它可省略，**不要**强行区分 fk / normal）。

## 语言与命名（与校验一致）

- **实体名 `entity`**：须含中文（CJK 表意文字）。
- **属性 `name`**：须含中文；**仅当**属性名为 **`ID` 或 `id`（大小写不敏感）** 时，允许全英文等非中文。
- 交给 **`er_draw` 的 `name` 字符串**：原样写入图内显示，**不要**改写、翻译、截断或换别的词。

## 数量与模板

- **`data.attributes` 至多 10 条**，超出则 **`validate_diagram_request` 失败**，须让用户删减后再校验。
- 选 **ER_odd / ER_even** 按**属性条数**奇偶决定。
- 写入时 **主键排第一**，其余保持传入顺序；`name` 原样写入。

## er_draw 调用

传入四个参数（**不要**自拼文件路径）：

1. **`project_root`**：用户消息里给出的项目根目录绝对路径，须**逐字一致**。
2. **`user`**：校验通过的顶层 `user`。
3. **`entity`**：校验通过的 `data.entity`。
4. **`attributes`**：校验通过的 `data.attributes`。

保存路径由工具内部固定：`{project_root}/data/{user}/er/{entity}.vsdx`。
