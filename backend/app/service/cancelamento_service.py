from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.asaas import charges as asaas_charges
from app.integrations.asaas.exceptions import AsaasAPIError
from app.models.pagamento import StatusPagamento
from app.models.pedido import Pedido, StatusPedido
from app.repositories import cupom_repo, lote_repo, pagamento_repo, pedido_repo


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
                pass
        await pagamento_repo.update_status(db, pagamento, motivo_status_pagamento)

    return await pedido_repo.update_status(db, pedido, StatusPedido.CANCELADO)
