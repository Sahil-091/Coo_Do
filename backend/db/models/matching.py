"""Phase 11 tables owned exclusively by matching-service.

The service never joins these tables to core-api-owned profile data.  It asks
core-api for an opt-in candidate pool, then applies these safety exclusions in
its own SQL query before it scores or returns anyone.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class MatchStatus(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    BLOCKED = "blocked"


class Match(Base):
    """A pair is stored once in canonical user-id order, never as two rows."""

    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("user_one_id", "user_two_id", name="uq_matches_pair"),
        Index("ix_matches_user_one_id", "user_one_id"),
        Index("ix_matches_user_two_id", "user_two_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_one_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    user_two_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, name="match_status"), default=MatchStatus.PENDING, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MatchBlock(Base):
    """A bilateral exclusion: either party will disappear from matching."""

    __tablename__ = "match_blocks"
    __table_args__ = (
        UniqueConstraint("blocker_user_id", "blocked_user_id", name="uq_match_blocks_pair"),
        Index("ix_match_blocks_blocker_user_id", "blocker_user_id"),
        Index("ix_match_blocks_blocked_user_id", "blocked_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blocker_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    blocked_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MatchReportCategory(enum.StrEnum):
    DATING_OR_ROMANTIC_APPROACH = "dating_or_romantic_approach"
    HARASSMENT = "harassment"
    SAFETY_CONCERN = "safety_concern"
    OTHER = "other"


class MatchReport(Base):
    """Minimal Phase 11 report history used immediately as an exclusion signal."""

    __tablename__ = "match_reports"
    __table_args__ = (
        Index("ix_match_reports_reporter_user_id", "reporter_user_id"),
        Index("ix_match_reports_target_user_id", "target_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    target_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    category: Mapped[MatchReportCategory] = mapped_column(
        Enum(MatchReportCategory, name="match_report_category"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
