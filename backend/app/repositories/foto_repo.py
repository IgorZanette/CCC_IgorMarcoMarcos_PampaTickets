import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.foto import FotoEvento


async def get_by_id(db: AsyncSession, foto_id: uuid.UUID) -> FotoEvento | None:
    result = await db.execute(select(FotoEvento).where(FotoEvento.id == foto_id))
    return result.scalar_one_or_none()


async def list_by_evento(db: AsyncSession, evento_id: uuid.UUID) -> list[FotoEvento]:
    stmt = (
        select(FotoEvento)
        .where(FotoEvento.evento_id == evento_id)
        .order_by(FotoEvento.publicado_em.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create(db: AsyncSession, foto: FotoEvento) -> FotoEvento:
    db.add(foto)
    await db.commit()
    await db.refresh(foto)
    return foto


async def delete(db: AsyncSession, foto: FotoEvento) -> None:
    await db.delete(foto)
    await db.commit()
