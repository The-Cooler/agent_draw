"""
ER 图工具 - 单次调用完成所有操作

工具函数: er_draw
--------------------------
功能: 绘制单个 ER 实体到 Visio 文件

参数:
    entity (str): 实体名称，如 "学生"
    attributes (list): 属性列表，如 [{"name": "学号", "type": "pk"}, {"name": "姓名", "type": "normal"}]
    output_path (str): 输出文件路径，必须是 .vsdx 格式

模板选择:
    - 奇数属性数量: template/ER_odd.vsdx
    - 偶数属性数量: template/ER_even.vsdx
    - 属性超过模板容量时，超出部分舍弃
    - 模板第1个属性位置固定为主键

属性类型:
    pk: 主键（自动排第1位，不加特殊符号）
    fk: 外键（不加特殊符号）
    normal: 普通属性

返回值:
    dict: {"success": bool, "message": str}
    - success=True: 成功，返回 {"success": True, "message": "已保存: /path/to/file.vsdx"}
    - success=False: 失败，返回 {"success": False, "message": "错误原因"}

使用示例:
    er_draw(
        entity="学生",
        attributes=[
            {"name": "学号", "type": "pk"},
            {"name": "姓名", "type": "normal"}
        ],
        output_path="学生.vsdx"
    )
"""

import os
import pythoncom
import win32com.client
from langchain_core.tools import tool


@tool
def er_draw(entity: str, attributes: list, output_path: str) -> dict:
    """
    绘制单个 ER 实体

    Args:
        entity: 实体名称
        attributes: 属性列表 [{"name": "学号", "type": "pk"}, ...]
        output_path: 输出文件路径 (.vsdx)

    Returns:
        {"success": bool, "message": str}
    """
    skills_dir = os.path.dirname(__file__)
    template_dir = os.path.join(skills_dir, "template")

    # 根据属性数量选择模板
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

        # 1. 复制模板
        abs_output = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_output), exist_ok=True)
        shutil.copy2(template_path, abs_output)

        # 2. 打开文件
        visio = win32com.client.Dispatch("Visio.Application")
        visio.Visible = False
        doc = visio.Documents.Open(abs_output)
        page = doc.Pages.ItemU(1)

        # 3. 查找形状
        entities = []
        attrs = []
        for i in range(1, page.Shapes.Count + 1):
            shape = page.Shapes.ItemU(i)
            if "流程图过程" in shape.Name:
                entities.append(shape)
            elif "ER图-属性" in shape.Name:
                attrs.append(shape)

        # 4. 按位置排序实体
        def get_pos(s):
            try:
                return (s.get_Cells("PinY").ResultIU, s.get_Cells("PinX").ResultIU)
            except:
                return (0, 0)
        entities.sort(key=get_pos)

        # 5. 按文本数字排序属性
        def get_num(s):
            try:
                return int(s.Text)
            except:
                return 0
        attrs.sort(key=get_num)

        # 6. 修改实体名
        if entities:
            entities[0].Text = entity

        # 7. 修改属性（主键排第1位，其他保持原始顺序）
        # pk 排第1位，其余按原始顺序
        pk = None
        non_pk = []
        for attr in attributes:
            if attr.get("type") == "pk":
                pk = attr
            else:
                non_pk.append(attr)
        sorted_attrs = [pk] + non_pk if pk else non_pk

        for i, attr_info in enumerate(sorted_attrs):
            if i < len(attrs):
                attrs[i].Text = attr_info.get("name", "")

        # 8. 删除多余属性
        for i in range(len(attributes), len(attrs)):
            attrs[i].Delete()

        # 9. 保存并关闭
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
