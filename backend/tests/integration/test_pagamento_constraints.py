"""Backstops de UNIQUE de pagamento/reembolso (#7) — impedem duplicacao no banco."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.evento import StatusEvento
from app.models.pagamento import MetodoPagamento
from app.repositories import pagamento_repo, reembolso_repo
from app.schemas.pedido import PedidoCreate, PedidoItemCreate
from app.service import pedido_service


async def _pedido(db, participante, organizador, criar_evento, criar_lote):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)
    data = PedidoCreate(
        evento_id=evento.id,
        itens=[PedidoItemCreate(lote_id=lote.id, quantidade=1)],
        metodo=MetodoPagamento.PIX,
    )
    return await pedido_service.criar(db, participante, data)


async def test_pagamento_duplicado_por_pedido_viola_unique(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    resultado = await _pedido(
        db_session, participante_pagante, organizador, criar_evento, criar_lote
    )
    with pytest.raises(IntegrityError):
        await pagamento_repo.create(
            db_session,
            pedido_id=resultado["pedido"].id,
            metodo=MetodoPagamento.PIX,
            valor=100.0,
        )
    await db_session.rollback()


async def test_reembolso_duplicado_por_pagamento_viola_unique(
    db_session,
    participante_pagante,
    organizador,
    criar_evento,
    criar_lote,
    mock_asaas_charges,
):
    resultado = await _pedido(
        db_session, participante_pagante, organizador, criar_evento, criar_lote
    )
    pagamento = await pagamento_repo.get_by_pedido_id(
        db_session, resultado["pedido"].id
    )
    await reembolso_repo.create(
        db_session, pagamento_id=pagamento.id, valor=100.0, motivo="primeiro"
    )
    with pytest.raises(IntegrityError):
        await reembolso_repo.create(
            db_session, pagamento_id=pagamento.id, valor=100.0, motivo="segundo"
        )
    await db_session.rollback()
