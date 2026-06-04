"""Testes de API do webhook do Asaas (validação de token, estrutura, despacho)."""

from unittest.mock import AsyncMock

from app.core.config import settings

WEBHOOK_URL = "/api/webhooks/asaas"
_PAYLOAD = {"event": "PAYMENT_CONFIRMED", "payment": {"id": "pay_1"}}


async def test_webhook_sem_token_401(client):
    resp = await client.post(WEBHOOK_URL, json=_PAYLOAD)
    assert resp.status_code == 401


async def test_webhook_token_errado_401(client):
    resp = await client.post(
        WEBHOOK_URL, json=_PAYLOAD, headers={"asaas-access-token": "token-errado"}
    )
    assert resp.status_code == 401


async def test_webhook_json_invalido_400(client):
    resp = await client.post(
        WEBHOOK_URL,
        content=b"isso nao e json",
        headers={"asaas-access-token": settings.ASAAS_WEBHOOK_TOKEN},
    )
    assert resp.status_code == 400


async def test_webhook_estrutura_invalida_400(client):
    resp = await client.post(
        WEBHOOK_URL,
        json={"event": "PAYMENT_CONFIRMED"},  # falta "payment"
        headers={"asaas-access-token": settings.ASAAS_WEBHOOK_TOKEN},
    )
    assert resp.status_code == 400


async def test_webhook_valido_200_despacha_processamento(client, monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr("app.api.routes.webhooks.processar_webhook", mock)
    resp = await client.post(
        WEBHOOK_URL,
        json=_PAYLOAD,
        headers={"asaas-access-token": settings.ASAAS_WEBHOOK_TOKEN},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    mock.assert_awaited_once()
