from app.db.session import Base
from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


class Plan(Base):
    """Plan SaaS del tenant. Límite 0 = ilimitado."""
    __tablename__ = "planes"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(80))
    descripcion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    precio_mensual: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    moneda: Mapped[str] = mapped_column(String(3), default="BOB")
    max_sucursales: Mapped[int] = mapped_column(Integer, default=0)
    max_pantallas: Mapped[int] = mapped_column(Integer, default=0)
    max_clientes: Mapped[int] = mapped_column(Integer, default=0)
    max_empleados: Mapped[int] = mapped_column(Integer, default=0)
    ruleta_habilitada: Mapped[bool] = mapped_column(Boolean, default=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
