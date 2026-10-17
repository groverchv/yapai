"""indices_hot_paths

Índices compuestos para las consultas reales del negocio:
- movimientos por (tenant, fecha): liquidaciones, métricas, segmento inactivos
- movimientos por (cliente, fecha): wallet ordenado
- clientes por tenant_registro: directorio/segmentación por comercio
- pases por (estado, expira): job de expiración horario
- premios por (tenant, estado): catálogo de canje
- campañas por (tenant, activa): multiplicador vigente en kiosco
- facturas por (estado, vence): job de mora/suspensión

Revision ID: 9c4f2e71ab08
Revises: e08bad9f7dad
Create Date: 2026-02-13

"""
from typing import Sequence, Union

from alembic import op

revision: str = '9c4f2e71ab08'
down_revision: Union[str, Sequence[str], None] = 'e08bad9f7dad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_mov_tenant_created', 'movimientos_puntos', ['tenant_id', 'created_at'])
    op.create_index('ix_mov_cliente_created', 'movimientos_puntos', ['cliente_id', 'created_at'])
    op.create_index('ix_clientes_tenant_registro', 'clientes', ['tenant_registro_id'])
    op.create_index('ix_pases_estado_expira', 'pases_digitales', ['estado', 'expira_en'])
    op.create_index('ix_premios_tenant_estado', 'premios', ['tenant_id', 'estado'])
    op.create_index('ix_campanas_tenant_activa', 'campanas', ['tenant_id', 'activa'])
    op.create_index('ix_facturas_estado_vence', 'facturas_plan', ['estado', 'vence_en'])


def downgrade() -> None:
    op.drop_index('ix_facturas_estado_vence', table_name='facturas_plan')
    op.drop_index('ix_campanas_tenant_activa', table_name='campanas')
    op.drop_index('ix_premios_tenant_estado', table_name='premios')
    op.drop_index('ix_pases_estado_expira', table_name='pases_digitales')
    op.drop_index('ix_clientes_tenant_registro', table_name='clientes')
    op.drop_index('ix_mov_cliente_created', table_name='movimientos_puntos')
    op.drop_index('ix_mov_tenant_created', table_name='movimientos_puntos')
