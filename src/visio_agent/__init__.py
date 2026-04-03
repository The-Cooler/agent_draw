"""
Visio Agent 包
基于 LangChain 的自动 Visio 图表绘制 Agent
使用 LangChain Agent Skills 规范（SKILL.md 文件）
"""

from .agent import VisioAgent, create_agent
from .visio_controller import VisioController
from .diagram_engine import DiagramEngine, ChenERDiagram, FlowchartDiagram, SequenceDiagram
from .parser import parse_diagram_description
from .skill_loader import SkillLoader, Skill, register_skills

__version__ = "0.2.0"

__all__ = [
    # 核心 Agent
    "VisioAgent",
    "create_agent",
    # Visio 组件
    "VisioController",
    "DiagramEngine",
    "ChenERDiagram",
    "FlowchartDiagram",
    "SequenceDiagram",
    # 解析器
    "parse_diagram_description",
    # 技能系统（LangChain Agent Skills 规范）
    "SkillLoader",
    "Skill",
    "register_skills",
]
