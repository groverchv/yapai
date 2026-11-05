"""Fixtures de tests: DB SQLite aislada + seed + TestClient.

DATABASE_URL se fija ANTES de importar la app para que settings/engine
apunten a la base de tests.
"""

import os
import tempfile

_tmpdir = tempfile.mkdtemp(prefix="yapai_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["JOBS_ENABLED"] = "false"  # los jobs corren en threads; determinismo en tests

import pytest  # noqa: E402
from app.core import ratelimit  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import run as seed_run  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

_TRIGGER_SQLITE = """
CREATE TRIGGER IF NOT EXISTS trg_{tabla}_inmutable_{op}
BEFORE {op} ON {tabla}
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'La tabla {tabla} es append-only: {op} prohibido');
END;
"""


@pytest.fixture(scope="session", autouse=True)
def db_seeded():
    Base.metadata.create_all(bind=engine)
    # Mismos triggers de inmutabilidad que crea la migración a1b2c3d4e5f6
    with engine.begin() as conn:
        for tabla in ("movimientos_puntos", "audit_log"):
            for op in ("UPDATE", "DELETE"):
                conn.execute(text(_TRIGGER_SQLITE.format(tabla=tabla, op=op)))
    seed_run()
    yield


@pytest.fixture(autouse=True)
def limpiar_rate_limits():
    ratelimit._ventanas.clear()
    yield
    ratelimit._ventanas.clear()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def login(client: TestClient, email: str, password: str) -> dict:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}


@pytest.fixture()
def admin_headers(client):
    return login(client, "admin@yapai.com", "Admin123!")


@pytest.fixture()
def owner_headers(client):
    return login(client, "owner@demo.com", "Owner123!")


@pytest.fixture()
def cajero_headers(client):
    return login(client, "cajero@demo.com", "Cajero123!")
