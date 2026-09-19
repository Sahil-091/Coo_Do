"""Narrow, server-to-server client for core-api's matching data contract."""
import uuid

import httpx

from app.config import settings


def fetch_candidate_pool(user_id: uuid.UUID) -> dict:
    response = httpx.get(
        f"{settings.core_api_internal_url}/internal/matching/candidates/{user_id}",
        headers={"X-Internal-Secret": settings.internal_shared_secret},
        timeout=5.0,
    )
    response.raise_for_status()
    return response.json()
