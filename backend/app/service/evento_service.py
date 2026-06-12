import uuid

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evento import Evento, StatusEvento
from app.models.usuario import Usuario
from app.repositories import evento_repo
from app.schemas.evento import EventoCreate, EventoUpdate
from app.service import cancelamento_service

_STATUS_EDITAVEIS = {StatusEvento.RASCUNHO, StatusEvento.PUBLICADO}
_STATUS_CANCELAVEIS = {StatusEvento.RASCUNHO, StatusEvento.PUBLICADO}
_STATUS_VISIVEIS = {StatusEvento.PUBLICADO, StatusEvento.ENCERRADO}


async def criar(db: AsyncSession, organizador: Usuario, data: EventoCreate) -> Evento:
    return await evento_repo.create(
        db,
        organizador_id=organizador.id,
        nome=data.nome,
        descricao=data.descricao,
        data_inicio=data.data_inicio,
        data_fim=data.data_fim,
        local=data.local,
    )


async def listar_publicados(
    db: AsyncSession, *, limit: int = 50, offset: int = 0
) -> list[Evento]:
    return await evento_repo.list_publicados(db, limit=limit, offset=offset)


async def obter_publico(db: AsyncSession, evento_id: uuid.UUID) -> Evento:
    evento = await evento_repo.get_by_id(db, evento_id)
    if evento is None or evento.status not in _STATUS_VISIVEIS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado.",
        )
    return evento


async def listar_do_organizador(db: AsyncSession, organizador: Usuario) -> list[Evento]:
    return await evento_repo.list_by_organizador(db, organizador.id)


async def obter_do_organizador(
    db: AsyncSession, organizador: Usuario, evento_id: uuid.UUID
) -> Evento:
    """Retorna o evento de qualquer status, desde que o requester seja o dono.

    Contraparte privada de `obter_publico` — usada quando o organizador
    precisa ver o próprio evento ainda em RASCUNHO ou CANCELADO.
    """
    return await _obter_proprio(db, organizador, evento_id)


async def editar(
    db: AsyncSession,
    organizador: Usuario,
    evento_id: uuid.UUID,
    data: EventoUpdate,
) -> Evento:
    evento = await _obter_proprio(db, organizador, evento_id)
    if evento.status not in _STATUS_EDITAVEIS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evento não pode ser editado neste status.",
        )

    campos = data.model_dump(exclude_unset=True)
    if not campos:
        return evento

    novo_inicio = campos.get("data_inicio", evento.data_inicio)
    novo_fim = campos.get("data_fim", evento.data_fim)
    if novo_fim <= novo_inicio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="data_fim deve ser posterior a data_inicio.",
        )

    return await evento_repo.update(db, evento, **campos)


async def publicar(
    db: AsyncSession, organizador: Usuario, evento_id: uuid.UUID
) -> Evento:
    evento = await _obter_proprio(db, organizador, evento_id)
    if evento.status != StatusEvento.RASCUNHO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Apenas eventos em rascunho podem ser publicados.",
        )
    return await evento_repo.update_status(db, evento, StatusEvento.PUBLICADO)


async def encerrar(
    db: AsyncSession, organizador: Usuario, evento_id: uuid.UUID
) -> Evento:
    evento = await _obter_proprio(db, organizador, evento_id)
    if evento.status != StatusEvento.PUBLICADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Apenas eventos publicados podem ser encerrados.",
        )
    return await evento_repo.update_status(db, evento, StatusEvento.ENCERRADO)


async def cancelar(
    db: AsyncSession,
    organizador: Usuario,
    evento_id: uuid.UUID,
    background_tasks: BackgroundTasks | None = None,
) -> Evento:
    evento = await _obter_proprio(db, organizador, evento_id)
    if evento.status not in _STATUS_CANCELAVEIS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evento não pode ser cancelado neste status.",
        )
    # Cascata: cancela pendentes e estorna pagos antes de marcar o evento.
    await cancelamento_service.cancelar_pedidos_do_evento(
        db, evento.id, background_tasks=background_tasks, evento_nome=evento.nome
    )
    return await evento_repo.update_status(db, evento, StatusEvento.CANCELADO)


async def _obter_proprio(
    db: AsyncSession, organizador: Usuario, evento_id: uuid.UUID
) -> Evento:
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
