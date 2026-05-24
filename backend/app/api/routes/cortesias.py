import uuid

from fastapi import APIRouter, Response, status

from app.api.deps import DbDep, OrganizadorUser
from app.schemas.cortesia import CortesiaCreate, CortesiaResponse
from app.service import cortesia_service

router = APIRouter(tags=["Cortesias"])


@router.post(
    "/eventos/{evento_id}/cortesias",
    response_model=CortesiaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def emitir_cortesia(
    evento_id: uuid.UUID,
    data: CortesiaCreate,
    db: DbDep,
    organizador: OrganizadorUser,
):
    cortesia = await cortesia_service.emitir(db, organizador, evento_id, data)
    return CortesiaResponse.from_cortesia(cortesia)


@router.get(
    "/eventos/{evento_id}/cortesias",
    response_model=list[CortesiaResponse],
)
async def listar_cortesias_do_evento(
    evento_id: uuid.UUID,
    db: DbDep,
    organizador: OrganizadorUser,
):
    cortesias = await cortesia_service.listar_por_evento(db, organizador, evento_id)
    return [CortesiaResponse.from_cortesia(c) for c in cortesias]


@router.get("/cortesias/{cortesia_id}", response_model=CortesiaResponse)
async def obter_cortesia(
    cortesia_id: uuid.UUID,
    db: DbDep,
    organizador: OrganizadorUser,
):
    cortesia = await cortesia_service.obter(db, organizador, cortesia_id)
    return CortesiaResponse.from_cortesia(cortesia)


@router.delete("/cortesias/{cortesia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancelar_cortesia(
    cortesia_id: uuid.UUID,
    db: DbDep,
    organizador: OrganizadorUser,
):
    await cortesia_service.cancelar(db, organizador, cortesia_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
