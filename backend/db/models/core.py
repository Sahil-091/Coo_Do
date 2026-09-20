"""
Tables owned by core-api. See R&D doc Section 19 (Database Design).

Deliberately NOT included yet (see /docs/schema-plan.md for the full
deferred list and which phase adds each): communities/rooms/messages and
their moderation workflow (Phase 12), activities/presence_rooms (Phase 9),
campus_locations (P2, not in current 14-phase plan), journals (Phase 8),
trusted_contacts (Phase 10), professional_resources (Phase 7).
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


def enum_values(enum_class: type[enum.Enum]) -> list[str]:
    """
    Persist enum values instead of Python enum member names.

    For example:

        ActivityTopic.STUDY.name  -> "STUDY"
        ActivityTopic.STUDY.value -> "study"

    The PostgreSQL migrations define the lowercase values, so SQLAlchemy must
    store enum.value rather than enum.name.
    """
    return [member.value for member in enum_class]


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    auth_subject: Mapped[str | None] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=True,
    )
    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String)
    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    pseudonymous_display_name: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    age_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    profile: Mapped["Profile"] = relationship(
        back_populates="user",
        uselist=False,
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        index=True,
    )
    course: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    interests: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    activity_types: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    region: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    language: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="profile")


class CheckIn(Base):
    __tablename__ = "checkins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    feelings: Mapped[list[str]] = mapped_column(ARRAY(String))
    stated_need: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    time_of_day: Mapped[str] = mapped_column(String)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class TinyAction(Base):
    __tablename__ = "tiny_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    category: Mapped[str] = mapped_column(
        String,
        index=True,
    )
    difficulty_level: Mapped[int] = mapped_column(Integer)
    ladder_parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tiny_actions.id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)


class ActionAttemptStatus(enum.StrEnum):
    SUGGESTED = "suggested"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    REDUCED = "reduced"


class ActionAttempt(Base):
    __tablename__ = "action_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    tiny_action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tiny_actions.id"),
        index=True,
    )
    status: Mapped[ActionAttemptStatus] = mapped_column(
        Enum(
            ActionAttemptStatus,
            name="action_attempt_status",
            values_callable=enum_values,
        )
    )
    related_checkin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("checkins.id"),
        nullable=True,
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ConsentType(enum.StrEnum):
    AI_CHAT = "ai_chat"
    ANONYMOUS_COMMUNITY = "anonymous_community"
    MATCHING_VISIBILITY = "matching_visibility"
    INSTITUTIONAL_DATA_SHARING = "institutional_data_sharing"
    ACTIVITY_ALERTS = "activity_alerts"


class ConsentRecord(Base):
    """
    Append-only per R&D doc Section 11.

    Never update a row here. To change consent state, insert a new row; the
    current state for a given user and consent type is the latest row.
    """

    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    consent_type: Mapped[ConsentType] = mapped_column(
        Enum(
            ConsentType,
            name="consent_type",
            values_callable=enum_values,
        )
    )
    granted: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class PrivacySettings(Base):
    """
    Per-feature visibility toggles, distinct from ConsentRecord.
    """

    __tablename__ = "privacy_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        index=True,
    )
    profile_visible_in_matching: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    display_name_visible_in_rooms: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class DataRequestType(enum.StrEnum):
    EXPORT = "export"
    DELETION = "deletion"


class DataRequestStatus(enum.StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    DENIED = "denied"


class DataRequest(Base):
    """
    Record-keeping for privacy export and deletion requests.
    """

    __tablename__ = "data_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    request_type: Mapped[DataRequestType] = mapped_column(
        Enum(
            DataRequestType,
            name="data_request_type",
            values_callable=enum_values,
        )
    )
    status: Mapped[DataRequestStatus] = mapped_column(
        Enum(
            DataRequestStatus,
            name="data_request_status",
            values_callable=enum_values,
        ),
        default=DataRequestStatus.PENDING,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    completed_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class TinyActionVoiceOutcome(enum.StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"
    REFUSED = "refused"


class TinyActionVoiceEvent(Base):
    """
    Metadata-only audit record for each physical Phase 6 provider call.
    """

    __tablename__ = "tiny_action_voice_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    tiny_action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tiny_actions.id"),
        index=True,
    )
    checkin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("checkins.id"),
        index=True,
    )
    provider: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    prompt_version: Mapped[str] = mapped_column(String)
    attempt_number: Mapped[int] = mapped_column(Integer)
    outcome: Mapped[TinyActionVoiceOutcome] = mapped_column(
        Enum(
            TinyActionVoiceOutcome,
            name="tiny_action_voice_outcome",
            values_callable=enum_values,
        )
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ProfessionalResource(Base):
    """
    A human-curated, versioned support-directory entry.
    """

    __tablename__ = "professional_resources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    resource_key: Mapped[str] = mapped_column(
        String,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer)
    region: Mapped[str] = mapped_column(
        String,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String,
        index=True,
    )
    title: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text)
    contact_label: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    contact_value: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    contact_uri: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    booking_steps: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
    )
    what_to_expect: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    opening_lines: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
    )
    last_verified_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class JournalEntry(Base):
    """
    Private Phase 8 reflections; plaintext is never stored.
    """

    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    encrypted_body: Mapped[str] = mapped_column(Text)
    encryption_version: Mapped[str] = mapped_column(
        String,
        default="fernet-v1",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class HelpSeekingAction(Base):
    """
    Explicit actions only; never infer help-seeking from a check-in.
    """

    __tablename__ = "help_seeking_actions"

    __table_args__ = (
        CheckConstraint(
            "action_type IN ('open_resource', 'call_resource')",
            name="ck_help_seeking_actions_explicit_action_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("professional_resources.id"),
        nullable=True,
    )
    action_type: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ActivityTopic(enum.StrEnum):
    STUDY = "study"
    CODING = "coding"
    READING = "reading"
    WRITING = "writing"
    QUIET_WORK = "quiet_work"


class ActivityStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    CLOSED = "closed"


class Activity(Base):
    """
    A virtual activity built from a fixed topic.
    """

    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    creator_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    topic: Mapped[ActivityTopic] = mapped_column(
        Enum(
            ActivityTopic,
            name="activity_topic",
            values_callable=enum_values,
        ),
        index=True,
    )
    status: Mapped[ActivityStatus] = mapped_column(
        Enum(
            ActivityStatus,
            name="activity_status",
            values_callable=enum_values,
        ),
        default=ActivityStatus.LIVE,
        index=True,
    )
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class PresenceRoom(Base):
    """
    One low-pressure Presence Mode room per virtual activity.
    """

    __tablename__ = "presence_rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activities.id"),
        unique=True,
        index=True,
    )
    is_open: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class PresenceFeedback(enum.StrEnum):
    LESS_ALONE = "less_alone"
    NEUTRAL = "neutral"
    NOT_FOR_ME = "not_for_me"


class ActivityParticipant(Base):
    """
    Private attendance metadata; never returned as a participant list.
    """

    __tablename__ = "activity_participants"

    __table_args__ = (
        CheckConstraint(
            "join_count >= 1",
            name="ck_activity_participants_join_count",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activities.id"),
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    join_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )
    first_joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    feedback: Mapped[PresenceFeedback | None] = mapped_column(
        Enum(
            PresenceFeedback,
            name="presence_feedback",
            values_callable=enum_values,
        ),
        nullable=True,
    )


class MeetupCategory(enum.StrEnum):
    CRICKET = "cricket"
    FOOTBALL = "football"
    STUDY_GROUP = "study_group"
    CODING = "coding"
    COFFEE_CHAT = "coffee_chat"
    WALK = "walk"
    GYM = "gym"


class MeetupStatus(enum.StrEnum):
    PUBLISHED = "published"
    HELD_FOR_REVIEW = "held_for_review"
    CANCELLED = "cancelled"


class RSVPStatus(enum.StrEnum):
    JOINING = "joining"
    MAYBE = "maybe"
    IGNORED = "ignored"


class ActivityMeetup(Base):
    __tablename__ = "activity_meetups"

    __table_args__ = (
        CheckConstraint(
            "max_participants BETWEEN 2 AND 100",
            name="ck_activity_meetups_capacity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    creator_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[MeetupCategory] = mapped_column(
        Enum(
            MeetupCategory,
            name="meetup_category",
            values_callable=enum_values,
        ),
        index=True,
    )
    venue_provider_id: Mapped[str] = mapped_column(
        String(160),
        index=True,
    )
    venue_name: Mapped[str] = mapped_column(String(160))
    venue_map_url: Mapped[str] = mapped_column(String(500))
    area_cell: Mapped[str] = mapped_column(
        String(32),
        index=True,
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    max_participants: Mapped[int] = mapped_column(Integer)
    status: Mapped[MeetupStatus] = mapped_column(
        Enum(
            MeetupStatus,
            name="meetup_status",
            values_callable=enum_values,
        ),
        default=MeetupStatus.PUBLISHED,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ActivityRSVP(Base):
    __tablename__ = "activity_rsvps"

    __table_args__ = (
        UniqueConstraint(
            "activity_meetup_id",
            "user_id",
            name="uq_activity_rsvp_user",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    activity_meetup_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity_meetups.id"),
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    status: Mapped[RSVPStatus] = mapped_column(
        Enum(
            RSVPStatus,
            name="rsvp_status",
            values_callable=enum_values,
        ),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ActivityAlertPreference(Base):
    __tablename__ = "activity_alert_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        index=True,
    )
    area_cell: Mapped[str] = mapped_column(
        String(32),
        index=True,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class TrustedContactRelationship(enum.StrEnum):
    FRIEND = "friend"
    PARENT = "parent"
    SIBLING = "sibling"
    TEACHER = "teacher"
    COUNSELOR = "counselor"
    MENTOR = "mentor"
    OTHER = "other"


class TrustedContactScenario(enum.StrEnum):
    FEELING_OVERWHELMED = "feeling_overwhelmed"
    NEED_TO_TALK = "need_to_talk"
    PRACTICAL_SUPPORT = "practical_support"
    URGENT_BUT_NOT_EMERGENCY = "urgent_but_not_emergency"


class TrustedContact(Base):
    """
    A student-owned contact with identifying/contact data encrypted.
    """

    __tablename__ = "trusted_contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    relationship: Mapped[TrustedContactRelationship] = mapped_column(
        Enum(
            TrustedContactRelationship,
            name="trusted_contact_relationship",
            values_callable=enum_values,
        )
    )
    allowed_scenarios: Mapped[list[str]] = mapped_column(
        ARRAY(String)
    )
    encrypted_payload: Mapped[str] = mapped_column(Text)
    encryption_version: Mapped[str] = mapped_column(
        String,
        default="fernet-multikey-v1",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )