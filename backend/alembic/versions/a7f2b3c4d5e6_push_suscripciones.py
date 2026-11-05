"""push_suscripciones

Revision ID: a7f2b3c4d5e6
Revises: f4a1b2c3d5e6
Create Date: 2026-11-05 14:25:00.909135

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7f2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'f4a1b2c3d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "push_suscripciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("endpoint", sa.String(500), nullable=False, unique=True),
        sa.Column("p256dh", sa.String(200), nullable=False),
        sa.Column("auth", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_index("ix_push_suscripciones_cliente_id", "push_suscripciones", ["cliente_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("push_suscripciones")
