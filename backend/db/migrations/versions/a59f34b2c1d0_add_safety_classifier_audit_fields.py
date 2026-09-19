"""add safety classifier audit fields

Revision ID: a59f34b2c1d0
Revises: 9b33b7bc1eac
Create Date: 2026-09-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a59f34b2c1d0"
down_revision: Union[str, Sequence[str], None] = "9b33b7bc1eac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "safety_events",
        sa.Column("classifier_model", sa.String(), nullable=False, server_default="legacy-unavailable"),
    )
    op.add_column(
        "safety_events",
        sa.Column("classifier_prompt_version", sa.String(), nullable=False, server_default="legacy"),
    )
    op.alter_column("safety_events", "classifier_model", server_default=None)
    op.alter_column("safety_events", "classifier_prompt_version", server_default=None)


def downgrade() -> None:
    op.drop_column("safety_events", "classifier_prompt_version")
    op.drop_column("safety_events", "classifier_model")
