"""otp pre-registro por teléfono + verificación de email + aviso trial

Revision ID: d7e9f1a3b5c8
Revises: c3a5d8e2f1b9
Create Date: 2025-01-01 00:00:00.000000

- otp_codes: cliente_id nullable + columna telefono (OTP antes de que exista
  el cliente — verificación del número al registrarse en la app)
- usuarios.email_verificado_en: flag de email confirmado (signup socio)
- tenants.trial_avisado_en: marca para no reenviar el aviso de fin de trial
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd7e9f1a3b5c8'
down_revision: Union[str, Sequence[str], None] = 'c3a5d8e2f1b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('otp_codes') as b:
        b.alter_column('cliente_id', existing_type=sa.Integer(), nullable=True)
        b.add_column(sa.Column('telefono', sa.String(50), nullable=True))
        b.create_index('ix_otp_codes_telefono', ['telefono'])
    with op.batch_alter_table('usuarios') as b:
        b.add_column(sa.Column('email_verificado_en', sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table('tenants') as b:
        b.add_column(sa.Column('trial_avisado_en', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('tenants') as b:
        b.drop_column('trial_avisado_en')
    with op.batch_alter_table('usuarios') as b:
        b.drop_column('email_verificado_en')
    with op.batch_alter_table('otp_codes') as b:
        b.drop_index('ix_otp_codes_telefono')
        b.drop_column('telefono')
        b.alter_column('cliente_id', existing_type=sa.Integer(), nullable=False)
