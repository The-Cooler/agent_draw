"""
枚举 Visio 模板中形状的 Name / Text，便于对照 sequence / flowchart 占位格式。
路径相对本仓库根目录，勿写死盘符。
"""
from pathlib import Path

import win32com.client as win32

ROOT = Path(__file__).resolve().parent


def _dump_page_shapes(label: str, vsdx: Path) -> None:
    if not vsdx.is_file():
        print(f"=== {label} ===\n(跳过，文件不存在: {vsdx})\n")
        return
    visio = win32.Dispatch("Visio.Application")
    try:
        doc = visio.Documents.Open(str(vsdx))
        page = doc.Pages(1)
        print(f"=== {label} ({vsdx.name}) ===")
        for shape in page.Shapes:
            try:
                txt = shape.Text
            except Exception:
                txt = "<读取失败>"
            print(f"  名称: {shape.Name}, 文本: {txt!r}")
        doc.Close()
    finally:
        visio.Quit()
    print()


if __name__ == "__main__":
    seq_dir = ROOT / "src" / "visio_agent" / "skills" / "sequence" / "template"
    flow_dir = ROOT / "src" / "visio_agent" / "skills" / "flowchart" / "template"

    _dump_page_shapes("时序·单程", seq_dir / "one_way.vsdx")
    _dump_page_shapes("时序·双程", seq_dir / "double_way.vsdx")
    _dump_page_shapes("流程图·模板1", flow_dir / "template_1.vsdx")
    _dump_page_shapes("流程图·模板2", flow_dir / "template_2.vsdx")
