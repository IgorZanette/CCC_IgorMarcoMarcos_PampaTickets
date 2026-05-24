import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TipoDesconto(str, enum.Enum):
    PERCENTUAL = "PERCENTUAL"
    VALOR_FIXO = "VALOR_FIXO"


class Cupom(Base):
    __tablename__ = "cupons"
    __table_args__ = (
        UniqueConstraint("codigo", "evento_id", name="uq_cupom_codigo_evento"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    evento_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("eventos.id"), nullable=False
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    tipo_desconto: Mapped[TipoDesconto] = mapped_column(
        Enum(TipoDesconto), nullable=False
    )
    valor_desconto: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantidade_maxima: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantidade_usada: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valido_ate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
