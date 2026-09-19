import uuid
from datetime import datetime

import httpx

from app.config import settings


class DependencyUnavailable(RuntimeError):
    pass


def account_created_at(user_id: uuid.UUID) -> datetime:
    try:
        response = httpx.get(
            f"{settings.core_api_internal_url}/internal/users/{user_id}",
            headers={"X-Internal-Secret": settings.internal_shared_secret}, timeout=5.0,
        )
        response.raise_for_status()
        return datetime.fromisoformat(response.json()["created_at"].replace("Z", "+00:00"))
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        raise DependencyUnavailable("Account state is temporarily unavailable") from exc


def screen_self_harm(text: str, user_id: uuid.UUID) -> dict:
    try:
        response = httpx.post(
            f"{settings.safety_service_internal_url}/v1/check-text",
            headers={"X-Internal-Secret": settings.internal_shared_secret},
            json={"text": text, "source": "community_post", "user_ref": str(user_id)}, timeout=12.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        # Fail closed: the text must not be stored or displayed when the
        # canonical self-harm screen is unavailable.
        raise DependencyUnavailable("Safety screening is temporarily unavailable") from exc
