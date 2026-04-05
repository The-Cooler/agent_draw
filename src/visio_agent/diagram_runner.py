"""
自然语言 → Deep Agent：由模型自行判断图类型（er / sequence / flowchart），流式输出运行过程。
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

from .agent import create_agent


class DiagramAgentRunner:
    """封装项目根路径、用户话术拼装与 graph.stream。"""

    def __init__(
        self,
        project_root: str | None = None,
        *,
        thread_id: str = "default",
    ) -> None:
        self.project_root = os.path.abspath(project_root or os.getcwd())
        self.thread_id = thread_id
        self._agent = None

    def _get_agent(self) -> Any:
        if self._agent is None:
            self._agent = create_agent(project_root=self.project_root)
        return self._agent

    @staticmethod
    def _tools_and_root_block(project_root: str) -> str:
        pr = os.path.abspath(project_root)
        pr_norm = pr.replace("\\", "/")
        return f"""项目根目录（唯一合法的路径前缀）: {pr}

【路径与工具】
- 根据自然语言判断图类型，整理顶层 JSON（user / type / data），先 validate_diagram_request 直至 valid。
- type=er 时调用 **er_draw**，参数为：**project_root**（必须与下方「项目根目录」字符串完全一致）、**user**（顶层 user）、**entity**（data.entity）、**attributes**（data.attributes）。**不要**传入或自拼 output_path；文件路径由工具在代码里固定为 {pr_norm}/data/<user>/er/<entity>.vsdx。
- type=sequence 时调用 **sequence_draw**：**project_root**、**user**、**title**（data.title）、**trip**（data.trip）、**messages**（data.messages）；保存路径固定为 {pr_norm}/data/<user>/sequence/<title>.vsdx。
- type=flowchart 时调用 **flowchart_draw**：**project_root**、**user**、**title**（data.title）、**template**（data.template：1 或 2）、**nodes**（data.nodes）；保存路径固定为 {pr_norm}/data/<user>/flowchart/<title>.vsdx。可先 **check_flowchart_nodes** 自查 nodes。"""

    @staticmethod
    def build_user_content(project_root: str, natural_language: str) -> str:
        return (
            DiagramAgentRunner._tools_and_root_block(project_root)
            + "\n\n【自然语言】\n"
            + natural_language.strip()
        )

    @staticmethod
    def build_thesis_batch_content(
        project_root: str,
        user: str,
        section_321: str,
        chapter4: str,
    ) -> str:
        """论文模式：固定 user + 3.2.1 + 第四章，批量 ER / 时序 / 流程。"""
        head = DiagramAgentRunner._tools_and_root_block(project_root)
        u = user.strip()
        s321 = section_321.strip()
        ch4 = chapter4.strip()
        return f"""{head}

【论文批量任务 — 固定 user】
顶层 JSON 的 **user** 必须为: `{u}`（与 input 下所选目录名**完全一致**，严禁改写）。

【任务一：ER 图】
以下为论文 **3.2.1 数据库概念设计** 的正文摘录。请根据文中各 **实体** 及其 **属性**（含「xx 实体属性图如图」等表述），为 **每个实体** 分别构造 type=er 的 JSON，`validate_diagram_request` 通过后调用 **er_draw**（一实体一图；data.entity / data.attributes 与论文一致）。

--- 3.2.1 ---
{s321}
--- 结束 3.2.1 ---

【任务二：时序图与流程图】
以下为论文 **第四章** 正文。请通读后按章内 **各功能模块** 分别：需要体现多角色交互的绘制 **时序图**（type=sequence，遵守单程/双程与消息规则）；需要体现步骤与分支的绘制 **流程图**（type=flowchart，template 取 1 或 2 与叙述一致；nodes 仅填 text，占位序号规则见技能）。每项先校验再 **sequence_draw** / **flowchart_draw**。title 可取模块名或小节标题。

--- 第四章 ---
{ch4}
--- 结束 第四章 ---"""

    def stream(
        self,
        natural_language: str,
    ) -> Iterator[tuple[str, Any]]:
        """
        流式执行。当 stream_mode 为列表时，LangGraph 产出 (mode, payload)。

        - mode == \"messages\": payload 多为 (token_chunk, metadata)，token 常有 .content
        - mode == \"updates\": payload 为节点状态增量
        """
        agent = self._get_agent()
        content = self.build_user_content(self.project_root, natural_language)
        inp = {"messages": [{"role": "user", "content": content}]}
        config = {"configurable": {"thread_id": self.thread_id}}
        yield from agent.stream(
            inp,
            config=config,
            stream_mode=["messages", "updates"],
        )

    def stream_content(self, content: str) -> Iterator[tuple[str, Any]]:
        """直接传入完整 user 消息（如论文模式拼装结果），不经 build_user_content。"""
        agent = self._get_agent()
        inp = {"messages": [{"role": "user", "content": content}]}
        config = {"configurable": {"thread_id": self.thread_id}}
        yield from agent.stream(
            inp,
            config=config,
            stream_mode=["messages", "updates"],
        )

    def invoke(self, natural_language: str) -> dict[str, Any]:
        """非流式，返回最终 state（含 messages）。"""
        agent = self._get_agent()
        content = self.build_user_content(self.project_root, natural_language)
        return agent.invoke(
            {"messages": [{"role": "user", "content": content}]},
            config={"configurable": {"thread_id": self.thread_id}},
        )

    def invoke_content(self, content: str) -> dict[str, Any]:
        agent = self._get_agent()
        return agent.invoke(
            {"messages": [{"role": "user", "content": content}]},
            config={"configurable": {"thread_id": self.thread_id}},
        )


def _filter_stream_updates(
    payload: Any,
    *,
    skip_middleware: bool = True,
    skip_model_node: bool = True,
) -> Any:
    """
    精简 LangGraph updates：去掉中间件内部状态与冗长的 model 节点（助手逐字已由 messages 流打印）。
    若过滤后无键可展示则返回 None。
    """
    if not isinstance(payload, dict):
        return payload
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if skip_middleware and "Middleware" in k:
            continue
        if skip_model_node and k == "model":
            continue
        out[k] = v
    return out if out else None


def print_stream_events(
    runner: DiagramAgentRunner,
    natural_language: str = "",
    *,
    content: str | None = None,
    print_updates: bool = False,
    skip_middleware_updates: bool = True,
    skip_model_updates: bool = True,
) -> None:
    """默认把流式事件打到 stdout（供 examples 使用）。

    若传入 ``content``，则使用该完整消息，忽略 ``natural_language``。
    print_updates: 为 True 时打印 ``updates`` 流；默认 False，仅助手逐字输出。
    """
    stream_iter = (
        runner.stream_content(content)
        if content is not None
        else runner.stream(natural_language)
    )
    for mode, payload in stream_iter:
        if mode == "messages":
            if isinstance(payload, tuple) and len(payload) >= 1:
                chunk = payload[0]
                c = getattr(chunk, "content", None)
                if c:
                    print(c, end="", flush=True)
            else:
                print(f"\n[messages] {payload!r}")
        elif mode == "updates":
            if print_updates:
                filtered = _filter_stream_updates(
                    payload,
                    skip_middleware=skip_middleware_updates,
                    skip_model_node=skip_model_updates,
                )
                if filtered is not None:
                    print(f"\n[updates] {filtered}\n", flush=True)
        else:
            print(f"\n[{mode}] {payload}\n", flush=True)
    print()
