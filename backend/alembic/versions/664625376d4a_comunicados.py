"""comunicados

Ofertas/comunicados que el socio publica y aparecen en el feed de la app.
Índice (estado, publicado_en) para el feed del cliente.

Revision ID: 664625376d4a
Revises: 7b3a9c1de204
Create Date: 2026-10-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '664625376d4a'
down_revision: Union[str, Sequence[str], None] = '7b3a9c1de204'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('comunicados',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(length=160), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('imagen_url', sa.String(length=500), nullable=False),
        sa.Column('imagen_public_id', sa.String(length=200), nullable=True),
        sa.Column('premio_id', sa.Integer(), nullable=True),
        sa.Column('estado', sa.Enum('borrador', 'publicado', 'archivado',
                  name='estadocomunicado', native_enum=False, length=20), nullable=False),
        sa.Column('publicado_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('vigencia_hasta', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'),
                  nullable=False),
        sa.ForeignKeyConstraint(['premio_id'], ['premios.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_comunicados_estado'), 'comunicados', ['estado'])
    op.create_index(op.f('ix_comunicados_tenant_id'), 'comunicados', ['tenant_id'])
    # Feed del cliente: publicados ordenados por fecha
    op.create_index('ix_comunicados_estado_fecha', 'comunicados',
                    ['estado', 'publicado_en'])


def downgrade() -> None:
    op.drop_index('ix_comunicados_estado_fecha', table_name='comunicados')
    op.drop_index(op.f('ix_comunicados_tenant_id'), table_name='comunicados')
    op.drop_index(op.f('ix_comunicados_estado'), table_name='comunicados')
    op.drop_table('comunicados')
