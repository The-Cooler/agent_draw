"""
Visio Agent - 基于 LangChain Agent Skills 规范的技能型 Agent
"""
import json
import os
import re
import threading
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .visio_controller import VisioController
from .diagram_engine import DiagramEngine
from .skill_loader import SkillLoader, Skill, register_skills
from .parser import parse_diagram_description
from dotenv import load_dotenv

load_dotenv()


# Visio 绘图工具定义
DRAW_TOOLS = [
    {
        "name": "draw_er_diagram",
        "description": "绘制陈氏 ER（实体-关系）图，输入为包含 title、entities、relationships 的 JSON",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "ER 图数据，包含 title、entities（name、attributes）、relationships"
                },
                "output_path": {
                    "type": "string",
                    "description": "输出 .vsdx 文件路径"
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "draw_flowchart",
        "description": "绘制标准 ISO 流程图，输入为包含 title、nodes、edges 的 JSON",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "流程图数据，包含 title、nodes（id、type、label）、edges（from、to、label）"
                },
                "output_path": {
                    "type": "string",
                    "description": "输出 .vsdx 文件路径"
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "draw_sequence_diagram",
        "description": "绘制 UML 时序图，输入为包含 title、participants、interactions 的 JSON",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "时序图数据，包含 title、participants、interactions（from、to、message、type）"
                },
                "output_path": {
                    "type": "string",
                    "description": "输出 .vsdx 文件路径"
                }
            },
            "required": ["data"]
        }
    },
]


class VisioAgent:
    """Visio Agent - 技能型图表绘制 Agent"""

    def __init__(
        self,
        api_provider: str = "openai",
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.0,
        skills_dir: Optional[str] = None,
    ):
        """
        初始化 Visio Agent

        Args:
            api_provider: "openai" | "deepseek" | "groq"
            model: 模型名称
            api_key: API 密钥（未提供时从环境变量读取）
            api_base: API base URL
            temperature: 温度参数
            skills_dir: 技能目录路径（未提供时自动检测）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("GROQ_API_KEY")
        self.api_base = api_base or os.getenv("API_BASE") or os.getenv("OPENAI_API_BASE")
        self.model = model
        self.temperature = temperature

        # 设置 LLM
        if api_provider == "deepseek":
            self._setup_deepseek()
        elif api_provider == "groq":
            self._setup_groq()
        else:
            self._setup_openai()

        # 加载技能
        if skills_dir:
            SkillLoader.load_skills_from_dir(skills_dir)
        else:
            register_skills()  # 使用默认技能目录

        # 绑定工具
        self._llm_with_tools = self.llm.bind_tools(DRAW_TOOLS)

        # Visio 组件
        self.visio = VisioController(visible=True)
        self.engine = DiagramEngine(self.visio)

        # 当前技能状态
        self._current_skill: Optional[Skill] = None
        self._diagram_type: str = "er-diagram"

        # 后台绘图线程
        self._draw_thread: Optional[threading.Thread] = None

    def _setup_openai(self):
        """配置 OpenAI LLM"""
        extra_kwargs = {}
        if self.api_base:
            extra_kwargs["base_url"] = self.api_base

        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            **extra_kwargs
        )

    def _setup_deepseek(self):
        """配置 DeepSeek LLM"""
        base_url = self.api_base or "https://api.deepseek.com"
        self.llm = ChatOpenAI(
            model=self.model or "deepseek-chat",
            api_key=self.api_key,
            base_url=base_url,
            temperature=self.temperature
        )

    def _setup_groq(self):
        """配置 Groq LLM"""
        self.llm = ChatOpenAI(
            model=self.model or "mixtral-8x7b-32768",
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
            temperature=self.temperature
        )

    def _detect_diagram_type(self, description: str) -> str:
        """从描述中检测图表类型"""
        return SkillLoader.detect_skill(description)

    def _get_system_prompt(self, skill: Skill) -> str:
        """从技能内容构建系统提示词"""
        base_prompt = """你是一个专业的图表工程师，将自然语言描述转换为结构化的图表数据。

你可以使用以下绘图工具：
- draw_er_diagram: 绘制陈氏 ER 图
- draw_flowchart: 绘制标准流程图
- draw_sequence_diagram: 绘制 UML 时序图

当用户请求绘制图表时：
1. 分析描述识别图表类型
2. 提取所有实体/节点/参与者及其属性
3. 生成结构化的 JSON 数据
4. 调用相应的绘图工具

始终输出有效的 JSON 工具调用。"""

        if skill and skill.content:
            # 注入技能特定指令
            return f"""{base_prompt}

## 技能: {skill.name}

