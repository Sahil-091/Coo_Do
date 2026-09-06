"""
Aggregates all models so Alembic's autogenerate can see the full
metadata. Import this module (not the individual files) when you need
Base.metadata for migrations.
"""
from db.base import Base
from db.models.core import (  # noqa: F401
    ActionAttempt,
    CheckIn,
    ConsentRecord,
    DataRequest,
    PrivacySettings,
    Profile,
    TinyAction,
    User,
)
from db.models.safety import SafetyEvent  # noqa: F401

__all__ = [
    "Base",
    "User",
    "Profile",
    "CheckIn",
    "TinyAction",
    "ActionAttempt",
    "ConsentRecord",
    "PrivacySettings",
    "DataRequest",
    "SafetyEvent",
]
