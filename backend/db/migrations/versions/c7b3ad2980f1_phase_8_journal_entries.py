"""phase 8: encrypted journal entries

Revision ID: c7b3ad2980f1
Revises: b623fc1489ab
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c7b3ad2980f1"
down_revision: Union[str, Sequence[str], None] = "b623fc1489ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table("journal_entries", sa.Column("id", sa.UUID(), nullable=False), sa.Column("user_id", sa.UUID(), nullable=False), sa.Column("encrypted_body", sa.Text(), nullable=False), sa.Column("encryption_version", sa.String(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_journal_entries_user_id", "journal_entries", ["user_id"])

def downgrade() -> None:
    op.drop_index("ix_journal_entries_user_id", table_name="journal_entries")
    op.drop_table("journal_entries")
