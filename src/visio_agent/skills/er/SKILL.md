---
name: er
description: "当用户要求绘制 ER 图、实体-关系图时使用此技能"
---

# ER 图绘制技能

## 与全局协议的关系

标准外部请求格式见 **diagram_protocol** 技能：`{"user", "type", "data"}`。当 `type` 为 `er` 时，`data` 为本技能下的结构化对象（`entity`、`attributes`）。本技能说明如何在该场景下正确调用 `er_draw`。

## 输入格式

用户输入单个实体，属性使用列表格式：
```
实体"学生"：
1. 学号pk
2. 姓名
3. 性别
4. 年龄
```

或单行格式：
```
实体"学生"：[学号pk, 姓名, 性别, 年龄]
```

## 属性数量检查

**必须先检查属性数量是否符合规定，才能填充：**
- 奇数属性数量 → 使用 ER_odd 模板
- 偶数属性数量 → 使用 ER_even 模板
- **属性数量不能超过模板可容纳的最大数量**
- 如果属性数量不符合规定，返回错误信息

## 工具调用

调用 `er_draw` 工具，参数必须正确：

```json
{
  "entity": "学生",
  "attributes": [
    {"name": "学号", "type": "pk"},
    {"name": "姓名", "type": "normal"},
    {"name": "性别", "type": "normal"},
    {"name": "年龄", "type": "normal"}
  ],
  "output_path": "学生.vsdx"
}
```

## 错误示例（不要这样做）

- output_path: "/学生.png" ❌
- output_path: "/学生_ER图.txt" ❌
- output_path: "/tmp/学生.vsdx" ❌

## 正确示例

- output_path: "学生.vsdx" ✅（相对路径示例）
- output_path: "课程.vsdx" ✅
- 来自标准 JSON 时：使用 **绝对路径** `{项目根目录}/data/{user}/er/{entity}.vsdx`（见 diagram_protocol）✅

## 重要

- output_path 必须以 .vsdx 结尾
- 相对路径示例中不要加 `/` 前缀；标准 JSON 场景下使用协议给出的绝对路径
- 不要用其他扩展名
