"""foto_url en clientes

Revision ID: b8f1c2a9d3e4
Revises: 664625376d4a
Create Date: 2026-10-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b8f1c2a9d3e4'
down_revision: Union[str, Sequence[str], None] = '664625376d4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clientes', sa.Column('foto_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('clientes', 'foto_url')
