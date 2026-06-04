from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.asaas import charges as asaas_charges
from app.integrations.asaas.exceptions import AsaasAPIError
from app.models.ingresso import StatusIngresso
from app.models.pagamento import StatusPagamento
from app.models.pedido import Pedido, StatusPedido
from app.repositories import (
    cupom_repo,
    ingresso_repo,
    lote_repo,
    pagamento_repo,
    pedido_repo,
    reembolso_repo,
)


async def aplicar_cancelamento(
    db: AsyncSession,
    *,
    pedido: Pedido,
    motivo_status_pagamento: StatusPagamento,
) -> Pedido:
    """
    Cancela um pedido completo: devolve estoque, deleta a cobrança no Asaas
    e marca pagamento + pedido como cancelados.

    Idempotente: se o pedido já estiver CANCELADO, retorna sem fazer nada.
    Espera o pedido carregado com itens (use pedido_repo.get_by_id_com_itens).
    """
    if pedido.status == StatusPedido.CANCELADO:
        return pedido

    for item in pedido.itens:
        lote = await lote_repo.get_by_id(db, item.lote_id)
        if lote is not None:
            lote_repo.decrementar_vendidas(lote, item.quantidade)

    if pedido.cupom_id is not None:
        cupom = await cupom_repo.get_by_id(db, pedido.cupom_id)
        if cupom is not None and cupom.quantidade_usada > 0:
            cupom_repo.decrementar_usado(cupom)

    pagamento = await pagamento_repo.get_by_pedido_id(db, pedido.id)
    if pagamento is not None:
        if pagamento.charge_id is not None:
            try:
                await asaas_charges.delete_charge(charge_id=pagamento.charge_id)
            except AsaasAPIError:
                logger.warning(
                    "Falha ao deletar cobrança {} no Asaas durante cancelamento "
                    "(pode haver cobrança órfã no gateway)",
                    pagamento.charge_id,
                )
        await pagamento_repo.update_status(db, pagamento, motivo_status_pagamento)

    return await pedido_repo.update_status(db, pedido, StatusPedido.CANCELADO)


async def cancelar_pedidos_do_evento(db: AsyncSession, evento_id) -> None:
    """Cancela/estorna todos os pedidos não-terminais de um evento cancelado.

    PENDENTE -> cancelamento normal (devolve estoque, deleta a cobrança).
    PAGO -> estorno no gateway, ingressos cancelados, pedido marcado REEMBOLSADO.
    """
    pedidos = await pedido_repo.list_by_evento(
        db, evento_id, status_in=[StatusPedido.PENDENTE, StatusPedido.PAGO]
    )
    for pedido in pedidos:
        if pedido.status == StatusPedido.PENDENTE:
            await aplicar_cancelamento(
                db, pedido=pedido, motivo_status_pagamento=StatusPagamento.CANCELADO
            )
        elif pedido.status == StatusPedido.PAGO:
            await _estornar_pedido_pago(db, pedido)


async def _estornar_pedido_pago(db: AsyncSession, pedido: Pedido) -> None:
    """Estorna um pedido pago: devolve estoque, reembolsa no gateway, cancela os
    ingressos e marca o pedido como REEMBOLSADO. Espera pedido com itens carregados."""
    for item in pedido.itens:
        lote = await lote_repo.get_by_id(db, item.lote_id)
        if lote is not None:
            lote_repo.decrementar_vendidas(lote, item.quantidade)

    pagamento = await pagamento_repo.get_by_pedido_id(db, pedido.id)
    if pagamento is not None:
        if pagamento.charge_id is not None:
            try:
                await asaas_charges.refund_charge(charge_id=pagamento.charge_id)
            except AsaasAPIError:
                logger.warning(
                    "Falha ao estornar cobrança {} no Asaas (evento cancelado)",
                    pagamento.charge_id,
                )
        await pagamento_repo.update_status(db, pagamento, StatusPagamento.ESTORNADO)

        reembolso = await reembolso_repo.get_by_pagamento_id(db, pagamento.id)
        if reembolso is None:
            reembolso = await reembolso_repo.create(
                db,
                pagamento_id=pagamento.id,
                valor=float(pagamento.valor),
                motivo="Evento cancelado pelo organizador.",
            )
        if reembolso.processado_em is None:
            await reembolso_repo.marcar_processado(db, reembolso)

    ingressos = await ingresso_repo.get_by_pedido_id(db, pedido.id)
    for ing in ingressos:
        await ingresso_repo.update_status(db, ing.id, StatusIngresso.CANCELADO)

    await pedido_repo.update_status(db, pedido, StatusPedido.REEMBOLSADO)
