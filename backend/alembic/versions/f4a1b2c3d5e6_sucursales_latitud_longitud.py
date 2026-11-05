"""sucursales latitud longitud

Revision ID: f4a1b2c3d5e6
Revises: c9d3e7a1b5f2
Create Date: 2026-11-05 00:15:26.139120

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f4a1b2c3d5e6'
down_revision: Union[str, Sequence[str], None] = 'c9d3e7a1b5f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("sucursales", sa.Column("latitud", sa.Float(), nullable=True))
    op.add_column("sucursales", sa.Column("longitud", sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("sucursales", "longitud")
    op.drop_column("sucursales", "latitud")
