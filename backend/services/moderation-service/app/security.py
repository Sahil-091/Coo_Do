import secrets

from fastapi import Header, HTTPException, status

from app.config import settings


def verify_internal_secret(x_internal_secret: str = Header(default="")) -> None:
    if not secrets.compare_digest(x_internal_secret, settings.internal_shared_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal credential")


def verify_reviewer_token(x_moderation_reviewer_token: str = Header(default="")) -> None:
    if not settings.moderation_reviewer_token or not secrets.compare_digest(
        x_moderation_reviewer_token, settings.moderation_reviewer_token
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reviewer credential")
