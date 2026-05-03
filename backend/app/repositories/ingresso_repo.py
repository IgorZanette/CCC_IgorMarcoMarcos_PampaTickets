from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ingresso import Ingresso, StatusIngresso
from app.models.lote import Lote
from app.models.pedido import Pedido


async def get_with_relations(db: AsyncSession, ingresso_id: str) -> Optional[Ingresso]:
    """
    Busca ingresso com todos os relacionamentos necessários para geração de PDF.
    """
    stmt = (
        select(Ingresso)
        .options(
            selectinload(Ingresso.pedido)
            .selectinload(Pedido.usuario),
            selectinload(Ingresso.pedido)
            .selectinload(Pedido.lote)
            .selectinload(Lote.evento)
        )
        .where(Ingresso.id == ingresso_id)
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_qr_hash(db: AsyncSession, qr_hash: str) -> Optional[Ingresso]:
    """
    Busca ingresso pelo hash do QR Code.
    """
    stmt = select(Ingresso).where(Ingresso.qr_code_hash == qr_hash)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_pdf_url(db: AsyncSession, ingresso_id: str, pdf_url: str) -> None:
    """
    Atualiza a URL do PDF do ingresso.
    """
    ingresso = await db.get(Ingresso, ingresso_id)
    if ingresso:
        ingresso.pdf_url = pdf_url
        await db.commit()


async def update_status(db: AsyncSession, ingresso_id: str, status: StatusIngresso) -> None:
    """
    Atualiza o status do ingresso.
    """
    ingresso = await db.get(Ingresso, ingresso_id)
    if ingresso:
        ingresso.status = status
        await db.commit()


async def get_by_pedido_id(db: AsyncSession, pedido_id: str) -> list[Ingresso]:
    """
    Busca todos os ingressos de um pedido.
    """
    stmt = select(Ingresso).where(Ingresso.pedido_id == pedido_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())