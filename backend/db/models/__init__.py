"""
Aggregates all models so Alembic's autogenerate can see the full
metadata. Import this module (not the individual files) when you need
Base.metadata for migrations.
"""
from db.base import Base
from db.models.core import (  # noqa: F401
    ActionAttempt,
    Activity,
    ActivityAlertPreference,
    ActivityMeetup,
    ActivityParticipant,
    ActivityRSVP,
    CheckIn,
    ConsentRecord,
    DataRequest,
    PresenceRoom,
    PrivacySettings,
    Profile,
    TinyAction,
    TrustedContact,
    User,
)
from db.models.matching import Match, MatchBlock, MatchReport  # noqa: F401
from db.models.moderation import (  # noqa: F401
    CommunityGuidelinesAcceptance,
    CommunityPost,
    CommunityReport,
    CommunityRoom,
    ModerationEvent,
)
from db.models.safety import SafetyEvent  # noqa: F401

__all__ = [
    "Base",
    "User",
    "Profile",
    "CheckIn",
    "TinyAction",
    "ActionAttempt",
    "Activity",
    "ActivityParticipant",
    "ActivityMeetup",
    "ActivityRSVP",
    "ActivityAlertPreference",
    "ConsentRecord",
    "PrivacySettings",
    "PresenceRoom",
    "TrustedContact",
    "DataRequest",
    "SafetyEvent",
    "Match",
    "MatchBlock",
    "MatchReport",
    "CommunityRoom",
    "CommunityGuidelinesAcceptance",
    "CommunityPost",
    "CommunityReport",
    "ModerationEvent",
]
