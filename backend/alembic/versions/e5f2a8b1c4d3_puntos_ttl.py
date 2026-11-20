"""puntos_ttl_meses: expiración configurable de puntos por tenant

Revision ID: e5f2a8b1c4d3
Revises: d7e9f1a3b5c8
Create Date: 2025-01-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e5f2a8b1c4d3'
down_revision: Union[str, Sequence[str], None] = 'd7e9f1a3b5c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('tenants') as b:
        b.add_column(sa.Column('puntos_ttl_meses', sa.Integer(),
                               server_default='0', nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('tenants') as b:
        b.drop_column('puntos_ttl_meses')
