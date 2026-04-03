import win32com.client as win32

visio = win32.Dispatch("Visio.Application")
doc = visio.Documents.Open(r"E:\Desktop\langchain_draw\src\visio_agent\skills\er\template\ER_even.vsdx")

page_index = 1  # 指定要读取的页面索引（从1开始）
page = doc.Pages(page_index)

# 遍历页面上的所有形状
for shape in page.Shapes:
    print("形状名称: ", shape.Name)
    print("形状文本: ", shape.Text)
        
doc.Close()
visio.Quit()