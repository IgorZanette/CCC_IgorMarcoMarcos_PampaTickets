import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import DbDep, OrganizadorUser
from app.schemas.evento import EventoCreate, EventoResponse, EventoUpdate
from app.service import evento_service

router = APIRouter(tags=["Eventos"])


@router.post(
    "/eventos",
    response_model=EventoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_evento(data: EventoCreate, db: DbDep, organizador: OrganizadorUser):
    return await evento_service.criar(db, organizador, data)


@router.get("/eventos", response_model=list[EventoResponse])
async def listar_eventos(
    db: DbDep,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await evento_service.listar_publicados(db, limit=limit, offset=offset)


@router.get("/organizador/eventos", response_model=list[EventoResponse])
async def listar_meus_eventos(db: DbDep, organizador: OrganizadorUser):
    return await evento_service.listar_do_organizador(db, organizador)


@router.get(
    "/organizador/eventos/{evento_id}",
    response_model=EventoResponse,
)
async def obter_meu_evento(
    evento_id: uuid.UUID, db: DbDep, organizador: OrganizadorUser
):
    return await evento_service.obter_do_organizador(db, organizador, evento_id)


@router.get("/eventos/{evento_id}", response_model=EventoResponse)
async def obter_evento(evento_id: uuid.UUID, db: DbDep):
    return await evento_service.obter_publico(db, evento_id)


@router.put("/eventos/{evento_id}", response_model=EventoResponse)
async def editar_evento(
    evento_id: uuid.UUID,
    data: EventoUpdate,
    db: DbDep,
    organizador: OrganizadorUser,
):
    return await evento_service.editar(db, organizador, evento_id, data)


@router.patch("/eventos/{evento_id}/publicar", response_model=EventoResponse)
async def publicar_evento(
    evento_id: uuid.UUID, db: DbDep, organizador: OrganizadorUser
):
    return await evento_service.publicar(db, organizador, evento_id)


@router.patch("/eventos/{evento_id}/encerrar", response_model=EventoResponse)
async def encerrar_evento(
    evento_id: uuid.UUID, db: DbDep, organizador: OrganizadorUser
):
    return await evento_service.encerrar(db, organizador, evento_id)


@router.patch("/eventos/{evento_id}/cancelar", response_model=EventoResponse)
async def cancelar_evento(
    evento_id: uuid.UUID, db: DbDep, organizador: OrganizadorUser
):
    return await evento_service.cancelar(db, organizador, evento_id)
