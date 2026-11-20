"""comprobante de pago manual en facturas_plan

Revision ID: g7b4c1d3e6f5
Revises: f6a3b9c2d5e4
Create Date: 2025-01-04 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'g7b4c1d3e6f5'
down_revision: Union[str, Sequence[str], None] = 'f6a3b9c2d5e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('facturas_plan') as b:
        b.add_column(sa.Column('comprobante_url', sa.String(500), nullable=True))
        b.add_column(sa.Column('comprobante_en', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('facturas_plan') as b:
        b.drop_column('comprobante_en')
        b.drop_column('comprobante_url')
