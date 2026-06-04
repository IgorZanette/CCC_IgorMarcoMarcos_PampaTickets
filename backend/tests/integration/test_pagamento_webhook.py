"""Testes de integração do processamento de webhooks do Asaas (pagamento_service)."""

from datetime import datetime, timezone

from app.models.evento import StatusEvento
from app.models.ingresso import StatusIngresso
from app.models.pagamento import MetodoPagamento, StatusPagamento
from app.models.pedido import Pedido, StatusPedido
from app.repositories import ingresso_repo, pagamento_repo
from app.schemas.pedido import PedidoCreate, PedidoItemCreate
from app.service import pagamento_service, pedido_service


async def _criar_pedido(
    db, participante, organizador, criar_evento, criar_lote, *, qtd=2
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)
    data = PedidoCreate(
        evento_id=evento.id,
        itens=[PedidoItemCreate(lote_id=lote.id, quantidade=qtd)],
        metodo=MetodoPagamento.PIX,
    )
    resultado = await pedido_service.criar(db, participante, data)
    return resultado["pedido"], resultado["charge_id"], lote


async def test_webhook_pagamento_inexistente_noop(db_session):
    # charge_id desconhecido não deve levantar exceção nem alterar nada.
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id="charge-desconhecido"
    )


async def test_webhook_confirmed_aprova_e_cria_ingressos(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    pedido, charge_id, _ = await _criar_pedido(
        db_session, participante_pagante, organizador, criar_evento, criar_lote, qtd=2
    )

    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id
    )

    pagamento = await pagamento_repo.get_by_charge_id(db_session, charge_id)
    assert pagamento.status == StatusPagamento.APROVADO

    pedido_db = await db_session.get(Pedido, pedido.id)
    assert pedido_db.status == StatusPedido.PAGO

    ingressos = await ingresso_repo.get_by_pedido_id(db_session, pedido.id)
    assert len(ingressos) == 2
    assert all(i.status == StatusIngresso.ATIVO for i in ingressos)


async def test_webhook_confirmed_idempotente(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    pedido, charge_id, _ = await _criar_pedido(
        db_session, participante_pagante, organizador, criar_evento, criar_lote, qtd=2
    )

    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id
    )
    # Segundo evento idêntico: pagamento já APROVADO → não duplica ingressos.
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id
    )

    ingressos = await ingresso_repo.get_by_pedido_id(db_session, pedido.id)
    assert len(ingressos) == 2


async def test_webhook_overdue_cancela_pedido(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    pedido, charge_id, lote = await _criar_pedido(
        db_session, participante_pagante, organizador, criar_evento, criar_lote, qtd=2
    )

    mock_asaas_charges.get_charge.return_value = {"status": "OVERDUE"}
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_OVERDUE", payment_id=charge_id
    )

    pedido_db = await db_session.get(Pedido, pedido.id)
    assert pedido_db.status == StatusPedido.CANCELADO
    await db_session.refresh(lote)
    assert lote.quantidade_vendida == 0


async def test_webhook_refunded_estorna_e_cancela_ingressos(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    pedido, charge_id, _ = await _criar_pedido(
        db_session, participante_pagante, organizador, criar_evento, criar_lote, qtd=2
    )
    # Confirma pagamento (cria ingressos, pedido PAGO).
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id
    )
    # Solicita reembolso (cria registro de Reembolso).
    pagamento = await pagamento_repo.get_by_pedido_id(db_session, pedido.id)
    await pagamento_service.solicitar_reembolso(
        db_session, pagamento=pagamento, motivo="teste"
    )

    mock_asaas_charges.get_charge.return_value = {"status": "REFUNDED"}
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_REFUNDED", payment_id=charge_id
    )

    pagamento = await pagamento_repo.get_by_charge_id(db_session, charge_id)
    assert pagamento.status == StatusPagamento.ESTORNADO

    pedido_db = await db_session.get(Pedido, pedido.id)
    assert pedido_db.status == StatusPedido.REEMBOLSADO

    ingressos = await ingresso_repo.get_by_pedido_id(db_session, pedido.id)
    assert ingressos
    assert all(i.status == StatusIngresso.CANCELADO for i in ingressos)


async def test_webhook_confirmed_forjado_e_ignorado(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    # Anti-fraude (#1): mesmo o corpo dizendo CONFIRMED, se o Asaas não confirma
    # o pagamento, o webhook é no-op — nenhum ingresso é emitido.
    pedido, charge_id, _ = await _criar_pedido(
        db_session, participante_pagante, organizador, criar_evento, criar_lote, qtd=2
    )
    mock_asaas_charges.get_charge.return_value = {"status": "PENDING"}

    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id
    )

    pedido_db = await db_session.get(Pedido, pedido.id)
    assert pedido_db.status == StatusPedido.PENDENTE
    ingressos = await ingresso_repo.get_by_pedido_id(db_session, pedido.id)
    assert ingressos == []


async def test_webhook_overdue_apos_pago_e_ignorado(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    # #6: OVERDUE entregue fora de ordem sobre um pedido já PAGO não pode cancelá-lo.
    pedido, charge_id, lote = await _criar_pedido(
        db_session, participante_pagante, organizador, criar_evento, criar_lote, qtd=2
    )
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id
    )

    mock_asaas_charges.get_charge.return_value = {"status": "OVERDUE"}
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_OVERDUE", payment_id=charge_id
    )

    pedido_db = await db_session.get(Pedido, pedido.id)
    assert pedido_db.status == StatusPedido.PAGO


async def test_webhook_confirmed_recupera_ingressos_faltantes(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    # #8: se uma entrega anterior marcou PAGO mas falhou antes de emitir ingressos,
    # a reentrega do webhook deve criar os ingressos faltantes (auto-recuperação).
    pedido, charge_id, _ = await _criar_pedido(
        db_session, participante_pagante, organizador, criar_evento, criar_lote, qtd=2
    )
    pagamento = await pagamento_repo.get_by_charge_id(db_session, charge_id)
    await pagamento_repo.update_status(
        db_session,
        pagamento,
        StatusPagamento.APROVADO,
        pago_em=datetime.now(timezone.utc),
    )
    pedido_db = await db_session.get(Pedido, pedido.id)
    pedido_db.status = StatusPedido.PAGO
    await db_session.commit()
    assert await ingresso_repo.get_by_pedido_id(db_session, pedido.id) == []

    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id
    )

    ingressos = await ingresso_repo.get_by_pedido_id(db_session, pedido.id)
    assert len(ingressos) == 2
