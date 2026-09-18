"""create email and queue tables

Revision ID: 0001
Revises:
Create Date: 2026-09-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "retrieved_email",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email_id", sa.Integer(), nullable=False),
        sa.Column("from_email", sa.String(length=320), nullable=False),
        sa.Column("subject", sa.String(length=998), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email_id"),
    )
    op.create_table(
        "queued_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "IN_PROGRESS", "COMPLETED", name="jobstatus"), nullable=False),
        sa.Column("email_id", sa.Integer(), nullable=False),
        sa.Column("meta_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["email_id"], ["retrieved_email.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_queued_jobs_email_id", "queued_jobs", ["email_id"])


def downgrade() -> None:
    op.drop_index("ix_queued_jobs_email_id", table_name="queued_jobs")
    op.drop_table("queued_jobs")
    op.drop_table("retrieved_email")
