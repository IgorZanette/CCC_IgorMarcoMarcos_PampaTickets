import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cupom import Cupom


async def get_by_id(db: AsyncSession, cupom_id: uuid.UUID) -> Cupom | None:
    result = await db.execute(select(Cupom).where(Cupom.id == cupom_id))
    return result.scalar_one_or_none()


async def get_by_codigo_and_evento(
    db: AsyncSession, codigo: str, evento_id: uuid.UUID
) -> Cupom | None:
    result = await db.execute(
        select(Cupom).where(
            Cupom.codigo == codigo,
            Cupom.evento_id == evento_id,
        )
    )
    return result.scalar_one_or_none()


async def list_by_evento(db: AsyncSession, evento_id: uuid.UUID) -> list[Cupom]:
    result = await db.execute(
        select(Cupom)
        .where(Cupom.evento_id == evento_id)
        .order_by(Cupom.criado_em.desc())
    )
    return list(result.scalars().all())


async def create(db: AsyncSession, cupom: Cupom) -> Cupom:
    db.add(cupom)
    await db.commit()
    await db.refresh(cupom)
    return cupom


async def update(db: AsyncSession, cupom: Cupom, **campos: Any) -> Cupom:
    for chave, valor in campos.items():
        setattr(cupom, chave, valor)
    await db.commit()
    await db.refresh(cupom)
    return cupom


async def delete(db: AsyncSession, cupom: Cupom) -> None:
    await db.delete(cupom)
    await db.commit()


def incrementar_usado(cupom: Cupom, quantidade: int = 1) -> None:
    cupom.quantidade_usada += quantidade


def decrementar_usado(cupom: Cupom, quantidade: int = 1) -> None:
    cupom.quantidade_usada -= quantidade
