"""Verifica la integridad de la cadena audit_log (hash-chain).

Uso:  python scripts/verify_audit_chain.py
Exit 0 = íntegra · 1 = manipulación detectada (registro editado/borrado en DB).

Registros con registro_hash NULL (anteriores a la migración) se omiten.
Un fork (dos registros con el mismo prev_hash) se reporta como anomalía.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal  # noqa: E402
from app.models import AuditLog  # noqa: E402
from app.services.audit import _hash_registro  # noqa: E402
from sqlalchemy import select  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        filas = db.scalars(
            select(AuditLog).where(AuditLog.registro_hash.is_not(None)).order_by(AuditLog.id)
        ).all()
        vistos: set[str] = set()
        prev_esperado: str | None = None
        errores = 0
        for f in filas:
            if f.prev_hash in vistos:
                print(f"!! FORK en id={f.id}: prev_hash duplicado {f.prev_hash[:16]}…")
                errores += 1
            esperado = _hash_registro(f.prev_hash, f.actor_id, f.accion, f.entidad, f.entidad_id, f.detalle)
            if esperado != f.registro_hash:
                print(f"!! REGISTRO ALTERADO id={f.id} accion={f.accion}")
                errores += 1
            if prev_esperado is not None and f.prev_hash != prev_esperado:
                print(f"!! CADENA ROTA antes de id={f.id} (fila intermedia borrada o reordenada)")
                errores += 1
            vistos.add(f.prev_hash)
            prev_esperado = f.registro_hash
        total = len(filas)
        if errores:
            print(f"\n{errores} anomalía(s) en {total} registros verificados")
            return 1
        print(f"Cadena íntegra: {total} registros verificados")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
