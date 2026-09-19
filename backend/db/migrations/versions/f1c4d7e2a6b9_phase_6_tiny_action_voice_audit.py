"""phase 6: structured check-in time and Tiny Action Voice audit records

Revision ID: f1c4d7e2a6b9
Revises: a59f34b2c1d0
Create Date: 2026-09-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f1c4d7e2a6b9"
down_revision: Union[str, Sequence[str], None] = "a59f34b2c1d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing Phase 3 rows predate this field. Give those rows a neutral
    # fixed tag during migration, then remove the default so future rows must
    # provide the client-derived check-in tag explicitly.
    op.add_column(
        "checkins",
        sa.Column("time_of_day", sa.String(), nullable=False, server_default="afternoon"),
    )
    op.alter_column("checkins", "time_of_day", server_default=None)

    # PostgreSQL named enums must be created separately before the table.
    # ``create_type=False`` prevents ``create_table`` from trying to create
    # the same type a second time in this transaction.
    voice_outcome = postgresql.ENUM(
        "ACCEPTED",
        "REJECTED",
        "UNAVAILABLE",
        "REFUSED",
        name="tiny_action_voice_outcome",
        create_type=False,
    )
    voice_outcome.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "tiny_action_voice_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("tiny_action_id", sa.UUID(), nullable=False),
        sa.Column("checkin_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("prompt_version", sa.String(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("outcome", voice_outcome, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["checkin_id"], ["checkins.id"]),
        sa.ForeignKeyConstraint(["tiny_action_id"], ["tiny_actions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tiny_action_voice_events_user_id", "tiny_action_voice_events", ["user_id"])
    op.create_index("ix_tiny_action_voice_events_tiny_action_id", "tiny_action_voice_events", ["tiny_action_id"])
    op.create_index("ix_tiny_action_voice_events_checkin_id", "tiny_action_voice_events", ["checkin_id"])


def downgrade() -> None:
    op.drop_index("ix_tiny_action_voice_events_checkin_id", table_name="tiny_action_voice_events")
    op.drop_index("ix_tiny_action_voice_events_tiny_action_id", table_name="tiny_action_voice_events")
    op.drop_index("ix_tiny_action_voice_events_user_id", table_name="tiny_action_voice_events")
    op.drop_table("tiny_action_voice_events")
    postgresql.ENUM(name="tiny_action_voice_outcome").drop(op.get_bind(), checkfirst=True)
    op.drop_column("checkins", "time_of_day")
