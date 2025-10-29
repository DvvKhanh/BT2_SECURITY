from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from pikepdf import Pdf
from pathlib import Path
from datetime import datetime

INPUT_PDF = Path(r"D:\BT2_Security\pdf\signed.pdf")
OUTPUT_DIR = Path(r"D:\BT2_Security\output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OVERLAY_PDF = OUTPUT_DIR / "watermark_overlay.pdf"
FIRSTPAGE_OVERLAY = OUTPUT_DIR / "firstpage_alert.pdf"
LAST_OVERLAY = OUTPUT_DIR / "lastpage_overlay.pdf"
OUTPUT_PDF = OUTPUT_DIR / f"tampered.pdf"


FONT_PATH = Path("C:/Windows/Fonts/times.ttf")
pdfmetrics.registerFont(TTFont("TimesUnicode", str(FONT_PATH)))


def create_overlay_watermark(path: Path, page_w: float, page_h: float):
    """Tạo watermark nghiêng mờ nền."""
    c = canvas.Canvas(str(path), pagesize=(page_w, page_h))
    c.saveState()
    try:
        c.setFillAlpha(0.12)
    except Exception:
        pass
    c.setFont("TimesUnicode", 72)
    c.setFillColorRGB(0.2, 0.2, 0.25)
    c.translate(page_w / 2.0, page_h / 2.0)
    c.rotate(30)
    c.drawCentredString(0, 0, "WATERMARK - FILE ĐÃ BỊ CHỈNH SỬA")
    c.restoreState()

    c.setFont("TimesUnicode", 10)
    c.setFillColorRGB(0, 0, 0)
    margin = 15 * mm
    footer_w = 260
    footer_x = page_w - margin - footer_w
    footer_y = margin
    c.rect(footer_x - 6, footer_y - 6, footer_w + 12, 40, stroke=1, fill=0)
    c.drawString(footer_x, footer_y + 18, "[!] CẢNH BÁO: Đây KHÔNG PHẢI là bản PDF gốc đã ký.")
    c.save()
    print(f"✅ Đã tạo watermark overlay: {path.name}")


def create_overlay_firstpage_alert(path: Path, page_w: float, page_h: float):
    """Thêm dòng cảnh báo lớn ở đầu trang (không đè nội dung)."""
    c = canvas.Canvas(str(path), pagesize=(page_w, page_h))
    c.setFont("TimesUnicode", 24)
    c.setFillColorRGB(1, 0, 0)

    y_top = page_h - 50  
    c.drawCentredString(page_w / 2, y_top, "File PDF đã bị chỉnh sửa ")
    c.setFont("TimesUnicode", 13)
    c.drawCentredString(page_w / 2, y_top - 20, "Chữ ký số không còn hợp lệ.")
    c.save()
    print(f"🚨 Đã tạo cảnh báo trang đầu: {path.name}")

def create_overlay_footer_time(path: Path, page_w: float, page_h: float):
    """Hiển thị thời gian chỉnh sửa ở dưới khung cảnh báo."""
    c = canvas.Canvas(str(path), pagesize=(page_w, page_h))
    c.setFont("TimesUnicode", 10)
    c.setFillColorRGB(0, 0, 0)
    ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    c.drawRightString(page_w - 15 * mm, 8 * mm, f"Đã chỉnh sửa ngày: {ts}")
    c.save()
    print(f"🕒 Đã tạo footer thời gian: {path.name}")


def main():
    if not INPUT_PDF.exists():
        raise FileNotFoundError(f"Không tìm thấy file nguồn: {INPUT_PDF}")

    base = Pdf.open(INPUT_PDF)
    mb = base.pages[0].MediaBox
    page_w = float(mb[2]) - float(mb[0])
    page_h = float(mb[3]) - float(mb[1])


    create_overlay_watermark(OVERLAY_PDF, page_w, page_h)
    create_overlay_firstpage_alert(FIRSTPAGE_OVERLAY, page_w, page_h)
    create_overlay_footer_time(LAST_OVERLAY, page_w, page_h)


    wm_pdf = Pdf.open(OVERLAY_PDF)
    alert_pdf = Pdf.open(FIRSTPAGE_OVERLAY)
    footer_pdf = Pdf.open(LAST_OVERLAY)


    for page in base.pages:
        page.add_overlay(wm_pdf.pages[0])

    base.pages[0].add_overlay(alert_pdf.pages[0])      # cảnh báo đầu trang
    base.pages[-1].add_overlay(footer_pdf.pages[0])    # ngày giờ cuối trang

    base.save(OUTPUT_PDF)
    print(f"💾 Đã lưu file mới: {OUTPUT_PDF}")

if __name__ == "__main__":
    main()
