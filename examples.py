#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试绘图引擎（无需 AI）
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from visio_agent import DiagramEngine, VisioController


def demo_er():
    """演示：绘制学生选课 ER 图"""
    print("绘制陈氏 ER 图：学生选课系统...")

    data = {
        "title": "学生选课系统 ER 图",
        "entities": [
            {
                "name": "学生",
                "attributes": [
                    {"name": "学号", "type": "pk"},
                    {"name": "姓名", "type": "normal"},
                    {"name": "性别", "type": "normal"},
                    {"name": "年龄", "type": "normal"}
                ]
            },
            {
                "name": "课程",
                "attributes": [
                    {"name": "课程号", "type": "pk"},
                    {"name": "课程名", "type": "normal"},
                    {"name": "学分", "type": "normal"}
                ]
            },
            {
                "name": "教师",
                "attributes": [
                    {"name": "工号", "type": "pk"},
                    {"name": "姓名", "type": "normal"},
                    {"name": "职称", "type": "normal"}
                ]
            }
        ],
        "relationships": [
            {
                "name": "选修",
                "entities": ["学生", "课程"],
                "cardinality": "N:M",
                "attributes": [
                    {"name": "成绩", "type": "normal"}
                ]
            },
            {
                "name": "讲授",
                "entities": ["教师", "课程"],
                "cardinality": "1:N",
                "attributes": []
            }
        ]
    }

    output_path = os.path.join(os.path.dirname(__file__), "src", "visio_agent", "diagrams", "student_er.vsdx")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    visio = VisioController(visible=True)
    engine = DiagramEngine(visio)
    success = engine.draw("er", data, output_path, title=data["title"])
    print(f"ER 图绘制: {'成功' if success else '失败'}")
    print(f"文件: {output_path}")
    return success


def demo_flowchart():
    """演示：绘制订单处理流程图"""
    print("\n绘制流程图：订单处理...")

    data = {
        "title": "订单处理流程",
        "nodes": [
            {"id": "start", "type": "terminal", "label": "开始"},
            {"id": "p1", "type": "io", "label": "接收订单"},
            {"id": "p2", "type": "process", "label": "验证库存"},
            {"id": "d1", "type": "decision", "label": "库存充足?"},
            {"id": "p3", "type": "process", "label": "扣减库存"},
            {"id": "p4", "type": "process", "label": "生成发货单"},
            {"id": "p5", "type": "io", "label": "通知客户"},
            {"id": "d2", "type": "decision", "label": "付款成功?"},
            {"id": "p6", "type": "process", "label": "补货"},
            {"id": "end1", "type": "terminal", "label": "流程结束"},
            {"id": "end2", "type": "terminal", "label": "订单取消"}
        ],
        "edges": [
            {"from": "start", "to": "p1"},
            {"from": "p1", "to": "p2"},
            {"from": "p2", "to": "d1"},
            {"from": "d1", "to": "p3", "label": "是"},
            {"from": "d1", "to": "p6", "label": "否"},
            {"from": "p3", "to": "p4"},
            {"from": "p4", "to": "d2"},
            {"from": "d2", "to": "p5", "label": "是"},
            {"from": "d2", "to": "end2", "label": "否"},
            {"from": "p5", "to": "end1"},
            {"from": "p6", "to": "end2"}
        ]
    }

    output_path = os.path.join(os.path.dirname(__file__), "src", "visio_agent", "diagrams", "order_flowchart.vsdx")

    visio = VisioController(visible=True)
    engine = DiagramEngine(visio)
    success = engine.draw("flowchart", data, output_path, title=data["title"])
    print(f"流程图绘制: {'成功' if success else '失败'}")
    print(f"文件: {output_path}")
    return success


def demo_sequence():
    """演示：绘制用户登录时序图"""
    print("\n绘制时序图：用户登录...")

    data = {
        "title": "用户登录时序图",
        "participants": ["用户", "前端", "后端", "数据库"],
        "interactions": [
            {"from": "用户", "to": "前端", "message": "输入用户名密码", "type": "sync"},
            {"from": "前端", "to": "后端", "message": "POST /api/login", "type": "sync"},
            {"from": "后端", "to": "数据库", "message": "SELECT * FROM users WHERE ...", "type": "sync"},
            {"from": "数据库", "to": "后端", "message": "返回用户记录", "type": "return"},
            {"from": "后端", "to": "前端", "message": "返回 JWT Token", "type": "return"},
            {"from": "前端", "to": "用户", "message": "登录成功页面", "type": "return"},
            {"from": "前端", "to": "前端", "message": "localStorage.setItem(token)", "type": "self"}
        ]
    }

    output_path = os.path.join(os.path.dirname(__file__), "src", "visio_agent", "diagrams", "login_sequence.vsdx")

    visio = VisioController(visible=True)
    engine = DiagramEngine(visio)
    success = engine.draw("sequence", data, output_path, title=data["title"])
    print(f"时序图绘制: {'成功' if success else '失败'}")
    print(f"文件: {output_path}")
    return success


if __name__ == "__main__":
    print("=" * 50)
    print("  Visio 智能体 - 直接绘图演示")
    print("=" * 50)
    print("\n演示模式下图表将在 Visio 中打开，")
    print("请手动保存或关闭 Visio 窗口。\n")

    # 依次绘制三个图表示例
    results = []
    results.append(("ER 图", demo_er()))
    # results.append(("流程图", demo_flowchart()))
    # results.append(("时序图", demo_sequence()))

    print("\n" + "=" * 50)
    print("  演示结果汇总")
    print("=" * 50)
    for name, ok in results:
        status = "OK" if ok else "FAIL"
        print(f"  {name}: {status}")

    print("\n演示完成！图表文件保存在 src/visio_agent/diagrams/ 目录")
