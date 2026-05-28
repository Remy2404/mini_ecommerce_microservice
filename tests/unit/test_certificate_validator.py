from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from packages.security.certificate_validator import (
    CertificateValidationError,
    validate_mtls_certificate_bundle,
)


def _create_certificate_authority() -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MiniEcommerce"),
            x509.NameAttribute(NameOID.COMMON_NAME, "MiniEcommerce Root CA"),
        ]
    )
    now = datetime.now(UTC)
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_subject)
        .issuer_name(ca_subject)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(private_key=ca_key, algorithm=hashes.SHA256())
    )
    return ca_key, ca_cert


def _create_client_certificate(
    *,
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    client_key: rsa.RSAPrivateKey,
    include_client_auth_eku: bool = True,
) -> x509.Certificate:
    now = datetime.now(UTC)
    builder = (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name(
                [
                    x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                    x509.NameAttribute(NameOID.COMMON_NAME, "client-user"),
                ]
            )
        )
        .issuer_name(ca_cert.subject)
        .public_key(client_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=365))
    )

    if include_client_auth_eku:
        builder = builder.add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=True,
        )

    return builder.sign(private_key=ca_key, algorithm=hashes.SHA256())


def _write_bundle(
    tmp_path,
    *,
    ca_cert: x509.Certificate,
    client_cert: x509.Certificate,
    client_key: rsa.RSAPrivateKey,
) -> tuple[str, str, str]:
    ca_path = tmp_path / "ca.pem"
    client_cert_path = tmp_path / "client.pem"
    client_key_path = tmp_path / "client-key.pem"

    ca_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))
    client_cert_path.write_bytes(client_cert.public_bytes(serialization.Encoding.PEM))
    client_key_path.write_bytes(
        client_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    return str(ca_path), str(client_cert_path), str(client_key_path)


def test_validate_mtls_bundle_success(tmp_path) -> None:
    ca_key, ca_cert = _create_certificate_authority()
    client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client_cert = _create_client_certificate(
        ca_key=ca_key,
        ca_cert=ca_cert,
        client_key=client_key,
    )
    ca_path, cert_path, key_path = _write_bundle(
        tmp_path,
        ca_cert=ca_cert,
        client_cert=client_cert,
        client_key=client_key,
    )

    result = validate_mtls_certificate_bundle(
        ca_cert_path=ca_path,
        client_cert_path=cert_path,
        client_key_path=key_path,
    )

    assert result.ca_certificate.subject == ca_cert.subject
    assert result.client_certificate.subject == client_cert.subject


def test_validate_mtls_bundle_fails_when_key_mismatch(tmp_path) -> None:
    ca_key, ca_cert = _create_certificate_authority()
    client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    mismatched_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client_cert = _create_client_certificate(
        ca_key=ca_key,
        ca_cert=ca_cert,
        client_key=client_key,
    )
    ca_path, cert_path, key_path = _write_bundle(
        tmp_path,
        ca_cert=ca_cert,
        client_cert=client_cert,
        client_key=mismatched_key,
    )

    with pytest.raises(CertificateValidationError, match="does not match"):
        validate_mtls_certificate_bundle(
            ca_cert_path=ca_path,
            client_cert_path=cert_path,
            client_key_path=key_path,
        )


def test_validate_mtls_bundle_fails_without_client_auth_eku(tmp_path) -> None:
    ca_key, ca_cert = _create_certificate_authority()
    client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client_cert = _create_client_certificate(
        ca_key=ca_key,
        ca_cert=ca_cert,
        client_key=client_key,
        include_client_auth_eku=False,
    )
    ca_path, cert_path, key_path = _write_bundle(
        tmp_path,
        ca_cert=ca_cert,
        client_cert=client_cert,
        client_key=client_key,
    )

    with pytest.raises(CertificateValidationError, match="CLIENT_AUTH"):
        validate_mtls_certificate_bundle(
            ca_cert_path=ca_path,
            client_cert_path=cert_path,
            client_key_path=key_path,
        )


def test_validate_mtls_bundle_fails_when_files_missing(tmp_path) -> None:
    missing_path = tmp_path / "missing.pem"

    with pytest.raises(CertificateValidationError, match="does not exist"):
        validate_mtls_certificate_bundle(
            ca_cert_path=str(missing_path),
            client_cert_path=str(missing_path),
            client_key_path=str(missing_path),
        )