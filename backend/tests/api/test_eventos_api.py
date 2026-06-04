"""Testes de API dos endpoints de eventos (auth, perfil, visibilidade)."""

import uuid
from datetime import datetime, timedelta, timezone

from app.models.evento import StatusEvento


def _payload() -> dict:
    base = datetime.now(timezone.utc)
    return {
        "nome": "Festival Pampa",
        "data_inicio": (base + timedelta(days=30)).isoformat(),
        "data_fim": (base + timedelta(days=31)).isoformat(),
        "local": "Porto Alegre",
    }


async def test_criar_evento_sem_auth_rejeitado(client):
    resp = await client.post("/api/eventos", json=_payload())
    # HTTPBearer sem credenciais rejeita antes de chegar ao handler.
    assert resp.status_code in (401, 403)


async def test_criar_evento_participante_403(client, participante, auth_headers):
    resp = await client.post(
        "/api/eventos", json=_payload(), headers=auth_headers(participante)
    )
    assert resp.status_code == 403


async def test_criar_evento_organizador_201(client, organizador, auth_headers):
    resp = await client.post(
        "/api/eventos", json=_payload(), headers=auth_headers(organizador)
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "RASCUNHO"
    assert body["nome"] == "Festival Pampa"
    assert body["organizador_id"] == str(organizador.id)


async def test_listar_eventos_retorna_apenas_publicados(
    client, organizador, criar_evento
):
    await criar_evento(organizador, status=StatusEvento.RASCUNHO, nome="EmRascunho")
    await criar_evento(organizador, status=StatusEvento.PUBLICADO, nome="Publicado")
    resp = await client.get("/api/eventos")
    assert resp.status_code == 200
    nomes = [e["nome"] for e in resp.json()]
    assert "Publicado" in nomes
    assert "EmRascunho" not in nomes


async def test_obter_evento_inexistente_404(client):
    resp = await client.get(f"/api/eventos/{uuid.uuid4()}")
    assert resp.status_code == 404
