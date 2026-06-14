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


async def get_urls_by_ingresso_ids(
    db: AsyncSession, ingresso_ids: list[uuid.UUID]
) -> dict[uuid.UUID, str]:
    """Retorna mapa {ingresso_id: pdf_url} para os ids informados."""
    if not ingresso_ids:
        return {}
    result = await db.execute(
        select(Certificado.ingresso_id, Certificado.pdf_url).where(
            Certificado.ingresso_id.in_(ingresso_ids),
            Certificado.pdf_url.isnot(None),
        )
    )
    return {row.ingresso_id: row.pdf_url for row in result}
