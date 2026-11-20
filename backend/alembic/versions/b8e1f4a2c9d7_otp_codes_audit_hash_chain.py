"""otp_codes + audit_log hash chain

- Tabla otp_codes: segundo factor del login de clientes (teléfono+CI+código).
- audit_log: prev_hash/registro_hash para cadena de integridad (detección de
  manipulación directa en DB). Filas existentes quedan con NULL = pre-cadena.

Revision ID: b8e1f4a2c9d7
Revises: a7f2b3c4d5e6
Create Date: 2026-11-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b8e1f4a2c9d7'
down_revision: Union[str, Sequence[str], None] = 'a7f2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "otp_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("codigo_hash", sa.String(64), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("usado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_otp_codes_cliente_id", "otp_codes", ["cliente_id"])
    op.create_index("ix_otp_codes_codigo_hash", "otp_codes", ["codigo_hash"])

    op.add_column("audit_log", sa.Column("prev_hash", sa.String(64), nullable=True))
    op.add_column("audit_log", sa.Column("registro_hash", sa.String(64), nullable=True))
    op.create_index("ix_audit_log_registro_hash", "audit_log", ["registro_hash"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_registro_hash", "audit_log")
    op.drop_column("audit_log", "registro_hash")
    op.drop_column("audit_log", "prev_hash")
    op.drop_index("ix_otp_codes_codigo_hash", "otp_codes")
    op.drop_index("ix_otp_codes_cliente_id", "otp_codes")
    op.drop_table("otp_codes")
