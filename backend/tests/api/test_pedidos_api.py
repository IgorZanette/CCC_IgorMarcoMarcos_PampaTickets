"""Testes de API de pedidos: status de pagamento reidratável (#10) e ownership."""

import uuid

from app.models.evento import StatusEvento
from app.models.pagamento import MetodoPagamento
from app.models.usuario import PerfilUsuario
from app.schemas.pedido import PedidoCreate, PedidoItemCreate
from app.service import pedido_service


async def _criar_pedido(db, participante, organizador, criar_evento, criar_lote):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)
    data = PedidoCreate(
        evento_id=evento.id,
        itens=[PedidoItemCreate(lote_id=lote.id, quantidade=1)],
        metodo=MetodoPagamento.PIX,
    )
    return await pedido_service.criar(db, participante, data)


async def test_status_pagamento_reidrata_pix_e_fatura(
    client,
    db_session,
    participante_pagante,
    organizador,
    auth_headers,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    resultado = await _criar_pedido(
        db_session, participante_pagante, organizador, criar_evento, criar_lote
    )
    pedido_id = resultado["pedido"].id

    resp = await client.get(
        f"/api/pedidos/{pedido_id}/pagamento",
        headers=auth_headers(participante_pagante),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["charge_id"] == "pay_test1"
    assert body["invoice_url"] == "http://invoice.test/pay"
    assert body["pix_qrcode"] is not None


async def test_status_pagamento_de_outro_participante_403(
    client,
    db_session,
    participante_pagante,
    organizador,
    auth_headers,
    criar_usuario,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    resultado = await _criar_pedido(
        db_session, participante_pagante, organizador, criar_evento, criar_lote
    )
    outro = await criar_usuario(
        perfil=PerfilUsuario.PARTICIPANTE, email="outro-part@test.com"
    )
    resp = await client.get(
        f"/api/pedidos/{resultado['pedido'].id}/pagamento",
        headers=auth_headers(outro),
    )
    assert resp.status_code == 403


async def test_status_pagamento_pedido_inexistente_404(
    client, participante, auth_headers
):
    resp = await client.get(
        f"/api/pedidos/{uuid.uuid4()}/pagamento",
        headers=auth_headers(participante),
    )
    assert resp.status_code == 404
