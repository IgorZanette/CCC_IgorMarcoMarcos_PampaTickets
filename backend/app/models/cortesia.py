import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Cortesia(Base):
    __tablename__ = "cortesias"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    evento_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("eventos.id"), nullable=False
    )
    lote_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lotes_ingresso.id"), nullable=False
    )
    beneficiado_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False
    )
    emitida_por: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False
    )
    ingresso_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ingressos.id"), nullable=True
    )
    emitida_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    beneficiado: Mapped["Usuario"] = relationship(  # noqa: F821
        "Usuario", foreign_keys=[beneficiado_id], lazy="raise"
    )
    lote: Mapped["Lote"] = relationship("Lote", lazy="raise")  # noqa: F821
    ingresso: Mapped["Ingresso | None"] = relationship(  # noqa: F821
        "Ingresso", lazy="raise"
    )
