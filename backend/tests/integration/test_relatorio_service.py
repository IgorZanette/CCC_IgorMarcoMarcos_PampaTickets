"""Relatório financeiro (#16): receita exclui reembolsados; reembolso só processado."""

from app.models.evento import StatusEvento
from app.models.pagamento import MetodoPagamento
from app.repositories import pagamento_repo
from app.schemas.pedido import PedidoCreate, PedidoItemCreate
from app.service import pagamento_service, pedido_service, relatorio_service


async def _comprar_e_pagar(db, participante, evento, lote):
    data = PedidoCreate(
        evento_id=evento.id,
        itens=[PedidoItemCreate(lote_id=lote.id, quantidade=1)],
        metodo=MetodoPagamento.PIX,
    )
    resultado = await pedido_service.criar(db, participante, data)
    await pagamento_service.processar_webhook(
        db, evento="PAYMENT_CONFIRMED", payment_id=resultado["charge_id"]
    )
    return resultado


async def test_relatorio_exclui_reembolsado_e_conta_so_processado(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)

    # Pedido 1: pago e mantido.
    await _comprar_e_pagar(db_session, participante_pagante, evento, lote)

    # Pedido 2: pago e depois reembolsado (reembolso processado pelo webhook).
    r2 = await _comprar_e_pagar(db_session, participante_pagante, evento, lote)
    pag2 = await pagamento_repo.get_by_pedido_id(db_session, r2["pedido"].id)
    await pagamento_service.solicitar_reembolso(db_session, pagamento=pag2, motivo="x")
    mock_asaas_charges.get_charge.return_value = {"status": "REFUNDED"}
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_REFUNDED", payment_id=pag2.charge_id
    )

    dados = await relatorio_service.montar_dados(db_session, organizador, evento.id)

    # Receita só do pedido 1 (pago, não reembolsado).
    assert dados.receita_bruta == 100.0
    # Reembolso processado do pedido 2 é reportado à parte.
    assert dados.valor_reembolsado == 100.0
    # Líquida = bruta - desconto; o reembolsado não é subtraído de novo.
    assert dados.receita_liquida == 100.0
