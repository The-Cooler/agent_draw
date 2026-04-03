#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visio Agent - 命令行入口
使用 LangChain Agent Skills（SKILL.md 文件）

示例:
  python main.py --type er --desc "学生选课系统 ER 图"
  python main.py --skill flowchart --desc "订单处理流程图"
  python main.py --list-skills
"""
import argparse
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from visio_agent import (
    create_agent,
    parse_diagram_description,
    DiagramEngine,
    VisioController,
    SkillLoader,
)


def main():
    parser = argparse.ArgumentParser(
        description="Visio Agent - AI 驱动的图表绘制工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
技能从 SKILL.md 文件加载，使用 --list-skills 查看可用技能。

示例:
  # ER 图
  python main.py --type er --desc "学生选课 ER 图"

  # 流程图
  python main.py --skill flowchart --desc "订单处理流程"

  # 时序图
  python main.py --skill sequence --desc "登录时序图"

  # 使用 DeepSeek API
  python main.py --provider deepseek --type er --desc "..."

  # 无 AI 模式（本地解析）
  python main.py --no-ai --type er --desc "..."
"""
    )

    parser.add_argument("--type", "-t", choices=["er", "flowchart", "sequence", "flow", "seq"],
                        help="图表类型")
    parser.add_argument("--skill", "-s", choices=["er-diagram", "flowchart", "sequence-diagram", "flow", "seq"],
                        help="技能名称（与 --type 等效）")
    parser.add_argument("--desc", "-d", type=str, help="图表描述")
    parser.add_argument("--file", "-f", type=str, help="从文件读取描述")
    parser.add_argument("--output", "-o", type=str, help="输出文件路径 (.vsdx)")
    parser.add_argument("--data", type=str, help="直接传入 JSON 数据")
    parser.add_argument("--provider", choices=["openai", "deepseek", "groq"],
                        default="openai", help="API 提供商")
    parser.add_argument("--model", "-m", type=str, help="模型名称")
    parser.add_argument("--api-key", type=str, help="API 密钥")
    parser.add_argument("--api-base", type=str, help="API base URL")
    parser.add_argument("--no-ai", action="store_true", help="使用本地解析器（无 AI）")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    parser.add_argument("--export", "-e", type=str, help="导出为 PNG 图片")
    parser.add_argument("--list-skills", action="store_true", help="列出可用技能")
    parser.add_argument("--sync", action="store_true", help="同步执行（禁用后台绘图）")

    args = parser.parse_args()

    # 列出可用技能
    if args.list_skills:
        skills = SkillLoader.get_all_skills()
        print("可用技能:")
        for name, skill in skills.items():
            print(f"  - {name}: {skill.description[:60]}...")
            print(f"    工具: {', '.join(skill.allowed_tools)}")
        if not skills:
            print("  未从 SKILL.md 文件加载任何技能")
        return

    # 读取描述
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            description = f.read()
    elif args.desc:
        description = args.desc
    else:
        print("错误: 请提供 --desc 或 --file 参数")
        parser.print_help()
        sys.exit(1)

    # 处理换行符
    description = description.replace("\\n", "\n")

    # 确定图表类型
    skill_or_type = args.skill or args.type
    if not skill_or_type:
        skill_or_type = SkillLoader.detect_skill(description)
        print(f"[自动检测] 技能: {skill_or_type}")

    # 别名映射
    alias_map = {"flow": "flowchart", "seq": "sequence-diagram", "flowchart": "flowchart",
                 "sequence": "sequence-diagram", "er": "er-diagram"}
    diagram_type = alias_map.get(skill_or_type, skill_or_type)

    # 引擎类型（er, flowchart, sequence）
    engine_type = diagram_type.replace("-diagram", "").replace("-", "")

    # 处理数据
    if args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}")
            sys.exit(1)
    elif args.no_ai:
        data = parse_diagram_description(engine_type, description)
        print(f"[本地解析] {json.dumps(data, ensure_ascii=False, indent=2)[:300]}")
    else:
        # 创建 Agent 并绘制
        agent = create_agent(
            provider=args.provider,
            model=args.model,
            api_key=args.api_key,
            api_base=args.api_base,
        )
        print(f"[Agent] 使用 {args.provider} / {args.model or 'default'}")

        # 同步模式禁用后台绘图
        background = not args.sync

        success = agent.draw(description, args.output, background=background)

        if success and args.export:
            visio = VisioController(visible=False)
            engine = DiagramEngine(visio)
            engine.draw(engine_type, data, "temp.vsdx", title=data.get("title", ""))
            visio.export_image(args.export)
            visio.close()

        if background:
            print("[提示] 图表正在后台绘制，使用 --sync 等待完成")

        agent.close()
        return

    # 直接绘制（无 AI 模式）
    if args.no_ai and not args.data:
        output_path = args.output
        if not output_path:
            output_dir = os.path.join(os.path.dirname(__file__), "src", "visio_agent", "diagrams")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"diagram_{engine_type}.vsdx")

        visio = VisioController(visible=True)
        engine = DiagramEngine(visio)
        success = engine.draw(engine_type, data, output_path, title=data.get("title", ""))
        if success:
            print(f"已保存: {output_path}")
        else:
            print("绘图失败")
        visio.close()


def interactive_mode():
    """交互式对话模式"""
    print("=" * 60)
    print("  Visio Agent - 交互模式")
    print("  支持: ER 图、流程图、时序图")
    print("  输入 'quit' 退出")
    print("=" * 60)

    agent = create_agent(provider="openai")
    print(f"[Agent] 使用 OpenAI\n")

    while True:
        try:
            user_input = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见!")
            break

        if user_input.lower() in ["help", "h", "?"]:
            print("""
支持的图表:
  - ER 图: "画一个学生选课 ER 图"
  - 流程图: "订单处理流程"
  - 时序图: "登录时序图"

命令:
  quit/exit - 退出
  help - 显示此消息
""")
            continue

        try:
            agent.draw(user_input)
            print("图表正在后台生成!\n")
        except Exception as e:
            print(f"错误: {e}\n")

    agent.close()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        main()
