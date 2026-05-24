import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cortesia import Cortesia


def _eager_load_options():
    return (
        selectinload(Cortesia.beneficiado),
        selectinload(Cortesia.lote),
        selectinload(Cortesia.ingresso),
    )


async def get_by_id(db: AsyncSession, cortesia_id: uuid.UUID) -> Cortesia | None:
    stmt = (
        select(Cortesia)
        .options(*_eager_load_options())
        .where(Cortesia.id == cortesia_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_by_evento(db: AsyncSession, evento_id: uuid.UUID) -> list[Cortesia]:
    stmt = (
        select(Cortesia)
        .options(*_eager_load_options())
        .where(Cortesia.evento_id == evento_id)
        .order_by(Cortesia.emitida_em.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create(db: AsyncSession, cortesia: Cortesia) -> Cortesia:
    db.add(cortesia)
    await db.commit()
    await db.refresh(cortesia)
    return cortesia


async def delete(db: AsyncSession, cortesia: Cortesia) -> None:
    await db.delete(cortesia)
    await db.commit()
