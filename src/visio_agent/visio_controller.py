"""
Visio COM Automation Controller
通过 python-win32 (pywin32) 控制 Visio 绘图
优先使用 Draw* 族方法（DrawRectangle/DrawEllipse/DrawLine），
避免 Shapes.AddShape 的 pywin32 兼容性问题。
"""
import win32com.client
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import win32com.client

    _Shape = win32com.client.CDispatch


class VisioController:
    """Visio COM 自动化控制类"""

    def __init__(self, visible: bool = True):
        self.visible = visible
        self.visio: Optional["_Shape"] = None
        self.app: Optional["_Shape"] = None
        self.page: Optional["_Shape"] = None
        self.doc: Optional["_Shape"] = None
        self._connect()

    def _connect(self):
        """连接到 Visio 实例"""
        self.visio = win32com.client.Dispatch("Visio.Application")
        self.app = self.visio
        self.app.Visible = self.visible

    def new_document(self):
        """创建新文档"""
        # 首先检查是否已有打开的文档，如果有则关闭
        try:
            if self.app.Documents.Count > 0:
                for i in range(self.app.Documents.Count):
                    try:
                        doc = self.app.Documents.ItemU(i + 1)
                        if doc and doc.Type != 2:  # 2 = stencil
                            doc.Close()
                    except:
                        pass
        except:
            pass

        # 创建新的空白绘图文档
        # 空字符串 "" 表示使用默认模板
        self.doc = self.app.Documents.Add("")

        # 确保文档已完全创建
        if not self.doc:
            raise RuntimeError("无法创建 Visio 文档")

        # 获取页面 - 使用 ItemU(1) 获取第一页
        # Pages 是 1-based 索引集合
        pages = self.doc.Pages
        if pages.Count < 1:
            # 如果没有页面，创建一个
            self.page = pages.Add()
        else:
            self.page = pages.ItemU(1)

        # 验证 page 是有效的 Page 对象
        if not hasattr(self.page, 'DrawRectangle'):
            raise RuntimeError(f"Page 对象无效: {type(self.page)}")

        return self.doc, self.page

    def open(self, path: str):
        """打开现有文档"""
        try:
            # 关闭当前文档
            if self.doc:
                self.doc.Close()
            # 打开文件
            self.doc = self.app.Documents.Open(os.path.abspath(path))
            if not self.doc:
                raise RuntimeError("无法打开文档")
            # 获取页面
            pages = self.doc.Pages
            if pages.Count >= 1:
                self.page = pages.ItemU(1)
            if not self.page or not hasattr(self.page, 'DrawRectangle'):
                raise RuntimeError("Page 对象无效")
            return self.doc, self.page
        except Exception as e:
            print(f"打开文档失败: {e}")
            raise

    def _parse_color(self, color_str: str) -> int:
        """解析颜色字符串为 RGB 整数"""
        color_str = color_str.strip()
        if color_str.startswith("RGB("):
            parts = color_str[4:-1].split(",")
            r = int(parts[0].strip())
            g = int(parts[1].strip())
            b = int(parts[2].strip())
            return (r << 16) | (g << 8) | b
        return 0

    def _apply_style(self, shape: "_Shape", text: str,
                     fill: str, line: str, weight: float = 1.5):
        """应用样式到图形"""
        try:
            if text:
                shape.Text = text
            # 验证 shape 是否有有效的 Fill 和 Line 属性
            shape.Fill.ForeColor.RGB = self._parse_color(fill)
            shape.Line.Color.RGB = self._parse_color(line)
            shape.Line.Weight = weight
            shape.TextBlock.HorizontalAlign = 4  # visCenter
            shape.TextBlock.VerticalAlign = 4   # visMiddle
        except Exception as e:
            # 如果样式应用失败，尝试基本样式
            try:
                shape.Fill.ForeColor.RGB = self._parse_color(fill)
            except Exception:
                pass
            try:
                shape.Line.Color.RGB = self._parse_color(line)
                shape.Line.Weight = weight
            except Exception:
                pass

    def _drop_from_stencil(self, master_name: str, x: float, y: float,
                            w: float, h: float) -> Optional["_Shape"]:
        """从内置模具中 Drop 指定母版"""
        try:
            # 获取基本模具
            stencil_path = self.app.GetBuiltInStencilFile(1, 2)  # 基本模具，英寸
            stencil = self.app.Documents.OpenEx(stencil_path)
            master = None
            for m in stencil.Masters:
                if m.NameU.lower() == master_name.lower():
                    master = m
                    break
            stencil.Close()
            if master:
                shape = self.page.Drop(master, x, y)
                shape.Width = w
                shape.Height = h
                return shape
        except Exception as e:
            print(f"Drop {master_name} 失败: {e}")
        return None

    def _validate_shape(self, shape) -> bool:
        """验证 shape 是否有有效的 COM 接口"""
        if shape is None:
            return False
        try:
            # 尝试访问基本属性
            _ = shape.Type
            return True
        except Exception:
            return False

    def add_rectangle(self, x: float, y: float,
                      width: float, height: float,
                      text: str = "", fill: str = "RGB(220, 230, 241)",
                      line: str = "RGB(46, 117, 182)") -> Optional["_Shape"]:
        """添加矩形"""
        # 方法1: DrawRectangle (最可靠)
        try:
            shape = self.page.DrawRectangle(x, y, x + width, y + height)
            if shape and self._validate_shape(shape):
                self._apply_style(shape, text, fill, line)
                return shape
        except Exception as e:
            print(f"DrawRectangle 失败: {e}")

        # 方法2: 从模具 Drop
        return self._drop_from_stencil("Rectangle", x, y, width, height)

    def add_ellipse(self, x: float, y: float,
                    width: float, height: float,
                    text: str = "", fill: str = "RGB(255, 245, 238)",
                    line: str = "RGB(218, 112, 70)") -> Optional["_Shape"]:
        """添加椭圆"""
        try:
            shape = self.page.DrawEllipse(x, y, x + width, y + height)
            if shape and self._validate_shape(shape):
                self._apply_style(shape, text, fill, line)
                return shape
        except Exception as e:
            print(f"DrawEllipse 失败: {e}")

        return self._drop_from_stencil("Ellipse", x, y, width, height)

    def add_diamond(self, x: float, y: float,
                    width: float, height: float,
                    text: str = "",
                    fill: str = "RGB(255, 242, 204)",
                    line: str = "RGB(192, 80, 77)") -> Optional["_Shape"]:
        """添加菱形"""
        # 菱形用矩形 + 旋转实现，或用 Isometric Diamond 母版
        try:
            shape = self._drop_from_stencil("Isometric Diamond", x, y, width, height)
            if shape and self._validate_shape(shape):
                self._apply_style(shape, text, fill, line, weight=2.0)
                return shape
        except Exception:
            pass
        # Fallback: 使用菱形母版
        try:
            stencil_path = self.app.GetBuiltInStencilFile(1, 2)
            stencil = self.app.Documents.OpenEx(stencil_path)
            shape = None
            for m in stencil.Masters:
                if "Diamond" in m.NameU or "diamond" in m.NameU:
                    shape = self.page.Drop(m, x + width/2, y + height/2)
                    shape.Width = width
                    shape.Height = height
                    break
            stencil.Close()
            if shape and self._validate_shape(shape):
                self._apply_style(shape, text, fill, line, weight=2.0)
                return shape
        except Exception as e:
            print(f"添加菱形失败: {e}")
        return None

    def add_line(self, x1: float, y1: float,
                 x2: float, y2: float,
                 text: str = "") -> Optional["_Shape"]:
        """添加直线"""
        try:
            shape = self.page.DrawLine(x1, y1, x2, y2)
            if shape and self._validate_shape(shape):
                shape.Line.Color.RGB = self._parse_color("RGB(89, 89, 89)")
                shape.Line.Weight = 1.5
                if text:
                    shape.Text = text
                return shape
        except Exception as e:
            print(f"DrawLine 失败: {e}")

        return self._drop_from_stencil("Line", x1, y1, x2 - x1, y2 - y1)

    def add_rounded_rectangle(self, x: float, y: float,
                               width: float, height: float,
                               text: str = "",
                               fill: str = "RGB(217, 234, 211)",
                               line: str = "RGB(83, 147, 72)") -> Optional["_Shape"]:
        """添加圆角矩形"""
        shape = self._drop_from_stencil("Rounded Rectangle", x, y, width, height)
        if shape and self._validate_shape(shape):
            self._apply_style(shape, text, fill, line)
            return shape
        # 回退到普通矩形
        return self.add_rectangle(x, y, width, height, text, fill, line)

    def add_parallelogram(self, x: float, y: float,
                          width: float, height: float,
                          text: str = "",
                          fill: str = "RGB(221, 217, 195)",
                          line: str = "RGB(148, 138, 84)") -> Optional["_Shape"]:
        """添加平行四边形（输入/输出框）"""
        shape = self._drop_from_stencil("Parallelogram", x, y, width, height)
        if shape and self._validate_shape(shape):
            self._apply_style(shape, text, fill, line)
            return shape
        # 回退到普通矩形
        return self.add_rectangle(x, y, width, height, text, fill, line)

    def add_stadium(self, x: float, y: float,
                    width: float, height: float,
                    text: str = "",
                    fill: str = "RGB(83, 147, 72)",
                    line: str = "RGB(56, 96, 49)") -> Optional["_Shape"]:
        """添加体育场形状（开始/结束）"""
        shape = self._drop_from_stencil("Stadium", x, y, width, height)
        if shape and self._validate_shape(shape):
            self._apply_style(shape, text, fill, line, weight=2.0)
            try:
                shape.Characters.Color.RGB = self._parse_color("RGB(255,255,255)")
            except Exception:
                pass
            return shape
        # 回退到圆角矩形
        return self.add_rounded_rectangle(x, y, width, height, text, fill, line)

    def connect_shapes(self, from_shape: "_Shape",
                       to_shape: "_Shape",
                       connector_name: str = "") -> Optional["_Shape"]:
        """连接两个图形（直线箭头）"""
        try:
            from_x = from_shape.get_Cells("PinX").ResultIU
            from_y = from_shape.get_Cells("PinY").ResultIU
            to_x = to_shape.get_Cells("PinX").ResultIU
            to_y = to_shape.get_Cells("PinY").ResultIU
            shape = self.page.DrawLine(from_x, from_y, to_x, to_y)
            if shape and self._validate_shape(shape):
                shape.Line.Color.RGB = self._parse_color("RGB(89, 89, 89)")
                shape.Line.Weight = 1.5
                shape.EndArrow = 2  # 箭头
                return shape
        except Exception as e:
            print(f"连接图形失败: {e}")
        return None

    def set_shape_style(self, shape: "_Shape",
                        fill_color: str = "RGB(220, 230, 241)",
                        line_color: str = "RGB(46, 117, 182)",
                        text_color: str = "RGB(0, 0, 0)"):
        """设置图形样式"""
        try:
            shape.Fill.ForeColor.RGB = self._parse_color(fill_color)
            shape.Line.Color.RGB = self._parse_color(line_color)
            shape.Characters.Color.RGB = self._parse_color(text_color)
        except Exception as e:
            print(f"设置样式失败: {e}")

    def bring_to_front(self, shape):
        """将图形置于顶层"""
        try:
            shape.BringToFront()
        except Exception:
            pass

    def set_grid_size(self, x_grid: float = 0.25, y_grid: float = 0.25):
        """设置网格大小"""
        try:
            self.page.GridSizeX = x_grid
            self.page.GridSizeY = y_grid
        except Exception:
            pass

    def page_setup(self, width: float = 11.0, height: float = 8.5,
                   orientation: str = "landscape"):
        """设置页面大小"""
        try:
            self.page.PageSheet.get_Cells("PageWidth").FormulaU = f"{width} in"
            self.page.PageSheet.get_Cells("PageHeight").FormulaU = f"{height} in"
        except Exception:
            pass

    def get_page_width(self) -> float:
        """获取页面宽度(英寸)"""
        try:
            return self.page.PageSheet.get_Cells("PageWidth").ResultIU
        except Exception:
            return 11.0

    def get_page_height(self) -> float:
        """获取页面高度(英寸)"""
        try:
            return self.page.PageSheet.get_Cells("PageHeight").ResultIU
        except Exception:
            return 8.5

    def save(self, path: str):
        """保存文档"""
        try:
            if self.doc:
                self.doc.SaveAs(path)
                print(f"已保存到: {path}")
        except Exception as e:
            print(f"保存失败: {e}")

    def export_image(self, path: str):
        """导出为 PNG 图片"""
        try:
            self.page.Export(path)
            print(f"已导出图片到: {path}")
        except Exception as e:
            print(f"导出失败: {e}")

    def close(self):
        """关闭 Visio"""
        try:
            if self.doc:
                self.doc.Close()
            if self.app:
                self.app.Quit()
        except Exception:
            pass
