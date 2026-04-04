"""
ER 图工具 - 单次调用完成所有操作

工具函数: er_draw
--------------------------
功能: 绘制单个 ER 实体到 Visio 文件

输出路径（代码内固定拼接，禁止由模型自拟）:
    {project_root}/data/{user}/er/{entity}.vsdx

参数:
    project_root (str): 项目根目录绝对路径（须与用户消息中给出的项目根一致）
    user (str): 顶层 JSON 的 user
    entity (str): 实体名称，如 "学生"
    attributes (list): 属性列表，如 [{"name": "学号", "type": "pk"}, {"name": "姓名"}]；仅 type=="pk" 表示主键，其余 type 可省略或任意

模板:
    - 合法请求的 attributes 已由校验限制为至多 10 条；本工具仍按 ER_TEMPLATE_ATTR_SLOTS 截断以防万一
    - 奇偶模板按「传入 attributes 的总条数」区分
    - 写入 Visio 的属性显示文本与传入的 name 一致，不做改写、翻译或裁剪（仅顺序上 pk 排第一）
    - 实体名与属性 name 须符合校验（中文为主，名为 ID/id 除外），由 validate_diagram_request 约束

属性 type:
    仅当值为 "pk" 时视为主键（排第1位）；其它取值或省略均视为非主键，不在 fk/normal 上区分。

返回值:
    dict: {"success": bool, "message": str}
    - success=True: 成功，返回 {"success": True, "message": "已保存: /path/to/file.vsdx"}
    - success=False: 失败，返回 {"success": False, "message": "错误原因"}

使用示例:
    er_draw(
        project_root="D:/proj",
        user="张三",
        entity="学生",
        attributes=[
            {"name": "学号", "type": "pk"},
            {"name": "姓名"},
        ],
    )
"""

import os
from pathlib import Path

import pythoncom
import win32com.client
from langchain_core.tools import tool

# 与 Visio 模板中「ER图-属性」形状数量一致
ER_TEMPLATE_ATTR_SLOTS = 10


@tool
def er_draw(project_root: str, user: str, entity: str, attributes: list) -> dict:
    """
    绘制单个 ER 实体；输出路径固定为 project_root/data/user/er/entity.vsdx。

    Args:
        project_root: 项目根目录绝对路径
        user: 顶层请求中的 user
        entity: 实体名称（亦为文件名主体）
        attributes: 属性列表；仅 type "pk" 为主键，其余不区分类型

    Returns:
        {"success": bool, "message": str}
    """
    skills_dir = os.path.dirname(__file__)
    template_dir = os.path.join(skills_dir, "template")

    root = os.path.abspath(project_root.strip())
    usr = user.strip()
    ent = entity.strip()
    out_dir = os.path.join(root, "data", usr, "er")
    abs_output = str(Path(out_dir) / f"{ent}.vsdx")

    pk = None
    non_pk = []
    for attr in attributes:
        if attr.get("type") == "pk":
            pk = attr
        else:
            non_pk.append(attr)
    sorted_attrs = [pk] + non_pk if pk else non_pk
    draw_attrs = sorted_attrs[:ER_TEMPLATE_ATTR_SLOTS]

    attr_count = len(attributes)
    if attr_count % 2 == 1:
        template_path = os.path.join(template_dir, "ER_odd.vsdx")
    else:
        template_path = os.path.join(template_dir, "ER_even.vsdx")

    if not os.path.exists(template_path):
        return {"success": False, "message": f"模板不存在: {template_path}"}

    pythoncom.CoInitialize()
    try:
        import shutil

        os.makedirs(out_dir, exist_ok=True)
        shutil.copy2(template_path, abs_output)

        visio = win32com.client.Dispatch("Visio.Application")
        visio.Visible = False
        doc = visio.Documents.Open(abs_output)
        page = doc.Pages.ItemU(1)

        entities = []
        attrs = []
        for i in range(1, page.Shapes.Count + 1):
            shape = page.Shapes.ItemU(i)
            if "流程图过程" in shape.Name:
                entities.append(shape)
            elif "ER图-属性" in shape.Name:
                attrs.append(shape)

        def get_pos(s):
            try:
                return (s.get_Cells("PinY").ResultIU, s.get_Cells("PinX").ResultIU)
            except:
                return (0, 0)
        entities.sort(key=get_pos)

        def get_num(s):
            try:
                return int(s.Text)
            except:
                return 0
        attrs.sort(key=get_num)

        if entities:
            entities[0].Text = ent

        for i, attr_info in enumerate(draw_attrs):
            if i < len(attrs):
                attrs[i].Text = attr_info.get("name", "")

        for i in range(len(draw_attrs), len(attrs)):
            attrs[i].Delete()

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
