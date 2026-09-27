"""add agent sessions table

Revision ID: d42a6c1f8e77
Revises: c17f3c4a2d91
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d42a6c1f8e77"
down_revision: Union[str, None] = "c17f3c4a2d91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("queued_job_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "WAITING_FOR_HUMAN",
                "READY_TO_RESUME",
                "COMPLETED",
                "FAILED",
                name="agentsessionstatus",
            ),
            nullable=False,
        ),
        sa.Column("current_step", sa.String(length=100), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("message_history", sa.JSON(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["queued_job_id"], ["queued_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("queued_job_id"),
    )
    op.create_index(
        op.f("ix_agent_sessions_queued_job_id"),
        "agent_sessions",
        ["queued_job_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_agent_sessions_queued_job_id"),
        table_name="agent_sessions",
    )
    op.drop_table("agent_sessions")
