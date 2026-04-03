"""
Visio Agent
"""
import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL")
API_KEY = os.getenv("API_KEY")
API_BASE = os.getenv("API_BASE")


def create_agent() -> any:
    from deepagents import create_deep_agent
    from langchain_openai import ChatOpenAI
    from .skills.diagram_protocol.stub_tools import flowchart_draw, sequence_draw
    from .skills.er.tools import er_draw
    from .skills.sequence.tools import sequence_draw, check_message_count, check_message_length

    skills_dir = os.path.join(os.path.dirname(__file__), "skills")

    llm = ChatOpenAI(
        model=MODEL,
        api_key=API_KEY,
        base_url=API_BASE,
        temperature=0,
    )

    agent = create_deep_agent(
        model=llm,
        tools=[er_draw, sequence_draw, check_message_count, check_message_length],
        skills=[skills_dir],
    )

    return agent
