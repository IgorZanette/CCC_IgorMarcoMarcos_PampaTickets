from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncEngine


class Base(DeclarativeBase):
    pass


# Importar todos os models aqui para que o Alembic os detecte nas migrações
from app.models.usuario import Usuario  # noqa: E402
from app.models.evento import Evento  # noqa: E402
from app.models.lote import Lote  # noqa: E402
from app.models.cupom import Cupom  # noqa: E402
from app.models.pedido import Pedido, PedidoItem  # noqa: E402
from app.models.pagamento import Pagamento, Reembolso  # noqa: E402
from app.models.ingresso import Ingresso  # noqa: E402
from app.models.cortesia import Cortesia  # noqa: E402
from app.models.checkin import Checkin  # noqa: E402
from app.models.certificado import Certificado  # noqa: E402
from app.models.relatorio import Relatorio  # noqa: E402
from app.models.foto import FotoEvento, CompraFoto  # noqa: E402
from app.models.recuperacao_senha import RecuperacaoSenha  # noqa: E402

__all__ = [
    "Usuario",
    "Evento",
    "Lote",
    "Cupom",
    "Pedido",
    "PedidoItem",
    "Pagamento",
    "Reembolso",
    "Ingresso",
    "Cortesia",
    "Checkin",
    "Certificado",
    "Relatorio",
    "FotoEvento",
    "CompraFoto",
    "RecuperacaoSenha",
]


async def init_models(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
