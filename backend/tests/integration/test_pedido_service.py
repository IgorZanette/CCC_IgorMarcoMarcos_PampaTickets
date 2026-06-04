"""Testes de integração do pedido_service (criação, cupom, validações, rollback)."""

import pytest
from fastapi import HTTPException

from app.integrations.asaas.exceptions import AsaasAPIError
from app.models.cupom import TipoDesconto
from app.models.evento import StatusEvento
from app.models.pagamento import MetodoPagamento
from app.models.pedido import StatusPedido
from app.schemas.pedido import PedidoCreate, PedidoItemCreate
from app.service import pedido_service


def _data(evento, lote, *, quantidade=1, metodo=MetodoPagamento.PIX, cupom=None):
    return PedidoCreate(
        evento_id=evento.id,
        itens=[PedidoItemCreate(lote_id=lote.id, quantidade=quantidade)],
        metodo=metodo,
        cupom_codigo=cupom,
    )


async def test_criar_pedido_pix_ok(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)
    resultado = await pedido_service.criar(
        db_session, participante_pagante, _data(evento, lote, quantidade=2)
    )
    assert resultado["charge_id"] == "pay_test1"
    assert resultado["pix_qrcode"] is not None
    assert float(resultado["pedido"].valor_total) == 200.0
    assert resultado["pedido"].status == StatusPedido.PENDENTE
    mock_asaas_charges.create_charge.assert_awaited_once()
    mock_asaas_charges.get_pix_qrcode.assert_awaited_once()
    await db_session.refresh(lote)
    assert lote.quantidade_vendida == 2


async def test_criar_pedido_precisao_decimal(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    # 33.33 * 3 = 99.99 exato (com float daria 99.99000000000001).
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=33.33, quantidade_total=10)
    resultado = await pedido_service.criar(
        db_session, participante_pagante, _data(evento, lote, quantidade=3)
    )
    assert str(resultado["pedido"].valor_total) == "99.99"


async def test_criar_pedido_aplica_cupom_percentual(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    criar_cupom,
    mock_asaas_charges,
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)
    await criar_cupom(
        evento,
        codigo="OFF20",
        tipo_desconto=TipoDesconto.PERCENTUAL,
        valor_desconto=20.0,
    )
    resultado = await pedido_service.criar(
        db_session,
        participante_pagante,
        _data(evento, lote, quantidade=1, cupom="OFF20"),
    )
    assert float(resultado["pedido"].valor_total) == 80.0
    assert float(resultado["pedido"].valor_desconto) == 20.0


async def test_criar_pedido_evento_nao_publicado_404(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    evento = await criar_evento(organizador, status=StatusEvento.RASCUNHO)
    lote = await criar_lote(evento)
    with pytest.raises(HTTPException) as exc:
        await pedido_service.criar(
            db_session, participante_pagante, _data(evento, lote)
        )
    assert exc.value.status_code == 404


async def test_criar_pedido_sem_asaas_customer_502(
    db_session, participante, organizador, criar_evento, criar_lote, mock_asaas_charges
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento)
    # participante padrão não tem asaas_customer_id
    with pytest.raises(HTTPException) as exc:
        await pedido_service.criar(db_session, participante, _data(evento, lote))
    assert exc.value.status_code == 502


async def test_criar_pedido_estoque_insuficiente_409(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, quantidade_total=2, quantidade_vendida=1)
    with pytest.raises(HTTPException) as exc:
        await pedido_service.criar(
            db_session, participante_pagante, _data(evento, lote, quantidade=5)
        )
    assert exc.value.status_code == 409


async def test_criar_pedido_lote_inativo_409(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, ativo=False)
    with pytest.raises(HTTPException) as exc:
        await pedido_service.criar(
            db_session, participante_pagante, _data(evento, lote)
        )
    assert exc.value.status_code == 409


async def test_criar_pedido_rollback_em_erro_cliente_asaas_422(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)
    mock_asaas_charges.create_charge.side_effect = AsaasAPIError(
        400, '{"errors":[{"description":"CPF inválido"}]}'
    )
    with pytest.raises(HTTPException) as exc:
        await pedido_service.criar(
            db_session, participante_pagante, _data(evento, lote, quantidade=2)
        )
    assert exc.value.status_code == 422
    # Estoque deve ter sido revertido no rollback de negócio.
    await db_session.refresh(lote)
    assert lote.quantidade_vendida == 0


async def test_criar_pedido_erro_servidor_asaas_502(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)
    mock_asaas_charges.create_charge.side_effect = AsaasAPIError(503, "indisponível")
    with pytest.raises(HTTPException) as exc:
        await pedido_service.criar(
            db_session, participante_pagante, _data(evento, lote)
        )
    assert exc.value.status_code == 502


async def test_cancelar_pedido_pendente_ok(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)
    resultado = await pedido_service.criar(
        db_session, participante_pagante, _data(evento, lote, quantidade=2)
    )
    pedido = await pedido_service.cancelar(
        db_session, participante_pagante, resultado["pedido"].id
    )
    assert pedido.status == StatusPedido.CANCELADO
    await db_session.refresh(lote)
    assert lote.quantidade_vendida == 0


async def test_reembolsar_pedido_pendente_409(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)
    resultado = await pedido_service.criar(
        db_session, participante_pagante, _data(evento, lote)
    )
    with pytest.raises(HTTPException) as exc:
        await pedido_service.reembolsar(
            db_session, participante_pagante, resultado["pedido"].id, motivo=None
        )
    assert exc.value.status_code == 409
