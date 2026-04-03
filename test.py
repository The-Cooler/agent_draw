import win32com.client as win32

visio = win32.Dispatch("Visio.Application")

# 读取单程模板
doc = visio.Documents.Open(r"E:\Desktop\langchain_draw\src\visio_agent\skills\sequence\template\one_way.vsdx")
page_index = 1
page = doc.Pages(page_index)

print("=== 单程模板 ===")
for shape in page.Shapes:
    print(f"名称: {shape.Name}, 文本: {shape.Text}")
doc.Close()

print()

# 读取双程模板
doc = visio.Documents.Open(r"E:\Desktop\langchain_draw\src\visio_agent\skills\sequence\template\double_way.vsdx")
page_index = 1
page = doc.Pages(page_index)

print("=== 双程模板 ===")
for shape in page.Shapes:
    print(f"名称: {shape.Name}, 文本: {shape.Text}")
doc.Close()

visio.Quit()