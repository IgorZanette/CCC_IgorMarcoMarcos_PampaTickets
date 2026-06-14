import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StatusConfirmacaoEmail(str, enum.Enum):
    PENDENTE = "PENDENTE"
    UTILIZADO = "UTILIZADO"
    EXPIRADO = "EXPIRADO"


class ConfirmacaoEmail(Base):
    __tablename__ = "confirmacoes_email"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    # HMAC-SHA256 do código de 6 dígitos — nunca o código em claro.
    codigo_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    tentativas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[StatusConfirmacaoEmail] = mapped_column(
        Enum(StatusConfirmacaoEmail), default=StatusConfirmacaoEmail.PENDENTE, nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def esta_expirado(self) -> bool:
        return datetime.now(self.expira_em.tzinfo) > self.expira_em

    def esta_pendente(self) -> bool:
        return self.status == StatusConfirmacaoEmail.PENDENTE and not self.esta_expirado()
