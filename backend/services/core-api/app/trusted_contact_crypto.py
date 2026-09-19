"""Encryption keyring for Phase 10 trusted contact details."""

from cryptography.fernet import Fernet, MultiFernet


def build_trusted_contact_cipher(serialized_keys: str) -> MultiFernet:
    """Build a required newest-first Fernet keyring with no dev fallback."""
    keys = [key.strip().encode() for key in serialized_keys.split(",") if key.strip()]
    if not keys:
        raise ValueError("TRUSTED_CONTACT_ENCRYPTION_KEYS must contain at least one Fernet key.")
    return MultiFernet([Fernet(key) for key in keys])
