"""Encryption primitives for private journal entries.

The value comes from the deployment's managed ``JOURNAL_ENCRYPTION_KEYS``
secret.  It is deliberately not given a development default: losing or
silently changing the key would make a student's journal unreadable.
"""

from cryptography.fernet import Fernet, MultiFernet


def build_journal_cipher(serialized_keys: str) -> MultiFernet:
    """Build a newest-first Fernet keyring from the managed secret.

    MultiFernet encrypts with its first key and attempts every supplied key
    when decrypting.  To rotate safely, prepend the new key and retain the
    retiring key until all existing entries have been re-encrypted or aged
    out.  Empty keyrings and malformed values fail startup rather than
    accepting an unsafe fallback key.
    """
    keys = [key.strip().encode() for key in serialized_keys.split(",") if key.strip()]
    if not keys:
        raise ValueError("JOURNAL_ENCRYPTION_KEYS must contain at least one Fernet key.")
    return MultiFernet([Fernet(key) for key in keys])
