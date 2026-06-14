"""Configuração e fixtures compartilhadas da suíte de testes.

Pontos críticos do harness:

- As variáveis de ambiente são definidas ANTES de qualquer ``import app.*`` porque
  ``app.core.config.Settings()`` é instanciado no import e exige essas chaves. Também
  apontamos ``ASYNC_DATABASE_URL`` para SQLite, tornando a engine module-level inofensiva
  (nos testes ela nunca é usada — sobrescrevemos ``get_db``).
- ``SUPABASE_*`` é deixado SEM valor de propósito: assim a geração/upload de PDF vira
  no-op automático e não há chamadas de rede.
- O banco de teste é uma engine SQLite em memória dedicada com ``StaticPool`` (uma única
  conexão compartilhada), recriada por teste para isolamento total.
"""

import itertools
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# --- Env mínimo ANTES de importar app.* ---
os.environ.setdefault("ASYNC_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-nao-usar-em-producao")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("ASAAS_API_KEY", "test-asaas-key")
os.environ.setdefault("ASAAS_BASE_URL_UAT", "https://sandbox.asaas.test/api/v3")
os.environ.setdefault("ASAAS_WEBHOOK_TOKEN", "test-webhook-token")
# SMTP_PASSWORD é o único campo de e-mail sem default em Settings — localmente
# o backend/.env supre, mas no CI não existe .env (a suíte é autossuficiente).
os.environ.setdefault("SMTP_PASSWORD", "test-smtp-password")

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.cupom import Cupom, TipoDesconto  # noqa: E402
from app.models.evento import Evento, StatusEvento  # noqa: E402
from app.models.lote import Lote, TipoLote  # noqa: E402
from app.models.usuario import PerfilUsuario, Usuario  # noqa: E402
from app.service import auth_service  # noqa: E402

# CPF/CNPJ válidos pelo Mod 11 — o @validates do model Usuario rejeita inválidos no seed.
CPF_VALIDO = "52998224725"
CNPJ_VALIDO = "11222333000181"


