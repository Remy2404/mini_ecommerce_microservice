"""Certificate validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dsa, ec, ed25519, ed448, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID


class CertificateValidationError(ValueError):
    """Raised when a certificate bundle fails validation."""


@dataclass(frozen=True, slots=True)
class CertificateBundleValidationResult:
    """Validated mTLS bundle metadata."""

    ca_certificate: x509.Certificate
    client_certificate: x509.Certificate


def _read_required_file(path_value: str, label: str) -> bytes:
    path = Path(path_value)
    if not path.is_file():
        raise CertificateValidationError(f"{label} does not exist: {path}")

    try:
        return path.read_bytes()
    except OSError as exc:
        raise CertificateValidationError(f"Unable to read {label}: {path}") from exc


def _load_pem_certificate(payload: bytes, label: str) -> x509.Certificate:
    try:
        return x509.load_pem_x509_certificate(payload)
    except ValueError as exc:
        raise CertificateValidationError(
            f"{label} is not a valid PEM certificate"
        ) from exc


def _load_private_key(payload: bytes):
    try:
        return serialization.load_pem_private_key(payload, password=None)
    except ValueError as exc:
        raise CertificateValidationError(
            "Client private key is not a valid unencrypted PEM key"
        ) from exc


def _is_ca_certificate(certificate: x509.Certificate) -> bool:
    try:
        constraints = certificate.extensions.get_extension_for_class(
            x509.BasicConstraints,
        ).value
    except x509.ExtensionNotFound:
        return False

    return constraints.ca is True


def _has_client_auth_eku(certificate: x509.Certificate) -> bool:
    try:
        usages = certificate.extensions.get_extension_for_class(
            x509.ExtendedKeyUsage,
        ).value
    except x509.ExtensionNotFound:
        return False

    return ExtendedKeyUsageOID.CLIENT_AUTH in usages


def _cert_not_valid_before(certificate: x509.Certificate) -> datetime:
    if hasattr(certificate, "not_valid_before_utc"):
        return certificate.not_valid_before_utc
    return certificate.not_valid_before.replace(tzinfo=UTC)


def _cert_not_valid_after(certificate: x509.Certificate) -> datetime:
    if hasattr(certificate, "not_valid_after_utc"):
        return certificate.not_valid_after_utc
    return certificate.not_valid_after.replace(tzinfo=UTC)


def _assert_certificate_time_window(
    certificate: x509.Certificate, now: datetime
) -> None:
    not_before = _cert_not_valid_before(certificate)
    not_after = _cert_not_valid_after(certificate)

    if now < not_before:
        raise CertificateValidationError("Client certificate is not yet valid")

    if now > not_after:
        raise CertificateValidationError("Client certificate is expired")


def _public_keys_match(client_certificate: x509.Certificate, private_key) -> bool:
    cert_public_key = client_certificate.public_key()
    private_public_key = private_key.public_key()

    if isinstance(cert_public_key, rsa.RSAPublicKey) and isinstance(
        private_public_key,
        rsa.RSAPublicKey,
    ):
        return cert_public_key.public_numbers() == private_public_key.public_numbers()

    if isinstance(cert_public_key, ec.EllipticCurvePublicKey) and isinstance(
        private_public_key,
        ec.EllipticCurvePublicKey,
    ):
        return cert_public_key.public_numbers() == private_public_key.public_numbers()

    if isinstance(cert_public_key, dsa.DSAPublicKey) and isinstance(
        private_public_key,
        dsa.DSAPublicKey,
    ):
        return cert_public_key.public_numbers() == private_public_key.public_numbers()

    if isinstance(cert_public_key, ed25519.Ed25519PublicKey) and isinstance(
        private_public_key,
        ed25519.Ed25519PublicKey,
    ):
        return (
            cert_public_key.public_bytes_raw() == private_public_key.public_bytes_raw()
        )

    if isinstance(cert_public_key, ed448.Ed448PublicKey) and isinstance(
        private_public_key,
        ed448.Ed448PublicKey,
    ):
        return (
            cert_public_key.public_bytes_raw() == private_public_key.public_bytes_raw()
        )

    return False


def validate_mtls_certificate_bundle(
    *,
    ca_cert_path: str,
    client_cert_path: str,
    client_key_path: str,
    now: datetime | None = None,
) -> CertificateBundleValidationResult:
    """Validate CA + client certificate + client key bundle for mTLS usage."""
    current_time = now.astimezone(UTC) if now is not None else datetime.now(UTC)

    ca_certificate = _load_pem_certificate(
        _read_required_file(ca_cert_path, "CA certificate"),
        "CA certificate",
    )
    client_certificate = _load_pem_certificate(
        _read_required_file(client_cert_path, "Client certificate"),
        "Client certificate",
    )
    private_key = _load_private_key(
        _read_required_file(client_key_path, "Client private key"),
    )

    if not _is_ca_certificate(ca_certificate):
        raise CertificateValidationError(
            "CA certificate must include BasicConstraints(ca=True)"
        )

    if not _has_client_auth_eku(client_certificate):
        raise CertificateValidationError(
            "Client certificate must include CLIENT_AUTH extended key usage"
        )

    _assert_certificate_time_window(client_certificate, current_time)

    if not _public_keys_match(client_certificate, private_key):
        raise CertificateValidationError(
            "Client private key does not match client certificate public key",
        )

    return CertificateBundleValidationResult(
        ca_certificate=ca_certificate,
        client_certificate=client_certificate,
    )


__all__ = [
    "CertificateBundleValidationResult",
    "CertificateValidationError",
    "validate_mtls_certificate_bundle",
]
