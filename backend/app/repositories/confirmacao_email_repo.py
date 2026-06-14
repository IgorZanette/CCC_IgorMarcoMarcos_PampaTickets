"""Repositório para gerenciar confirmações de email."""

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.confirmacao_email import ConfirmacaoEmail, StatusConfirmacaoEmail


async def create(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    codigo_hash: str,
    token: str,
    expira_em: datetime,
) -> ConfirmacaoEmail:
    confirmacao = ConfirmacaoEmail(
        usuario_id=usuario_id,
        codigo_hash=codigo_hash,
        token=token,
        expira_em=expira_em,
        status=StatusConfirmacaoEmail.PENDENTE,
    )
    db.add(confirmacao)
    await db.flush()
    return confirmacao


async def incrementar_tentativas(db: AsyncSession, confirmacao_id: uuid.UUID) -> int:
    """Incrementa o contador atomicamente e devolve o novo valor."""
    result = await db.execute(
        update(ConfirmacaoEmail)
        .where(ConfirmacaoEmail.id == confirmacao_id)
        .values(tentativas=ConfirmacaoEmail.tentativas + 1)
        .returning(ConfirmacaoEmail.tentativas)
    )
    await db.flush()
    return result.scalar_one()


async def invalidar_pendentes(db: AsyncSession, usuario_id: uuid.UUID) -> None:
    """Expira as confirmações pendentes do usuário — um código válido por vez."""
    result = await db.execute(
        select(ConfirmacaoEmail)
        .where(ConfirmacaoEmail.usuario_id == usuario_id)
        .where(ConfirmacaoEmail.status == StatusConfirmacaoEmail.PENDENTE)
    )
    for confirmacao in result.scalars():
        confirmacao.status = StatusConfirmacaoEmail.EXPIRADO
    await db.flush()


async def get_pendente_por_usuario(
    db: AsyncSession, usuario_id: uuid.UUID
) -> ConfirmacaoEmail | None:
    result = await db.execute(
        select(ConfirmacaoEmail)
        .where(ConfirmacaoEmail.usuario_id == usuario_id)
        .where(ConfirmacaoEmail.status == StatusConfirmacaoEmail.PENDENTE)
        .order_by(ConfirmacaoEmail.criado_em.desc())
    )
    return result.scalars().first()


async def update_status(
    db: AsyncSession, confirmacao_id: uuid.UUID, novo_status: StatusConfirmacaoEmail
) -> None:
    confirmacao = await db.get(ConfirmacaoEmail, confirmacao_id)
    if confirmacao:
        confirmacao.status = novo_status
        await db.flush()
