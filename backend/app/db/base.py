# Importa todos los modelos para registrar en Base.metadata (usado por Alembic y create_all)
from app.db.session import Base
from app.models import *  # noqa: F401,F403
