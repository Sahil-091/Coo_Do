"""
Tables owned by core-api. See R&D doc Section 19 (Database Design).

Deliberately NOT included yet (see /docs/schema-plan.md for the full
deferred list and which phase adds each): interests as a normalized
table (folded into profiles.interests as a simple array for now, will
likely need real normalization once Phase 11 matching needs to query
against it), communities/rooms/messages/reports/moderation_events
(Phase 12), matches (Phase 11), activities/presence_rooms (Phase 9),
campus_locations (P2, not in current 14-phase plan), journals (Phase 8),
trusted_contacts (Phase 10), professional_resources (Phase 7).
"""
import enum
import uuid
from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
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
    # Simple array for now — see module docstring re: normalized interests
    # table, deferred until Phase 11 (matching) actually needs to query it.
    interests: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

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
