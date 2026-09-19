"""phase 12: anonymous situation rooms and moderation queue

Revision ID: 9e4b7d2a1f06
Revises: 3a7c2e1f9b04
"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa

revision: str = "9e4b7d2a1f06"
down_revision: Union[str, Sequence[str], None] = "3a7c2e1f9b04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

room_topic = postgresql.ENUM(
    "feeling_lonely", "exam_anxiety", "homesick", "need_someone_to_talk_to",
    name="community_room_topic",
    create_type=False,
)
post_status = postgresql.ENUM(
    "visible", "held_for_review", "removed",
    name="community_post_status",
    create_type=False,
)
report_category = postgresql.ENUM(
    "harassment", "sexual_content", "spam_or_scam", "self_harm_concern", "other",
    name="community_report_category",
    create_type=False,
)
review_status = postgresql.ENUM(
    "pending", "approved", "removed",
    name="moderation_review_status",
    create_type=False,
)

def upgrade() -> None:
    for enum_type in (room_topic, post_status, report_category, review_status):
        enum_type.create(op.get_bind(), checkfirst=True)
    op.create_table("community_rooms", sa.Column("id", sa.UUID(), nullable=False), sa.Column("topic", room_topic, nullable=False), sa.Column("created_by_user_ref", sa.UUID(), nullable=False), sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_community_rooms_topic", "community_rooms", ["topic"])
    op.create_index("ix_community_rooms_created_by_user_ref", "community_rooms", ["created_by_user_ref"])
    op.create_index("ix_community_rooms_is_open", "community_rooms", ["is_open"])
    op.create_table("community_guidelines_acceptances", sa.Column("id", sa.UUID(), nullable=False), sa.Column("user_ref", sa.UUID(), nullable=False), sa.Column("guidelines_version", sa.String(), nullable=False), sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("user_ref", "guidelines_version", name="uq_community_guidelines_acceptance"))
    op.create_index("ix_community_guidelines_acceptances_user_ref", "community_guidelines_acceptances", ["user_ref"])
    op.create_table("community_posts", sa.Column("id", sa.UUID(), nullable=False), sa.Column("room_id", sa.UUID(), nullable=False), sa.Column("author_user_ref", sa.UUID(), nullable=False), sa.Column("body", sa.Text(), nullable=False), sa.Column("status", post_status, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.ForeignKeyConstraint(["room_id"], ["community_rooms.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_community_posts_room_id", "community_posts", ["room_id"])
    op.create_index("ix_community_posts_author_user_ref", "community_posts", ["author_user_ref"])
    op.create_index("ix_community_posts_status", "community_posts", ["status"])
    op.create_index("ix_community_posts_room_created", "community_posts", ["room_id", "created_at"])
    op.create_table("community_reports", sa.Column("id", sa.UUID(), nullable=False), sa.Column("post_id", sa.UUID(), nullable=False), sa.Column("reporter_user_ref", sa.UUID(), nullable=False), sa.Column("category", report_category, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("post_id", "reporter_user_ref", name="uq_community_report_once"))
    op.create_index("ix_community_reports_post_id", "community_reports", ["post_id"])
    op.create_index("ix_community_reports_reporter_user_ref", "community_reports", ["reporter_user_ref"])
    op.create_index("ix_community_reports_category", "community_reports", ["category"])
    op.create_table("moderation_events", sa.Column("id", sa.UUID(), nullable=False), sa.Column("post_id", sa.UUID(), nullable=False), sa.Column("reasons", sa.ARRAY(sa.String()), nullable=False), sa.Column("self_harm_level", sa.String(), nullable=False, server_default="none"), sa.Column("review_status", review_status, nullable=False), sa.Column("reviewer_ref", sa.UUID(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True), sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("post_id", name="uq_moderation_event_post"))
    op.create_index("ix_moderation_events_review_status", "moderation_events", ["review_status"])


def downgrade() -> None:
    op.drop_index("ix_moderation_events_review_status", table_name="moderation_events")
    op.drop_table("moderation_events")
    op.drop_index("ix_community_reports_category", table_name="community_reports")
    op.drop_index("ix_community_reports_reporter_user_ref", table_name="community_reports")
    op.drop_index("ix_community_reports_post_id", table_name="community_reports")
    op.drop_table("community_reports")
    op.drop_index("ix_community_posts_room_created", table_name="community_posts")
    op.drop_index("ix_community_posts_status", table_name="community_posts")
    op.drop_index("ix_community_posts_author_user_ref", table_name="community_posts")
    op.drop_index("ix_community_posts_room_id", table_name="community_posts")
    op.drop_table("community_posts")
    op.drop_index("ix_community_guidelines_acceptances_user_ref", table_name="community_guidelines_acceptances")
    op.drop_table("community_guidelines_acceptances")
    op.drop_index("ix_community_rooms_is_open", table_name="community_rooms")
    op.drop_index("ix_community_rooms_created_by_user_ref", table_name="community_rooms")
    op.drop_index("ix_community_rooms_topic", table_name="community_rooms")
    op.drop_table("community_rooms")
    for enum_type in (review_status, report_category, post_status, room_topic):
        enum_type.drop(op.get_bind(), checkfirst=True)
