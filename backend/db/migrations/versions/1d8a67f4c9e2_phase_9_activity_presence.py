"""phase 9: virtual activities and presence mode

Revision ID: 1d8a67f4c9e2
Revises: f5a8c91d2e43
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql
revision: str = "1d8a67f4c9e2"
down_revision: Union[str, Sequence[str], None] = "f5a8c91d2e43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


activity_topic = postgresql.ENUM(
    "study", "coding", "reading", "writing", "quiet_work",
    name="activity_topic",
    create_type=False,
)
activity_status = postgresql.ENUM(
    "scheduled", "live", "closed",
    name="activity_status",
    create_type=False,
)
presence_feedback = postgresql.ENUM(
    "less_alone", "neutral", "not_for_me",
    name="presence_feedback",
    create_type=False,
)

def upgrade() -> None:
    activity_topic.create(op.get_bind(), checkfirst=True)
    activity_status.create(op.get_bind(), checkfirst=True)
    presence_feedback.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "activities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("creator_user_id", sa.UUID(), nullable=False),
        sa.Column("topic", activity_topic, nullable=False),
        sa.Column("status", activity_status, nullable=False, server_default="live"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["creator_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activities_creator_user_id", "activities", ["creator_user_id"])
    op.create_index("ix_activities_topic", "activities", ["topic"])
    op.create_index("ix_activities_status", "activities", ["status"])
    op.create_index("ix_activities_starts_at", "activities", ["starts_at"])
    op.create_table(
        "presence_rooms",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("activity_id", sa.UUID(), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("activity_id"),
    )
    op.create_index("ix_presence_rooms_activity_id", "presence_rooms", ["activity_id"])
    op.create_index("ix_presence_rooms_is_open", "presence_rooms", ["is_open"])
    op.create_table(
        "activity_participants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("activity_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("join_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("feedback", presence_feedback, nullable=True),
        sa.CheckConstraint("join_count >= 1", name="ck_activity_participants_join_count"),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("activity_id", "user_id", name="uq_activity_participants_activity_user"),
    )
    op.create_index("ix_activity_participants_activity_id", "activity_participants", ["activity_id"])
    op.create_index("ix_activity_participants_user_id", "activity_participants", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_activity_participants_user_id", table_name="activity_participants")
    op.drop_index("ix_activity_participants_activity_id", table_name="activity_participants")
    op.drop_table("activity_participants")
    op.drop_index("ix_presence_rooms_is_open", table_name="presence_rooms")
    op.drop_index("ix_presence_rooms_activity_id", table_name="presence_rooms")
    op.drop_table("presence_rooms")
    op.drop_index("ix_activities_starts_at", table_name="activities")
    op.drop_index("ix_activities_status", table_name="activities")
    op.drop_index("ix_activities_topic", table_name="activities")
    op.drop_index("ix_activities_creator_user_id", table_name="activities")
    op.drop_table("activities")
    presence_feedback.drop(op.get_bind(), checkfirst=True)
    activity_status.drop(op.get_bind(), checkfirst=True)
    activity_topic.drop(op.get_bind(), checkfirst=True)
