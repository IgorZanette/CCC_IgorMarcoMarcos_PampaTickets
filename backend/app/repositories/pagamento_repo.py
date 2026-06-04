import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pagamento import MetodoPagamento, Pagamento, StatusPagamento


async def create(
    db: AsyncSession,
    *,
    pedido_id: uuid.UUID,
    metodo: MetodoPagamento,
    valor: float,
    charge_id: str | None = None,
) -> Pagamento:
    pagamento = Pagamento(
        pedido_id=pedido_id,
        metodo=metodo,
        valor=valor,
        charge_id=charge_id,
    )
    db.add(pagamento)
    await db.commit()
    await db.refresh(pagamento)
    return pagamento


async def get_by_id(db: AsyncSession, pagamento_id: uuid.UUID) -> Pagamento | None:
    result = await db.execute(select(Pagamento).where(Pagamento.id == pagamento_id))
    return result.scalar_one_or_none()


async def get_by_pedido_id(db: AsyncSession, pedido_id: uuid.UUID) -> Pagamento | None:
    result = await db.execute(select(Pagamento).where(Pagamento.pedido_id == pedido_id))
    return result.scalar_one_or_none()


async def get_by_pedido_id_for_update(
    db: AsyncSession, pedido_id: uuid.UUID
) -> Pagamento | None:
    """Igual a get_by_pedido_id, mas com lock de linha — serializa o reembolso
    para evitar estorno em dobro sob concorrência."""
    result = await db.execute(
        select(Pagamento).where(Pagamento.pedido_id == pedido_id).with_for_update()
    )
    return result.scalar_one_or_none()


async def get_by_charge_id(db: AsyncSession, charge_id: str) -> Pagamento | None:
    result = await db.execute(select(Pagamento).where(Pagamento.charge_id == charge_id))
    return result.scalar_one_or_none()


async def update_status(
    db: AsyncSession,
    pagamento: Pagamento,
    status: StatusPagamento,
    pago_em: datetime | None = None,
) -> Pagamento:
    pagamento.status = status
    if pago_em is not None:
        pagamento.pago_em = pago_em
    await db.commit()
    await db.refresh(pagamento)
    return pagamento


async def update_charge_id(
    db: AsyncSession,
    pagamento: Pagamento,
    charge_id: str,
) -> Pagamento:
    pagamento.charge_id = charge_id
    await db.commit()
    await db.refresh(pagamento)
    return pagamento
