"""moneda_liquidaciones

Snapshot de la moneda del esquema de comisión en cada liquidación —
sin ella una liquidación generada con esquema en USD se mostraría como BOB.

Revision ID: 7b3a9c1de204
Revises: 9c4f2e71ab08
Create Date: 2026-02-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '7b3a9c1de204'
down_revision: Union[str, Sequence[str], None] = '9c4f2e71ab08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('liquidaciones',
                  sa.Column('moneda', sa.String(3), server_default='BOB', nullable=False))
    # Backfill: las liquidaciones existentes heredan la moneda de su esquema
    op.execute("""
        UPDATE liquidaciones SET moneda = (
            SELECT e.moneda FROM esquemas_comision e
            JOIN tenants t ON t.esquema_comision_id = e.id
            WHERE t.id = liquidaciones.tenant_id
        )
        WHERE EXISTS (
            SELECT 1 FROM esquemas_comision e
            JOIN tenants t ON t.esquema_comision_id = e.id
            WHERE t.id = liquidaciones.tenant_id
        )
    """)


def downgrade() -> None:
    op.drop_column('liquidaciones', 'moneda')