@pytest.fixture(autouse=True)
def _rate_limit_desligado():
    """Desliga o rate limiting por padrão (evita interferência entre testes).

    O teste dedicado de rate limit reativa explicitamente.
    """
    from app.core.rate_limit import limiter

    limiter.enabled = False
    yield
    limiter.enabled = False


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    session_maker = async_sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP de API. Sobrescreve get_db para a sessão de teste.

    Usa ASGITransport, que NÃO dispara o lifespan — logo init_db()/close_asaas_client()
    não rodam e a engine Postgres module-level nunca é tocada.
    """

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _seed_usuario(
    db: AsyncSession,
    *,
    perfil: PerfilUsuario,
    email: str,
    cpf_cnpj: str,
) -> Usuario:
    usuario = Usuario(
        nome="Usuário de Teste",
        email=email,
        cpf_cnpj=cpf_cnpj,
        celular="54999407969",
        senha_hash=auth_service._hash_senha("senha-secreta"),
        perfil=perfil,
        ativo=True,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


@pytest_asyncio.fixture
async def organizador(db_session: AsyncSession) -> Usuario:
    return await _seed_usuario(
        db_session,
        perfil=PerfilUsuario.ORGANIZADOR,
        email="organizador@test.com",
        cpf_cnpj=CNPJ_VALIDO,
    )


@pytest_asyncio.fixture
async def participante(db_session: AsyncSession) -> Usuario:
    return await _seed_usuario(
        db_session,
        perfil=PerfilUsuario.PARTICIPANTE,
        email="participante@test.com",
        cpf_cnpj=CPF_VALIDO,
    )


@pytest_asyncio.fixture
async def participante_pagante(
    db_session: AsyncSession, participante: Usuario
) -> Usuario:
    """Participante já com asaas_customer_id — apto a criar pedidos/pagamentos."""
    participante.asaas_customer_id = "cus_test123"
    await db_session.commit()
    await db_session.refresh(participante)
    return participante


@pytest.fixture
def criar_usuario(db_session: AsyncSession) -> Callable[..., Awaitable[Usuario]]:
    """Fábrica de usuários extra (ex.: um segundo organizador para testes de ownership)."""

    async def _criar(
        *,
        perfil: PerfilUsuario = PerfilUsuario.PARTICIPANTE,
        email: str = "extra@test.com",
        cpf_cnpj: str = CPF_VALIDO,
    ) -> Usuario:
        return await _seed_usuario(
            db_session, perfil=perfil, email=email, cpf_cnpj=cpf_cnpj
        )

    return _criar


@pytest.fixture
def auth_headers() -> Callable[[Usuario], dict[str, str]]:
    """Devolve uma função que gera o header Authorization com JWT real do usuário."""

    def _make(usuario: Usuario) -> dict[str, str]:
        token = auth_service._gerar_token(str(usuario.id))
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def criar_evento(
    db_session: AsyncSession,
) -> Callable[..., Awaitable[Evento]]:
    """Fábrica de eventos. Datas padrão no futuro; status configurável."""

    async def _criar(
        organizador: Usuario,
        *,
        status: StatusEvento = StatusEvento.PUBLICADO,
        nome: str = "Evento de Teste",
        descricao: str | None = None,
        local: str = "Porto Alegre, RS",
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> Evento:
        agora = datetime.now(timezone.utc)
        evento = Evento(
            organizador_id=organizador.id,
            nome=nome,
            descricao=descricao,
            data_inicio=data_inicio or (agora + timedelta(days=30)),
            data_fim=data_fim or (agora + timedelta(days=31)),
            local=local,
            status=status,
        )
        db_session.add(evento)
        await db_session.commit()
        await db_session.refresh(evento)
        return evento

    return _criar


@pytest.fixture
def criar_lote(db_session: AsyncSession) -> Callable[..., Awaitable[Lote]]:
    """Fábrica de lotes. Janela de venda padrão dentro do permitido."""

    async def _criar(
        evento: Evento,
        *,
        nome: str = "Lote Padrão",
        tipo: TipoLote = TipoLote.INTEIRA,
        preco: float = 100.0,
        quantidade_total: int = 10,
        quantidade_vendida: int = 0,
        ativo: bool = True,
        data_inicio_venda: datetime | None = None,
        data_fim_venda: datetime | None = None,
    ) -> Lote:
        agora = datetime.now(timezone.utc)
        lote = Lote(
            evento_id=evento.id,
            nome=nome,
            tipo=tipo,
            preco=preco,
            quantidade_total=quantidade_total,
            quantidade_vendida=quantidade_vendida,
            data_inicio_venda=data_inicio_venda or (agora - timedelta(days=1)),
            data_fim_venda=data_fim_venda or (agora + timedelta(days=29)),
            ativo=ativo,
        )
        db_session.add(lote)
        await db_session.commit()
        await db_session.refresh(lote)
        return lote

    return _criar


@pytest.fixture
def criar_cupom(db_session: AsyncSession) -> Callable[..., Awaitable[Cupom]]:
    """Fábrica de cupons. Válido por 30 dias por padrão."""

    async def _criar(
        evento: Evento,
        *,
        codigo: str = "PROMO10",
        tipo_desconto: TipoDesconto = TipoDesconto.PERCENTUAL,
        valor_desconto: float = 10.0,
        quantidade_maxima: int | None = None,
        quantidade_usada: int = 0,
        ativo: bool = True,
        valido_ate: datetime | None = None,
    ) -> Cupom:
        cupom = Cupom(
            evento_id=evento.id,
            codigo=codigo,
            tipo_desconto=tipo_desconto,
            valor_desconto=valor_desconto,
            quantidade_maxima=quantidade_maxima,
            quantidade_usada=quantidade_usada,
            valido_ate=valido_ate or (datetime.now(timezone.utc) + timedelta(days=30)),
            ativo=ativo,
        )
        db_session.add(cupom)
        await db_session.commit()
        await db_session.refresh(cupom)
        return cupom

    return _criar


@pytest.fixture
def mock_asaas_charges(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Substitui as funções de cobrança do Asaas por AsyncMock com retornos válidos.

    Patcha no módulo de definição (app.integrations.asaas.charges), cobrindo todos os
    consumidores (pedido_service, pagamento_service, cancelamento_service) de uma vez.
    """
    from app.integrations.asaas import charges

    # charge_id único por cobrança (como o Asaas real) — respeita o UNIQUE(charge_id).
    contador = itertools.count(1)

    def _criar_cobranca(**kwargs):
        return {
            "id": f"pay_test{next(contador)}",
            "invoiceUrl": "http://invoice.test/pay",
            "bankSlipUrl": "http://invoice.test/boleto.pdf",
        }

    mocks = SimpleNamespace(
        create_charge=AsyncMock(side_effect=_criar_cobranca),
        get_pix_qrcode=AsyncMock(
            return_value={"encodedImage": "iVBORw0KGgo=", "payload": "00020126..."}
        ),
        get_boleto_identificacao=AsyncMock(
            return_value={
                "identificationField": "23793.38128 60000.000000 00000.000000 0 00000000000000",
                "barCode": "23790000000000000000000000000000000000000000",
            }
        ),
        get_charge=AsyncMock(
            return_value={
                "id": "pay_test1",
                "status": "CONFIRMED",
                "invoiceUrl": "http://invoice.test/pay",
                "bankSlipUrl": "http://invoice.test/boleto.pdf",
            }
        ),
        refund_charge=AsyncMock(return_value={"id": "pay_test1", "status": "REFUNDED"}),
        delete_charge=AsyncMock(return_value=True),
    )
    monkeypatch.setattr(charges, "create_charge", mocks.create_charge)
    monkeypatch.setattr(charges, "get_pix_qrcode", mocks.get_pix_qrcode)
    monkeypatch.setattr(
        charges, "get_boleto_identificacao", mocks.get_boleto_identificacao
    )
    monkeypatch.setattr(charges, "get_charge", mocks.get_charge)
    monkeypatch.setattr(charges, "refund_charge", mocks.refund_charge)
    monkeypatch.setattr(charges, "delete_charge", mocks.delete_charge)
    return mocks


@pytest.fixture
def mock_asaas_customers(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Substitui create_customer do Asaas por AsyncMock (retorno com 'id')."""
    from app.integrations.asaas import customers

    mock = AsyncMock(return_value={"id": "cus_test123"})
    monkeypatch.setattr(customers, "create_customer", mock)
    return mock
