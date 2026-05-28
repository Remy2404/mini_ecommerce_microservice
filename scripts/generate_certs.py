import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# 1. Create Directory
os.makedirs("certs", exist_ok=True)

# 2. Generate CA Key and Certificate
ca_key = rsa.generate_private_key(
    public_exponent=65537, key_size=4096, backend=default_backend()
)

ca_subject = x509.Name(
    [
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MyOrganization"),
        x509.NameAttribute(NameOID.COMMON_NAME, "MyRootCA"),
    ]
)

ca_cert = (
    x509.CertificateBuilder()
    .subject_name(ca_subject)
    .issuer_name(ca_subject)
    .public_key(ca_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)  # 10 years
    )
    .add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    )
    .sign(ca_key, hashes.SHA256(), default_backend())
)

# 3. Generate Client Key
client_key = rsa.generate_private_key(
    public_exponent=65537, key_size=2048, backend=default_backend()
)

client_subject = x509.Name(
    [
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MyOrganization"),
        x509.NameAttribute(NameOID.COMMON_NAME, "client-user"),
    ]
)

# 4. Generate and Sign Client Certificate
client_cert = (
    x509.CertificateBuilder()
    .subject_name(client_subject)
    .issuer_name(ca_subject)  # Signed by CA
    .public_key(client_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)  # 1 year
    )
    .add_extension(
        x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
        critical=True,
    )
    .sign(ca_key, hashes.SHA256(), default_backend())
)

# 5. Write Files
# CA Certificate
with open("certs/ca.pem", "wb") as f:
    f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

# Client Private Key
with open("certs/client-key.pem", "wb") as f:
    f.write(
        client_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

# Client Certificate
with open("certs/client.pem", "wb") as f:
    f.write(client_cert.public_bytes(serialization.Encoding.PEM))

print("Certificates generated successfully in ./certs")
print("   - CA_CERT_PATH=certs/ca.pem")
print("   - CLIENT_CERT_PATH=certs/client.pem")
print("   - CLIENT_KEY_PATH=certs/client-key.pem")
