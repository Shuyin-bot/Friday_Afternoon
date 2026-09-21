"""extend product table for machine catalog

Revision ID: 9d10280cdeab
Revises: bdf91b057fb9
Create Date: 2026-09-21 19:30:17.118588
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '9d10280cdeab'
down_revision: Union[str, None] = 'bdf91b057fb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite does not support ALTER COLUMN directly, so nullability changes
    # and the new columns are applied through batch_alter_table, which
    # rebuilds the table under the hood. The `category`/`status` Enum "type
    # change" that autogenerate detected is a false positive (SQLite stores
    # Enum columns as VARCHAR and re-detects this every time); it is
    # intentionally left out since no real change is needed there.
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name_de', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('description_de', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('specs_json', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('moq', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('price_min_eur', sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column('price_max_eur', sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column('lead_time_weeks', sa.String(length=50), nullable=True))
        batch_op.alter_column('box_style', existing_type=sa.VARCHAR(length=150), nullable=True)
        batch_op.alter_column('material', existing_type=sa.VARCHAR(length=200), nullable=True)
        batch_op.alter_column('dimensions', existing_type=sa.VARCHAR(length=100), nullable=True)
        batch_op.alter_column('unit_of_measure', existing_type=sa.VARCHAR(length=30), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column('unit_of_measure', existing_type=sa.VARCHAR(length=30), nullable=False)
        batch_op.alter_column('dimensions', existing_type=sa.VARCHAR(length=100), nullable=False)
        batch_op.alter_column('material', existing_type=sa.VARCHAR(length=200), nullable=False)
        batch_op.alter_column('box_style', existing_type=sa.VARCHAR(length=150), nullable=False)
        batch_op.drop_column('lead_time_weeks')
        batch_op.drop_column('price_max_eur')
        batch_op.drop_column('price_min_eur')
        batch_op.drop_column('moq')
        batch_op.drop_column('specs_json')
        batch_op.drop_column('description_de')
        batch_op.drop_column('name_de')
