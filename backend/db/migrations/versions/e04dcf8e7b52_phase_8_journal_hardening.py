"""phase 8: explicit help-seeking events

Revision ID: e04dcf8e7b52
Revises: c7b3ad2980f1
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "e04dcf8e7b52"
down_revision: Union[str, Sequence[str], None] = "c7b3ad2980f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table("help_seeking_actions", sa.Column("id", sa.UUID(), nullable=False), sa.Column("user_id", sa.UUID(), nullable=False), sa.Column("resource_id", sa.UUID(), nullable=True), sa.Column("action_type", sa.String(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["resource_id"], ["professional_resources.id"]), sa.ForeignKeyConstraint(["user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_help_seeking_actions_user_id", "help_seeking_actions", ["user_id"])

def downgrade() -> None:
    op.drop_index("ix_help_seeking_actions_user_id", table_name="help_seeking_actions")
    op.drop_table("help_seeking_actions")
