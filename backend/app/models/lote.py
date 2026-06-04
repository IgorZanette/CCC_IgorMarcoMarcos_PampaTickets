import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TipoLote(str, enum.Enum):
    INTEIRA = "INTEIRA"
    MEIA = "MEIA"
    PROMOCIONAL = "PROMOCIONAL"


class Lote(Base):
    __tablename__ = "lotes_ingresso"
    __table_args__ = (
        CheckConstraint(
            "quantidade_vendida >= 0", name="ck_lote_vendida_nao_negativa"
        ),
        CheckConstraint(
            "quantidade_vendida <= quantidade_total",
            name="ck_lote_vendida_ate_total",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    evento_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("eventos.id"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoLote] = mapped_column(Enum(TipoLote), nullable=False)
    preco: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantidade_total: Mapped[int] = mapped_column(Integer, nullable=False)
    quantidade_vendida: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_inicio_venda: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    data_fim_venda: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    evento: Mapped["Evento"] = relationship("Evento", lazy="raise")  # noqa: F821
