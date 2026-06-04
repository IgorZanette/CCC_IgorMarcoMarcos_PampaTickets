import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MetodoPagamento(str, enum.Enum):
    PIX = "PIX"
    CARTAO_CREDITO = "CREDIT_CARD"
    BOLETO = "BOLETO"


class StatusPagamento(str, enum.Enum):
    AGUARDANDO = "AGUARDANDO"
    APROVADO = "APROVADO"
    CANCELADO = "CANCELADO"
    RECUSADO = "RECUSADO"
    ESTORNADO = "ESTORNADO"


class Pagamento(Base):
    __tablename__ = "pagamentos"
    __table_args__ = (
        UniqueConstraint("pedido_id", name="uq_pagamento_pedido"),
        UniqueConstraint("charge_id", name="uq_pagamento_charge"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pedido_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pedidos.id"), nullable=False
    )
    charge_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metodo: Mapped[MetodoPagamento] = mapped_column(
        Enum(MetodoPagamento), nullable=False
    )
    status: Mapped[StatusPagamento] = mapped_column(
        Enum(StatusPagamento), default=StatusPagamento.AGUARDANDO, nullable=False
    )
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    pago_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Reembolso(Base):
    __tablename__ = "reembolsos"
    __table_args__ = (
        UniqueConstraint("pagamento_id", name="uq_reembolso_pagamento"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pagamento_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pagamentos.id"), nullable=False
    )
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_reembolsado: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    processado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
