import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StatusRecuperacao(str, enum.Enum):
    PENDENTE = "PENDENTE"
    VALIDADO = "VALIDADO"
    UTILIZADO = "UTILIZADO"
    EXPIRADO = "EXPIRADO"


class RecuperacaoSenha(Base):
    """Modelo para armazenar requisições de recuperação de senha."""

    __tablename__ = "recuperacao_senhas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(6), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[StatusRecuperacao] = mapped_column(
        Enum(StatusRecuperacao), default=StatusRecuperacao.PENDENTE, nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def esta_expirado(self) -> bool:
        """Verifica se o token de recuperação expirou."""
        return datetime.now(self.expira_em.tzinfo) > self.expira_em

    def esta_pendente(self) -> bool:
        """Verifica se está no status PENDENTE e não expirou."""
        return self.status == StatusRecuperacao.PENDENTE and not self.esta_expirado()
