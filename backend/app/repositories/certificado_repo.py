import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certificado import Certificado


async def create(
    db: AsyncSession,
    *,
    ingresso_id: uuid.UUID,
    participante_id: uuid.UUID,
    pdf_url: str,
) -> Certificado:
    certificado = Certificado(
        ingresso_id=ingresso_id,
        participante_id=participante_id,
        pdf_url=pdf_url,
    )
    db.add(certificado)
    await db.commit()
    await db.refresh(certificado)
    return certificado


async def get_by_ingresso_id(
    db: AsyncSession, ingresso_id: uuid.UUID
) -> Certificado | None:
    result = await db.execute(
        select(Certificado).where(Certificado.ingresso_id == ingresso_id)
    )
    return result.scalar_one_or_none()
