#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试入口：DiagramAgentRunner + 流式打印。

用法：
  uv run python examples.py er
  uv run python examples.py sequence
  uv run python examples.py flowchart
  uv run python examples.py "你的任意自然语言……"
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from visio_agent.diagram_runner import DiagramAgentRunner, print_stream_events

# 单参数且为下列关键字时使用内置话术，便于快速测三类图
_PRESETS = {
    "er": (
        "我是张三。请画 ER 图：实体叫商品，属性有编号（主键）、名称、价格。"
    ),
    "sequence": (
        "我是李四。请画单程时序图，标题叫「下单」：用户发起下单，前端请求后端，"
        "后端访问数据库，数据库内部校验，数据库返回后端，后端响应前端，前端展示结果。"
    ),
    "flowchart": (
        "用户进入分类页面后，系统加载所有分类及对应资源概要数据，同时根据业务规则计算各分类下的推荐榜单。随后对资源进行排序与筛选，将处理结果返回前端进行展示，实现分类浏览与推荐功能。特色分类管理流程图如图4-2所示。"
    ),
}


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.dirname(__file__))

    if len(sys.argv) < 2:
        print(
            "用法:\n"
            "  uv run python examples.py er\n"
            "  uv run python examples.py sequence\n"
            "  uv run python examples.py flowchart\n"
            "  uv run python examples.py \"<一句自然语言>\"",
            file=sys.stderr,
        )
        sys.exit(2)

    if len(sys.argv) == 2 and sys.argv[1].strip().lower() in _PRESETS:
        natural_language = _PRESETS[sys.argv[1].strip().lower()]
    else:
        natural_language = " ".join(sys.argv[1:]).strip()

    if not natural_language:
        print("自然语言为空", file=sys.stderr)
        sys.exit(2)

    print("自然语言:", natural_language)
    print("-" * 50)
    print_stream_events(DiagramAgentRunner(project_root=project_root), natural_language)
