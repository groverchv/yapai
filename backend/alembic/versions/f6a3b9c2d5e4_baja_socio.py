"""baja_solicitada_en: offboarding del socio con período de retención

Revision ID: f6a3b9c2d5e4
Revises: e5f2a8b1c4d3
Create Date: 2025-01-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f6a3b9c2d5e4'
down_revision: Union[str, Sequence[str], None] = 'e5f2a8b1c4d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('tenants') as b:
        b.add_column(sa.Column('baja_solicitada_en', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('tenants') as b:
        b.drop_column('baja_solicitada_en')
