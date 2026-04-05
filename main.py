#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sys


def main() -> int:
    env = os.environ.get("VISIO_PROJECT_ROOT", "").strip()
    if env:
        project_root = os.path.abspath(env)
    else:
        project_root = os.path.dirname(os.path.abspath(__file__))

    src_dir = os.path.join(project_root, "src")
    if os.path.isdir(src_dir) and src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    from visio_agent.diagram_runner import DiagramAgentRunner, print_stream_events
    from visio_agent.paper_input import run_paper_mode

    result = run_paper_mode(project_root)
    if result is None:
        return 1
    uid, doc_path, _s321, _ch4, content = result
    print(f"用户: {uid}")
    print(f"论文: {doc_path}")
    print("-" * 50)
    print_stream_events(DiagramAgentRunner(project_root=project_root), content=content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
