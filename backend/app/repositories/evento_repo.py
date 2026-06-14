import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evento import Evento, StatusEvento


async def get_by_id(db: AsyncSession, evento_id: uuid.UUID) -> Evento | None:
    result = await db.execute(select(Evento).where(Evento.id == evento_id))
    return result.scalar_one_or_none()


async def list_publicados(
    db: AsyncSession, *, limit: int = 50, offset: int = 0
) -> list[Evento]:
    result = await db.execute(
        select(Evento)
        .where(Evento.status == StatusEvento.PUBLICADO)
        .order_by(Evento.data_inicio)
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def list_by_organizador(
    db: AsyncSession, organizador_id: uuid.UUID
) -> list[Evento]:
    result = await db.execute(
        select(Evento)
        .where(Evento.organizador_id == organizador_id)
        .order_by(Evento.criado_em.desc())
    )
    return list(result.scalars().all())


async def create(
    db: AsyncSession,
    *,
    organizador_id: uuid.UUID,
    nome: str,
    descricao: str | None,
    data_inicio: datetime,
    data_fim: datetime,
    local: str,
    endereco_completo: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> Evento:
    evento = Evento(
        organizador_id=organizador_id,
        nome=nome,
        descricao=descricao,
        data_inicio=data_inicio,
        data_fim=data_fim,
        local=local,
        endereco_completo=endereco_completo,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(evento)
    await db.commit()
    await db.refresh(evento)
    return evento


async def update(db: AsyncSession, evento: Evento, **campos: Any) -> Evento:
    for chave, valor in campos.items():
        setattr(evento, chave, valor)
    await db.commit()
    await db.refresh(evento)
    return evento


async def update_status(
    db: AsyncSession, evento: Evento, novo_status: StatusEvento
) -> Evento:
    evento.status = novo_status
    await db.commit()
    await db.refresh(evento)
    return evento
