"""Phase 12 anonymous-room and moderation tables owned by moderation-service."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class CommunityRoomTopic(enum.StrEnum):
    FEELING_LONELY = "feeling_lonely"
    EXAM_ANXIETY = "exam_anxiety"
    HOMESICK = "homesick"
    NEED_SOMEONE_TO_TALK_TO = "need_someone_to_talk_to"


class CommunityPostStatus(enum.StrEnum):
    VISIBLE = "visible"
    HELD_FOR_REVIEW = "held_for_review"
    REMOVED = "removed"


class ModerationReviewStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REMOVED = "removed"


class CommunityRoom(Base):
    __tablename__ = "community_rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic: Mapped[CommunityRoomTopic] = mapped_column(
        Enum(CommunityRoomTopic, name="community_room_topic"), index=True
    )
    # Opaque, non-FK references keep this service from gaining core user-table access.
    created_by_user_ref: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommunityGuidelinesAcceptance(Base):
    __tablename__ = "community_guidelines_acceptances"
    __table_args__ = (
        UniqueConstraint("user_ref", "guidelines_version", name="uq_community_guidelines_acceptance"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_ref: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    guidelines_version: Mapped[str] = mapped_column(String)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommunityPost(Base):
    __tablename__ = "community_posts"
    __table_args__ = (Index("ix_community_posts_room_created", "room_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community_rooms.id"), index=True)
    author_user_ref: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[CommunityPostStatus] = mapped_column(
        Enum(CommunityPostStatus, name="community_post_status"), default=CommunityPostStatus.VISIBLE, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommunityReportCategory(enum.StrEnum):
    HARASSMENT = "harassment"
    SEXUAL_CONTENT = "sexual_content"
    SPAM_OR_SCAM = "spam_or_scam"
    SELF_HARM_CONCERN = "self_harm_concern"
    OTHER = "other"


class CommunityReport(Base):
    __tablename__ = "community_reports"
    __table_args__ = (UniqueConstraint("post_id", "reporter_user_ref", name="uq_community_report_once"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community_posts.id"), index=True)
    reporter_user_ref: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    category: Mapped[CommunityReportCategory] = mapped_column(
        Enum(CommunityReportCategory, name="community_report_category"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModerationEvent(Base):
    __tablename__ = "moderation_events"
    __table_args__ = (UniqueConstraint("post_id", name="uq_moderation_event_post"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("community_posts.id"), index=True)
    reasons: Mapped[list[str]] = mapped_column(ARRAY(String))
    self_harm_level: Mapped[str] = mapped_column(String, default="none")
    review_status: Mapped[ModerationReviewStatus] = mapped_column(
        Enum(ModerationReviewStatus, name="moderation_review_status"), default=ModerationReviewStatus.PENDING, index=True
    )
    reviewer_ref: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
