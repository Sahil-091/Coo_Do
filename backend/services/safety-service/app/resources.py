"""Region-specific crisis resources loaded from an operator-managed JSON file."""
import json
from pathlib import Path

from pydantic import BaseModel, Field


class CrisisResource(BaseModel):
    name: str
    phone: str
    phone_uri: str
    description: str


class ResourceConfig(BaseModel):
    region: str
    emergency_note: str
    resources: list[CrisisResource] = Field(min_length=1)


def load_resources(path: Path) -> ResourceConfig:
    """Read on every request so an externally mounted config can change without a redeploy."""
    with path.open(encoding="utf-8") as resource_file:
        return ResourceConfig.model_validate(json.load(resource_file))
