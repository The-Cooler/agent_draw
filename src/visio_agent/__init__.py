"""
Visio Agent 包
AI 驱动的 Visio 图表绘制工具
"""

from .agent import create_agent
from .diagram_runner import DiagramAgentRunner, print_stream_events
from .skills.er.tools import er_draw
from .skills.sequence.tools import sequence_draw

__version__ = "0.4.0"

__all__ = [
    "create_agent",
    "DiagramAgentRunner",
    "print_stream_events",
    "er_draw",
    "sequence_draw",
]
