"""stripe webhook: eventos_stripe + tenants.stripe_customer_id

Revision ID: c3a5d8e2f1b9
Revises: b8e1f4a2c9d7
Create Date: 2025-01-01 00:00:00.000000

- eventos_stripe: dedupe/idempotencia de eventos del webhook (UNIQUE event_id)
- tenants.stripe_customer_id: mapeo Stripe customer → tenant para facturación
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c3a5d8e2f1b9'
down_revision: Union[str, Sequence[str], None] = 'b8e1f4a2c9d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'eventos_stripe',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.String(80), nullable=False),
        sa.Column('tipo', sa.String(60), nullable=False),
        sa.Column('procesado_en', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('event_id', name='uq_eventos_stripe_event_id'),
    )
    op.create_index('ix_eventos_stripe_event_id', 'eventos_stripe', ['event_id'])
    op.add_column('tenants', sa.Column('stripe_customer_id', sa.String(80), nullable=True))
    op.create_index('ix_tenants_stripe_customer_id', 'tenants', ['stripe_customer_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_tenants_stripe_customer_id', table_name='tenants')
    op.drop_column('tenants', 'stripe_customer_id')
    op.drop_index('ix_eventos_stripe_event_id', table_name='eventos_stripe')
    op.drop_table('eventos_stripe')
