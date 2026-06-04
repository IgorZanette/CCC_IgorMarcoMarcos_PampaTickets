"""Testes de integração do cupom_service (criação, validação/desconto, edição, exclusão)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.models.cupom import TipoDesconto
from app.models.usuario import PerfilUsuario
from app.schemas.cupom import CupomCreate, CupomUpdate
from app.service import cupom_service


def _futuro(dias: int = 30) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=dias)


class TestCriar:
    async def test_criar_ok(self, db_session, organizador, criar_evento):
        evento = await criar_evento(organizador)
        data = CupomCreate(
            codigo="PROMO10",
            tipo_desconto=TipoDesconto.PERCENTUAL,
            valor_desconto=10.0,
            valido_ate=_futuro(),
        )
        cupom = await cupom_service.criar(db_session, organizador, evento.id, data)
        assert cupom.id is not None
        assert cupom.codigo == "PROMO10"

    async def test_evento_inexistente_404(self, db_session, organizador):
        data = CupomCreate(
            codigo="PROMO10",
            tipo_desconto=TipoDesconto.PERCENTUAL,
            valor_desconto=10.0,
            valido_ate=_futuro(),
        )
        with pytest.raises(HTTPException) as exc:
            await cupom_service.criar(db_session, organizador, uuid.uuid4(), data)
        assert exc.value.status_code == 404

    async def test_nao_dono_403(
        self, db_session, organizador, criar_evento, criar_usuario
    ):
        evento = await criar_evento(organizador)
        outro = await criar_usuario(
            perfil=PerfilUsuario.ORGANIZADOR, email="outro-org@test.com"
        )
        data = CupomCreate(
            codigo="PROMO10",
            tipo_desconto=TipoDesconto.PERCENTUAL,
            valor_desconto=10.0,
            valido_ate=_futuro(),
        )
        with pytest.raises(HTTPException) as exc:
            await cupom_service.criar(db_session, outro, evento.id, data)
        assert exc.value.status_code == 403

    async def test_codigo_duplicado_409(self, db_session, organizador, criar_evento):
        evento = await criar_evento(organizador)
        data = CupomCreate(
            codigo="DUP",
            tipo_desconto=TipoDesconto.PERCENTUAL,
            valor_desconto=10.0,
            valido_ate=_futuro(),
        )
        await cupom_service.criar(db_session, organizador, evento.id, data)
        with pytest.raises(HTTPException) as exc:
            await cupom_service.criar(db_session, organizador, evento.id, data)
        assert exc.value.status_code == 409


class TestValidarECalcularDesconto:
    async def test_percentual(self, db_session, organizador, criar_evento, criar_cupom):
        evento = await criar_evento(organizador)
        await criar_cupom(
            evento,
            codigo="P10",
            tipo_desconto=TipoDesconto.PERCENTUAL,
            valor_desconto=10.0,
        )
        _, desconto = await cupom_service.validar_e_calcular_desconto(
            db_session, evento.id, "P10", 100.0
        )
        assert desconto == 10.0

    async def test_valor_fixo_com_cap_no_valor_base(
        self, db_session, organizador, criar_evento, criar_cupom
    ):
        evento = await criar_evento(organizador)
        await criar_cupom(
            evento,
            codigo="F50",
            tipo_desconto=TipoDesconto.VALOR_FIXO,
            valor_desconto=50.0,
        )
        _, capado = await cupom_service.validar_e_calcular_desconto(
            db_session, evento.id, "F50", 30.0
        )
        assert capado == 30.0  # desconto não passa do valor base
        _, normal = await cupom_service.validar_e_calcular_desconto(
            db_session, evento.id, "F50", 200.0
        )
        assert normal == 50.0

    async def test_inativo_404(
        self, db_session, organizador, criar_evento, criar_cupom
    ):
        evento = await criar_evento(organizador)
        await criar_cupom(evento, codigo="OFF", ativo=False)
        with pytest.raises(HTTPException) as exc:
            await cupom_service.validar_e_calcular_desconto(
                db_session, evento.id, "OFF", 100.0
            )
        assert exc.value.status_code == 404

    async def test_expirado_409(
        self, db_session, organizador, criar_evento, criar_cupom
    ):
        evento = await criar_evento(organizador)
        await criar_cupom(
            evento,
            codigo="OLD",
            valido_ate=datetime.now(timezone.utc) - timedelta(days=1),
        )
        with pytest.raises(HTTPException) as exc:
            await cupom_service.validar_e_calcular_desconto(
                db_session, evento.id, "OLD", 100.0
            )
        assert exc.value.status_code == 409

    async def test_esgotado_409(
        self, db_session, organizador, criar_evento, criar_cupom
    ):
        evento = await criar_evento(organizador)
        await criar_cupom(evento, codigo="MAX", quantidade_maxima=5, quantidade_usada=5)
        with pytest.raises(HTTPException) as exc:
            await cupom_service.validar_e_calcular_desconto(
                db_session, evento.id, "MAX", 100.0
            )
        assert exc.value.status_code == 409


class TestEditarExcluir:
    async def test_editar_qtd_menor_que_usada_409(
        self, db_session, organizador, criar_evento, criar_cupom
    ):
        evento = await criar_evento(organizador)
        cupom = await criar_cupom(
            evento, codigo="E1", quantidade_maxima=10, quantidade_usada=5
        )
        with pytest.raises(HTTPException) as exc:
            await cupom_service.editar(
                db_session, organizador, cupom.id, CupomUpdate(quantidade_maxima=3)
            )
        assert exc.value.status_code == 409

    async def test_excluir_cupom_usado_409(
        self, db_session, organizador, criar_evento, criar_cupom
    ):
        evento = await criar_evento(organizador)
        cupom = await criar_cupom(evento, codigo="E2", quantidade_usada=1)
        with pytest.raises(HTTPException) as exc:
            await cupom_service.excluir(db_session, organizador, cupom.id)
        assert exc.value.status_code == 409

    async def test_editar_fixo_alto_para_percentual_422(
        self, db_session, organizador, criar_evento, criar_cupom
    ):
        # Trocar VALOR_FIXO (150) para PERCENTUAL geraria "150%" — deve ser barrado.
        evento = await criar_evento(organizador)
        cupom = await criar_cupom(
            evento,
            codigo="FX150",
            tipo_desconto=TipoDesconto.VALOR_FIXO,
            valor_desconto=150.0,
        )
        with pytest.raises(HTTPException) as exc:
            await cupom_service.editar(
                db_session,
                organizador,
                cupom.id,
                CupomUpdate(tipo_desconto=TipoDesconto.PERCENTUAL),
            )
        assert exc.value.status_code == 422
