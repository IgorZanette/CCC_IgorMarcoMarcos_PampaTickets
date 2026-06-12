"""Notificações WhatsApp (UC15): orquestração, cliente Meta (mockado),
degradação graciosa e os três ganchos event-driven."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import BackgroundTasks
from sqlalchemy import select

from app.integrations.whatsapp import client as wa_client
from app.integrations.whatsapp.exceptions import WhatsAppAPIError
from app.models.evento import Evento, StatusEvento
from app.models.ingresso import Ingresso
from app.models.pagamento import MetodoPagamento
from app.models.pedido import StatusPedido
from app.schemas.pedido import PedidoCreate, PedidoItemCreate
from app.service import (
    ingresso_service,
    pagamento_service,
    pedido_service,
    whatsapp_service,
)


# ---------------------------------------------------------------------------
# whatsapp_service — agendamento (sem I/O)
# ---------------------------------------------------------------------------
def test_notificar_agenda_task_com_telefone_normalizado():
    bg = BackgroundTasks()
    whatsapp_service.notificar_pagamento_confirmado(
        bg, nome="Ana", telefone="(54) 99999-8888", evento_nome="Festa Junina"
    )
    assert len(bg.tasks) == 1
    task = bg.tasks[0]
    assert task.kwargs["to"] == "+5554999998888"
    assert task.kwargs["template"] == whatsapp_service.TEMPLATE_PAGAMENTO_CONFIRMADO
    # nome, evento e o link de ingressos/certificado (roadmap).
    nome, evento, link = task.kwargs["params"]
    assert (nome, evento) == ("Ana", "Festa Junina")
    assert link.endswith("/meus-ingressos")


def test_notificar_telefone_invalido_nao_agenda():
    bg = BackgroundTasks()
    whatsapp_service.notificar_checkin(
        bg, nome="Ana", telefone="123", evento_nome="Festa"
    )
    assert bg.tasks == []


def test_notificar_sem_background_tasks_e_noop():
    # background_tasks None (ex.: service chamado fora de um request) não levanta.
    whatsapp_service.notificar_evento_cancelado(
        None, nome="Ana", telefone="54999998888", evento_nome="Festa"
    )


# ---------------------------------------------------------------------------
# cliente Meta — degradação graciosa e payload
# ---------------------------------------------------------------------------
async def test_client_noop_sem_credenciais(monkeypatch):
    monkeypatch.setattr(wa_client.settings, "META_WHATSAPP_TOKEN", None)
    monkeypatch.setattr(wa_client.settings, "META_PHONE_NUMBER_ID", None)
    # get_client nem deve ser chamado quando não configurado.
    monkeypatch.setattr(
        wa_client, "get_client", MagicMock(side_effect=AssertionError("não chamar"))
    )
    assert await wa_client.send_template_message("+55...", "t", ["a"]) is None


async def test_client_envia_payload_de_template(monkeypatch):
    monkeypatch.setattr(wa_client.settings, "META_WHATSAPP_TOKEN", "tok")
    monkeypatch.setattr(wa_client.settings, "META_PHONE_NUMBER_ID", "999")
    resp = MagicMock(is_error=False)
    resp.json.return_value = {"messages": [{"id": "wamid.X"}]}
    fake = MagicMock(post=AsyncMock(return_value=resp))
    monkeypatch.setattr(wa_client, "get_client", lambda: fake)

    out = await wa_client.send_template_message(
        "+5554999998888", "pagamento_confirmado", ["Ana", "Festa"]
    )
    assert out == {"messages": [{"id": "wamid.X"}]}
    fake.post.assert_awaited_once()
    url = fake.post.call_args.args[0]
    payload = fake.post.call_args.kwargs["json"]
    assert url == "/999/messages"
    assert payload["to"] == "+5554999998888"
    assert payload["template"]["name"] == "pagamento_confirmado"
    assert payload["template"]["language"]["code"] == "pt_BR"
    assert payload["template"]["components"][0]["parameters"] == [
        {"type": "text", "text": "Ana"},
        {"type": "text", "text": "Festa"},
    ]


async def test_client_erro_da_meta_vira_excecao(monkeypatch):
    monkeypatch.setattr(wa_client.settings, "META_WHATSAPP_TOKEN", "tok")
    monkeypatch.setattr(wa_client.settings, "META_PHONE_NUMBER_ID", "999")
    resp = MagicMock(is_error=True, status_code=400, text='{"error":"x"}')
    fake = MagicMock(post=AsyncMock(return_value=resp))
    monkeypatch.setattr(wa_client, "get_client", lambda: fake)
    with pytest.raises(WhatsAppAPIError):
        await wa_client.send_template_message("+5554999998888", "t", [])


async def test_enviar_e_best_effort(monkeypatch):
    # _enviar roda em background: falha da Meta é engolida (logada), não sobe.
    async def boom(*a, **k):
        raise WhatsAppAPIError(500, "fail")

    monkeypatch.setattr(whatsapp_service.whatsapp_client, "send_template_message", boom)
    await whatsapp_service._enviar(to="+5554999998888", template="t", params=[])


# ---------------------------------------------------------------------------
# Ganchos event-driven
# ---------------------------------------------------------------------------
async def _criar_pedido_pago_pendente(
    db, participante, organizador, criar_evento, criar_lote
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, preco=100.0, quantidade_total=10)
    data = PedidoCreate(
        evento_id=evento.id,
        itens=[PedidoItemCreate(lote_id=lote.id, quantidade=1)],
        metodo=MetodoPagamento.PIX,
    )
    resultado = await pedido_service.criar(db, participante, data)
    return resultado["pedido"], resultado["charge_id"], evento


async def test_gancho_pagamento_confirmado_agenda_notificacao(
    db_session, participante_pagante, organizador, criar_evento, criar_lote,
    mock_asaas_charges,
):
    _, charge_id, evento = await _criar_pedido_pago_pendente(
        db_session, participante_pagante, organizador, criar_evento, criar_lote
    )
    bg = BackgroundTasks()
    await pagamento_service.processar_webhook(
        db_session,
        evento="PAYMENT_CONFIRMED",
        payment_id=charge_id,
        background_tasks=bg,
    )
    # Uma notificação agendada, para o telefone do participante.
    assert len(bg.tasks) == 1
    task = bg.tasks[0]
    assert task.kwargs["template"] == whatsapp_service.TEMPLATE_PAGAMENTO_CONFIRMADO
    assert task.kwargs["to"].startswith("+55")
    assert evento.nome in task.kwargs["params"]


async def test_gancho_pagamento_reentrega_nao_renotifica(
    db_session, participante_pagante, organizador, criar_evento, criar_lote,
    mock_asaas_charges,
):
    _, charge_id, _ = await _criar_pedido_pago_pendente(
        db_session, participante_pagante, organizador, criar_evento, criar_lote
    )
    # 1ª entrega confirma e notifica.
    bg1 = BackgroundTasks()
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id, background_tasks=bg1
    )
    assert len(bg1.tasks) == 1
    # Reentrega do mesmo webhook (já APROVADO) não dispara nova notificação.
    bg2 = BackgroundTasks()
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id, background_tasks=bg2
    )
    assert bg2.tasks == []


async def test_gancho_checkin_agenda_notificacao(
    db_session, participante_pagante, organizador, criar_evento, criar_lote,
    mock_asaas_charges,
):
    _, charge_id, _ = await _criar_pedido_pago_pendente(
        db_session, participante_pagante, organizador, criar_evento, criar_lote
    )
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id
    )
    # Pega um ingresso emitido para fazer o check-in.
    ingressos = (
        await db_session.execute(select(Ingresso).limit(1))
    ).scalars().all()
    assert ingressos
    qr = ingressos[0].qr_code_hash

    bg = BackgroundTasks()
    await ingresso_service.validar_checkin(
        db_session, qr_code_hash=qr, usuario=organizador, background_tasks=bg
    )
    assert len(bg.tasks) == 1
    assert bg.tasks[0].kwargs["template"] == whatsapp_service.TEMPLATE_CHECKIN_REALIZADO


async def test_gancho_evento_cancelado_notifica_participantes(
    db_session, participante_pagante, organizador, criar_evento, criar_lote,
    mock_asaas_charges,
):
    from app.service import evento_service

    pedido, charge_id, evento = await _criar_pedido_pago_pendente(
        db_session, participante_pagante, organizador, criar_evento, criar_lote
    )
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id
    )
    bg = BackgroundTasks()
    await evento_service.cancelar(
        db_session, organizador, evento.id, background_tasks=bg
    )
    evento_db = await db_session.get(Evento, evento.id)
    assert evento_db.status == StatusEvento.CANCELADO
    pedido_db = await db_session.get(type(pedido), pedido.id)
    assert pedido_db.status == StatusPedido.REEMBOLSADO
    # Um participante afetado → uma notificação de cancelamento.
    assert len(bg.tasks) == 1
    assert bg.tasks[0].kwargs["template"] == whatsapp_service.TEMPLATE_EVENTO_CANCELADO


async def test_cancelamento_nao_notifica_se_pedido_mudou_na_race(
    db_session, participante_pagante, organizador, criar_evento, criar_lote,
    mock_asaas_charges, monkeypatch,
):
    """Achado da revisão: a cascata só notifica pedidos que ELA cancelou. Se a
    race com um webhook deixa o pedido recarregado num status terminal (nenhum
    ramo roda), não há cancelamento a anunciar — e notificar seria enganoso."""
    from app.repositories import pedido_repo
    from app.service import cancelamento_service

    pedido, charge_id, evento = await _criar_pedido_pago_pendente(
        db_session, participante_pagante, organizador, criar_evento, criar_lote
    )
    await pagamento_service.processar_webhook(
        db_session, evento="PAYMENT_CONFIRMED", payment_id=charge_id
    )

    # Simula a race: o reload traz o pedido já REEMBOLSADO (um webhook
    # concorrente mudou o status entre a listagem e o reload da cascata).
    pedido_race = await pedido_repo.get_by_id_com_itens(db_session, pedido.id)
    pedido_race.status = StatusPedido.REEMBOLSADO

    async def fake_reload(db, pedido_id):
        return pedido_race

    monkeypatch.setattr(pedido_repo, "get_by_id_com_itens", fake_reload)

    bg = BackgroundTasks()
    await cancelamento_service.cancelar_pedidos_do_evento(
        db_session, evento.id, background_tasks=bg, evento_nome=evento.nome
    )
    assert bg.tasks == []
