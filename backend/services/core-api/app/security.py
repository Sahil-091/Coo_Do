import secrets

import bcrypt
from fastapi import Header, HTTPException, status

from app.config import settings


def verify_internal_secret(x_internal_secret: str = Header(...)) -> None:
    """
    FastAPI dependency guarding every /internal/* route. Only Next.js's
    server should ever know this secret — the browser never sees it, and
    never calls these routes directly. Constant-time comparison to avoid
    a timing side-channel on the secret itself.
    """
    if not secrets.compare_digest(x_internal_secret, settings.internal_shared_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service credentials.",
        )


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
