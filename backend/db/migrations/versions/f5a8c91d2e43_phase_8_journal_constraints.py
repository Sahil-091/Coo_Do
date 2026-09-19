"""phase 8: constrain auditable help-seeking event types

Revision ID: f5a8c91d2e43
Revises: e04dcf8e7b52
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f5a8c91d2e43"
down_revision: Union[str, Sequence[str], None] = "e04dcf8e7b52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # These are intentional student interactions only.  Keeping the values
    # constrained prevents check-in tags or future inferred events from being
    # quietly mixed into the Phase 8 help-seeking indicator.
    op.create_check_constraint(
        "ck_help_seeking_actions_explicit_action_type",
        "help_seeking_actions",
        "action_type IN ('open_resource', 'call_resource')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_help_seeking_actions_explicit_action_type",
        "help_seeking_actions",
        type_="check",
    )
