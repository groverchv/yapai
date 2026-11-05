"""triggers de inmutabilidad: ledger de puntos y audit_log son append-only (regla #1)

Revision ID: a1b2c3d4e5f6
Revises: d42c5e1fffd6
Create Date: 2026-10-17

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd42c5e1fffd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLAS = ("movimientos_puntos", "audit_log")

# PostgreSQL: función + trigger que aborta UPDATE/DELETE
_PG_FUNCION = """
CREATE OR REPLACE FUNCTION bloquear_mutacion_ledger() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'La tabla % es append-only: UPDATE/DELETE prohibidos', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;
"""

_PG_TRIGGER = """
CREATE TRIGGER trg_{tabla}_inmutable
BEFORE UPDATE OR DELETE ON {tabla}
FOR EACH ROW EXECUTE FUNCTION bloquear_mutacion_ledger();
"""

# SQLite: trigger equivalente con RAISE(ABORT)
_SQLITE_TRIGGER = """
CREATE TRIGGER trg_{tabla}_inmutable_{op}
BEFORE {op} ON {tabla}
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'La tabla {tabla} es append-only: {op} prohibido');
END;
"""


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(_PG_FUNCION)
        for tabla in TABLAS:
            op.execute(_PG_TRIGGER.format(tabla=tabla))
    else:
        # SQLite y otros: un trigger por operación
        for tabla in TABLAS:
            for operacion in ("UPDATE", "DELETE"):
                op.execute(_SQLITE_TRIGGER.format(tabla=tabla, op=operacion))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for tabla in TABLAS:
            op.execute(f"DROP TRIGGER IF EXISTS trg_{tabla}_inmutable ON {tabla}")
        op.execute("DROP FUNCTION IF EXISTS bloquear_mutacion_ledger")
    else:
        for tabla in TABLAS:
            for operacion in ("UPDATE", "DELETE"):
                op.execute(f"DROP TRIGGER IF EXISTS trg_{tabla}_inmutable_{operacion}")
