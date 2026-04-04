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
    def build_user_content(project_root: str, natural_language: str) -> str:
        pr = os.path.abspath(project_root)
        pr_norm = pr.replace("\\", "/")
        return f"""项目根目录（唯一合法的路径前缀）: {pr}

【路径与工具】
- 根据自然语言判断图类型，整理顶层 JSON（user / type / data），先 validate_diagram_request 直至 valid。
- type=er 时调用 **er_draw**，参数为：**project_root**（必须与下方「项目根目录」字符串完全一致）、**user**（顶层 user）、**entity**（data.entity）、**attributes**（data.attributes）。**不要**传入或自拼 output_path；文件路径由工具在代码里固定为 {pr_norm}/data/<user>/er/<entity>.vsdx。
- type=sequence 时调用 **sequence_draw**：**project_root**、**user**、**title**（data.title）、**trip**（data.trip）、**messages**（data.messages）；保存路径固定为 {pr_norm}/data/<user>/sequence/<title>.vsdx。
- type=flowchart 仍用占位工具 flowchart_draw；若未实现须如实说明。

【自然语言】
{natural_language.strip()}"""

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

    def invoke(self, natural_language: str) -> dict[str, Any]:
        """非流式，返回最终 state（含 messages）。"""
        agent = self._get_agent()
        content = self.build_user_content(self.project_root, natural_language)
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
    natural_language: str,
    *,
    print_updates: bool = False,
    skip_middleware_updates: bool = True,
    skip_model_updates: bool = True,
) -> None:
    """默认把流式事件打到 stdout（供 examples 使用）。

    print_updates: 为 True 时打印 ``updates`` 流；默认 False，仅助手逐字输出。
    """
    for mode, payload in runner.stream(natural_language):
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
