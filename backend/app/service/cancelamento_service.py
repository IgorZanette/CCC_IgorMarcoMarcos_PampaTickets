from fastapi import HTTPException, status
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

# Statuses de pagamento que SÓ são atribuídos por aplicar_cancelamento — sempre
# no mesmo commit das compensações (estoque/cupom). Ver _ja_compensado abaixo.
_STATUS_CANCELAMENTO = {StatusPagamento.CANCELADO, StatusPagamento.RECUSADO}


async def aplicar_cancelamento(
    db: AsyncSession,
    *,
    pedido: Pedido,
    motivo_status_pagamento: StatusPagamento,
) -> Pedido:
    """
    Cancela um pedido completo: devolve estoque/cupom, deleta a cobrança no
    Asaas e marca pagamento + pedido como cancelados.

    Idempotente e retomável: se o pedido já estiver CANCELADO, retorna sem
    fazer nada. Se o pagamento já estiver num status de cancelamento, as
    compensações (estoque/cupom) não são reaplicadas — elas commitam junto com
    o status do pagamento, então esse status é o marcador confiável de "já
    compensado" quando uma execução anterior falhou antes de finalizar o
    pedido. Sem o marcador, um retry devolveria estoque/cupom em dobro
    (contagem de vendidas abaixo do real → risco de oversell).

    Espera o pedido carregado com itens (use pedido_repo.get_by_id_com_itens).
    """
    if pedido.status == StatusPedido.CANCELADO:
        return pedido

    pagamento = await pagamento_repo.get_by_pedido_id(db, pedido.id)
    ja_compensado = (
        pagamento is not None and pagamento.status in _STATUS_CANCELAMENTO
    )

    if not ja_compensado:
        for item in pedido.itens:
            lote = await lote_repo.get_by_id(db, item.lote_id)
            if lote is not None:
                lote_repo.decrementar_vendidas(lote, item.quantidade)

        if pedido.cupom_id is not None:
            cupom = await cupom_repo.get_by_id(db, pedido.cupom_id)
            if cupom is not None and cupom.quantidade_usada > 0:
                cupom_repo.decrementar_usado(cupom)

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
            # Este commit persiste também as devoluções de estoque/cupom acima —
            # é o que torna o status do pagamento um marcador de retomada seguro.
            await pagamento_repo.update_status(db, pagamento, motivo_status_pagamento)

    return await pedido_repo.update_status(db, pedido, StatusPedido.CANCELADO)


async def cancelar_pedidos_do_evento(db: AsyncSession, evento_id) -> None:
    """Cancela/estorna todos os pedidos não-terminais de um evento cancelado.

    PENDENTE -> cancelamento normal (devolve estoque, deleta a cobrança).
    PAGO -> estorno no gateway, ingressos cancelados, pedido marcado REEMBOLSADO.

    Resiliente e retomável (ressalva do merge ad83d78): cada pedido é
    processado isoladamente — uma falha faz rollback apenas das mutações do
    pedido atual (para não vazarem no commit do próximo) e não impede os
    demais. Havendo falhas, levanta 502 ao final SEM o evento ter sido
    cancelado: o organizador repete o cancelamento e a cascata retoma apenas
    os pedidos que faltaram, sem dupla devolução de estoque (ver os marcadores
    de compensação em aplicar_cancelamento/_estornar_pedido_pago).
    """
    pedidos = await pedido_repo.list_by_evento(
        db, evento_id, status_in=[StatusPedido.PENDENTE, StatusPedido.PAGO]
    )
    pedido_ids = [p.id for p in pedidos]

    falhas = 0
    for pedido_id in pedido_ids:
        # Recarrega fresco: um rollback de falha anterior expira os objetos da
        # listagem, e o status pode ter mudado entre a listagem e o processamento
        # (ex.: webhook confirmou o pagamento no meio da cascata).
        pedido = await pedido_repo.get_by_id_com_itens(db, pedido_id)
        if pedido is None:
            continue
        try:
            if pedido.status == StatusPedido.PENDENTE:
                await aplicar_cancelamento(
                    db,
                    pedido=pedido,
                    motivo_status_pagamento=StatusPagamento.CANCELADO,
                )
            elif pedido.status == StatusPedido.PAGO:
                await _estornar_pedido_pago(db, pedido)
        except Exception:
            falhas += 1
            logger.exception(
                "Falha ao cancelar/estornar pedido {} do evento {}",
                pedido_id,
                evento_id,
            )
            await db.rollback()

    if falhas:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Falha ao cancelar/estornar {falhas} pedido(s) do evento. "
                "O evento não foi cancelado — tente novamente para concluir."
            ),
        )


async def _estornar_pedido_pago(db: AsyncSession, pedido: Pedido) -> None:
    """Estorna um pedido pago: devolve estoque, reembolsa no gateway, cancela os
    ingressos e marca o pedido como REEMBOLSADO. Espera pedido com itens carregados.

    Retomável: usa o status ESTORNADO do pagamento como marcador de que o
    estoque já foi devolvido e o estorno já foi pedido ao gateway (commitam
    juntos) — um retry pula essa etapa e só refaz as partes idempotentes.

    Decisão (ressalva do merge ad83d78): o cupom NÃO é devolvido neste caminho.
    O cupom pertence ao próprio evento cancelado — não haverá compra futura que
    o utilize, então decrementar quantidade_usada seria inócuo. E o reembolso
    individual (webhook PAYMENT_REFUNDED) também não devolve, por design
    anti-abuso: o desconto foi consumido em uma compra concluída. Devolver
    apenas aqui criaria uma terceira semântica para a mesma operação.
    """
    pagamento = await pagamento_repo.get_by_pedido_id(db, pedido.id)
    ja_compensado = (
        pagamento is not None and pagamento.status == StatusPagamento.ESTORNADO
    )

    if not ja_compensado:
        for item in pedido.itens:
            lote = await lote_repo.get_by_id(db, item.lote_id)
            if lote is not None:
                lote_repo.decrementar_vendidas(lote, item.quantidade)

        if pagamento is not None:
            if pagamento.charge_id is not None:
                try:
                    await asaas_charges.refund_charge(charge_id=pagamento.charge_id)
                except AsaasAPIError:
                    logger.warning(
                        "Falha ao estornar cobrança {} no Asaas (evento cancelado)",
                        pagamento.charge_id,
                    )
            # Commit que também persiste a devolução de estoque acima (marcador).
            await pagamento_repo.update_status(db, pagamento, StatusPagamento.ESTORNADO)

    if pagamento is not None:
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
