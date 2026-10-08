from datetime import date, time, datetime
from typing import Optional, List
from sqlalchemy import Integer, String, Date, Time, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Orden(Base):
    __tablename__ = "ordenes"

    id_orden: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_cliente: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clientes.id_ab", ondelete="SET NULL"), nullable=True)
    estado_orden: Mapped[str] = mapped_column(String(50), nullable=False)
    f_recepcion: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    hora_recep: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    f_atencion: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    hora_inicio: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    hora_fin: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    obs_recepcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    obs_descargo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    usuario_ing: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fecha_ing: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    asignaciones: Mapped[List["AsignacionOrden"]] = relationship(
        "AsignacionOrden",
        back_populates="orden",
        cascade="all, delete-orphan"
    )


class AsignacionOrden(Base):
    __tablename__ = "asignacion_ordenes"

    id_asignacion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_personal: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("personal.id_personal", ondelete="SET NULL"), nullable=True)
    id_orden: Mapped[int] = mapped_column(Integer, ForeignKey("ordenes.id_orden", ondelete="CASCADE"), nullable=False)
    f_asignacion: Mapped[date] = mapped_column(Date, default=date.today)
    hora_i: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    hora_f: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    estado_asignacion: Mapped[str] = mapped_column(String(50), default="PENDIENTE")
    motivo_asignacion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    orden: Mapped["Orden"] = relationship("Orden", back_populates="asignaciones")
