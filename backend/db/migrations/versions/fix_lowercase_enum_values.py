"""add lowercase enum values used by SQLAlchemy models

Revision ID: fix_lowercase_enum_values
Revises: c13a5e7d9b20
"""

from typing import Sequence, Union

from alembic import op


revision: str = "fix_lowercase_enum_values"
down_revision: Union[str, Sequence[str], None] = "c13a5e7d9b20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL enum values are case-sensitive. The application stores the
    # lowercase values from the Python StrEnum definitions.
    with op.get_context().autocommit_block():
        op.execute(
            """
            ALTER TYPE action_attempt_status
            ADD VALUE IF NOT EXISTS 'suggested'
            """
        )
        op.execute(
            """
            ALTER TYPE action_attempt_status
            ADD VALUE IF NOT EXISTS 'completed'
            """
        )
        op.execute(
            """
            ALTER TYPE action_attempt_status
            ADD VALUE IF NOT EXISTS 'skipped'
            """
        )
        op.execute(
            """
            ALTER TYPE action_attempt_status
            ADD VALUE IF NOT EXISTS 'reduced'
            """
        )

        op.execute(
            """
            ALTER TYPE consent_type
            ADD VALUE IF NOT EXISTS 'ai_chat'
            """
        )
        op.execute(
            """
            ALTER TYPE consent_type
            ADD VALUE IF NOT EXISTS 'anonymous_community'
            """
        )
        op.execute(
            """
            ALTER TYPE consent_type
            ADD VALUE IF NOT EXISTS 'matching_visibility'
            """
        )
        op.execute(
            """
            ALTER TYPE consent_type
            ADD VALUE IF NOT EXISTS 'institutional_data_sharing'
            """
        )
        op.execute(
            """
            ALTER TYPE consent_type
            ADD VALUE IF NOT EXISTS 'activity_alerts'
            """
        )

        op.execute(
            """
            ALTER TYPE data_request_type
            ADD VALUE IF NOT EXISTS 'export'
            """
        )
        op.execute(
            """
            ALTER TYPE data_request_type
            ADD VALUE IF NOT EXISTS 'deletion'
            """
        )


def downgrade() -> None:
    # PostgreSQL does not safely support removing enum values.
    pass