#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试入口：DiagramAgentRunner + 流式打印。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from visio_agent.diagram_runner import DiagramAgentRunner, print_stream_events

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.dirname(__file__))
    natural_language = """
        特色分类管理模块通过预定义分类标签对资源进行结构化管理，并结合用户点击量、点赞量等行为数据生成推荐结果。系统采用前后端分离架构，前端请求分类数据，后端控制器调用服务层查询分类及资源信息，并依据热度指标进行排序处理，最终以JSON格式返回前端渲染。特色分类管理时序图如图4-1所示。
    """
    print("-" * 50)
    print_stream_events(DiagramAgentRunner(project_root=project_root), natural_language)
