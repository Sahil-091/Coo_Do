"""phase 13: privacy-safe local activity discovery

Revision ID: c13a5e7d9b20
Revises: 9e4b7d2a1f06
"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa

revision: str = "c13a5e7d9b20"
down_revision: Union[str, Sequence[str], None] = "9e4b7d2a1f06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

category = postgresql.ENUM(
    "cricket", "football", "study_group", "coding", "coffee_chat", "walk", "gym",
    name="meetup_category",
    create_type=False,
)
meetup_status = postgresql.ENUM(
    "published", "held_for_review", "cancelled",
    name="meetup_status",
    create_type=False,
)
rsvp_status = postgresql.ENUM(
    "joining", "maybe", "ignored",
    name="rsvp_status",
    create_type=False,
)

def upgrade() -> None:
    # ADD VALUE cannot be transactionally used by older Postgres releases;
    # alembic's autocommit block keeps this additive migration portable.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE consent_type ADD VALUE IF NOT EXISTS 'activity_alerts'")
    for enum_type in (category, meetup_status, rsvp_status):
        enum_type.create(op.get_bind(), checkfirst=True)
    op.create_table("activity_meetups", sa.Column("id", sa.UUID(), nullable=False), sa.Column("creator_user_id", sa.UUID(), nullable=False), sa.Column("title", sa.String(length=120), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("category", category, nullable=False), sa.Column("venue_provider_id", sa.String(length=160), nullable=False), sa.Column("venue_name", sa.String(length=160), nullable=False), sa.Column("venue_map_url", sa.String(length=500), nullable=False), sa.Column("area_cell", sa.String(length=32), nullable=False), sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False), sa.Column("max_participants", sa.Integer(), nullable=False), sa.Column("status", meetup_status, nullable=False, server_default="published"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.CheckConstraint("max_participants BETWEEN 2 AND 100", name="ck_activity_meetups_capacity"), sa.ForeignKeyConstraint(["creator_user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"))
    for column in ("creator_user_id", "category", "venue_provider_id", "area_cell", "starts_at", "status"):
        op.create_index(f"ix_activity_meetups_{column}", "activity_meetups", [column])
    op.create_table("activity_rsvps", sa.Column("id", sa.UUID(), nullable=False), sa.Column("activity_meetup_id", sa.UUID(), nullable=False), sa.Column("user_id", sa.UUID(), nullable=False), sa.Column("status", rsvp_status, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.ForeignKeyConstraint(["activity_meetup_id"], ["activity_meetups.id"]), sa.ForeignKeyConstraint(["user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("activity_meetup_id", "user_id", name="uq_activity_rsvp_user"))
    for column in ("activity_meetup_id", "user_id", "status"):
        op.create_index(f"ix_activity_rsvps_{column}", "activity_rsvps", [column])
    op.create_table("activity_alert_preferences", sa.Column("id", sa.UUID(), nullable=False), sa.Column("user_id", sa.UUID(), nullable=False), sa.Column("area_cell", sa.String(length=32), nullable=False), sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.ForeignKeyConstraint(["user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("user_id"))
    op.create_index("ix_activity_alert_preferences_user_id", "activity_alert_preferences", ["user_id"])
    op.create_index("ix_activity_alert_preferences_area_cell", "activity_alert_preferences", ["area_cell"])


def downgrade() -> None:
    op.drop_index("ix_activity_alert_preferences_area_cell", table_name="activity_alert_preferences")
    op.drop_index("ix_activity_alert_preferences_user_id", table_name="activity_alert_preferences")
    op.drop_table("activity_alert_preferences")
    for column in ("status", "user_id", "activity_meetup_id"):
        op.drop_index(f"ix_activity_rsvps_{column}", table_name="activity_rsvps")
    op.drop_table("activity_rsvps")
    for column in ("status", "starts_at", "area_cell", "venue_provider_id", "category", "creator_user_id"):
        op.drop_index(f"ix_activity_meetups_{column}", table_name="activity_meetups")
    op.drop_table("activity_meetups")
    for enum_type in (rsvp_status, meetup_status, category):
        enum_type.drop(op.get_bind(), checkfirst=True)
    # consent_type values are intentionally never removed: records may exist.
