# ==========================================
# gen_keys.py - Sinh khóa RSA + chứng chỉ tự ký
# ==========================================
import os
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa

# === Hàm tạo thư mục nếu chưa tồn tại ===
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"📂 Tạo thư mục: {path}")

# === Hàm sinh khóa RSA 2048-bit ===
def generate_rsa_private_key(bits=2048):
    print("🔐 Đang tạo private key RSA...")
    return rsa.generate_private_key(public_exponent=65537, key_size=bits)

# === Hàm tạo certificate tự ký (self-signed) ===
def create_self_signed_cert(private_key, subject_info, valid_days=365):
    print("📜 Đang tạo chứng chỉ tự ký...")
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, subject_info.get("C", "VN")),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, subject_info.get("ST", "Bac Ninh")),
        x509.NameAttribute(NameOID.LOCALITY_NAME, subject_info.get("L", "Bac Ninh")),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, subject_info.get("O", "K58KTP")),
        x509.NameAttribute(NameOID.COMMON_NAME, subject_info.get("CN", "Dau Van Khanh")),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=valid_days))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        )
        .sign(private_key, hashes.SHA256())
    )
    return cert

# === Hàm lưu private key ra file PEM ===
def save_private_key(private_key, path):
    with open(path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print(f"✅ Private key đã lưu tại: {path}")

# === Hàm lưu certificate ra file PEM ===
def save_certificate(cert, path):
    with open(path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"✅ Certificate đã lưu tại: {path}")

# === Main ===
if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    KEYS_DIR = os.path.join(BASE_DIR, "..", "keys")
    ensure_dir(KEYS_DIR)

    private_key_path = os.path.join(KEYS_DIR, "signer_key.pem")
    cert_path = os.path.join(KEYS_DIR, "signer_cert.pem")

    private_key = generate_rsa_private_key()

    subject_info = {
        "C": "VN",
        "ST": "Bac Ninh",
        "L": "Bac Ninh",
        "O": "K58KTP",
        "CN": "Dau Van Khanh"
    }

    cert = create_self_signed_cert(private_key, subject_info)

    save_private_key(private_key, private_key_path)
    save_certificate(cert, cert_path)

    print("\n🎉 Hoàn tất: Cặp khóa & chứng chỉ tự ký đã sẵn sàng!")