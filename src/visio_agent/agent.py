"""
Visio Agent
"""
import os
import platform
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL")
API_KEY = os.getenv("API_KEY")
API_BASE = os.getenv("API_BASE")

_PACKAGE_DIR = Path(__file__).resolve().parent
# 仓库根目录（含 src/ 的上一级），与典型 examples 的 project_root 一致
_DEFAULT_PROJECT_ROOT = _PACKAGE_DIR.parent.parent

_VISIO_PATH_RULES = """## Visio 绘图助手（路径约定）

- 用户消息中的 **本机绝对路径**（Windows 如 `D:\\...`，Linux/macOS 如 `/home/...`）**只**作为 **`er_draw` 的 `project_root` 参数**（写 .vsdx）；**不要**把它传给内置文件工具 `ls` / `glob` / `read_file` / `write_file` / `edit_file`（这些工具只接受以 **`/`** 开头的虚拟路径）。
- 当前工作区挂载在虚拟路径 **`/`** 下（对应本机上的项目根目录）；例如浏览根目录用 **`/`**，源码多在 **`/src`**。
- 画 ER / 时序图通常**不需要**浏览磁盘：校验通过后分别调 `er_draw`、`sequence_draw`（`project_root` 同上；保存路径由工具固定，见各技能）。
"""


def _build_visio_system_prompt() -> str:
    os_lines = (
        f"- platform.system(): **{platform.system()}**\n"
        f"- sys.platform: **{sys.platform}**\n"
        f"- platform.release(): **{platform.release()}**\n"
        f"- platform.machine(): **{platform.machine()}**\n"
        f"- platform.platform(): **{platform.platform()}**"
    )
    return f"""## 当前设备运行环境

{os_lines}

{_VISIO_PATH_RULES}"""


def create_agent(project_root: str | None = None) -> Any:
    from deepagents import create_deep_agent
    from deepagents.backends.filesystem import FilesystemBackend
    from langchain_openai import ChatOpenAI

    from .skills.diagram_protocol.stub_tools import flowchart_draw
    from .skills.sequence.tools import sequence_draw
    from .skills.diagram_protocol.validate_tool import validate_diagram_request
    from .skills.er.tools import er_draw

    root = Path(os.path.abspath(project_root)) if project_root else _DEFAULT_PROJECT_ROOT
    skills_dir = _PACKAGE_DIR / "skills"
    try:
        skills_virt = "/" + skills_dir.relative_to(root).as_posix()
    except ValueError as e:
        msg = (
            f"project_root 必须包含技能目录：{skills_dir} 应在 {root} 之下。"
            "请把 DiagramAgentRunner / create_agent 的 project_root 设为仓库根目录。"
        )
        raise ValueError(msg) from e

    def backend_factory(rt: Any) -> FilesystemBackend:
        return FilesystemBackend(root_dir=str(root), virtual_mode=True)

    llm = ChatOpenAI(
        model=MODEL,
        api_key=API_KEY,
        base_url=API_BASE,
        temperature=0,
    )

    agent = create_deep_agent(
        model=llm,
        tools=[
            validate_diagram_request,
            er_draw,
            sequence_draw,
            flowchart_draw,
        ],
        skills=[skills_virt],
        backend=backend_factory,
        system_prompt=_build_visio_system_prompt(),
    )

    return agent
