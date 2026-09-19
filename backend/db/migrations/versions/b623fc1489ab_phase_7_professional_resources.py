"""phase 7: professional help directory

Revision ID: b623fc1489ab
Revises: f1c4d7e2a6b9
Create Date: 2026-09-19
"""
from datetime import date
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b623fc1489ab"
down_revision: Union[str, Sequence[str], None] = "f1c4d7e2a6b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "professional_resources",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("resource_key", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("contact_label", sa.String(), nullable=True),
        sa.Column("contact_value", sa.String(), nullable=True),
        sa.Column("contact_uri", sa.String(), nullable=True),
        sa.Column("booking_steps", postgresql.ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("what_to_expect", sa.Text(), nullable=True),
        sa.Column("opening_lines", postgresql.ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("last_verified_at", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resource_key", "region", "version", name="uq_professional_resources_key_region_version"),
    )
    op.create_index("ix_professional_resources_resource_key", "professional_resources", ["resource_key"])
    op.create_index("ix_professional_resources_region", "professional_resources", ["region"])
    op.create_index("ix_professional_resources_category", "professional_resources", ["category"])
    op.create_index("ix_professional_resources_is_active", "professional_resources", ["is_active"])

    # Starter entries mirror the reviewed Phase 5 India resource config. A
    # local campus editor should add their own counselling service before a
    # deployment; the editor UI keeps that change out of source code.
    resources = sa.table(
        "professional_resources",
        sa.column("id", sa.UUID()), sa.column("resource_key", sa.String()), sa.column("version", sa.Integer()),
        sa.column("region", sa.String()), sa.column("category", sa.String()), sa.column("title", sa.String()),
        sa.column("summary", sa.Text()), sa.column("contact_label", sa.String()), sa.column("contact_value", sa.String()),
        sa.column("contact_uri", sa.String()), sa.column("booking_steps", postgresql.ARRAY(sa.String())),
        sa.column("what_to_expect", sa.Text()), sa.column("opening_lines", postgresql.ARRAY(sa.String())),
        sa.column("last_verified_at", sa.Date()), sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(resources, [
        {
            "id": "42000000-0000-4000-8000-000000000001", "resource_key": "tele-manas", "version": 1,
            "region": "India", "category": "Immediate support", "title": "Tele-MANAS",
            "summary": "A national mental-health support helpline. You can call to talk through what is happening and ask what support might fit.",
            "contact_label": "Call", "contact_value": "14416 or 1-800-891-4416", "contact_uri": "tel:14416",
            "booking_steps": ["Call 14416 when you are ready.", "You can start by saying you are a student looking for mental-health support.", "Ask what the next available support option is if you would like ongoing care."],
            "what_to_expect": "You do not need a polished explanation. Start with the part that feels easiest to say.",
            "opening_lines": ["I have been having a hard time lately and would like to talk to someone.", "I am a student and I am not sure what kind of support I need, but I would like help figuring it out."],
            "last_verified_at": date(2026, 9, 19), "is_active": True,
        },
        {
            "id": "42000000-0000-4000-8000-000000000002", "resource_key": "kiran-helpline", "version": 1,
            "region": "India", "category": "Immediate support", "title": "KIRAN helpline",
            "summary": "A national mental-health rehabilitation helpline listed in the project safety directory.",
            "contact_label": "Call", "contact_value": "1800-599-0019", "contact_uri": "tel:18005990019",
            "booking_steps": ["Call the helpline.", "Say you would like to understand available mental-health support.", "If you need counselling, ask how to find a local or ongoing option."],
            "what_to_expect": "It is okay if you only know that things have felt difficult. You can take the conversation one sentence at a time.",
            "opening_lines": ["I have been struggling and would like to know what support is available.", "I am nervous about asking for help, but I think I need to talk to someone."],
            "last_verified_at": date(2026, 9, 19), "is_active": True,
        },
    ])


def downgrade() -> None:
    op.drop_index("ix_professional_resources_is_active", table_name="professional_resources")
    op.drop_index("ix_professional_resources_category", table_name="professional_resources")
    op.drop_index("ix_professional_resources_region", table_name="professional_resources")
    op.drop_index("ix_professional_resources_resource_key", table_name="professional_resources")
    op.drop_table("professional_resources")
