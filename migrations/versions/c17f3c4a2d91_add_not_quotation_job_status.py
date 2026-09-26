"""separate non-quotation emails from completed quotations

Revision ID: c17f3c4a2d91
Revises: 983c9bf690a4
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c17f3c4a2d91"
down_revision: Union[str, None] = "983c9bf690a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite stores this enum as text. Existing COMPLETED jobs were created
    # by the classifier for emails that were not quotation requests.
    op.execute(
        "UPDATE queued_jobs SET status = 'NOT_QUOTATION' "
        "WHERE status = 'COMPLETED'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE queued_jobs SET status = 'COMPLETED' "
        "WHERE status = 'NOT_QUOTATION'"
    )
