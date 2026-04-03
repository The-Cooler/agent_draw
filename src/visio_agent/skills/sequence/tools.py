"""
时序图工具 - 单次调用完成所有操作

工具函数:
- check_message_count: 检查消息条数是否符合流程类型要求
- check_message_length: 检查每条消息字数是否超过8个
- sequence_draw: 绘制时序图

使用流程:
1. 调用 check_message_count 检查消息条数
2. 调用 check_message_length 检查字数
3. 确认通过后调用 sequence_draw
"""

import os
import shutil
import re
import pythoncom
import win32com.client
from langchain_core.tools import tool


@tool
def check_message_count(flow_type: str, messages: list) -> dict:
    """
    检查消息条数是否符合流程类型要求

    单程(7条) 或 双程(13条)

    Args:
        flow_type: "one_way" 或 "double_way"
        messages: 消息列表

    Returns:
        {"pass": bool, "message": str}
        - pass=True: 检查通过
        - pass=False: 检查失败，说明原因
    """
    if flow_type == "one_way":
        required = 7
    elif flow_type == "double_way":
        required = 13
    else:
        return {"pass": False, "message": f"未知的流程类型: {flow_type}"}

    actual = len(messages)
    if actual == required:
        return {"pass": True, "message": f"消息条数正确: {actual}条"}
    elif actual < required:
        return {"pass": False, "message": f"消息条数不足: 当前{actual}条，需要{required}条，请补充"}
    else:
        return {"pass": False, "message": f"消息条数过多: 当前{actual}条，需要{required}条，请删减"}


@tool
def check_message_length(messages: list) -> dict:
    """
    检查每条消息字数是否超过8个

    Args:
        messages: 消息列表

    Returns:
        {"pass": bool, "message": str, "errors": list}
        - pass=True: 全部通过
        - pass=False: 有超长消息，列出错误
    """
    errors = []
    for i, msg in enumerate(messages, 1):
        if len(msg) > 8:
            errors.append(f"第{i}条消息超长: 「{msg}」({len(msg)}字)，必须≤8字")

    if errors:
        return {"pass": False, "message": "存在超长消息", "errors": errors}
    else:
        return {"pass": True, "message": "所有消息字数符合要求"}


def parse_sequence_from_nl(natural_language: str, messages_list: list = None) -> tuple[list, str]:
    """
    从输入解析出消息列表

    Args:
        natural_language: 自然语言描述（格式：时序图"名称"：描述）
        messages_list: 直接提供的消息列表，如果有则优先使用

    Returns:
        (messages, title): 消息列表和标题
    """
    # 匹配格式: 时序图"xxx"：描述
    pattern = r'时序图[''"]([^''"]+)[''"][:：](.+)'
    match = re.search(pattern, natural_language)

    if match:
        title = match.group(1).strip()
        desc = match.group(2).strip()
    else:
        title = ""
        desc = natural_language

    # 如果直接提供了消息列表，直接使用
    if messages_list:
        return [{"content": msg} for msg in messages_list], title

    # 否则按逗号分割描述（支持中英文逗号）
    parts = [s.strip() for s in re.split(r'[,，]', desc)]
    parts = [s for s in parts if s]

    return [{"content": msg} for msg in parts], title


@tool
def sequence_draw(flow_type: str, messages: list, output_path: str) -> dict:
    """
    绘制时序图

    Args:
        flow_type: 流程类型，"one_way" 或 "double_way"，由LLM根据用户描述判断
        messages: 消息列表，如 ["发送请求", "验证身份", "查询数据库", ...]
        output_path: 输出文件路径 (.vsdx)

    Returns:
        {"success": bool, "message": str}
    """
    # 直接使用消息列表
    messages = [{"content": msg} for msg in messages]

    # 根据流程类型确定目标消息数量
    if flow_type == "one_way":
        target_count = 7
    elif flow_type == "double_way":
        target_count = 13
    else:
        return {"success": False, "message": f"未知的流程类型: {flow_type}"}

    # 截断或补充消息列表
    messages = messages[:target_count] if len(messages) >= target_count else messages + [{"content": ""}] * (target_count - len(messages))

    skills_dir = os.path.dirname(__file__)
    template_dir = os.path.join(skills_dir, "template")

    # 选择模板
    if flow_type == "one_way":
        template_path = os.path.join(template_dir, "one_way.vsdx")
    elif flow_type == "double_way":
        template_path = os.path.join(template_dir, "double_way.vsdx")
    else:
        return {"success": False, "message": f"未知的流程类型: {flow_type}"}

    if not os.path.exists(template_path):
        return {"success": False, "message": f"模板不存在: {template_path}"}

    pythoncom.CoInitialize()
    try:
        # 1. 处理路径：去除前导斜杠，确保是相对路径
        clean_path = output_path.lstrip('/\\')
        abs_output = os.path.abspath(clean_path)
        os.makedirs(os.path.dirname(abs_output), exist_ok=True)
        shutil.copy2(template_path, abs_output)

        # 2. 打开文件
        visio = win32com.client.Dispatch("Visio.Application")
        visio.Visible = False
        doc = visio.Documents.Open(abs_output)
        page = doc.Pages.ItemU(1)

        # 3. 遍历所有形状，查找和替换消息
        for i in range(1, page.Shapes.Count + 1):
            shape = page.Shapes.ItemU(i)
            original_text = shape.Text

            # 匹配 "x. 消息x" 格式
            match = re.match(r'^(\d+)\.\s*消息\d+$', original_text)
            if match:
                idx = int(match.group(1)) - 1  # 转为0-based索引
                if idx < len(messages):
                    msg = messages[idx]
                    # 替换为 "序号. 消息内容"
                    shape.Text = f"{idx + 1}. {msg.get('content', '')}"

        # 4. 保存并关闭
        doc.Save()
        doc.Close()
        visio.Quit()

        return {"success": True, "message": f"已保存: {abs_output}"}

    except Exception as e:
        try:
            visio.Quit()
        except:
            pass
        return {"success": False, "message": f"失败: {e}"}

    finally:
        pythoncom.CoUninitialize()