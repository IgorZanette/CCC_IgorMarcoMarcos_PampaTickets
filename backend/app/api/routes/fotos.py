import uuid

from fastapi import APIRouter, File, Response, UploadFile, status

from app.api.deps import CurrentUser, DbDep, OrganizadorUser
from app.schemas.foto import FotoResponse
from app.service import foto_service

router = APIRouter(tags=["Fotos"])


@router.post(
    "/eventos/{evento_id}/fotos",
    response_model=list[FotoResponse],
    status_code=status.HTTP_201_CREATED,
)
async def publicar_fotos(
    evento_id: uuid.UUID,
    db: DbDep,
    organizador: OrganizadorUser,
    files: list[UploadFile] = File(...),
):
    return await foto_service.publicar(db, organizador, evento_id, files)


@router.get(
    "/eventos/{evento_id}/fotos",
    response_model=list[FotoResponse],
)
async def listar_fotos_do_evento(
    evento_id: uuid.UUID,
    db: DbDep,
    usuario: CurrentUser,
):
    # Exige login para ver (qualquer perfil autenticado). As URLs vêm assinadas.
    return await foto_service.listar_por_evento(db, evento_id)


@router.delete("/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_foto(
    foto_id: uuid.UUID,
    db: DbDep,
    organizador: OrganizadorUser,
):
    await foto_service.excluir(db, organizador, foto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
