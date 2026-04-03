"""时序图工具测试 - 由 Agent 智能判断流程类型"""

from src.visio_agent.agent import create_agent

# 创建 agent（会加载 skills/sequence/SKILL.md）
agent = create_agent()

# 测试用例 - 只需描述业务，agent 自动判断单程还是双程
test_prompts = [
    '特色分类管理模块通过预定义分类标签对资源进行结构化管理，并结合用户点击量、点赞量等行为数据生成推荐结果。系统采用前后端分离架构，前端请求分类数据，后端控制器调用服务层查询分类及资源信息，并依据热度指标进行排序处理，最终以JSON格式返回前端渲染。特色分类管理时序图如图4-1所示。'
]

print("=== 测试 Agent 智能判断 ===\n")

for prompt in test_prompts:
    print(f"用户: {prompt}")
    for chunk in agent.stream({"messages": [("user", prompt)]}):
        # 只打印有意义的文本内容
        if isinstance(chunk, dict):
            for key, value in chunk.items():
                if hasattr(value, 'content') and value.content:
                    print(value.content, end="", flush=True)
                elif isinstance(value, str) and value.strip():
                    print(value, end="", flush=True)
    print()