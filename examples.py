#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟外部传入的 JSON，经 Agent 按 type 选择工具处理（无本地路由表）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from langchain_core.messages import AIMessage

from visio_agent.agent import create_agent


def _print_invoke_result(result: dict) -> None:
    msgs = result.get("messages") or []
    for m in reversed(msgs):
        if isinstance(m, AIMessage):
            print(m.content)
            return
    print(result)


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.dirname(__file__))
    json_input = {
        "user": "张三",
        "type": "er",
        "data": {
            "entity": "学生",
            "attributes": [
                {"name": "学号", "type": "pk"},
                {"name": "姓名", "type": "normal"},
                {"name": "性别", "type": "normal"},
                {"name": "年龄", "type": "normal"},
            ],
        },
    }

    user_content = (
        "请根据以下 JSON 处理绘图请求：按 type 字段选择唯一对应的工具，遵守 diagram_protocol 技能中的路径约定。\n\n"
        f"项目根目录: {project_root}\n\n"
        f"{json.dumps(json_input, ensure_ascii=False)}"
    )

    print("输入:", json_input)
    print("-" * 50)

    agent = create_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_content}]},
        config={"configurable": {"thread_id": "examples"}},
    )
    print("结果:")
    _print_invoke_result(result)
