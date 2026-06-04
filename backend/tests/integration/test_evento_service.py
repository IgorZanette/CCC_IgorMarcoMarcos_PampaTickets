"""Testes de integração do evento_service (CRUD, ownership, transições de status)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.models.evento import StatusEvento
from app.models.usuario import PerfilUsuario
from app.schemas.evento import EventoCreate, EventoUpdate
from app.service import evento_service


def _dt(dias: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=dias)


async def test_criar_inicia_em_rascunho(db_session, organizador):
    data = EventoCreate(
        nome="Festival Pampa", data_inicio=_dt(30), data_fim=_dt(31), local="POA"
    )
    evento = await evento_service.criar(db_session, organizador, data)
    assert evento.status == StatusEvento.RASCUNHO
    assert evento.organizador_id == organizador.id


async def test_obter_publico_rascunho_404(db_session, organizador, criar_evento):
    evento = await criar_evento(organizador, status=StatusEvento.RASCUNHO)
    with pytest.raises(HTTPException) as exc:
        await evento_service.obter_publico(db_session, evento.id)
    assert exc.value.status_code == 404


async def test_obter_publico_publicado_ok(db_session, organizador, criar_evento):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    obtido = await evento_service.obter_publico(db_session, evento.id)
    assert obtido.id == evento.id


async def test_obter_proprio_de_outro_organizador_403(
    db_session, organizador, criar_evento, criar_usuario
):
    evento = await criar_evento(organizador)
    outro = await criar_usuario(
        perfil=PerfilUsuario.ORGANIZADOR, email="outro@test.com"
    )
    with pytest.raises(HTTPException) as exc:
        await evento_service.obter_do_organizador(db_session, outro, evento.id)
    assert exc.value.status_code == 403


async def test_publicar_de_rascunho_ok(db_session, organizador, criar_evento):
    evento = await criar_evento(organizador, status=StatusEvento.RASCUNHO)
    publicado = await evento_service.publicar(db_session, organizador, evento.id)
    assert publicado.status == StatusEvento.PUBLICADO


async def test_publicar_ja_publicado_409(db_session, organizador, criar_evento):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    with pytest.raises(HTTPException) as exc:
        await evento_service.publicar(db_session, organizador, evento.id)
    assert exc.value.status_code == 409


async def test_encerrar_so_publicado_409(db_session, organizador, criar_evento):
    rascunho = await criar_evento(organizador, status=StatusEvento.RASCUNHO)
    with pytest.raises(HTTPException) as exc:
        await evento_service.encerrar(db_session, organizador, rascunho.id)
    assert exc.value.status_code == 409


async def test_cancelar_encerrado_409(db_session, organizador, criar_evento):
    encerrado = await criar_evento(organizador, status=StatusEvento.ENCERRADO)
    with pytest.raises(HTTPException) as exc:
        await evento_service.cancelar(db_session, organizador, encerrado.id)
    assert exc.value.status_code == 409


async def test_editar_inexistente_404(db_session, organizador):
    with pytest.raises(HTTPException) as exc:
        await evento_service.editar(
            db_session, organizador, uuid.uuid4(), EventoUpdate(nome="Novo Nome")
        )
    assert exc.value.status_code == 404


async def test_editar_evento_encerrado_409(db_session, organizador, criar_evento):
    evento = await criar_evento(organizador, status=StatusEvento.ENCERRADO)
    with pytest.raises(HTTPException) as exc:
        await evento_service.editar(
            db_session, organizador, evento.id, EventoUpdate(nome="Outro Nome")
        )
    assert exc.value.status_code == 409
