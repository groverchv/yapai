"""totp_2fa

Revision ID: e08bad9f7dad
Revises: 8a33a1fe4f44
Create Date: 2026-10-17 11:00:16.462833

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e08bad9f7dad'
down_revision: Union[str, Sequence[str], None] = '8a33a1fe4f44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('usuarios', sa.Column('totp_secret', sa.String(length=64), nullable=True))
    op.add_column('usuarios', sa.Column('totp_habilitado', sa.Boolean(), server_default='0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('usuarios', 'totp_habilitado')
    op.drop_column('usuarios', 'totp_secret')
