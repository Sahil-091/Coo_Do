"""
Table owned EXCLUSIVELY by safety-service. See R&D doc Section 19
("safety_events... most access-restricted table in the schema") and
Section 11 (Privacy Architecture).

Access control: see /backend/db/grants.sql. Only the safety_service
Postgres role and a separate, narrower human-reviewer role may touch
this table. core_api's role has NO grants here at all.
"""
import enum
import uuid

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class SafetyFlagLevel(enum.StrEnum):
    ELEVATED = "elevated"
    CRISIS = "crisis"


class SafetySource(enum.StrEnum):
    CHECKIN_FREETEXT = "checkin_freetext"
    AI_NAVIGATOR = "ai_navigator"
    COMMUNITY_POST = "community_post"
    JOURNAL = "journal"


class EscalationStatus(enum.StrEnum):
    RESOURCE_SHOWN = "resource_shown"
    HUMAN_REVIEW_PENDING = "human_review_pending"
    HUMAN_REVIEWED = "human_reviewed"
    RESOLVED = "resolved"


class SafetyEvent(Base):
    __tablename__ = "safety_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Intentionally not a hard FK to users.id — safety-service's Postgres
    # role has no grants on the users table (see grants.sql), so this is
    # stored as an opaque reference, not a real relational join.
    user_ref: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    flag_level: Mapped[SafetyFlagLevel] = mapped_column(
        Enum(SafetyFlagLevel, name="safety_flag_level")
    )
    source: Mapped[SafetySource] = mapped_column(Enum(SafetySource, name="safety_source"))
    # Which scripted response template was shown — an id, not free text.
    response_template_id: Mapped[str] = mapped_column(String)
    # R&D doc Section 11 explicitly permits longer retention for
    # crisis-flagged content specifically, for safety review purposes,
    # WITH disclosure to the user. This is the one place in the schema
    # raw flagged text is allowed to live — nowhere else should persist
    # raw sensitive text this long. Nullable because not every flagged
    # event needs the full text retained (policy decision, not a schema
    # one) — leave null unless a specific review workflow requires it.
    flagged_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalation_status: Mapped[EscalationStatus] = mapped_column(
        Enum(EscalationStatus, name="escalation_status"),
        default=EscalationStatus.RESOURCE_SHOWN,
    )
    reviewer_ref: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
