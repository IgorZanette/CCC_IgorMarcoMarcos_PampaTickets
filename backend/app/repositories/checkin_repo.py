import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkin import Checkin


async def create(
    db: AsyncSession,
    *,
    ingresso_id: uuid.UUID,
    realizado_por: uuid.UUID,
) -> Checkin:
    checkin = Checkin(ingresso_id=ingresso_id, realizado_por=realizado_por)
    db.add(checkin)
    await db.commit()
    await db.refresh(checkin)
    return checkin


async def get_by_ingresso_id(
    db: AsyncSession, ingresso_id: uuid.UUID
) -> Checkin | None:
    result = await db.execute(select(Checkin).where(Checkin.ingresso_id == ingresso_id))
    return result.scalar_one_or_none()
