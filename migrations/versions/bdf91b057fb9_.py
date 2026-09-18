"""empty message

Revision ID: bdf91b057fb9
Revises: 92fff5075809
Create Date: 2026-09-14 16:01:13.743781
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = 'bdf91b057fb9'
down_revision: Union[str, None] = '92fff5075809'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
