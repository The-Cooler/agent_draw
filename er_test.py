import win32com.client as win32
from pathlib import Path

visio = win32.Dispatch("Visio.Application")

# 关键设置
visio.Visible = False          # 不显示窗口
visio.ScreenUpdating = False   # 禁止界面刷新
visio.AlertResponse = 7        # 自动处理弹窗（避免卡住）

FILE_PATH = Path(__file__).resolve().parent
ER_FILE_PATH = FILE_PATH / "src/visio_agent/skills/er/ER模板.vsdx"
print(ER_FILE_PATH.resolve())
doc = visio.Documents.Open(str(ER_FILE_PATH.resolve()))

page_index = 1
page = doc.Pages(page_index)

for shape in page.Shapes:
    print("形状名称: ", shape.Name)
    print("形状文本: ", shape.Text)

    fill_color_cell = shape.Cells("FillForegnd")
    if fill_color_cell.ResultIU is not None:
        fill_color = fill_color_cell.ResultIU
        print("形状颜色: ", fill_color)
        print("")
        fill_color_cell.FormulaU = "RGB(255, 0, 0)"

doc.Save()   # 建议显式保存
doc.Close()
visio.Quit()