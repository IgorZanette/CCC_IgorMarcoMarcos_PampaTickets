import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.pagamento import MetodoPagamento, StatusPagamento
from app.models.pedido import StatusPedido


class PedidoItemCreate(BaseModel):
    lote_id: uuid.UUID
    quantidade: int = Field(..., ge=1, examples=[2])


class PedidoCreate(BaseModel):
    evento_id: uuid.UUID
    itens: list[PedidoItemCreate] = Field(..., min_length=1)
    metodo: MetodoPagamento = Field(..., examples=["PIX"])
    cupom_codigo: str | None = Field(
        None, min_length=3, max_length=50, examples=["PROMO10"]
    )


class PedidoItemResponse(BaseModel):
    id: uuid.UUID
    pedido_id: uuid.UUID
    lote_id: uuid.UUID
    quantidade: int
    preco_unitario: float

    model_config = {"from_attributes": True}


class PedidoResponse(BaseModel):
    id: uuid.UUID
    participante_id: uuid.UUID
    evento_id: uuid.UUID
    valor_total: float
    valor_desconto: float
    status: StatusPedido
    criado_em: datetime
    itens: list[PedidoItemResponse] = []

    model_config = {"from_attributes": True}


class PedidoCriadoResponse(BaseModel):
    pedido: PedidoResponse
    invoice_url: str
    charge_id: str
    pix_qrcode: dict | None = None


class PagamentoStatusResponse(BaseModel):
    pedido_id: uuid.UUID
    metodo: MetodoPagamento
    status_pagamento: StatusPagamento
    status_pedido: StatusPedido
    charge_id: str | None = None
    invoice_url: str | None = None
    pix_qrcode: dict | None = None
