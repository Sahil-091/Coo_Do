"""phase 11: non-dating matching and safety exclusions

Revision ID: 3a7c2e1f9b04
Revises: 42d7b5e9c3f1
"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


revision: str = "3a7c2e1f9b04"
down_revision: Union[str, Sequence[str], None] = "42d7b5e9c3f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


match_status = postgresql.ENUM(
    "pending", "accepted", "declined", "blocked",
    name="match_status",
    create_type=False,
)
report_category = postgresql.ENUM(
    "dating_or_romantic_approach", "harassment", "safety_concern", "other",
    name="match_report_category",
    create_type=False,
)


def upgrade() -> None:
    op.add_column("profiles", sa.Column("activity_types", sa.ARRAY(sa.String()), nullable=True))
    op.add_column("profiles", sa.Column("region", sa.String(), nullable=True))
    op.add_column("profiles", sa.Column("language", sa.String(), nullable=True))

    match_status.create(op.get_bind(), checkfirst=True)
    report_category.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "matches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_one_id", sa.UUID(), nullable=False),
        sa.Column("user_two_id", sa.UUID(), nullable=False),
        sa.Column("requested_by_user_id", sa.UUID(), nullable=False),
        sa.Column("status", match_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_one_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_two_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_one_id", "user_two_id", name="uq_matches_pair"),
    )
    op.create_index("ix_matches_user_one_id", "matches", ["user_one_id"])
    op.create_index("ix_matches_user_two_id", "matches", ["user_two_id"])
    op.create_index("ix_matches_status", "matches", ["status"])

    op.create_table(
        "match_blocks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("blocker_user_id", sa.UUID(), nullable=False),
        sa.Column("blocked_user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["blocker_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["blocked_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("blocker_user_id", "blocked_user_id", name="uq_match_blocks_pair"),
    )
    op.create_index("ix_match_blocks_blocker_user_id", "match_blocks", ["blocker_user_id"])
    op.create_index("ix_match_blocks_blocked_user_id", "match_blocks", ["blocked_user_id"])

    op.create_table(
        "match_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("reporter_user_id", sa.UUID(), nullable=False),
        sa.Column("target_user_id", sa.UUID(), nullable=False),
        sa.Column("category", report_category, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["reporter_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_match_reports_reporter_user_id", "match_reports", ["reporter_user_id"])
    op.create_index("ix_match_reports_target_user_id", "match_reports", ["target_user_id"])
    op.create_index("ix_match_reports_category", "match_reports", ["category"])


def downgrade() -> None:
    op.drop_index("ix_match_reports_category", table_name="match_reports")
    op.drop_index("ix_match_reports_target_user_id", table_name="match_reports")
    op.drop_index("ix_match_reports_reporter_user_id", table_name="match_reports")
    op.drop_table("match_reports")
    op.drop_index("ix_match_blocks_blocked_user_id", table_name="match_blocks")
    op.drop_index("ix_match_blocks_blocker_user_id", table_name="match_blocks")
    op.drop_table("match_blocks")
    op.drop_index("ix_matches_status", table_name="matches")
    op.drop_index("ix_matches_user_two_id", table_name="matches")
    op.drop_index("ix_matches_user_one_id", table_name="matches")
    op.drop_table("matches")
    report_category.drop(op.get_bind(), checkfirst=True)
    match_status.drop(op.get_bind(), checkfirst=True)
    op.drop_column("profiles", "language")
    op.drop_column("profiles", "region")
    op.drop_column("profiles", "activity_types")
