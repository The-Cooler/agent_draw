"""
Visio Agent 包
AI 驱动的 Visio 图表绘制工具
"""

from .agent import create_agent
from .diagram_runner import DiagramAgentRunner, print_stream_events
from .skills.er.tools import er_draw
from .skills.flowchart.tools import check_flowchart_nodes, flowchart_draw
from .skills.sequence.tools import sequence_draw

__version__ = "0.4.0"

__all__ = [
    "check_flowchart_nodes",
    "create_agent",
    "DiagramAgentRunner",
    "er_draw",
    "flowchart_draw",
    "print_stream_events",
    "sequence_draw",
]