{skill.content}"""
        return base_prompt

    def _extract_json(self, text: str) -> dict:
        """从 LLM 响应中提取 JSON"""
        text = text.strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            print(f"内容: {text[:500]}")
            raise

    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行 LLM 返回的工具调用"""
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})

        data = args.get("data", {})
        output_path = args.get("output_path")

        # 根据工具名确定图表类型
        if tool_name == "draw_er_diagram":
            diagram_type = "er"
        elif tool_name == "draw_flowchart":
            diagram_type = "flowchart"
        elif tool_name == "draw_sequence_diagram":
            diagram_type = "sequence"
        else:
            raise ValueError(f"未知工具: {tool_name}")

        # 如果未提供输出路径则生成
        if not output_path:
            title = data.get("title", "diagram").replace(" ", "_").replace("/", "_")
            output_dir = os.path.join(os.path.dirname(__file__), "diagrams")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{title}_{diagram_type}.vsdx")

        # 绘制图表
        success = self.engine.draw(
            diagram_type, data, output_path, title=data.get("title", "")
        )

        return {"success": success, "output_path": output_path}

    def _draw_in_background(self, diagram_type: str, data: Dict[str, Any], output_path: str, title: str):
        """在后台线程中执行绘图"""
        try:
            success = self.engine.draw(diagram_type, data, output_path, title=title)
            if success:
                print(f"[后台] 图表已保存: {output_path}")
            else:
                print(f"[后台] 绘图失败")
        except Exception as e:
            print(f"[后台] 绘图异常: {e}")

    def draw(self, description: str, output_path: Optional[str] = None, background: bool = True) -> bool:
        """
        根据自然语言描述绘制图表

        Args:
            description: 自然语言图表描述
            output_path: 输出文件路径 (.vsdx)
            background: 是否在后台运行绘图（默认 True）

        Returns:
            bool: 成功状态
        """
        # 1. 检测图表类型
        self._diagram_type = self._detect_diagram_type(description)
        print(f"[VisioAgent] 检测到图表类型: {self._diagram_type}")

        # 2. 获取技能
        self._current_skill = SkillLoader.get_skill(self._diagram_type)
        if self._current_skill:
            print(f"[VisioAgent] 已加载技能: {self._current_skill.name}")

        # 3. 构建提示词
        system_prompt = self._get_system_prompt(self._current_skill)

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"根据以下描述绘制图表：\n\n{description}\n\n只输出 JSON 工具调用。")
        ])

        # 4. 调用 LLM
        try:
            chain = prompt | self._llm_with_tools
            response = chain.invoke({})

            # 5. 处理工具调用
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tool_call in response.tool_calls:
                    result = self._execute_tool_call(tool_call)
                    if result.get("success"):
                        print(f"[VisioAgent] 图表已保存: {result['output_path']}")
                        return True
                    else:
                        print(f"[VisioAgent] 绘图失败")
                        return False
            else:
                # 无工具调用，尝试从内容解析 JSON
                data = self._extract_json(response.content)
                return self._draw_from_data(data, output_path, background=background)

        except Exception as e:
            print(f"[VisioAgent] LLM 调用失败: {e}")
            # 备用本地解析器
            diagram_type = self._diagram_type.replace("-diagram", "").replace("-", "")
            if diagram_type == "er":
                diagram_type = "er"
            elif diagram_type == "flowchart":
                diagram_type = "flowchart"
            else:
                diagram_type = "sequence"

            data = parse_diagram_description(diagram_type, description)
            print(f"[VisioAgent] 使用本地解析器: {json.dumps(data, ensure_ascii=False)[:200]}")
            return self._draw_from_data(data, output_path, background=background)

    def _draw_from_data(self, data: Dict[str, Any], output_path: Optional[str] = None, background: bool = True) -> bool:
        """从结构化数据绘制图表"""
        # 根据数据结构确定图表类型
        if "entities" in data or "relationships" in data:
            diagram_type = "er"
        elif "nodes" in data or "edges" in data:
            diagram_type = "flowchart"
        elif "participants" in data or "interactions" in data:
            diagram_type = "sequence"
        else:
            print(f"[VisioAgent] 未知数据结构: {list(data.keys())}")
            return False

        if not output_path:
            title = data.get("title", "diagram").replace(" ", "_").replace("/", "_")
            output_dir = os.path.join(os.path.dirname(__file__), "diagrams")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{title}_{diagram_type}.vsdx")

        if background:
            # 在后台线程中执行绘图
            title_val = data.get("title", "")
            self._draw_thread = threading.Thread(
                target=self._draw_in_background,
                args=(diagram_type, data, output_path, title_val)
            )
            self._draw_thread.start()
            print(f"[VisioAgent] 图表正在后台绘制: {output_path}")
            return True
        else:
            # 同步绘图
            return self.engine.draw(
                diagram_type, data, output_path, title=data.get("title", "")
            )

    def draw_er_diagram(self, data: dict, output_path: str) -> bool:
        """直接绘制 ER 图"""
        return self.engine.draw("er", data, output_path, title=data.get("title", ""))

    def draw_flowchart(self, data: dict, output_path: str) -> bool:
        """直接绘制流程图"""
        return self.engine.draw("flowchart", data, output_path, title=data.get("title", ""))

    def draw_sequence_diagram(self, data: dict, output_path: str) -> bool:
        """直接绘制时序图"""
        return self.engine.draw("sequence", data, output_path, title=data.get("title", ""))

    def chat(self, message: str) -> str:
        """对话模式：分析请求并绘制"""
        try:
            self.draw(message)
            return "图表已生成并保存！"
        except Exception as e:
            return f"绘图失败: {e}"

    def wait_for_draw(self, timeout: Optional[float] = None) -> bool:
        """等待后台绘图完成"""
        if self._draw_thread and self._draw_thread.is_alive():
            self._draw_thread.join(timeout=timeout)
            return not self._draw_thread.is_alive()
        return True

    def close(self):
        """关闭 Visio"""
        # 等待绘图完成
        self.wait_for_draw(timeout=5.0)
        self.visio.close()


def create_agent(
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    skills_dir: Optional[str] = None,
) -> VisioAgent:
    """创建 VisioAgent 实例"""
    return VisioAgent(
        api_provider=provider,
        model=model,
        api_key=api_key,
        api_base=api_base,
        skills_dir=skills_dir,
    )
