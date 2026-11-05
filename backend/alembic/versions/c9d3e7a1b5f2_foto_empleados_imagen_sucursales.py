"""foto_url en usuarios + imagen_url en sucursales

Revision ID: c9d3e7a1b5f2
Revises: b8f1c2a9d3e4
Create Date: 2026-11-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c9d3e7a1b5f2'
down_revision: Union[str, Sequence[str], None] = 'b8f1c2a9d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('foto_url', sa.String(500), nullable=True))
    op.add_column('sucursales', sa.Column('imagen_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('sucursales', 'imagen_url')
    op.drop_column('usuarios', 'foto_url')
