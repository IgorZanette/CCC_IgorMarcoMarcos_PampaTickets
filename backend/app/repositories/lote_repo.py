import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lote import Lote, TipoLote


async def get_by_id(db: AsyncSession, lote_id: uuid.UUID) -> Lote | None:
    result = await db.execute(select(Lote).where(Lote.id == lote_id))
    return result.scalar_one_or_none()


async def get_by_id_for_update(db: AsyncSession, lote_id: uuid.UUID) -> Lote | None:
    """Igual a get_by_id, mas com lock de linha (SELECT ... FOR UPDATE).

    Usado na criação de pedido para serializar a checagem+incremento de estoque
    e evitar oversell sob concorrência. (No SQLite o lock é no-op.)
    """
    result = await db.execute(
        select(Lote).where(Lote.id == lote_id).with_for_update()
    )
    return result.scalar_one_or_none()


async def list_by_evento(db: AsyncSession, evento_id: uuid.UUID) -> list[Lote]:
    result = await db.execute(
        select(Lote).where(Lote.evento_id == evento_id).order_by(Lote.data_inicio_venda)
    )
    return list(result.scalars().all())


async def list_ativos_by_evento(db: AsyncSession, evento_id: uuid.UUID) -> list[Lote]:
    result = await db.execute(
        select(Lote)
        .where(Lote.evento_id == evento_id, Lote.ativo.is_(True))
        .order_by(Lote.data_inicio_venda)
    )
    return list(result.scalars().all())


async def create(
    db: AsyncSession,
    *,
    evento_id: uuid.UUID,
    nome: str,
    tipo: TipoLote,
    preco: float,
    quantidade_total: int,
    data_inicio_venda: datetime,
    data_fim_venda: datetime,
    ativo: bool = True,
) -> Lote:
    lote = Lote(
        evento_id=evento_id,
        nome=nome,
        tipo=tipo,
        preco=preco,
        quantidade_total=quantidade_total,
        data_inicio_venda=data_inicio_venda,
        data_fim_venda=data_fim_venda,
        ativo=ativo,
    )
    db.add(lote)
    await db.commit()
    await db.refresh(lote)
    return lote


async def update(db: AsyncSession, lote: Lote, **campos: Any) -> Lote:
    for chave, valor in campos.items():
        setattr(lote, chave, valor)
    await db.commit()
    await db.refresh(lote)
    return lote


async def update_ativo(db: AsyncSession, lote: Lote, ativo: bool) -> Lote:
    lote.ativo = ativo
    await db.commit()
    await db.refresh(lote)
    return lote


async def delete(db: AsyncSession, lote: Lote) -> None:
    await db.delete(lote)
    await db.commit()


def incrementar_vendidas(lote: Lote, quantidade: int) -> None:
    lote.quantidade_vendida += quantidade


def decrementar_vendidas(lote: Lote, quantidade: int) -> None:
    lote.quantidade_vendida = max(0, lote.quantidade_vendida - quantidade)
