"""phase 10: encrypted trusted contacts

Revision ID: 42d7b5e9c3f1
Revises: 1d8a67f4c9e2
"""

from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


revision: str = "42d7b5e9c3f1"
down_revision: Union[str, Sequence[str], None] = "1d8a67f4c9e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


relationship = postgresql.ENUM(
    "friend", "parent", "sibling", "teacher", "counselor", "mentor", "other",
    name="trusted_contact_relationship",
    create_type=False,
)

def upgrade() -> None:
    relationship.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "trusted_contacts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("relationship", relationship, nullable=False),
        sa.Column("allowed_scenarios", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("encrypted_payload", sa.Text(), nullable=False),
        sa.Column("encryption_version", sa.String(), nullable=False, server_default="fernet-multikey-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trusted_contacts_user_id", "trusted_contacts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_trusted_contacts_user_id", table_name="trusted_contacts")
    op.drop_table("trusted_contacts")
    relationship.drop(op.get_bind(), checkfirst=True)
