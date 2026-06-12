"""Testes da cascata de cancelamento de evento (#3) e do bloqueio de check-in."""

import secrets

import pytest
from fastapi import HTTPException

from app.models.evento import Evento, StatusEvento
from app.models.ingresso import Ingresso, StatusIngresso
from app.models.pagamento import MetodoPagamento, StatusPagamento
from app.models.pedido import Pedido, StatusPedido
from app.repositories import ingresso_repo, pagamento_repo
from app.schemas.pedido import PedidoCreate, PedidoItemCreate
from app.service import (
    evento_service,
    ingresso_service,
    pagamento_service,
    pedido_service,
)


def _pedido(evento, lote, *, quantidade):
    return PedidoCreate(
        evento_id=evento.id,
        itens=[PedidoItemCreate(lote_id=lote.id, quantidade=quantidade)],
        metodo=MetodoPagamento.PIX,
    )


async def test_cancelar_evento_cancela_pendente_e_devolve_estoque(
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
        db_session, participante_pagante, _pedido(evento, lote, quantidade=3)
    )

    await evento_service.cancelar(db_session, organizador, evento.id)

    pedido_db = await db_session.get(Pedido, resultado["pedido"].id)
    assert pedido_db.status == StatusPedido.CANCELADO
    await db_session.refresh(lote)
    assert lote.quantidade_vendida == 0
    evento_db = await db_session.get(Evento, evento.id)
    assert evento_db.status == StatusEvento.CANCELADO


async def test_cancelar_evento_estorna_pedido_pago_e_cancela_ingressos(
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
        db_session, participante_pagante, _pedido(evento, lote, quantidade=2)
    )
    # Confirma o pagamento: pedido PAGO + ingressos emitidos.
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=resultado["charge_id"]
    )

    await evento_service.cancelar(db_session, organizador, evento.id)

    pedido_db = await db_session.get(Pedido, resultado["pedido"].id)
    assert pedido_db.status == StatusPedido.REEMBOLSADO

    pagamento = await pagamento_repo.get_by_pedido_id(db_session, pedido_db.id)
    assert pagamento.status == StatusPagamento.ESTORNADO
    mock_asaas_charges.refund_charge.assert_awaited()

    ingressos = await ingresso_repo.get_by_pedido_id(db_session, pedido_db.id)
    assert ingressos
    assert all(i.status == StatusIngresso.CANCELADO for i in ingressos)

    await db_session.refresh(lote)
    assert lote.quantidade_vendida == 0


async def test_cancelar_evento_retoma_apos_falha_sem_estoque_em_dobro(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    """Ressalva do merge ad83d78: a cascata deve ser retomável por pedido.

    1ª tentativa: o estorno de um dos pedidos falha com erro inesperado →
    rollback só daquele pedido, o outro conclui, evento NÃO é cancelado (502).
    2ª tentativa: retoma apenas o pedido que faltou; o estoque do pedido já
    estornado não é devolvido de novo.
    """
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)
    r1 = await pedido_service.criar(
        db_session, participante_pagante, _pedido(evento, lote, quantidade=2)
    )
    r2 = await pedido_service.criar(
        db_session, participante_pagante, _pedido(evento, lote, quantidade=2)
    )
    for r in (r1, r2):
        await pagamento_service.processar_webhook(
            db_session, evento="PAYMENT_CONFIRMED", payment_id=r["charge_id"]
        )
    await db_session.refresh(lote)
    assert lote.quantidade_vendida == 4

    # O rollback por pedido expira os objetos da sessão — capturamos os IDs
    # antes e re-hidratamos o que for usado depois da 1ª tentativa.
    evento_id = evento.id
    pedido_ids = (r1["pedido"].id, r2["pedido"].id)

    # 1ª tentativa: primeiro estorno falha com erro NÃO-Asaas (inesperado).
    mock_asaas_charges.refund_charge.side_effect = [
        RuntimeError("gateway caiu"),
        {"id": "pay_test1", "status": "REFUNDED"},
    ]
    with pytest.raises(HTTPException) as exc:
        await evento_service.cancelar(db_session, organizador, evento_id)
    assert exc.value.status_code == 502

    evento_db = await db_session.get(Evento, evento_id)
    assert evento_db.status == StatusEvento.PUBLICADO  # evento segue cancelável
    await db_session.refresh(lote)
    assert lote.quantidade_vendida == 2  # só o pedido que concluiu devolveu

    # 2ª tentativa: retomada — só o pedido pendente de estorno é reprocessado.
    await db_session.refresh(organizador)
    mock_asaas_charges.refund_charge.side_effect = None
    await evento_service.cancelar(db_session, organizador, evento_id)

    await db_session.refresh(lote)
    assert lote.quantidade_vendida == 0  # sem devolução em dobro
    for pedido_id in pedido_ids:
        pedido_db = await db_session.get(Pedido, pedido_id)
        assert pedido_db.status == StatusPedido.REEMBOLSADO
    evento_db = await db_session.get(Evento, evento_id)
    assert evento_db.status == StatusEvento.CANCELADO


async def test_checkin_em_evento_cancelado_409(
    db_session, organizador, criar_evento, criar_lote
):
    evento = await criar_evento(organizador, status=StatusEvento.CANCELADO)
    lote = await criar_lote(evento)
    ingresso = Ingresso(
        lote_id=lote.id,
        participante_id=organizador.id,
        qr_code_hash=secrets.token_urlsafe(16),
        status=StatusIngresso.ATIVO,
    )
    db_session.add(ingresso)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await ingresso_service.validar_checkin(
            db_session, qr_code_hash=ingresso.qr_code_hash, usuario=organizador
        )
    assert exc.value.status_code == 409
