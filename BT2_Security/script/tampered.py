# =========================================================
# check_signature.py – PDF signature verification (custom version)
# =========================================================
import os
import hashlib
import datetime
from datetime import timezone, timedelta
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import validation
from pyhanko.sign.validation.status import SignatureStatus
from pyhanko.sign.diff_analysis import ModificationLevel
from pyhanko.keys import load_cert_from_pemder
from pyhanko_certvalidator import ValidationContext

# === 🔧 Configuration (synchronized with sign_pdf.py) ===
PDF_INPUT = r"D:\BT2_Security\pdf\signed.pdf"
CERT_ROOT = r"D:\BT2_Security\keys\signer_cert.pem"
VERIFY_LOG = r"D:\BT2_Security\pdf\verify_log.txt"


# === 🧩 Simple logger utility ===
def log_info(message, end="\n"):
    print(message, end=end)
    with open(VERIFY_LOG, "a", encoding="utf-8") as logf:
        logf.write(message + end)


# === 🧾 Main verification function ===
def analyze_signature(pdf_path, cert_path):
    """Perform step-by-step verification of the digital signature in a PDF."""
    if os.path.exists(VERIFY_LOG):
        os.remove(VERIFY_LOG)

    log_info("╔════════════════════════════════════════════╗")
    log_info("║      PDF SIGNATURE VALIDATION PROCESS      ║")
    log_info("╚════════════════════════════════════════════╝\n")
    log_info(f"[+] File under test : {pdf_path}")
    log_info(f"[+] Run time        : {datetime.datetime.now()}")
    log_info("----------------------------------------------------")

    # === Load certificate for trust validation ===
    try:
        trust_anchor = load_cert_from_pemder(cert_path)
        ctx = ValidationContext(trust_roots=[trust_anchor])
    except Exception as e:
        log_info(f"[!] Failed to load trust certificate: {e}")
        return

    # === Load PDF ===
    try:
        with open(pdf_path, "rb") as doc:
            doc_reader = PdfFileReader(doc)
            signatures = doc_reader.embedded_signatures
            if not signatures:
                log_info("❌ No embedded signature found in PDF.")
                return

            sig_obj = signatures[0]
            sig_name = sig_obj.field_name or "UnnamedSig"
            log_info(f"\n🔍 Found signature field: {sig_name}")

            sig_dict = sig_obj.sig_object
            contents_size = len(sig_dict.get("/Contents"))
            brange = sig_dict.get("/ByteRange")

            log_info(f"/Contents size: {contents_size} bytes")
            log_info(f"/ByteRange: {brange}")

            # === Calculate hash for ByteRange ===
            doc.seek(0)
            pdf_data = doc.read()
            parts = list(brange)
            signed_zone = pdf_data[parts[0]:parts[0] + parts[1]] + pdf_data[parts[2]:parts[2] + parts[3]]
            computed_hash = hashlib.sha256(signed_zone).hexdigest()
            log_info(f"Calculated SHA-256: {computed_hash[:64]} ✅")

            # === Validate signature content ===
            validation_result = validation.validate_pdf_signature(sig_obj, ctx)
            log_info("\n🧾 Signature Verification Details:")
            log_info(validation_result.pretty_print_details())

            # === Extract certificate info ===
            signer_cert = validation_result.signing_cert
            if signer_cert:
                log_info("\n📜 Signer Certificate Information:")
                log_info(f"  Subject: {signer_cert.subject.human_friendly}")

                sha1 = signer_cert.sha1_fingerprint
                sha256 = signer_cert.sha256_fingerprint
                if hasattr(sha1, "hex"):
                    sha1 = sha1.hex()
                if hasattr(sha256, "hex"):
                    sha256 = sha256.hex()
                log_info(f"  SHA1: {sha1}")
                log_info(f"  SHA256: {sha256}")
            else:
                log_info("⚠️ Signer certificate could not be extracted.")

            # === Time of signing ===
            sign_dt = getattr(validation_result, "signer_reported_dt", None)
            if sign_dt:
                vn_time = sign_dt.astimezone(timezone(timedelta(hours=7)))
                log_info(f"\n🕒 Reported signing time (VN): {vn_time}")
            else:
                log_info("⚠️ No RFC3161 timestamp available.")

            # === Check document modification ===
            mod_level = getattr(validation_result, "modification_level", None)
            if mod_level == ModificationLevel.NONE:
                log_info("✅ Document not modified since signing.")
            elif mod_level == ModificationLevel.FORM_FILLING:
                log_info("⚠️ Document modified (form fill) after signing.")
            else:
                log_info("❌ Document was altered after signing!")

            log_info("----------------------------------------------------")

            # === Final result ===
            if validation_result.bottom_line:
                log_info("✅ VALID SIGNATURE – Document integrity confirmed.")
            else:
                log_info("❌ INVALID SIGNATURE or document tampered!")

    except Exception as err:
        log_info(f"[!] Verification error: {err}")

    log_info("\n📄 Verification log saved successfully.")


# === 🚀 Run when script executed directly ===
if __name__ == "__main__":
    analyze_signature(PDF_INPUT, CERT_ROOT)
