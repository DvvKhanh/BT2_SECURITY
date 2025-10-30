# ==========================================
# sign_pdf.py - Chữ ký PDF đẹp (căn trái ảnh, chữ bên phải)
# ==========================================
from datetime import datetime
from pyhanko.sign import signers, fields
from pyhanko.stamp.text import TextStampStyle
from pyhanko.pdf_utils import images
from pyhanko.pdf_utils.text import TextBoxStyle
from pyhanko.pdf_utils.layout import SimpleBoxLayoutRule, AxisAlignment, Margins
from pyhanko.sign.general import load_cert_from_pemder
from pyhanko_certvalidator import ValidationContext
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigFieldSpec


PDF_IN = r"D:\BT2_Security\pdf\original.pdf"
PDF_OUT = r"D:\BT2_Security\pdf\signed.pdf"
KEY_FILE = r"D:\BT2_Security\keys\signer_key.pem"
CERT_FILE = r"D:\BT2_Security\keys\signer_cert.pem"
SIG_IMG = r"D:\BT2_Security\photo\anh.jpg"   # ảnh chữ ký tay

print("🔹 Khởi tạo signer & validation context ...")
signer = signers.SimpleSigner.load(KEY_FILE, CERT_FILE, key_passphrase=None)
vc = ValidationContext(trust_roots=[load_cert_from_pemder(CERT_FILE)])

print("📄 Đang mở file PDF gốc ...")
with open(PDF_IN, "rb") as inf:
    writer = IncrementalPdfFileWriter(inf)

    # Lấy trang cuối cùng
    try:
        num_pages = int(writer.root["/Pages"]["/Count"])
    except Exception:
        num_pages = 1
    target_page = num_pages - 1

    print("🖋 Đang tạo khung chữ ký đẹp ...")
    fields.append_signature_field(
        writer,
        SigFieldSpec(
            sig_field_name="SigField1",
            box=(230, 130, 560, 255),  # vị trí khung chữ ký
            on_page=target_page
        )
    )

    # Ảnh chữ ký tay
    background_img = images.PdfImage(SIG_IMG)

    # Căn ảnh sang trái giữa khung
    bg_layout = SimpleBoxLayoutRule(
        x_align=AxisAlignment.ALIGN_MIN,
        y_align=AxisAlignment.ALIGN_MID,
        margins=Margins(left=15, right=180)  # ảnh bên trái, chừa chỗ bên phải
    )

    # Căn text sang phải
    text_layout = SimpleBoxLayoutRule(
        x_align=AxisAlignment.ALIGN_MAX,
        y_align=AxisAlignment.ALIGN_MID,
        margins=Margins(right=15)
    )

    # Kiểu chữ (Unicode, dễ đọc)
    text_style = TextBoxStyle(font_size=11)

    # Thông tin chữ ký
    ngay_ky = datetime.now().strftime("%d/%m/%Y")
    stamp_text = (
        "Dau Van Khanh\n"
        "Lop: K58KTP\n"
        "SDT: 0962213503\n"
        "MSSV: K225480106099\n"
        f"Ngày ký: {ngay_ky}"
    )

    # Style khung chữ ký tổng thể
    stamp_style = TextStampStyle(
        stamp_text=stamp_text,
        background=background_img,
        background_layout=bg_layout,
        inner_content_layout=text_layout,
        text_box_style=text_style,
        border_width=0.8,
        background_opacity=1.0,
    )

    # Metadata
    meta = signers.PdfSignatureMetadata(
        field_name="SigField1",
        reason="Nộp bài BT2 - Chữ ký số PDF",
        location="Thái Nguyên, VN",
        md_algorithm="sha256",
    )

    # Tạo signer
    pdf_signer = signers.PdfSigner(
        signature_meta=meta,
        signer=signer,
        stamp_style=stamp_style,
    )

    # Tiến hành ký PDF
    with open(PDF_OUT, "wb") as outf:
        pdf_signer.sign_pdf(writer, output=outf)

print("✅ Đã ký PDF thành công! File lưu tại:", PDF_OUT)