import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbDep, ParticipanteUser
from app.schemas.pedido import (
    PagamentoStatusResponse,
    PedidoCreate,
    PedidoCriadoResponse,
    PedidoResponse,
)
from app.schemas.reembolso import ReembolsoCreate, ReembolsoResponse
from app.service import pedido_service

router = APIRouter(tags=["Pedidos"])


@router.post(
    "/pedidos",
    response_model=PedidoCriadoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_pedido(data: PedidoCreate, db: DbDep, participante: ParticipanteUser):
    resultado = await pedido_service.criar(db, participante, data)
    return resultado


@router.get("/pedidos/meus", response_model=list[PedidoResponse])
async def listar_meus_pedidos(db: DbDep, participante: ParticipanteUser):
    return await pedido_service.listar_meus(db, participante)


@router.get("/pedidos/{pedido_id}", response_model=PedidoResponse)
async def obter_pedido(pedido_id: uuid.UUID, db: DbDep, usuario: CurrentUser):
    return await pedido_service.obter(db, usuario, pedido_id)


@router.get(
    "/pedidos/{pedido_id}/pagamento", response_model=PagamentoStatusResponse
)
async def obter_status_pagamento(
    pedido_id: uuid.UUID, db: DbDep, participante: ParticipanteUser
):
    return await pedido_service.obter_status_pagamento(db, participante, pedido_id)


@router.post("/pedidos/{pedido_id}/cancelar", response_model=PedidoResponse)
async def cancelar_pedido(
    pedido_id: uuid.UUID, db: DbDep, participante: ParticipanteUser
):
    return await pedido_service.cancelar(db, participante, pedido_id)


@router.post(
    "/pedidos/{pedido_id}/reembolso",
    response_model=ReembolsoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reembolsar_pedido(
    pedido_id: uuid.UUID,
    data: ReembolsoCreate,
    db: DbDep,
    participante: ParticipanteUser,
):
    return await pedido_service.reembolsar(
        db, participante, pedido_id, motivo=data.motivo
    )
