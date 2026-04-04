"""
时序图固定泳道与每条消息的 from→to 约定（单程 7 条、双程 13 条）。
参与者名称须与 Visio 模板中泳道文案一致。
"""

from __future__ import annotations

from typing import Any

# 与模板四泳道一致
LANE_USER = "用户"
LANE_FRONTEND = "前端"
LANE_BACKEND = "后端"
LANE_DB = "数据库"

# 序号 1..7（单程）；8..13 为双程第二趟
ONE_WAY_SLOTS: tuple[tuple[str, str], ...] = (
    (LANE_USER, LANE_FRONTEND),  # 1
    (LANE_FRONTEND, LANE_BACKEND),  # 2
    (LANE_BACKEND, LANE_DB),  # 3
    (LANE_DB, LANE_DB),  # 4 内部处理
    (LANE_DB, LANE_BACKEND),  # 5
    (LANE_BACKEND, LANE_FRONTEND),  # 6
    (LANE_FRONTEND, LANE_USER),  # 7
)

DOUBLE_WAY_EXTRA: tuple[tuple[str, str], ...] = (
    (LANE_USER, LANE_FRONTEND),  # 8
    (LANE_FRONTEND, LANE_BACKEND),  # 9
    (LANE_BACKEND, LANE_DB),  # 10
    (LANE_DB, LANE_BACKEND),  # 11
    (LANE_BACKEND, LANE_FRONTEND),  # 12
    (LANE_FRONTEND, LANE_USER),  # 13
)

DOUBLE_WAY_SLOTS: tuple[tuple[str, str], ...] = ONE_WAY_SLOTS + DOUBLE_WAY_EXTRA

SEQUENCE_TEXT_MAX_LEN = 8

_TRIP_VALUES = frozenset({"one_way", "double_way"})


def slots_for_trip(trip: str) -> tuple[tuple[str, str], ...]:
    if trip == "one_way":
        return ONE_WAY_SLOTS
    if trip == "double_way":
        return DOUBLE_WAY_SLOTS
    raise ValueError(f"trip 须为 one_way 或 double_way，当前: {trip!r}")


def validate_sequence_data(data: dict[str, Any]) -> list[str]:
    """校验 type=sequence 的 data；返回错误列表（空表示通过）。"""
    errs: list[str] = []

    title = data.get("title")
    if not title or not isinstance(title, str) or not title.strip():
        errs.append("sequence: data.title 必须为非空字符串（用作保存文件名）")
    else:
        forbidden = '<>:"/\\|?*'
        t = title.strip()
        if any(c in forbidden or ord(c) < 32 for c in t):
            errs.append(
                "sequence: data.title 含非法文件名字符（不含 \\ / : * ? \" < > | 等）"
            )

    trip = data.get("trip")
    if not isinstance(trip, str) or trip not in _TRIP_VALUES:
        errs.append(
            'sequence: data.trip 必须为 "one_way"（单程 7 条）或 "double_way"（双程 13 条）'
        )
        return errs

    try:
        expected = slots_for_trip(trip)
    except ValueError as e:
        errs.append(f"sequence: {e}")
        return errs

    messages = data.get("messages")
    if not isinstance(messages, list):
        errs.append("sequence: data.messages 必须为数组")
        return errs

    n_exp = len(expected)
    if len(messages) != n_exp:
        errs.append(
            f"sequence: data.messages 须恰好 {n_exp} 条（当前 trip={trip}），当前 {len(messages)} 条"
        )
        return errs

    for i, m in enumerate(messages):
        if not isinstance(m, dict):
            errs.append(f"sequence: messages[{i}] 必须是对象")
            continue
        for k in ("from", "to", "text"):
            v = m.get(k)
            if not isinstance(v, str):
                errs.append(f"sequence: messages[{i}].{k} 必须为非空字符串")
                continue
            if k in ("from", "to") and not v.strip():
                errs.append(f"sequence: messages[{i}].{k} 必须为非空字符串")
        text = m.get("text")
        if not isinstance(text, str) or not text.strip():
            errs.append(
                f"sequence: messages[{i}].text 须为非空字符串（每条 ≤{SEQUENCE_TEXT_MAX_LEN} 字）"
            )
        else:
            ts = text.strip()
            if len(ts) > SEQUENCE_TEXT_MAX_LEN:
                errs.append(
                    f"sequence: messages[{i}].text 至多 {SEQUENCE_TEXT_MAX_LEN} 个字（当前 {len(ts)}）"
                )

        exp_from, exp_to = expected[i]
        mf, mt = m.get("from"), m.get("to")
        if isinstance(mf, str) and isinstance(mt, str):
            if mf.strip() != exp_from or mt.strip() != exp_to:
                errs.append(
                    f"sequence: messages[{i}] 须为 {exp_from} -> {exp_to}（序号 {i + 1}），"
                    f"当前为 {mf.strip()!r} -> {mt.strip()!r}"
                )

    return errs
