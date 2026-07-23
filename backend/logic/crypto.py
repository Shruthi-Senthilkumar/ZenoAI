"""Symmetric encryption for tokens stored at rest (Integration Spec §6.1:
"store token encrypted at rest, not plaintext").

Uses Fernet (AES-128-CBC + HMAC, via the `cryptography` package) with a
key from FERNET_KEY. This is deliberately simple, appropriate for a
single-process hackathon backend storing one OAuth token per student —
not a KMS-backed multi-tenant secrets story.

FERNET_KEY must be a urlsafe-base64-encoded 32-byte key. Generate one with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import os

from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet:
    key = os.getenv("FERNET_KEY")
    if not key:
        raise RuntimeError(
            "FERNET_KEY is not set. Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
            "and add it to .env"
        )
    return Fernet(key.encode())


def encrypt_token(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str | None:
    """Returns None on a bad/rotated key rather than raising — a token
    that can no longer be decrypted should be treated the same as no
    token at all (falls back to the connector's mock path), not a
    500 that takes down an unrelated request."""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        return None