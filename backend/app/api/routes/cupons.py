import uuid

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbDep, OrganizadorUser
from app.schemas.cupom import (
    CupomCreate,
    CupomResponse,
    CupomUpdate,
    CupomValidarRequest,
    CupomValidarResponse,
)
from app.service import cupom_service

router = APIRouter(tags=["Cupons"])


@router.post(
    "/eventos/{evento_id}/cupons",
    response_model=CupomResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_cupom(
    evento_id: uuid.UUID,
    data: CupomCreate,
    db: DbDep,
    organizador: OrganizadorUser,
):
    return await cupom_service.criar(db, organizador, evento_id, data)


@router.get(
    "/eventos/{evento_id}/cupons",
    response_model=list[CupomResponse],
)
async def listar_cupons_do_evento(
    evento_id: uuid.UUID,
    db: DbDep,
    organizador: OrganizadorUser,
):
    return await cupom_service.listar_por_evento(db, organizador, evento_id)


@router.post(
    "/eventos/{evento_id}/cupons/validar",
    response_model=CupomValidarResponse,
)
async def validar_cupom(
    evento_id: uuid.UUID,
    data: CupomValidarRequest,
    db: DbDep,
    _: CurrentUser,
):
    cupom, valor_desconto = await cupom_service.validar_e_calcular_desconto(
        db,
        evento_id=evento_id,
        codigo=data.codigo,
        valor_base=data.valor_base,
    )
    desconto = float(valor_desconto)
    return CupomValidarResponse(
        cupom_id=cupom.id,
        codigo=cupom.codigo,
        tipo_desconto=cupom.tipo_desconto,
        valor_desconto_aplicado=desconto,
        valor_final=round(data.valor_base - desconto, 2),
    )


@router.get("/cupons/{cupom_id}", response_model=CupomResponse)
async def obter_cupom(
    cupom_id: uuid.UUID,
    db: DbDep,
    organizador: OrganizadorUser,
):
    return await cupom_service.obter(db, organizador, cupom_id)


@router.put("/cupons/{cupom_id}", response_model=CupomResponse)
async def editar_cupom(
    cupom_id: uuid.UUID,
    data: CupomUpdate,
    db: DbDep,
    organizador: OrganizadorUser,
):
    return await cupom_service.editar(db, organizador, cupom_id, data)


@router.delete("/cupons/{cupom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_cupom(
    cupom_id: uuid.UUID,
    db: DbDep,
    organizador: OrganizadorUser,
):
    await cupom_service.excluir(db, organizador, cupom_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
