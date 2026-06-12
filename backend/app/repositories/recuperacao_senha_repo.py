"""Repositório para gerenciar recuperação de senhas."""

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recuperacao_senha import RecuperacaoSenha, StatusRecuperacao


async def create(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    codigo_hash: str,
    token: str,
    expira_em: datetime,
) -> RecuperacaoSenha:
    """Cria um novo registro de recuperação de senha (código já hasheado)."""
    recuperacao = RecuperacaoSenha(
        usuario_id=usuario_id,
        codigo_hash=codigo_hash,
        token=token,
        expira_em=expira_em,
        status=StatusRecuperacao.PENDENTE,
    )
    db.add(recuperacao)
    await db.flush()
    return recuperacao


async def incrementar_tentativas(
    db: AsyncSession, recuperacao_id: uuid.UUID
) -> int:
    """Incrementa o contador atomicamente (UPDATE ... tentativas + 1) e
    devolve o novo valor — sem janela de race entre leitura e escrita."""
    result = await db.execute(
        update(RecuperacaoSenha)
        .where(RecuperacaoSenha.id == recuperacao_id)
        .values(tentativas=RecuperacaoSenha.tentativas + 1)
        .returning(RecuperacaoSenha.tentativas)
    )
    await db.flush()
    return result.scalar_one()


async def invalidar_ativas(db: AsyncSession, usuario_id: uuid.UUID) -> None:
    """Expira as recuperações ativas do usuário — um código válido por vez."""
    result = await db.execute(
        select(RecuperacaoSenha)
        .where(RecuperacaoSenha.usuario_id == usuario_id)
        .where(
            RecuperacaoSenha.status.in_(
                [StatusRecuperacao.PENDENTE, StatusRecuperacao.VALIDADO]
            )
        )
    )
    for recuperacao in result.scalars():
        recuperacao.status = StatusRecuperacao.EXPIRADO
    await db.flush()


async def get_by_token(db: AsyncSession, token: str) -> RecuperacaoSenha | None:
    """Obtém um registro de recuperação pelo token."""
    result = await db.execute(
        select(RecuperacaoSenha).where(RecuperacaoSenha.token == token)
    )
    return result.scalars().first()


async def get_by_usuario_id(db: AsyncSession, usuario_id: uuid.UUID) -> RecuperacaoSenha | None:
    """Obtém o último registro de recuperação ativo para um usuário."""
    result = await db.execute(
        select(RecuperacaoSenha)
        .where(RecuperacaoSenha.usuario_id == usuario_id)
        .where(RecuperacaoSenha.status.in_([StatusRecuperacao.PENDENTE, StatusRecuperacao.VALIDADO]))
        .order_by(RecuperacaoSenha.criado_em.desc())
    )
    return result.scalars().first()


async def update_status(
    db: AsyncSession, recuperacao_id: uuid.UUID, novo_status: StatusRecuperacao
) -> None:
    """Atualiza o status de uma recuperação."""
    recuperacao = await db.get(RecuperacaoSenha, recuperacao_id)
    if recuperacao:
        recuperacao.status = novo_status
        await db.flush()
