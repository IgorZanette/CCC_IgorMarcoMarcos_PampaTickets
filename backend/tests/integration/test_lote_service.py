"""Testes de integração do lote_service (janela de venda, gerência, estoque)."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.evento import StatusEvento
from app.models.lote import TipoLote
from app.schemas.lote import LoteCreate, LoteUpdate
from app.service import lote_service


def _dt(dias: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=dias)


async def test_criar_lote_ok(db_session, organizador, criar_evento):
    evento = await criar_evento(organizador, status=StatusEvento.RASCUNHO)
    data = LoteCreate(
        nome="Pista",
        tipo=TipoLote.INTEIRA,
        preco=100.0,
        quantidade_total=50,
        data_inicio_venda=_dt(1),
        data_fim_venda=_dt(29),
    )
    lote = await lote_service.criar(db_session, organizador, evento.id, data)
    assert lote.id is not None
    assert lote.quantidade_vendida == 0


async def test_criar_lote_janela_apos_inicio_evento_422(
    db_session, organizador, criar_evento
):
    # Evento começa em +30 dias; venda iniciando em +31 viola a janela.
    evento = await criar_evento(organizador, status=StatusEvento.RASCUNHO)
    data = LoteCreate(
        nome="Tarde Demais",
        tipo=TipoLote.INTEIRA,
        preco=50.0,
        quantidade_total=10,
        data_inicio_venda=_dt(31),
        data_fim_venda=_dt(32),
    )
    with pytest.raises(HTTPException) as exc:
        await lote_service.criar(db_session, organizador, evento.id, data)
    assert exc.value.status_code == 422


async def test_gerenciar_lote_em_evento_encerrado_409(
    db_session, organizador, criar_evento
):
    evento = await criar_evento(organizador, status=StatusEvento.ENCERRADO)
    data = LoteCreate(
        nome="Lote Teste",
        tipo=TipoLote.INTEIRA,
        preco=10.0,
        quantidade_total=5,
        data_inicio_venda=_dt(1),
        data_fim_venda=_dt(29),
    )
    with pytest.raises(HTTPException) as exc:
        await lote_service.criar(db_session, organizador, evento.id, data)
    assert exc.value.status_code == 409


async def test_editar_total_menor_que_vendida_409(
    db_session, organizador, criar_evento, criar_lote
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, quantidade_total=10, quantidade_vendida=5)
    with pytest.raises(HTTPException) as exc:
        await lote_service.editar(
            db_session, organizador, lote.id, LoteUpdate(quantidade_total=3)
        )
    assert exc.value.status_code == 409


async def test_deletar_lote_com_vendas_409(
    db_session, organizador, criar_evento, criar_lote
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, quantidade_vendida=2)
    with pytest.raises(HTTPException) as exc:
        await lote_service.deletar(db_session, organizador, lote.id)
    assert exc.value.status_code == 409


async def test_deletar_lote_sem_vendas_ok(
    db_session, organizador, criar_evento, criar_lote
):
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, quantidade_vendida=0)
    await lote_service.deletar(db_session, organizador, lote.id)
    # Sem exceção = exclusão bem-sucedida.


async def test_check_constraint_impede_oversell_no_banco(
    db_session, organizador, criar_evento, criar_lote
):
    # Rede de segurança (#2): o banco recusa quantidade_vendida > quantidade_total.
    evento = await criar_evento(organizador, status=StatusEvento.PUBLICADO)
    lote = await criar_lote(evento, quantidade_total=5, quantidade_vendida=0)
    lote.quantidade_vendida = 6
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
