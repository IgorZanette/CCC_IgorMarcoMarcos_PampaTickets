import secrets
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import aware_utc
from app.models.cortesia import Cortesia
from app.models.evento import StatusEvento
from app.models.ingresso import Ingresso, StatusIngresso
from app.models.usuario import Usuario
from app.repositories import (
    cortesia_repo,
    evento_repo,
    ingresso_repo,
    lote_repo,
    usuario_repo,
)
from app.schemas.cortesia import CortesiaCreate
from app.service import ingresso_service


async def emitir(
    db: AsyncSession,
    organizador: Usuario,
    evento_id: uuid.UUID,
    data: CortesiaCreate,
) -> Cortesia:
    evento = await _validar_ownership_evento(db, organizador, evento_id)

    if evento.status != StatusEvento.PUBLICADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cortesias só podem ser emitidas em eventos publicados.",
        )
    if aware_utc(evento.data_inicio) <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível emitir cortesias após o início do evento.",
        )

    lote = await lote_repo.get_by_id(db, data.lote_id)
    if lote is None or lote.evento_id != evento.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lote não encontrado neste evento.",
        )
    if not lote.ativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lote '{lote.nome}' não está ativo.",
        )
    if lote.quantidade_total - lote.quantidade_vendida < 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lote '{lote.nome}' não possui ingressos disponíveis.",
        )

    beneficiado = await usuario_repo.get_by_email(db, data.email_beneficiado)
    if beneficiado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Nenhum usuário cadastrado com o email '{data.email_beneficiado}'. "
                "O beneficiado precisa criar conta antes de receber a cortesia."
            ),
        )
    if beneficiado.id == organizador.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Você não pode emitir uma cortesia para si mesmo.",
        )

    ingresso = Ingresso(
        pedido_item_id=None,
        lote_id=lote.id,
        participante_id=beneficiado.id,
        qr_code_hash=secrets.token_urlsafe(32),
        status=StatusIngresso.ATIVO,
    )
    db.add(ingresso)
    await db.flush()

    cortesia = Cortesia(
        evento_id=evento.id,
        lote_id=lote.id,
        beneficiado_id=beneficiado.id,
        emitida_por=organizador.id,
        ingresso_id=ingresso.id,
    )
    db.add(cortesia)
    lote_repo.incrementar_vendidas(lote, 1)

    await db.commit()

    await ingresso_service.gerar_pdf_ingresso_upload(db, str(ingresso.id))

    cortesia_carregada = await cortesia_repo.get_by_id(db, cortesia.id)
    assert cortesia_carregada is not None
    return cortesia_carregada


async def listar_por_evento(
    db: AsyncSession, organizador: Usuario, evento_id: uuid.UUID
) -> list[Cortesia]:
    await _validar_ownership_evento(db, organizador, evento_id)
    return await cortesia_repo.list_by_evento(db, evento_id)


async def obter(
    db: AsyncSession, organizador: Usuario, cortesia_id: uuid.UUID
) -> Cortesia:
    cortesia = await cortesia_repo.get_by_id(db, cortesia_id)
    if cortesia is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cortesia não encontrada.",
        )
    await _validar_ownership_evento(db, organizador, cortesia.evento_id)
    return cortesia


async def cancelar(
    db: AsyncSession, organizador: Usuario, cortesia_id: uuid.UUID
) -> None:
    cortesia = await cortesia_repo.get_by_id(db, cortesia_id)
    if cortesia is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cortesia não encontrada.",
        )
    await _validar_ownership_evento(db, organizador, cortesia.evento_id)

    if cortesia.ingresso is not None:
        if cortesia.ingresso.status == StatusIngresso.UTILIZADO:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cortesia já utilizada não pode ser cancelada.",
            )
        if cortesia.ingresso.status == StatusIngresso.ATIVO:
            await ingresso_repo.update_status(
                db, cortesia.ingresso.id, StatusIngresso.CANCELADO
            )
            lote = await lote_repo.get_by_id(db, cortesia.lote_id)
            if lote is not None and lote.quantidade_vendida > 0:
                lote_repo.decrementar_vendidas(lote, 1)
                await db.commit()

    await cortesia_repo.delete(db, cortesia)


async def _validar_ownership_evento(
    db: AsyncSession, organizador: Usuario, evento_id: uuid.UUID
):
    evento = await evento_repo.get_by_id(db, evento_id)
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado.",
        )
    if evento.organizador_id != organizador.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não é o organizador deste evento.",
        )
    return evento
