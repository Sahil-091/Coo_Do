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


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Phase 2: built-in email/password auth. `auth_subject` is reserved,
    # nullable, and unused for now — it's where an external provider's
    # (e.g. Clerk) subject id would go if one is added later, decoupled
    # from `email` so a user's login email can change without disturbing
    # whatever external identity reference points at them.
    auth_subject: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    pseudonymous_display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    age_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True
    )
    course: Mapped[str | None] = mapped_column(String, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Matching uses these bounded, student-selected signals.  They remain
    # core-api-owned; matching-service receives them only through its internal
    # API contract, never through a cross-service database join.
    interests: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    activity_types: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    # These are deliberately private matching weights, not browseable facets.
    # They are never returned to a browser as "students from X" / "students
    # who speak Y" filters.
    region: Mapped[str | None] = mapped_column(String, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship(back_populates="profile")


class CheckIn(Base):
    __tablename__ = "checkins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    # Quick-select chips only, per R&D doc Section 5.1 — no free text
    # required, no score computed from this.
    feelings: Mapped[list[str]] = mapped_column(ARRAY(String))
    stated_need: Mapped[str | None] = mapped_column(String, nullable=True)
    # Stored with the check-in so Phase 6 can use the same structured tags
    # that the deterministic router used.  This is a fixed enum value from
    # the client, never free text or a server-time guess.
    time_of_day: Mapped[str] = mapped_column(String)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TinyAction(Base):
    __tablename__ = "tiny_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category: Mapped[str] = mapped_column(String, index=True)
    difficulty_level: Mapped[int] = mapped_column(Integer)
    # Self-referential: implements the difficulty ladder from Section 5.3
    # ("talk to someone" -> "go where people are" -> "step outside for 2 min").
    ladder_parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tiny_actions.id"), nullable=True
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
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    tiny_action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tiny_actions.id"), index=True
    )
    status: Mapped[ActionAttemptStatus] = mapped_column(
        Enum(ActionAttemptStatus, name="action_attempt_status")
    )
    related_checkin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkins.id"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConsentType(enum.StrEnum):
    AI_CHAT = "ai_chat"
    ANONYMOUS_COMMUNITY = "anonymous_community"
    MATCHING_VISIBILITY = "matching_visibility"
    INSTITUTIONAL_DATA_SHARING = "institutional_data_sharing"
    ACTIVITY_ALERTS = "activity_alerts"


class ConsentRecord(Base):
    """
    Append-only per R&D doc Section 11 — never UPDATE a row here. To
    change consent state, INSERT a new row; the current state for a
    given (user_id, consent_type) is whichever row has the latest
    created_at.
    """
    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    consent_type: Mapped[ConsentType] = mapped_column(Enum(ConsentType, name="consent_type"))
    granted: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PrivacySettings(Base):
    """
    Per-feature visibility toggles (distinct from ConsentRecord's
    consent-to-process semantics). One row per user, updated in place.
    """
    __tablename__ = "privacy_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True
    )
    profile_visible_in_matching: Mapped[bool] = mapped_column(Boolean, default=False)
    display_name_visible_in_rooms: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
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
    Phase 2 scope note: this is intentionally record-keeping only, not an
    automated pipeline. The Privacy Center UI lets a student FILE a
    request; fulfilling it is a manual/admin process for now (R&D doc
    Section 17: "the deletion can be a stubbed admin-notify flow for
    now... but the request UI and record-keeping must exist now").
    """
    __tablename__ = "data_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    request_type: Mapped[DataRequestType] = mapped_column(
        Enum(DataRequestType, name="data_request_type")
    )
    status: Mapped[DataRequestStatus] = mapped_column(
        Enum(DataRequestStatus, name="data_request_status"), default=DataRequestStatus.PENDING
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TinyActionVoiceOutcome(enum.StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"
    REFUSED = "refused"


class TinyActionVoiceEvent(Base):
    """Metadata-only audit record for each physical Phase 6 provider call.

    Raw check-in tags and generated prose are deliberately not duplicated
    here.  Existing action/check-in records are enough to investigate an
    issue, while provider/model/prompt metadata makes later model swaps
    comparable without widening the sensitive-data footprint.
    """

    __tablename__ = "tiny_action_voice_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    tiny_action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tiny_actions.id"), index=True
    )
    checkin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkins.id"), index=True
    )
    provider: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    prompt_version: Mapped[str] = mapped_column(String)
    attempt_number: Mapped[int] = mapped_column(Integer)
    outcome: Mapped[TinyActionVoiceOutcome] = mapped_column(
        Enum(TinyActionVoiceOutcome, name="tiny_action_voice_outcome")
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProfessionalResource(Base):
    """A human-curated, versioned support-directory entry (Phase 7).

    Resources are never generated or edited by a model. Editors create a
    replacement version instead of changing a published row in place, keeping
    an auditable history of the information a student could have seen.
    """

    __tablename__ = "professional_resources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resource_key: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[int] = mapped_column(Integer)
    region: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text)
    contact_label: Mapped[str | None] = mapped_column(String, nullable=True)
    contact_value: Mapped[str | None] = mapped_column(String, nullable=True)
    contact_uri: Mapped[str | None] = mapped_column(String, nullable=True)
    booking_steps: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    what_to_expect: Mapped[str | None] = mapped_column(Text, nullable=True)
    opening_lines: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    last_verified_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class JournalEntry(Base):
    """Private Phase 8 reflections; plaintext is never stored in this table."""
    __tablename__ = "journal_entries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    encrypted_body: Mapped[str] = mapped_column(Text)
    encryption_version: Mapped[str] = mapped_column(String, default="fernet-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class HelpSeekingAction(Base):
    """Explicit actions only; never infer help-seeking from a check-in."""
    __tablename__ = "help_seeking_actions"
    __table_args__ = (
        CheckConstraint(
            "action_type IN ('open_resource', 'call_resource')",
            name="ck_help_seeking_actions_explicit_action_type",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("professional_resources.id"), nullable=True)
    action_type: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Phase 9 is deliberately limited to virtual, topic-based rooms.  Neither
# model carries a venue, coordinates, IP address, or any other location field.
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
    """A virtual activity built from a fixed topic, never a physical meetup."""

    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    topic: Mapped[ActivityTopic] = mapped_column(Enum(ActivityTopic, name="activity_topic"), index=True)
    status: Mapped[ActivityStatus] = mapped_column(
        Enum(ActivityStatus, name="activity_status"), default=ActivityStatus.LIVE, index=True
    )
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PresenceRoom(Base):
    """One low-pressure Presence Mode room per virtual activity."""

    __tablename__ = "presence_rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("activities.id"), unique=True, index=True
    )
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PresenceFeedback(enum.StrEnum):
    LESS_ALONE = "less_alone"
    NEUTRAL = "neutral"
    NOT_FOR_ME = "not_for_me"


class ActivityParticipant(Base):
    """Private attendance metadata; it is never returned as a participant list."""

    __tablename__ = "activity_participants"
    __table_args__ = (
        # A student's row is updated on rejoin rather than creating a history
        # that could become a detailed behavioural timeline.
        CheckConstraint("join_count >= 1", name="ck_activity_participants_join_count"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("activities.id"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    join_count: Mapped[int] = mapped_column(Integer, default=1)
    first_joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback: Mapped[PresenceFeedback | None] = mapped_column(
        Enum(PresenceFeedback, name="presence_feedback"), nullable=True
    )


# Phase 13 is deliberately distinct from Phase 9's virtual activities. User
# areas are stored only as server-generated coarse cells; no coordinate column
# exists anywhere in this model layer.
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
    __table_args__ = (CheckConstraint("max_participants BETWEEN 2 AND 100", name="ck_activity_meetups_capacity"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[MeetupCategory] = mapped_column(Enum(MeetupCategory, name="meetup_category"), index=True)
    # Selected from a server-owned public-venue catalogue / places provider;
    # client-supplied names and addresses are never persisted.
    venue_provider_id: Mapped[str] = mapped_column(String(160), index=True)
    venue_name: Mapped[str] = mapped_column(String(160))
    venue_map_url: Mapped[str] = mapped_column(String(500))
    area_cell: Mapped[str] = mapped_column(String(32), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    max_participants: Mapped[int] = mapped_column(Integer)
    status: Mapped[MeetupStatus] = mapped_column(Enum(MeetupStatus, name="meetup_status"), default=MeetupStatus.PUBLISHED, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ActivityRSVP(Base):
    __tablename__ = "activity_rsvps"
    __table_args__ = (UniqueConstraint("activity_meetup_id", "user_id", name="uq_activity_rsvp_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_meetup_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("activity_meetups.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    status: Mapped[RSVPStatus] = mapped_column(Enum(RSVPStatus, name="rsvp_status"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ActivityAlertPreference(Base):
    __tablename__ = "activity_alert_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True)
    area_cell: Mapped[str] = mapped_column(String(32), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


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
    """A student-owned contact, with all identifying/contact data encrypted.

    There is intentionally no background-job field, notification preference,
    or automatic-escalation state: the app can only prepare an outreach after
    an explicit user action in the moment.
    """

    __tablename__ = "trusted_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    relationship: Mapped[TrustedContactRelationship] = mapped_column(
        Enum(TrustedContactRelationship, name="trusted_contact_relationship")
    )
    # Validated against TrustedContactScenario at the API boundary.  It is a
    # per-scenario permission list, never a blanket "contact this person" flag.
    allowed_scenarios: Mapped[list[str]] = mapped_column(ARRAY(String))
    encrypted_payload: Mapped[str] = mapped_column(Text)
    encryption_version: Mapped[str] = mapped_column(String, default="fernet-multikey-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
