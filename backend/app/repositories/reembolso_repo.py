import uuid
from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pagamento import Pagamento, Reembolso


async def create(
    db: AsyncSession,
    *,
    pagamento_id: uuid.UUID,
    valor: float,
    motivo: str | None,
) -> Reembolso:
    reembolso = Reembolso(
        pagamento_id=pagamento_id,
        valor_reembolsado=valor,
        motivo=motivo,
    )
    db.add(reembolso)
    await db.commit()
    await db.refresh(reembolso)
    return reembolso


async def get_by_pagamento_id(
    db: AsyncSession, pagamento_id: uuid.UUID
) -> Reembolso | None:
    stmt = select(Reembolso).where(Reembolso.pagamento_id == pagamento_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def pedido_ids_com_reembolso(
    db: AsyncSession, pedido_ids: Iterable[uuid.UUID]
) -> set[uuid.UUID]:
    """
    Dentre os pedidos informados, retorna os que já têm reembolso solicitado
    (Reembolso → Pagamento → Pedido), em uma única query. Usado para a tela
    "Meus ingressos" exibir o estado antes do webhook confirmar o estorno.
    """
    ids = list(pedido_ids)
    if not ids:
        return set()
    stmt = (
        select(Pagamento.pedido_id)
        .join(Reembolso, Reembolso.pagamento_id == Pagamento.id)
        .where(Pagamento.pedido_id.in_(ids))
    )
    result = await db.execute(stmt)
    return set(result.scalars().all())


async def marcar_processado(db: AsyncSession, reembolso: Reembolso) -> Reembolso:
    reembolso.processado_em = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(reembolso)
    return reembolso
